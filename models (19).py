"""
Dashboard serializers for CRUD operations, widgets, layouts, and sharing.
"""

import secrets

from rest_framework import serializers

from .models import Dashboard, Widget, WidgetLayout, DashboardShare


class WidgetSerializer(serializers.ModelSerializer):
    """Serializer for dashboard widgets."""

    widget_type_display = serializers.CharField(
        source="get_widget_type_display", read_only=True
    )

    class Meta:
        model = Widget
        fields = [
            "id", "dashboard", "title", "widget_type", "widget_type_display",
            "data_source", "query_config", "visualization_config",
            "position_x", "position_y", "width", "height",
            "cache_duration_seconds", "cached_data", "cached_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "cached_data", "cached_at", "created_at", "updated_at"]


class WidgetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating widgets."""

    class Meta:
        model = Widget
        fields = [
            "title", "widget_type", "data_source", "query_config",
            "visualization_config", "position_x", "position_y",
            "width", "height", "cache_duration_seconds",
        ]


class WidgetLayoutSerializer(serializers.ModelSerializer):
    """Serializer for widget layout configurations."""

    class Meta:
        model = WidgetLayout
        fields = ["id", "dashboard", "breakpoint", "layout_data", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class DashboardListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dashboard listings."""

    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    widget_count = serializers.ReadOnlyField()

    class Meta:
        model = Dashboard
        fields = [
            "id", "title", "description", "owner", "owner_name",
            "is_public", "is_template", "tags", "widget_count",
            "auto_refresh_seconds", "thumbnail",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class DashboardDetailSerializer(serializers.ModelSerializer):
    """Full serializer for dashboard detail view with widgets."""

    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    widgets = WidgetSerializer(many=True, read_only=True)
    layouts = WidgetLayoutSerializer(many=True, read_only=True)
    widget_count = serializers.ReadOnlyField()

    class Meta:
        model = Dashboard
        fields = [
            "id", "title", "description", "owner", "owner_name",
            "organization", "is_public", "is_template", "tags",
            "settings", "auto_refresh_seconds", "thumbnail",
            "widgets", "layouts", "widget_count",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "owner", "organization", "created_at", "updated_at",
        ]


class DashboardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating dashboards."""

    class Meta:
        model = Dashboard
        fields = [
            "title", "description", "is_public", "is_template",
            "tags", "settings", "auto_refresh_seconds",
        ]


class DashboardShareSerializer(serializers.ModelSerializer):
    """Serializer for dashboard sharing."""

    shared_with_user_email = serializers.CharField(
        source="shared_with_user.email", read_only=True
    )
    shared_with_team_name = serializers.CharField(
        source="shared_with_team.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )

    class Meta:
        model = DashboardShare
        fields = [
            "id", "dashboard", "shared_with_user", "shared_with_user_email",
            "shared_with_team", "shared_with_team_name", "permission",
            "share_token", "expires_at", "created_by", "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "share_token", "created_by", "created_at"]


class DashboardShareCreateSerializer(serializers.Serializer):
    """Serializer for creating dashboard shares."""

    shared_with_user = serializers.UUIDField(required=False, allow_null=True)
    shared_with_team = serializers.UUIDField(required=False, allow_null=True)
    permission = serializers.ChoiceField(
        choices=DashboardShare.PERMISSION_CHOICES, default="view"
    )
    create_public_link = serializers.BooleanField(default=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        has_user = attrs.get("shared_with_user")
        has_team = attrs.get("shared_with_team")
        is_public = attrs.get("create_public_link", False)

        if not any([has_user, has_team, is_public]):
            raise serializers.ValidationError(
                "Must specify shared_with_user, shared_with_team, or create_public_link."
            )
        return attrs

    def create(self, validated_data):
        create_public = validated_data.pop("create_public_link", False)
        share_token = None
        if create_public:
            share_token = secrets.token_urlsafe(48)

        share = DashboardShare.objects.create(
            share_token=share_token,
            **validated_data,
        )
        return share


class BulkLayoutUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating widget positions."""

    layouts = serializers.ListField(
        child=serializers.DictField(),
        help_text="Array of {widget_id, x, y, w, h} objects.",
    )
