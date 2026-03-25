"""
Report views: CRUD for reports, schedules, exports, and generation triggers.
"""

import secrets

from django.http import FileResponse
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Report, ReportSchedule, ReportExport
from .serializers import (
    ReportListSerializer,
    ReportDetailSerializer,
    ReportCreateSerializer,
    ReportScheduleSerializer,
    ReportExportSerializer,
    ReportExportRequestSerializer,
)
from .tasks import generate_report_export


class ReportViewSet(viewsets.ModelViewSet):
    """Report CRUD viewset with export and schedule management."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return ReportListSerializer
        if self.action == "create":
            return ReportCreateSerializer
        return ReportDetailSerializer

    def get_queryset(self):
        return Report.objects.filter(
            organization=self.request.user.organization
        ).select_related("created_by")

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization,
        )

    @action(detail=True, methods=["post"])
    def export(self, request, pk=None):
        """Trigger a report export (async via Celery)."""
        report = self.get_object()
        serializer = ReportExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export_format = serializer.validated_data["format"]
        parameters = serializer.validated_data.get("parameters", {})

        report_export = ReportExport.objects.create(
            report=report,
            format=export_format,
            parameters_used=parameters,
            generated_by=request.user,
            status="pending",
        )

        generate_report_export.delay(str(report_export.id))

        return Response(
            ReportExportSerializer(report_export).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"])
    def exports(self, request, pk=None):
        """List all exports for a report."""
        report = self.get_object()
        exports = ReportExport.objects.filter(report=report)
        serializer = ReportExportSerializer(exports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="generate-share-link")
    def generate_share_link(self, request, pk=None):
        """Generate a public share link for the report."""
        report = self.get_object()
        if not request.user.has_org_permission("editor"):
            return Response(
                {"detail": "You do not have permission to share reports."},
                status=status.HTTP_403_FORBIDDEN,
            )
        report.share_token = secrets.token_urlsafe(48)
        report.is_public = True
        report.save(update_fields=["share_token", "is_public"])
        return Response({
            "share_token": report.share_token,
            "share_url": f"/reports/shared/{report.share_token}/",
        })

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Mark a report as published."""
        report = self.get_object()
        report.status = "published"
        report.save(update_fields=["status"])
        return Response(ReportDetailSerializer(report).data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive a report."""
        report = self.get_object()
        report.status = "archived"
        report.save(update_fields=["status"])
        return Response(ReportDetailSerializer(report).data)

    @action(detail=True, methods=["get", "post"])
    def schedules(self, request, pk=None):
        """List or create schedules for a report."""
        report = self.get_object()

        if request.method == "GET":
            schedules = ReportSchedule.objects.filter(report=report)
            serializer = ReportScheduleSerializer(schedules, many=True)
            return Response(serializer.data)

        serializer = ReportScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(report=report, created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """Schedule management viewset."""

    serializer_class = ReportScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReportSchedule.objects.filter(
            report__organization=self.request.user.organization
        ).select_related("report", "created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle schedule active/inactive."""
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save(update_fields=["is_active"])
        return Response(ReportScheduleSerializer(schedule).data)


class ReportExportViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for report exports."""

    serializer_class = ReportExportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReportExport.objects.filter(
            report__organization=self.request.user.organization
        ).select_related("report", "generated_by")

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download the exported report file."""
        export = self.get_object()
        if export.status != "completed" or not export.file:
            return Response(
                {"detail": "Export is not ready for download."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(
            export.file.open("rb"),
            as_attachment=True,
            filename=f"{export.report.title}.{export.format}",
        )


class SharedReportView(generics.RetrieveAPIView):
    """View a shared report via public token (no authentication)."""

    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        token = self.kwargs["token"]
        try:
            return Report.objects.get(share_token=token, is_public=True)
        except Report.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Report not found or link is invalid.")
