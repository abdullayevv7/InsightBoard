"""
Alert admin configuration.
"""

from django.contrib import admin

from .models import AlertRule, AlertCondition, AlertHistory


class AlertConditionInline(admin.TabularInline):
    model = AlertCondition
    extra = 0
    fields = ["operator", "threshold_value", "comparison_window_minutes", "logic_operator", "order"]
    readonly_fields = ["id"]


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = [
        "name", "severity", "status", "data_source",
        "metric_field", "evaluation_interval_minutes",
        "last_triggered_at", "last_evaluated_at", "last_value",
        "created_by",
    ]
    list_filter = ["severity", "status", "organization"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "id", "current_failure_count", "last_triggered_at",
        "last_evaluated_at", "last_value", "created_at", "updated_at",
    ]
    inlines = [AlertConditionInline]


@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "alert_rule", "event_type", "metric_value", "threshold_value",
        "notification_sent", "acknowledged_by", "created_at",
    ]
    list_filter = ["event_type", "notification_sent"]
    search_fields = ["alert_rule__name", "message"]
    readonly_fields = [
        "id", "alert_rule", "event_type", "metric_value", "threshold_value",
        "message", "notification_sent", "notification_channels_used",
        "created_at",
    ]
