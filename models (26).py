"""
DataSource serializers for CRUD, connections, queries, and results.
"""

from rest_framework import serializers

from .models import DataSource, DataConnection, DataQuery, QueryResult


class DataConnectionSerializer(serializers.ModelSerializer):
    """Serializer for data connections (write sensitive fields only)."""

    class Meta:
        model = DataConnection
        fields = [
            "id", "data_source", "host", "port", "database_name",
            "username", "password_encrypted", "ssl_enabled",
            "api_url", "api_key_encrypted", "api_headers", "auth_type",
            "file", "spreadsheet_id", "sheet_name", "extra_config",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "password_encrypted": {"write_only": True},
            "api_key_encrypted": {"write_only": True},
        }


class DataConnectionReadSerializer(serializers.ModelSerializer):
    """Read serializer for data connections (masks sensitive fields)."""

    has_password = serializers.SerializerMethodField()
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = DataConnection
        fields = [
            "id", "data_source", "host", "port", "database_name",
            "username", "has_password", "ssl_enabled",
            "api_url", "has_api_key", "api_headers", "auth_type",
            "file", "spreadsheet_id", "sheet_name", "extra_config",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_has_password(self, obj):
        return bool(obj.password_encrypted)

    def get_has_api_key(self, obj):
        return bool(obj.api_key_encrypted)


class DataSourceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for data source listings."""

    source_type_display = serializers.CharField(
        source="get_source_type_display", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )

    class Meta:
        model = DataSource
        fields = [
            "id", "name", "description", "source_type", "source_type_display",
            "status", "last_synced_at", "sync_interval_minutes",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "created_by", "created_at", "updated_at"]


class DataSourceDetailSerializer(serializers.ModelSerializer):
    """Full serializer for data source detail view."""

    source_type_display = serializers.CharField(
        source="get_source_type_display", read_only=True
    )
    connection = DataConnectionReadSerializer(read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    query_count = serializers.SerializerMethodField()

    class Meta:
        model = DataSource
        fields = [
            "id", "name", "description", "source_type", "source_type_display",
            "organization", "status", "last_synced_at", "sync_interval_minutes",
            "schema_cache", "connection", "query_count",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "organization", "status", "last_synced_at",
            "schema_cache", "created_by", "created_at", "updated_at",
        ]

    def get_query_count(self, obj):
        return obj.queries.count()


class DataSourceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating data sources."""

    connection = DataConnectionSerializer(required=False)

    class Meta:
        model = DataSource
        fields = [
            "name", "description", "source_type",
            "sync_interval_minutes", "connection",
        ]

    def create(self, validated_data):
        connection_data = validated_data.pop("connection", None)
        data_source = DataSource.objects.create(**validated_data)

        if connection_data:
            DataConnection.objects.create(
                data_source=data_source, **connection_data
            )

        return data_source


class DataQuerySerializer(serializers.ModelSerializer):
    """Serializer for data queries."""

    data_source_name = serializers.CharField(
        source="data_source.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )

    class Meta:
        model = DataQuery
        fields = [
            "id", "name", "description", "data_source", "data_source_name",
            "raw_sql", "query_config", "parameters",
            "cache_duration_seconds", "is_public",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class DataQueryExecuteSerializer(serializers.Serializer):
    """Serializer for executing a query."""

    query = serializers.CharField(required=False, allow_blank=True)
    parameters = serializers.DictField(required=False, default=dict)
    limit = serializers.IntegerField(required=False, default=1000, min_value=1, max_value=10000)


class QueryResultSerializer(serializers.ModelSerializer):
    """Serializer for query results."""

    class Meta:
        model = QueryResult
        fields = [
            "id", "query", "parameters_used", "result_data",
            "row_count", "execution_time_ms", "error_message",
            "executed_by", "executed_at", "expires_at",
        ]
        read_only_fields = [
            "id", "result_data", "row_count", "execution_time_ms",
            "error_message", "executed_by", "executed_at",
        ]
