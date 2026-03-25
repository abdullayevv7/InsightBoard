"""
DataSource views: CRUD, connection testing, schema fetch, query execution.
"""

import logging

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DataSource, DataConnection, DataQuery, QueryResult
from .serializers import (
    DataSourceListSerializer,
    DataSourceDetailSerializer,
    DataSourceCreateSerializer,
    DataConnectionSerializer,
    DataQuerySerializer,
    DataQueryExecuteSerializer,
    QueryResultSerializer,
)
from .services import (
    test_data_source_connection,
    fetch_data_source_schema,
    get_connector,
    DataFetchError,
)

logger = logging.getLogger(__name__)


class DataSourceViewSet(viewsets.ModelViewSet):
    """Data source CRUD with connection testing and schema fetching."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return DataSourceListSerializer
        if self.action == "create":
            return DataSourceCreateSerializer
        return DataSourceDetailSerializer

    def get_queryset(self):
        return DataSource.objects.filter(
            organization=self.request.user.organization
        ).select_related("created_by", "connection")

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization,
        )

    @action(detail=True, methods=["post"], url_path="test-connection")
    def test_connection(self, request, pk=None):
        """Test the connection to a data source."""
        data_source = self.get_object()
        try:
            result = test_data_source_connection(data_source)
            return Response(result)
        except DataFetchError as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], url_path="fetch-schema")
    def fetch_schema(self, request, pk=None):
        """Fetch schema from a data source and cache it."""
        data_source = self.get_object()
        try:
            schema = fetch_data_source_schema(data_source)
            return Response({"schema": schema})
        except DataFetchError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def query(self, request, pk=None):
        """Execute a query against a data source."""
        data_source = self.get_object()
        serializer = DataQueryExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_text = serializer.validated_data.get("query", "")
        params = serializer.validated_data.get("parameters", {})
        limit = serializer.validated_data.get("limit", 1000)

        try:
            connector = get_connector(data_source)

            if data_source.source_type in ("postgresql", "mysql") and query_text:
                if limit and "LIMIT" not in query_text.upper():
                    query_text = f"{query_text.rstrip(';')} LIMIT {limit}"

            result = connector.execute_query(query_text, params)

            QueryResult.objects.create(
                query=None,
                parameters_used=params,
                result_data=result,
                row_count=result.get("row_count", 0),
                execution_time_ms=result.get("execution_time_ms", 0),
                executed_by=request.user,
            )

            return Response(result)
        except DataFetchError as e:
            logger.error(
                "Query execution failed for data source %s: %s",
                data_source.id, str(e),
            )
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["put"], url_path="update-connection")
    def update_connection(self, request, pk=None):
        """Update connection details for a data source."""
        data_source = self.get_object()
        connection, created = DataConnection.objects.get_or_create(
            data_source=data_source
        )
        serializer = DataConnectionSerializer(
            connection, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DataQueryViewSet(viewsets.ModelViewSet):
    """Saved data queries viewset."""

    serializer_class = DataQuerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DataQuery.objects.filter(
            data_source__organization=self.request.user.organization
        ).select_related("data_source", "created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """Execute a saved query."""
        data_query = self.get_object()
        exec_serializer = DataQueryExecuteSerializer(data=request.data)
        exec_serializer.is_valid(raise_exception=True)

        params = exec_serializer.validated_data.get("parameters", {})
        query_text = data_query.raw_sql

        for param in data_query.parameters:
            name = param.get("name", "")
            if name in params:
                query_text = query_text.replace(f":{name}", str(params[name]))

        try:
            connector = get_connector(data_query.data_source)
            result = connector.execute_query(query_text, params)

            query_result = QueryResult.objects.create(
                query=data_query,
                parameters_used=params,
                result_data=result,
                row_count=result.get("row_count", 0),
                execution_time_ms=result.get("execution_time_ms", 0),
                executed_by=request.user,
            )

            return Response(QueryResultSerializer(query_result).data)
        except DataFetchError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        """List execution results for a query."""
        data_query = self.get_object()
        results = QueryResult.objects.filter(query=data_query)[:20]
        serializer = QueryResultSerializer(results, many=True)
        return Response(serializer.data)


class QueryResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for query results."""

    serializer_class = QueryResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return QueryResult.objects.filter(
            executed_by=self.request.user
        ).select_related("query")
