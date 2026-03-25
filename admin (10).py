"""
Alert serializers for rules, conditions, and history.
"""

from rest_framework import serializers

from .models import AlertRule, AlertCondition, AlertHistory


class AlertConditionSerializer(serializers.ModelSerializer):
    """Serializer for alert conditions."""

    operator_display = serializers.CharField(
        source="get_operator_display", read_only=True
    )

    class Meta:
        model = AlertCondition
        fields = [
            "id", "alert_rule", "operator", "operator_display",
            "threshold_value", "comparison_window_minutes",
            "logic_operator", "order",
        ]
        read_only_fields = ["id"]


class AlertConditionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert conditions inline."""

    class Meta:
        model = AlertCondition
        fields = [
            "operator", "threshold_value", "comparison_window_minutes",
            "logic_operator", "order",
        ]


class AlertRuleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for alert rule listings."""

    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    data_source_name = serializers.CharField(
        source="data_source.name", read_only=True
    )
    condition_count = serializers.SerializerMethodField()
    is_muted = serializers.ReadOnlyField()

    class Meta:
        model = AlertRule
        fields = [
            "id", "name", "description", "severity", "severity_display",
            "status", "status_display", "data_source", "data_source_name",
            "metric_field", "evaluation_interval_minutes",
            "last_triggered_at", "last_evaluated_at", "last_value",
            "is_muted", "condition_count", "tags",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "last_triggered_at", "last_evaluated_at",
            "last_value", "created_by", "created_at", "updated_at",
        ]

    def get_condition_count(self, obj):
        return obj.conditions.count()


class AlertRuleDetailSerializer(serializers.ModelSerializer):
    """Full serializer for alert rule detail view."""

    conditions = AlertConditionSerializer(many=True, read_only=True)
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    recent_history = serializers.SerializerMethodField()
    is_muted = serializers.ReadOnlyField()

    class Meta:
        model = AlertRule
        fields = [
            "id", "name", "description", "organization",
            "severity", "severity_display", "status", "status_display",
            "data_source", "metric_query", "metric_field",
            "evaluation_interval_minutes", "consecutive_failures",
            "current_failure_count", "notification_channels",
            "notify_on_resolve", "cooldown_minutes",
            "last_triggered_at", "last_evaluated_at", "last_value",
            "muted_until", "is_muted", "tags", "conditions", "recent_history",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "organization", "status", "current_failure_count",
            "last_triggered_at", "last_evaluated_at", "last_value",
            "created_by", "created_at", "updated_at",
        ]

    def get_recent_history(self, obj):
        history = obj.history.all()[:10]
        return AlertHistorySerializer(history, many=True).data


class AlertRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert rules with inline conditions."""

    conditions = AlertConditionCreateSerializer(many=True, required=False)

    class Meta:
        model = AlertRule
        fields = [
            "name", "description", "severity", "data_source",
            "metric_query", "metric_field",
            "evaluation_interval_minutes", "consecutive_failures",
            "notification_channels", "notify_on_resolve",
            "cooldown_minutes", "tags", "conditions",
        ]

    def create(self, validated_data):
        conditions_data = validated_data.pop("conditions", [])
        alert_rule = AlertRule.objects.create(**validated_data)

        for condition_data in conditions_data:
            AlertCondition.objects.create(
                alert_rule=alert_rule, **condition_data
            )

        return alert_rule


class AlertHistorySerializer(serializers.ModelSerializer):
    """Serializer for alert history records."""

    event_type_display = serializers.CharField(
        source="get_event_type_display", read_only=True
    )
    alert_name = serializers.CharField(
        source="alert_rule.name", read_only=True
    )
    acknowledged_by_name = serializers.CharField(
        source="acknowledged_by.full_name", read_only=True, allow_null=True
    )

    class Meta:
        model = AlertHistory
        fields = [
            "id", "alert_rule", "alert_name", "event_type",
            "event_type_display", "metric_value", "threshold_value",
            "message", "notification_sent", "notification_channels_used",
            "acknowledged_by", "acknowledged_by_name",
            "acknowledged_at", "resolved_at", "created_at",
        ]
        read_only_fields = [
            "id", "notification_sent", "notification_channels_used",
            "created_at",
        ]


class AlertMuteSerializer(serializers.Serializer):
    """Serializer for muting an alert."""

    muted_until = serializers.DateTimeField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
