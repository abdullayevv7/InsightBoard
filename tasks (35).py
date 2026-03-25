"""
Notification serializers.
"""

from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id", "recipient", "notification_type", "notification_type_display",
            "priority", "priority_display", "title", "message",
            "action_url", "source_type", "source_id",
            "is_read", "read_at", "created_at",
        ]
        read_only_fields = [
            "id", "recipient", "notification_type", "priority",
            "title", "message", "action_url", "source_type", "source_id",
            "email_sent", "created_at",
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences."""

    class Meta:
        model = NotificationPreference
        fields = [
            "id", "user", "in_app_enabled", "email_enabled",
            "email_alert_triggered", "email_alert_resolved",
            "email_dashboard_shared", "email_report_ready",
            "email_report_failed", "email_team_invite",
            "email_datasource_error", "email_digest",
            "quiet_hours_start", "quiet_hours_end",
            "quiet_hours_timezone", "updated_at",
        ]
        read_only_fields = ["id", "user", "updated_at"]
