"""
Report serializers for CRUD operations, schedules, and exports.
"""

from rest_framework import serializers

from .models import Report, ReportSchedule, ReportExport


class ReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for report listings."""

    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    export_count = serializers.ReadOnlyField()
    has_schedule = serializers.ReadOnlyField()

    class Meta:
        model = Report
        fields = [
            "id", "title", "description", "status", "default_format",
            "is_public", "tags", "export_count", "has_schedule",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ReportDetailSerializer(serializers.ModelSerializer):
    """Full serializer for report detail view."""

    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    export_count = serializers.ReadOnlyField()

    class Meta:
        model = Report
        fields = [
            "id", "title", "description", "organization", "status",
            "default_format", "sections", "parameters", "filters",
            "page_orientation", "page_size", "header_html", "footer_html",
            "cover_page", "is_public", "share_token", "tags",
            "export_count", "created_by", "created_by_name",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "organization", "share_token",
            "created_by", "created_at", "updated_at",
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports."""

    class Meta:
        model = Report
        fields = [
            "title", "description", "default_format", "sections",
            "parameters", "filters", "page_orientation", "page_size",
            "header_html", "footer_html", "cover_page", "tags",
        ]


class ReportScheduleSerializer(serializers.ModelSerializer):
    """Serializer for report schedules."""

    report_title = serializers.CharField(source="report.title", read_only=True)
    frequency_display = serializers.CharField(
        source="get_frequency_display", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )

    class Meta:
        model = ReportSchedule
        fields = [
            "id", "report", "report_title", "frequency", "frequency_display",
            "day_of_week", "day_of_month", "time_of_day", "timezone",
            "export_format", "recipients", "email_subject", "email_body",
            "include_attachment", "include_inline",
            "is_active", "last_run_at", "next_run_at",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "last_run_at", "next_run_at",
            "created_by", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        frequency = attrs.get("frequency")
        if frequency in ("weekly", "biweekly") and attrs.get("day_of_week") is None:
            raise serializers.ValidationError(
                {"day_of_week": "Required for weekly/bi-weekly schedules."}
            )
        if frequency in ("monthly", "quarterly") and attrs.get("day_of_month") is None:
            raise serializers.ValidationError(
                {"day_of_month": "Required for monthly/quarterly schedules."}
            )
        if attrs.get("day_of_month") is not None:
            if not (1 <= attrs["day_of_month"] <= 28):
                raise serializers.ValidationError(
                    {"day_of_month": "Must be between 1 and 28."}
                )
        return attrs


class ReportExportSerializer(serializers.ModelSerializer):
    """Serializer for report exports."""

    report_title = serializers.CharField(source="report.title", read_only=True)

    class Meta:
        model = ReportExport
        fields = [
            "id", "report", "report_title", "schedule", "format",
            "status", "file", "file_size_bytes", "parameters_used",
            "error_message", "generated_by", "generation_time_ms",
            "expires_at", "created_at",
        ]
        read_only_fields = [
            "id", "status", "file", "file_size_bytes", "error_message",
            "generated_by", "generation_time_ms", "created_at",
        ]


class ReportExportRequestSerializer(serializers.Serializer):
    """Serializer for requesting a new report export."""

    format = serializers.ChoiceField(
        choices=Report.FORMAT_CHOICES, default="pdf"
    )
    parameters = serializers.DictField(required=False, default=dict)
