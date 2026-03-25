"""
DataSource URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DataSourceViewSet, DataQueryViewSet, QueryResultViewSet

router = DefaultRouter()
router.register(r"", DataSourceViewSet, basename="datasource")
router.register(r"queries", DataQueryViewSet, basename="data-query")
router.register(r"results", QueryResultViewSet, basename="query-result")

urlpatterns = [
    path("", include(router.urls)),
]
