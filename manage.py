"""
Visualization URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ChartConfigViewSet, VisualizationViewSet

router = DefaultRouter()
router.register(r"charts", ChartConfigViewSet, basename="chart-config")
router.register(r"", VisualizationViewSet, basename="visualization")

urlpatterns = [
    path("", include(router.urls)),
]
