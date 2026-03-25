"""
Data source services: connectors for databases, APIs, files.
"""

import csv
import io
import json
import logging
import time
from typing import Any

import pandas as pd
import requests
from django.utils import timezone
from sqlalchemy import create_engine, text

from .models import DataSource, DataConnection, QueryResult

logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass


class BaseConnector:
    """Base class for all data source connectors."""

    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.connection = data_source.connection

    def test_connection(self) -> dict:
        """Test if the connection is valid. Returns {success, message}."""
        raise NotImplementedError

    def fetch_schema(self) -> dict:
        """Fetch schema information (tables, columns, types)."""
        raise NotImplementedError

    def execute_query(self, query: str, params: dict = None) -> dict:
        """Execute a query and return results as {columns, rows, row_count}."""
        raise NotImplementedError


class PostgreSQLConnector(BaseConnector):
    """Connector for PostgreSQL databases."""

    def _get_engine(self):
        conn = self.connection
        ssl_arg = "?sslmode=require" if conn.ssl_enabled else ""
        url = (
            f"postgresql://{conn.username}:{conn.password_encrypted}"
            f"@{conn.host}:{conn.port or 5432}/{conn.database_name}{ssl_arg}"
        )
        return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)

    def test_connection(self) -> dict:
        try:
            engine = self._get_engine()
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"success": True, "message": "Connection successful."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def fetch_schema(self) -> dict:
        engine = self._get_engine()
        schema = {"tables": []}
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result]

            for table in tables:
                col_result = connection.execute(text(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_name = :table AND table_schema = 'public' "
                    "ORDER BY ordinal_position"
                ), {"table": table})
                columns = [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                    }
                    for row in col_result
                ]
                schema["tables"].append({"name": table, "columns": columns})

        return schema

    def execute_query(self, query: str, params: dict = None) -> dict:
        engine = self._get_engine()
        start_time = time.time()
        try:
            with engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                execution_time = int((time.time() - start_time) * 1000)
                return {
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "execution_time_ms": execution_time,
                }
        except Exception as e:
            raise DataFetchError(f"Query execution failed: {str(e)}")


class MySQLConnector(BaseConnector):
    """Connector for MySQL databases."""

    def _get_engine(self):
        conn = self.connection
        ssl_arg = "?ssl=true" if conn.ssl_enabled else ""
        url = (
            f"mysql+pymysql://{conn.username}:{conn.password_encrypted}"
            f"@{conn.host}:{conn.port or 3306}/{conn.database_name}{ssl_arg}"
        )
        return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)

    def test_connection(self) -> dict:
        try:
            engine = self._get_engine()
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"success": True, "message": "Connection successful."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def fetch_schema(self) -> dict:
        engine = self._get_engine()
        schema = {"tables": []}
        with engine.connect() as connection:
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]

            for table in tables:
                col_result = connection.execute(text(f"DESCRIBE `{table}`"))
                columns = [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                    }
                    for row in col_result
                ]
                schema["tables"].append({"name": table, "columns": columns})

        return schema

    def execute_query(self, query: str, params: dict = None) -> dict:
        engine = self._get_engine()
        start_time = time.time()
        try:
            with engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                execution_time = int((time.time() - start_time) * 1000)
                return {
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "execution_time_ms": execution_time,
                }
        except Exception as e:
            raise DataFetchError(f"Query execution failed: {str(e)}")


