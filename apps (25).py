"""
DataSource models: DataSource, DataConnection, DataQuery, QueryResult.
"""

import uuid

from django.conf import settings
from django.db import models


class DataSource(models.Model):
    """
    Represents a data source connection (database, API, file, etc.).
    """

    SOURCE_TYPES = [
        ("postgresql", "PostgreSQL"),
        ("mysql", "MySQL"),
        ("rest_api", "REST API"),
        ("csv", "CSV Upload"),
        ("excel", "Excel Upload"),
        ("google_sheets", "Google Sheets"),
        ("json", "JSON Endpoint"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("error", "Error"),
        ("testing", "Testing"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPES)
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="datasources",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="datasources",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="inactive"
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_interval_minutes = models.PositiveIntegerField(
        default=0, help_text="Auto-sync interval in minutes. 0 = manual only."
    )
    schema_cache = models.JSONField(
        null=True, blank=True,
        help_text="Cached schema information (tables, columns, types).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class DataConnection(models.Model):
    """
    Stores connection credentials and configuration for a data source.
    Credentials are stored encrypted at the application level.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_source = models.OneToOneField(
        DataSource, on_delete=models.CASCADE, related_name="connection"
    )
    # Database connections
    host = models.CharField(max_length=255, blank=True, default="")
    port = models.PositiveIntegerField(null=True, blank=True)
    database_name = models.CharField(max_length=255, blank=True, default="")
    username = models.CharField(max_length=255, blank=True, default="")
    password_encrypted = models.TextField(
        blank=True, default="",
        help_text="Encrypted password for database connections.",
    )
    ssl_enabled = models.BooleanField(default=False)
    # API connections
    api_url = models.URLField(blank=True, default="")
    api_key_encrypted = models.TextField(blank=True, default="")
    api_headers = models.JSONField(
        default=dict, blank=True,
        help_text="Custom HTTP headers for API requests.",
    )
    auth_type = models.CharField(
        max_length=20,
        choices=[
            ("none", "None"),
            ("api_key", "API Key"),
            ("bearer", "Bearer Token"),
            ("basic", "Basic Auth"),
            ("oauth2", "OAuth 2.0"),
        ],
        default="none",
    )
    # File-based sources
    file = models.FileField(
        upload_to="datasource_files/", blank=True, null=True
    )
    # Google Sheets
    spreadsheet_id = models.CharField(max_length=255, blank=True, default="")
    sheet_name = models.CharField(max_length=255, blank=True, default="")
    # Connection extras
    extra_config = models.JSONField(
        default=dict, blank=True,
        help_text="Additional connection parameters.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Connection for {self.data_source.name}"


class DataQuery(models.Model):
    """
    A saved query against a data source.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    data_source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name="queries"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="data_queries",
    )
    # Query definition
    raw_sql = models.TextField(
        blank=True, default="",
        help_text="Raw SQL query (for database sources).",
    )
    query_config = models.JSONField(
        default=dict, blank=True,
        help_text="Visual query builder configuration.",
    )
    # Parameters
    parameters = models.JSONField(
        default=list, blank=True,
        help_text="Query parameters [{name, type, default_value}].",
    )
    # Caching
    cache_duration_seconds = models.PositiveIntegerField(default=300)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "Data queries"

    def __str__(self):
        return f"{self.name} ({self.data_source.name})"


class QueryResult(models.Model):
    """
    Cached result from executing a data query.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(
        DataQuery, on_delete=models.CASCADE, related_name="results"
    )
    parameters_used = models.JSONField(
        default=dict, blank=True,
        help_text="Parameter values used for this execution.",
    )
    result_data = models.JSONField(
        help_text="Query result as JSON (columns + rows)."
    )
    row_count = models.PositiveIntegerField(default=0)
    execution_time_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="query_results",
    )
    executed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-executed_at"]

    def __str__(self):
        return f"Result for {self.query.name} at {self.executed_at}"
