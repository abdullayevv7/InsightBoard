"""
Notification views: listing, marking as read, preferences.
"""

from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notification viewset (read-only). Users can list their notifications
    and mark them as read.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)

        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == "true")

        notification_type = self.request.query_params.get("type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """Mark all unread notifications as read."""
        now = timezone.now()
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True, read_at=now)
        return Response({"marked_count": count})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get the count of unread notifications."""
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count})

    @action(detail=False, methods=["delete"], url_path="clear-read")
    def clear_read(self, request):
        """Delete all read notifications older than 30 days."""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=30)
        count, _ = Notification.objects.filter(
            recipient=request.user,
            is_read=True,
            created_at__lt=cutoff,
        ).delete()
        return Response({"deleted_count": count})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """View and update notification preferences for the authenticated user."""

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return prefs