class RestAPIConnector(BaseConnector):
    """Connector for REST API endpoints."""

    def _build_headers(self) -> dict:
        conn = self.connection
        headers = dict(conn.api_headers) if conn.api_headers else {}

        if conn.auth_type == "api_key":
            headers["X-API-Key"] = conn.api_key_encrypted
        elif conn.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {conn.api_key_encrypted}"
        elif conn.auth_type == "basic":
            import base64
            credentials = base64.b64encode(
                f"{conn.username}:{conn.password_encrypted}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"

        return headers

    def test_connection(self) -> dict:
        try:
            response = requests.get(
                self.connection.api_url,
                headers=self._build_headers(),
                timeout=10,
            )
            response.raise_for_status()
            return {"success": True, "message": f"Status {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def fetch_schema(self) -> dict:
        try:
            response = requests.get(
                self.connection.api_url,
                headers=self._build_headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and data:
                columns = [
                    {"name": k, "type": type(v).__name__}
                    for k, v in data[0].items()
                ]
                return {"tables": [{"name": "api_data", "columns": columns}]}
            elif isinstance(data, dict):
                columns = [
                    {"name": k, "type": type(v).__name__}
                    for k, v in data.items()
                ]
                return {"tables": [{"name": "api_data", "columns": columns}]}

            return {"tables": []}
        except Exception as e:
            raise DataFetchError(f"Schema fetch failed: {str(e)}")

    def execute_query(self, query: str = None, params: dict = None) -> dict:
        start_time = time.time()
        try:
            url = self.connection.api_url
            if query:
                url = f"{url}/{query}" if not query.startswith("/") else f"{url}{query}"

            response = requests.get(
                url,
                headers=self._build_headers(),
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            execution_time = int((time.time() - start_time) * 1000)

            if isinstance(data, list):
                columns = list(data[0].keys()) if data else []
                return {
                    "columns": columns,
                    "rows": data,
                    "row_count": len(data),
                    "execution_time_ms": execution_time,
                }
            elif isinstance(data, dict):
                return {
                    "columns": list(data.keys()),
                    "rows": [data],
                    "row_count": 1,
                    "execution_time_ms": execution_time,
                }

            return {"columns": [], "rows": [], "row_count": 0, "execution_time_ms": execution_time}
        except Exception as e:
            raise DataFetchError(f"API request failed: {str(e)}")


class CSVConnector(BaseConnector):
    """Connector for CSV file uploads."""

    def test_connection(self) -> dict:
        if self.connection.file:
            return {"success": True, "message": "File uploaded successfully."}
        return {"success": False, "message": "No file uploaded."}

    def fetch_schema(self) -> dict:
        if not self.connection.file:
            return {"tables": []}

        try:
            self.connection.file.seek(0)
            df = pd.read_csv(self.connection.file, nrows=5)
            columns = [
                {"name": col, "type": str(dtype)}
                for col, dtype in df.dtypes.items()
            ]
            return {"tables": [{"name": "csv_data", "columns": columns}]}
        except Exception as e:
            raise DataFetchError(f"Schema fetch failed: {str(e)}")

    def execute_query(self, query: str = None, params: dict = None) -> dict:
        start_time = time.time()
        try:
            self.connection.file.seek(0)
            df = pd.read_csv(self.connection.file)

            if query:
                df = df.query(query)

            columns = list(df.columns)
            rows = df.to_dict(orient="records")
            execution_time = int((time.time() - start_time) * 1000)

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time,
            }
        except Exception as e:
            raise DataFetchError(f"CSV query failed: {str(e)}")


class ExcelConnector(BaseConnector):
    """Connector for Excel file uploads."""

    def test_connection(self) -> dict:
        if self.connection.file:
            return {"success": True, "message": "File uploaded successfully."}
        return {"success": False, "message": "No file uploaded."}

    def fetch_schema(self) -> dict:
        if not self.connection.file:
            return {"tables": []}

        try:
            self.connection.file.seek(0)
            xl = pd.ExcelFile(self.connection.file)
            tables = []
            for sheet in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet, nrows=5)
                columns = [
                    {"name": col, "type": str(dtype)}
                    for col, dtype in df.dtypes.items()
                ]
                tables.append({"name": sheet, "columns": columns})
            return {"tables": tables}
        except Exception as e:
            raise DataFetchError(f"Schema fetch failed: {str(e)}")

    def execute_query(self, query: str = None, params: dict = None) -> dict:
        start_time = time.time()
        try:
            self.connection.file.seek(0)
            sheet_name = params.get("sheet", 0) if params else 0
            df = pd.read_excel(self.connection.file, sheet_name=sheet_name)

            if query:
                df = df.query(query)

            columns = list(df.columns)
            rows = df.to_dict(orient="records")
            execution_time = int((time.time() - start_time) * 1000)

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time,
            }
        except Exception as e:
            raise DataFetchError(f"Excel query failed: {str(e)}")


CONNECTOR_MAP = {
    "postgresql": PostgreSQLConnector,
    "mysql": MySQLConnector,
    "rest_api": RestAPIConnector,
    "csv": CSVConnector,
    "excel": ExcelConnector,
}


def get_connector(data_source: DataSource) -> BaseConnector:
    """Factory function to get the appropriate connector for a data source."""
    connector_class = CONNECTOR_MAP.get(data_source.source_type)
    if not connector_class:
        raise DataFetchError(
            f"Unsupported source type: {data_source.source_type}"
        )
    return connector_class(data_source)


def test_data_source_connection(data_source: DataSource) -> dict:
    """Test connection for a data source and update status."""
    connector = get_connector(data_source)
    result = connector.test_connection()

    data_source.status = "active" if result["success"] else "error"
    data_source.save(update_fields=["status"])

    return result


def fetch_data_source_schema(data_source: DataSource) -> dict:
    """Fetch and cache schema for a data source."""
    connector = get_connector(data_source)
    schema = connector.fetch_schema()

    data_source.schema_cache = schema
    data_source.last_synced_at = timezone.now()
    data_source.save(update_fields=["schema_cache", "last_synced_at"])

    return schema


def execute_data_query(data_source: DataSource, query: str, params: dict = None, user=None) -> dict:
    """Execute a query against a data source and store the result."""
    connector = get_connector(data_source)
    result = connector.execute_query(query, params)

    QueryResult.objects.create(
        query=None if not hasattr(data_source, '_current_query') else data_source._current_query,
        parameters_used=params or {},
        result_data=result,
        row_count=result.get("row_count", 0),
        execution_time_ms=result.get("execution_time_ms", 0),
        executed_by=user,
    ) if hasattr(data_source, '_current_query') and data_source._current_query else None

    return result
