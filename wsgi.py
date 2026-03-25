"""
Visualization serializers.
"""

from rest_framework import serializers

from .models import ChartConfig, Visualization


class ChartConfigSerializer(serializers.ModelSerializer):
    """Serializer for chart configurations."""

    chart_type_display = serializers.CharField(
        source="get_chart_type_display", read_only=True
    )

    class Meta:
        model = ChartConfig
        fields = [
            "id", "name", "chart_type", "chart_type_display",
            "organization", "is_global", "color_palette", "theme",
            "x_axis", "y_axis", "secondary_y_axis",
            "legend", "tooltip", "annotations",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ChartConfigCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chart configurations."""

    class Meta:
        model = ChartConfig
        fields = [
            "name", "chart_type", "is_global", "color_palette", "theme",
            "x_axis", "y_axis", "secondary_y_axis",
            "legend", "tooltip", "annotations",
        ]


class VisualizationListSerializer(serializers.ModelSerializer):
    """Lightweight visualization serializer for listings."""

    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    data_source_name = serializers.CharField(
        source="data_source.name", read_only=True
    )

    class Meta:
        model = Visualization
        fields = [
            "id", "title", "description", "data_source", "data_source_name",
            "chart_config", "is_public", "thumbnail",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class VisualizationDetailSerializer(serializers.ModelSerializer):
    """Full visualization serializer with all configuration."""

    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    chart_config_detail = ChartConfigSerializer(
        source="chart_config", read_only=True
    )

    class Meta:
        model = Visualization
        fields = [
            "id", "title", "description", "organization",
            "data_source", "data_query", "chart_config",
            "chart_config_detail", "config_overrides",
            "data_mapping", "filters", "sort_by", "sort_order",
            "cache_duration_seconds", "is_public", "thumbnail",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "organization", "created_by", "created_at", "updated_at",
        ]


class VisualizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating visualizations."""

    class Meta:
        model = Visualization
        fields = [
            "title", "description", "data_source", "data_query",
            "chart_config", "config_overrides", "data_mapping",
            "filters", "sort_by", "sort_order",
            "cache_duration_seconds", "is_public",
        ]
