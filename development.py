"""
Visualization admin configuration.
"""

from django.contrib import admin

from .models import ChartConfig, Visualization


@admin.register(ChartConfig)
class ChartConfigAdmin(admin.ModelAdmin):
    list_display = [
        "name", "chart_type", "organization", "is_global",
        "created_by", "created_at",
    ]
    list_filter = ["chart_type", "is_global", "organization"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Visualization)
class VisualizationAdmin(admin.ModelAdmin):
    list_display = [
        "title", "organization", "data_source", "chart_config",
        "is_public", "created_by", "created_at",
    ]
    list_filter = ["is_public", "organization"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
