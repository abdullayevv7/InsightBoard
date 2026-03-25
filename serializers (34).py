"""
Notification models: in-app notifications for alerts, reports, sharing, etc.
"""

import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    In-app notification for a user. Created by system events (alerts, shares,
    report completions, team invites, etc.).
    """

    NOTIFICATION_TYPES = [
        ("alert_triggered", "Alert Triggered"),
        ("alert_resolved", "Alert Resolved"),
        ("dashboard_shared", "Dashboard Shared"),
        ("report_ready", "Report Ready"),
        ("report_failed", "Report Failed"),
        ("team_invite", "Team Invitation"),
        ("datasource_error", "Data Source Error"),
        ("datasource_synced", "Data Source Synced"),
        ("comment", "Comment"),
        ("system", "System Notification"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    # Link to the related object
    action_url = models.CharField(
        max_length=500, blank=True, default="",
        help_text="Frontend URL to navigate to when notification is clicked.",
    )
    # Metadata about the source
    source_type = models.CharField(
        max_length=50, blank=True, default="",
        help_text="Model name of the source object (e.g. 'AlertRule', 'Dashboard').",
    )
    source_id = models.UUIDField(
        null=True, blank=True,
        help_text="UUID of the source object.",
    )
    # Read tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    # Email delivery tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient.email}"

    def mark_as_read(self):
        """Mark this notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(models.Model):
    """
    User-level notification preferences controlling which notifications
    are received and through which channels.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    # In-app notifications
    in_app_enabled = models.BooleanField(default=True)
    # Email notifications
    email_enabled = models.BooleanField(default=True)
    email_alert_triggered = models.BooleanField(default=True)
    email_alert_resolved = models.BooleanField(default=True)
    email_dashboard_shared = models.BooleanField(default=True)
    email_report_ready = models.BooleanField(default=True)
    email_report_failed = models.BooleanField(default=True)
    email_team_invite = models.BooleanField(default=True)
    email_datasource_error = models.BooleanField(default=True)
    # Digest preferences
    email_digest = models.CharField(
        max_length=20,
        choices=[
            ("realtime", "Real-time"),
            ("hourly", "Hourly Digest"),
            ("daily", "Daily Digest"),
            ("weekly", "Weekly Digest"),
        ],
        default="realtime",
    )
    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    quiet_hours_timezone = models.CharField(max_length=50, default="UTC")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.email}"

    def should_email(self, notification_type: str) -> bool:
        """Check if an email should be sent for this notification type."""
        if not self.email_enabled:
            return False

        type_field_map = {
            "alert_triggered": self.email_alert_triggered,
            "alert_resolved": self.email_alert_resolved,
            "dashboard_shared": self.email_dashboard_shared,
            "report_ready": self.email_report_ready,
            "report_failed": self.email_report_failed,
            "team_invite": self.email_team_invite,
            "datasource_error": self.email_datasource_error,
        }

        return type_field_map.get(notification_type, True)
