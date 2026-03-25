"""
Dashboard admin configuration.
"""

from django.contrib import admin

from .models import Dashboard, Widget, WidgetLayout, DashboardShare


class WidgetInline(admin.TabularInline):
    model = Widget
    extra = 0
    fields = [
        "title", "widget_type", "data_source",
        "position_x", "position_y", "width", "height",
    ]
    readonly_fields = ["id"]


class DashboardShareInline(admin.TabularInline):
    model = DashboardShare
    extra = 0
    readonly_fields = ["id", "created_at"]


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = [
        "title", "owner", "organization", "is_public",
        "is_template", "widget_count", "created_at",
    ]
    list_filter = ["is_public", "is_template", "organization"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [WidgetInline, DashboardShareInline]


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = [
        "title", "widget_type", "dashboard", "data_source",
        "position_x", "position_y", "width", "height",
    ]
    list_filter = ["widget_type"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(WidgetLayout)
class WidgetLayoutAdmin(admin.ModelAdmin):
    list_display = ["dashboard", "breakpoint", "updated_at"]
    list_filter = ["breakpoint"]
    readonly_fields = ["id", "updated_at"]


@admin.register(DashboardShare)
class DashboardShareAdmin(admin.ModelAdmin):
    list_display = [
        "dashboard", "shared_with_user", "shared_with_team",
        "permission", "created_by", "created_at",
    ]
    list_filter = ["permission"]
    readonly_fields = ["id", "share_token", "created_at"]
