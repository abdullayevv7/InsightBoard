"""
Report URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ReportViewSet,
    ReportScheduleViewSet,
    ReportExportViewSet,
    SharedReportView,
)

router = DefaultRouter()
router.register(r"", ReportViewSet, basename="report")
router.register(r"schedules", ReportScheduleViewSet, basename="report-schedule")
router.register(r"exports", ReportExportViewSet, basename="report-export")

urlpatterns = [
    path("shared/<str:token>/", SharedReportView.as_view(), name="shared-report"),
    path("", include(router.urls)),
]
