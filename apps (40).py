"""
Report admin configuration.
"""

from django.contrib import admin

from .models import Report, ReportSchedule, ReportExport


class ReportScheduleInline(admin.TabularInline):
    model = ReportSchedule
    extra = 0
    readonly_fields = ["id", "last_run_at", "next_run_at", "created_at"]
    fields = [
        "frequency", "day_of_week", "day_of_month", "time_of_day",
        "timezone", "export_format", "is_active", "last_run_at", "next_run_at",
    ]


class ReportExportInline(admin.TabularInline):
    model = ReportExport
    extra = 0
    readonly_fields = [
        "id", "format", "status", "file", "file_size_bytes",
        "generation_time_ms", "created_at",
    ]
    fields = ["format", "status", "file", "file_size_bytes", "generation_time_ms", "created_at"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        "title", "organization", "created_by", "status",
        "default_format", "export_count", "created_at",
    ]
    list_filter = ["status", "default_format", "organization"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "share_token", "created_at", "updated_at"]
    inlines = [ReportScheduleInline, ReportExportInline]


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "report", "frequency", "time_of_day", "export_format",
        "is_active", "last_run_at", "next_run_at",
    ]
    list_filter = ["frequency", "is_active", "export_format"]
    search_fields = ["report__title"]
    readonly_fields = ["id", "last_run_at", "next_run_at", "created_at", "updated_at"]


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = [
        "report", "format", "status", "file_size_bytes",
        "generation_time_ms", "generated_by", "created_at",
    ]
    list_filter = ["status", "format"]
    search_fields = ["report__title"]
    readonly_fields = [
        "id", "file", "file_size_bytes", "error_message",
        "generation_time_ms", "created_at",
    ]
