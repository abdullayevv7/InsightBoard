"""
DataSource admin configuration.
"""

from django.contrib import admin

from .models import DataSource, DataConnection, DataQuery, QueryResult


class DataConnectionInline(admin.StackedInline):
    model = DataConnection
    extra = 0
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Database", {
            "fields": ("host", "port", "database_name", "username", "ssl_enabled"),
        }),
        ("API", {
            "fields": ("api_url", "auth_type", "api_headers"),
            "classes": ("collapse",),
        }),
        ("File", {
            "fields": ("file",),
            "classes": ("collapse",),
        }),
        ("Google Sheets", {
            "fields": ("spreadsheet_id", "sheet_name"),
            "classes": ("collapse",),
        }),
        ("Extra", {
            "fields": ("extra_config",),
            "classes": ("collapse",),
        }),
    )


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = [
        "name", "source_type", "organization", "status",
        "last_synced_at", "created_by", "created_at",
    ]
    list_filter = ["source_type", "status", "organization"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "schema_cache", "last_synced_at", "created_at", "updated_at"]
    inlines = [DataConnectionInline]


@admin.register(DataQuery)
class DataQueryAdmin(admin.ModelAdmin):
    list_display = [
        "name", "data_source", "created_by", "is_public",
        "cache_duration_seconds", "created_at",
    ]
    list_filter = ["is_public", "data_source"]
    search_fields = ["name", "description", "raw_sql"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(QueryResult)
class QueryResultAdmin(admin.ModelAdmin):
    list_display = [
        "query", "row_count", "execution_time_ms",
        "executed_by", "executed_at",
    ]
    list_filter = ["executed_at"]
    readonly_fields = [
        "id", "query", "result_data", "row_count",
        "execution_time_ms", "error_message", "executed_at",
    ]
