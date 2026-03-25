"""
Alert URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AlertRuleViewSet, AlertConditionViewSet, AlertHistoryViewSet

router = DefaultRouter()
router.register(r"rules", AlertRuleViewSet, basename="alert-rule")
router.register(r"conditions", AlertConditionViewSet, basename="alert-condition")
router.register(r"history", AlertHistoryViewSet, basename="alert-history")

urlpatterns = [
    path("", include(router.urls)),
]
