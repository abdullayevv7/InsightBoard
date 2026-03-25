"""
Dashboard models: Dashboard, Widget, WidgetLayout, DashboardShare.
"""

import uuid

from django.conf import settings
from django.db import models


class Dashboard(models.Model):
    """
    A dashboard containing a collection of widgets arranged in a grid layout.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_dashboards",
    )
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="dashboards",
    )
    is_public = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)
    thumbnail = models.ImageField(
        upload_to="dashboard_thumbnails/", blank=True, null=True
    )
    tags = models.JSONField(default=list, blank=True)
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dashboard-level settings (theme, refresh interval, etc.)",
    )
    auto_refresh_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def widget_count(self):
        return self.widgets.count()

    def clone(self, new_owner, new_title=None):
        """Create a copy of this dashboard with all its widgets."""
        new_dashboard = Dashboard.objects.create(
            title=new_title or f"Copy of {self.title}",
            description=self.description,
            owner=new_owner,
            organization=new_owner.organization,
            tags=self.tags.copy(),
            settings=self.settings.copy(),
            auto_refresh_seconds=self.auto_refresh_seconds,
        )

        for widget in self.widgets.all():
            Widget.objects.create(
                dashboard=new_dashboard,
                title=widget.title,
                widget_type=widget.widget_type,
                data_source=widget.data_source,
                query_config=widget.query_config.copy() if widget.query_config else {},
                visualization_config=widget.visualization_config.copy() if widget.visualization_config else {},
                position_x=widget.position_x,
                position_y=widget.position_y,
                width=widget.width,
                height=widget.height,
            )

        return new_dashboard


class Widget(models.Model):
    """
    A single widget on a dashboard (chart, metric card, table, map, etc.).
    """

    WIDGET_TYPES = [
        ("line_chart", "Line Chart"),
        ("bar_chart", "Bar Chart"),
        ("pie_chart", "Pie Chart"),
        ("area_chart", "Area Chart"),
        ("scatter_plot", "Scatter Plot"),
        ("metric_card", "Metric Card"),
        ("data_table", "Data Table"),
        ("map", "Map"),
        ("gauge", "Gauge"),
        ("heatmap", "Heatmap"),
        ("text", "Text / Markdown"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="widgets"
    )
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=30, choices=WIDGET_TYPES)
    data_source = models.ForeignKey(
        "datasources.DataSource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="widgets",
    )
    query_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Query parameters: table, columns, filters, aggregations, etc.",
    )
    visualization_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Visual config: colors, labels, axes, legend, etc.",
    )
    # Grid position (react-grid-layout compatible)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=4)
    height = models.IntegerField(default=3)
    # Caching
    cache_duration_seconds = models.PositiveIntegerField(default=300)
    cached_data = models.JSONField(null=True, blank=True)
    cached_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position_y", "position_x"]

    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"


class WidgetLayout(models.Model):
    """
    Stores saved layout configurations for responsive breakpoints.
    """

    BREAKPOINTS = [
        ("lg", "Large (1200px+)"),
        ("md", "Medium (996px+)"),
        ("sm", "Small (768px+)"),
        ("xs", "Extra Small (480px+)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="layouts"
    )
    breakpoint = models.CharField(max_length=5, choices=BREAKPOINTS)
    layout_data = models.JSONField(
        help_text="Array of {widget_id, x, y, w, h} objects for this breakpoint."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["dashboard", "breakpoint"]

    def __str__(self):
        return f"{self.dashboard.title} - {self.breakpoint}"


class DashboardShare(models.Model):
    """
    Sharing configuration for a dashboard with users, teams, or via public link.
    """

    PERMISSION_CHOICES = [
        ("view", "View Only"),
        ("edit", "Can Edit"),
        ("admin", "Full Access"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="shares"
    )
    shared_with_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shared_dashboards",
    )
    shared_with_team = models.ForeignKey(
        "accounts.Team",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shared_dashboards",
    )
    permission = models.CharField(
        max_length=10, choices=PERMISSION_CHOICES, default="view"
    )
    share_token = models.CharField(
        max_length=64, unique=True, null=True, blank=True,
        help_text="Token for public link sharing."
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_shares",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.shared_with_user or self.shared_with_team or "public link"
        return f"{self.dashboard.title} shared with {target}"
