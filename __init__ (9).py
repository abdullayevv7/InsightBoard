"""
Alert models: AlertRule, AlertCondition, AlertHistory for metric-based alerting.
"""

import uuid

from django.conf import settings
from django.db import models


class AlertRule(models.Model):
    """
    Defines an alert rule that monitors a metric and triggers notifications
    when conditions are met.
    """

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
        ("emergency", "Emergency"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("triggered", "Triggered"),
        ("resolved", "Resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="alert_rules",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alert_rules",
    )
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default="warning"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active"
    )
    # Data source linkage
    data_source = models.ForeignKey(
        "datasources.DataSource",
        on_delete=models.CASCADE,
        related_name="alert_rules",
    )
    # Metric definition
    metric_query = models.TextField(
        help_text="SQL query or API path that returns the metric value."
    )
    metric_field = models.CharField(
        max_length=100,
        help_text="Column name or JSON path in the query result to monitor.",
    )
    # Evaluation
    evaluation_interval_minutes = models.PositiveIntegerField(
        default=5,
        help_text="How often to check this alert (in minutes).",
    )
    consecutive_failures = models.PositiveIntegerField(
        default=1,
        help_text="Number of consecutive condition matches before triggering.",
    )
    current_failure_count = models.PositiveIntegerField(default=0)
    # Notification
    notification_channels = models.JSONField(
        default=list,
        help_text='Notification channels: [{"type": "email|slack|webhook", "target": "..."}].',
    )
    notify_on_resolve = models.BooleanField(
        default=True,
        help_text="Send a notification when the alert resolves.",
    )
    cooldown_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Minimum time between repeated notifications.",
    )
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    last_value = models.FloatField(null=True, blank=True)
    # Muting
    muted_until = models.DateTimeField(
        null=True, blank=True,
        help_text="Suppress notifications until this time.",
    )
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"

    @property
    def is_muted(self):
        from django.utils import timezone
        if self.muted_until and self.muted_until > timezone.now():
            return True
        return False


class AlertCondition(models.Model):
    """
    A specific condition within an alert rule. Multiple conditions can be
    combined with AND/OR logic.
    """

    OPERATOR_CHOICES = [
        ("gt", "Greater than"),
        ("gte", "Greater than or equal"),
        ("lt", "Less than"),
        ("lte", "Less than or equal"),
        ("eq", "Equal to"),
        ("neq", "Not equal to"),
        ("pct_increase", "Percentage increase"),
        ("pct_decrease", "Percentage decrease"),
        ("abs_change", "Absolute change"),
        ("is_null", "Is null / no data"),
    ]

    LOGIC_CHOICES = [
        ("and", "AND"),
        ("or", "OR"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_rule = models.ForeignKey(
        AlertRule, on_delete=models.CASCADE, related_name="conditions"
    )
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES)
    threshold_value = models.FloatField(
        null=True, blank=True,
        help_text="Threshold to compare against.",
    )
    comparison_window_minutes = models.PositiveIntegerField(
        default=0,
        help_text="For change-based operators: compare against value N minutes ago.",
    )
    logic_operator = models.CharField(
        max_length=3, choices=LOGIC_CHOICES, default="and",
        help_text="How this condition combines with other conditions in the rule.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.get_operator_display()} {self.threshold_value}"

    def evaluate(self, current_value, previous_value=None):
        """Evaluate this condition against the given values."""
        if self.operator == "is_null":
            return current_value is None

        if current_value is None:
            return False

        threshold = self.threshold_value

        if self.operator == "gt":
            return current_value > threshold
        elif self.operator == "gte":
            return current_value >= threshold
        elif self.operator == "lt":
            return current_value < threshold
        elif self.operator == "lte":
            return current_value <= threshold
        elif self.operator == "eq":
            return current_value == threshold
        elif self.operator == "neq":
            return current_value != threshold
        elif self.operator == "pct_increase":
            if previous_value is None or previous_value == 0:
                return False
            pct = ((current_value - previous_value) / abs(previous_value)) * 100
            return pct >= threshold
        elif self.operator == "pct_decrease":
            if previous_value is None or previous_value == 0:
                return False
            pct = ((previous_value - current_value) / abs(previous_value)) * 100
            return pct >= threshold
        elif self.operator == "abs_change":
            if previous_value is None:
                return False
            return abs(current_value - previous_value) >= threshold

        return False


class AlertHistory(models.Model):
    """
    Historical record of alert triggers and resolutions.
    """

    EVENT_TYPES = [
        ("triggered", "Triggered"),
        ("resolved", "Resolved"),
        ("acknowledged", "Acknowledged"),
        ("muted", "Muted"),
        ("escalated", "Escalated"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_rule = models.ForeignKey(
        AlertRule, on_delete=models.CASCADE, related_name="history"
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    metric_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)
    message = models.TextField(blank=True, default="")
    notification_sent = models.BooleanField(default=False)
    notification_channels_used = models.JSONField(default=list, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Alert histories"

    def __str__(self):
        return f"{self.alert_rule.name} - {self.get_event_type_display()} at {self.created_at}"
