"""
Dashboard URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardViewSet,
    WidgetViewSet,
    WidgetLayoutViewSet,
    SharedDashboardView,
)

router = DefaultRouter()
router.register(r"", DashboardViewSet, basename="dashboard")
router.register(r"widgets", WidgetViewSet, basename="widget")
router.register(r"layouts", WidgetLayoutViewSet, basename="widget-layout")

urlpatterns = [
    path("shared/<str:token>/", SharedDashboardView.as_view(), name="shared-dashboard"),
    path("", include(router.urls)),
]
