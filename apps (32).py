"""
Notification admin configuration.
"""

from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title", "recipient", "notification_type", "priority",
        "is_read", "email_sent", "created_at",
    ]
    list_filter = ["notification_type", "priority", "is_read", "email_sent"]
    search_fields = ["title", "message", "recipient__email"]
    readonly_fields = [
        "id", "recipient", "notification_type", "title", "message",
        "action_url", "source_type", "source_id",
        "read_at", "email_sent_at", "created_at",
    ]
    date_hierarchy = "created_at"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        "user", "in_app_enabled", "email_enabled",
        "email_digest", "updated_at",
    ]
    list_filter = ["email_digest", "email_enabled", "in_app_enabled"]
    search_fields = ["user__email"]
    readonly_fields = ["id", "updated_at"]
