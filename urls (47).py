"""
Visualization models: ChartConfig, Visualization.
"""

import uuid

from django.conf import settings
from django.db import models


class ChartConfig(models.Model):
    """
    Reusable chart configuration template defining chart appearance and behavior.
    """

    CHART_TYPES = [
        ("line", "Line Chart"),
        ("bar", "Bar Chart"),
        ("horizontal_bar", "Horizontal Bar"),
        ("stacked_bar", "Stacked Bar"),
        ("pie", "Pie Chart"),
        ("donut", "Donut Chart"),
        ("area", "Area Chart"),
        ("scatter", "Scatter Plot"),
        ("bubble", "Bubble Chart"),
        ("radar", "Radar Chart"),
        ("treemap", "Treemap"),
        ("gauge", "Gauge"),
        ("heatmap", "Heatmap"),
        ("funnel", "Funnel Chart"),
        ("waterfall", "Waterfall Chart"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    chart_type = models.CharField(max_length=30, choices=CHART_TYPES)
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chart_configs",
    )
    is_global = models.BooleanField(
        default=False,
        help_text="Global configs are available to all organizations.",
    )
    # Appearance configuration
    color_palette = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of hex colors, e.g. ["#1f77b4", "#ff7f0e"].',
    )
    theme = models.JSONField(
        default=dict,
        blank=True,
        help_text="Theme overrides: background, grid, fonts, etc.",
    )
    # Axis configuration
    x_axis = models.JSONField(
        default=dict,
        blank=True,
        help_text="X-axis config: label, format, scale, ticks.",
    )
    y_axis = models.JSONField(
        default=dict,
        blank=True,
        help_text="Y-axis config: label, format, scale, ticks.",
    )
    secondary_y_axis = models.JSONField(
        default=dict,
        blank=True,
        help_text="Secondary Y-axis for dual-axis charts.",
    )
    # Legend
    legend = models.JSONField(
        default=dict,
        blank=True,
        help_text="Legend config: position, show, alignment.",
    )
    # Tooltip
    tooltip = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tooltip config: format, custom template.",
    )
    # Annotations
    annotations = models.JSONField(
        default=list,
        blank=True,
        help_text="Reference lines, bands, labels.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="chart_configs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"


class Visualization(models.Model):
    """
    A saved visualization instance combining data query + chart config.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="visualizations",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="visualizations",
    )
    # Data source link
    data_source = models.ForeignKey(
        "datasources.DataSource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visualizations",
    )
    data_query = models.ForeignKey(
        "datasources.DataQuery",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visualizations",
    )
    # Chart configuration
    chart_config = models.ForeignKey(
        ChartConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visualizations",
    )
    # Inline config overrides
    config_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text="Inline overrides that merge on top of chart_config.",
    )
    # Data mapping
    data_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Maps query columns to chart axes/series: {x, y, group_by, size, color}.",
    )
    # Filters
    filters = models.JSONField(
        default=list,
        blank=True,
        help_text="Client-side filters applied to data.",
    )
    # Sort
    sort_by = models.CharField(max_length=100, blank=True, default="")
    sort_order = models.CharField(
        max_length=4,
        choices=[("asc", "Ascending"), ("desc", "Descending")],
        default="asc",
    )
    # Caching
    cache_duration_seconds = models.PositiveIntegerField(default=300)
    is_public = models.BooleanField(default=False)
    # Thumbnail for previews
    thumbnail = models.ImageField(
        upload_to="viz_thumbnails/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title
