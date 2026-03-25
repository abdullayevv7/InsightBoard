"""
Report models: Report, ReportSchedule, ReportExport for automated report generation.
"""

import uuid

from django.conf import settings
from django.db import models


class Report(models.Model):
    """
    A report definition combining multiple data sources, queries, and visualizations
    into a single exportable document.
    """

    FORMAT_CHOICES = [
        ("pdf", "PDF"),
        ("excel", "Excel"),
        ("csv", "CSV"),
        ("html", "HTML"),
        ("markdown", "Markdown"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_reports",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft"
    )
    default_format = models.CharField(
        max_length=10, choices=FORMAT_CHOICES, default="pdf"
    )
    # Report content structure
    sections = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Ordered list of report sections: "
            '[{"type": "text|chart|table|metric", "title": "...", '
            '"config": {...}, "visualization_id": "..."}]'
        ),
    )
    # Filters and parameters
    parameters = models.JSONField(
        default=list,
        blank=True,
        help_text="Report parameters: [{name, type, label, default_value}].",
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Default filter values for the report.",
    )
    # Page layout
    page_orientation = models.CharField(
        max_length=10,
        choices=[("portrait", "Portrait"), ("landscape", "Landscape")],
        default="portrait",
    )
    page_size = models.CharField(
        max_length=10,
        choices=[("a4", "A4"), ("letter", "Letter"), ("legal", "Legal")],
        default="a4",
    )
    header_html = models.TextField(
        blank=True, default="",
        help_text="Custom HTML header template.",
    )
    footer_html = models.TextField(
        blank=True, default="",
        help_text="Custom HTML footer template.",
    )
    cover_page = models.BooleanField(
        default=True,
        help_text="Include a cover page with title, date, and org branding.",
    )
    # Sharing
    is_public = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def export_count(self):
        return self.exports.count()

    @property
    def has_schedule(self):
        return self.schedules.exists()


class ReportSchedule(models.Model):
    """
    Schedule for automated report generation and delivery.
    """

    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("biweekly", "Bi-Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
    ]

    DAY_OF_WEEK_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="schedules"
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.IntegerField(
        choices=DAY_OF_WEEK_CHOICES, null=True, blank=True,
        help_text="Day of the week for weekly/biweekly schedules.",
    )
    day_of_month = models.IntegerField(
        null=True, blank=True,
        help_text="Day of the month for monthly schedules (1-28).",
    )
    time_of_day = models.TimeField(
        help_text="Time to generate the report (in org timezone)."
    )
    timezone = models.CharField(max_length=50, default="UTC")
    export_format = models.CharField(
        max_length=10,
        choices=Report.FORMAT_CHOICES,
        default="pdf",
    )
    # Delivery
    recipients = models.JSONField(
        default=list,
        help_text='List of email addresses or user IDs: ["user@email.com", ...].',
    )
    email_subject = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Custom email subject. Uses report title if blank.",
    )
    email_body = models.TextField(
        blank=True, default="",
        help_text="Custom email body text.",
    )
    include_attachment = models.BooleanField(
        default=True, help_text="Attach the report file to the email."
    )
    include_inline = models.BooleanField(
        default=False, help_text="Include an inline HTML preview in the email body."
    )
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_schedules",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_run_at"]

    def __str__(self):
        return f"{self.report.title} - {self.get_frequency_display()}"


class ReportExport(models.Model):
    """
    A generated export of a report (the rendered PDF/Excel/CSV file).
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="exports"
    )
    schedule = models.ForeignKey(
        ReportSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exports",
        help_text="The schedule that triggered this export, if any.",
    )
    format = models.CharField(max_length=10, choices=Report.FORMAT_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    file = models.FileField(upload_to="report_exports/", null=True, blank=True)
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    parameters_used = models.JSONField(
        default=dict, blank=True,
        help_text="Parameter values used when generating this export.",
    )
    error_message = models.TextField(blank=True, default="")
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_exports",
    )
    generation_time_ms = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Auto-delete exports after this date.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report.title} ({self.format}) - {self.get_status_display()}"
