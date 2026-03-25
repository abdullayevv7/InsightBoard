"""
Alert views: CRUD for alert rules, conditions, history, and actions.
"""

from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AlertRule, AlertCondition, AlertHistory
from .serializers import (
    AlertRuleListSerializer,
    AlertRuleDetailSerializer,
    AlertRuleCreateSerializer,
    AlertConditionSerializer,
    AlertHistorySerializer,
    AlertMuteSerializer,
)


class AlertRuleViewSet(viewsets.ModelViewSet):
    """Alert rule CRUD viewset with actions for pause, resume, mute, test."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return AlertRuleListSerializer
        if self.action == "create":
            return AlertRuleCreateSerializer
        return AlertRuleDetailSerializer

    def get_queryset(self):
        queryset = AlertRule.objects.filter(
            organization=self.request.user.organization
        ).select_related("data_source", "created_by").prefetch_related("conditions")

        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        rule_status = self.request.query_params.get("status")
        if rule_status:
            queryset = queryset.filter(status=rule_status)

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization,
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause an alert rule."""
        alert = self.get_object()
        alert.status = "paused"
        alert.save(update_fields=["status"])
        return Response(AlertRuleDetailSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a paused alert rule."""
        alert = self.get_object()
        alert.status = "active"
        alert.current_failure_count = 0
        alert.save(update_fields=["status", "current_failure_count"])
        return Response(AlertRuleDetailSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def mute(self, request, pk=None):
        """Mute an alert for a specified duration."""
        alert = self.get_object()
        serializer = AlertMuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert.muted_until = serializer.validated_data["muted_until"]
        alert.save(update_fields=["muted_until"])

        AlertHistory.objects.create(
            alert_rule=alert,
            event_type="muted",
            message=serializer.validated_data.get("reason", ""),
            metric_value=alert.last_value,
        )

        return Response(AlertRuleDetailSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def unmute(self, request, pk=None):
        """Remove mute from an alert."""
        alert = self.get_object()
        alert.muted_until = None
        alert.save(update_fields=["muted_until"])
        return Response(AlertRuleDetailSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Test an alert rule by evaluating it now without sending notifications."""
        alert = self.get_object()

        from .tasks import evaluate_single_alert
        result = evaluate_single_alert(str(alert.id), dry_run=True)
        return Response(result)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """List alert history for this rule."""
        alert = self.get_object()
        history = AlertHistory.objects.filter(alert_rule=alert)
        serializer = AlertHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"])
    def conditions(self, request, pk=None):
        """List or add conditions for an alert rule."""
        alert = self.get_object()

        if request.method == "GET":
            conditions = AlertCondition.objects.filter(alert_rule=alert)
            serializer = AlertConditionSerializer(conditions, many=True)
            return Response(serializer.data)

        serializer = AlertConditionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(alert_rule=alert)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AlertConditionViewSet(viewsets.ModelViewSet):
    """Alert condition CRUD viewset."""

    serializer_class = AlertConditionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertCondition.objects.filter(
            alert_rule__organization=self.request.user.organization
        ).select_related("alert_rule")


class AlertHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for alert history."""

    serializer_class = AlertHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = AlertHistory.objects.filter(
            alert_rule__organization=self.request.user.organization
        ).select_related("alert_rule", "acknowledged_by")

        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return queryset

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert event."""
        history_entry = self.get_object()

        if history_entry.acknowledged_at:
            return Response(
                {"detail": "This alert has already been acknowledged."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        history_entry.acknowledged_by = request.user
        history_entry.acknowledged_at = timezone.now()
        history_entry.save(update_fields=["acknowledged_by", "acknowledged_at"])

        return Response(AlertHistorySerializer(history_entry).data)
