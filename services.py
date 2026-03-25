"""
Dashboard views: CRUD, widget management, layout updates, sharing.
"""

from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Dashboard, Widget, WidgetLayout, DashboardShare
from .serializers import (
    DashboardListSerializer,
    DashboardDetailSerializer,
    DashboardCreateSerializer,
    WidgetSerializer,
    WidgetCreateSerializer,
    WidgetLayoutSerializer,
    DashboardShareSerializer,
    DashboardShareCreateSerializer,
    BulkLayoutUpdateSerializer,
)


class DashboardPermission(permissions.BasePermission):
    """Custom permission for dashboard access based on ownership and sharing."""

    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True

        if obj.organization == request.user.organization:
            if request.method in permissions.SAFE_METHODS:
                return True
            return request.user.has_org_permission("editor")

        share = DashboardShare.objects.filter(
            dashboard=obj,
            shared_with_user=request.user,
        ).first()

        if share:
            if share.expires_at and share.expires_at < timezone.now():
                return False
            if request.method in permissions.SAFE_METHODS:
                return True
            return share.permission in ("edit", "admin")

        team_share = DashboardShare.objects.filter(
            dashboard=obj,
            shared_with_team__memberships__user=request.user,
        ).first()

        if team_share:
            if team_share.expires_at and team_share.expires_at < timezone.now():
                return False
            if request.method in permissions.SAFE_METHODS:
                return True
            return team_share.permission in ("edit", "admin")

        return obj.is_public and request.method in permissions.SAFE_METHODS


class DashboardViewSet(viewsets.ModelViewSet):
    """Main dashboard CRUD viewset."""

    permission_classes = [permissions.IsAuthenticated, DashboardPermission]

    def get_serializer_class(self):
        if self.action == "list":
            return DashboardListSerializer
        if self.action == "create":
            return DashboardCreateSerializer
        return DashboardDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return Dashboard.objects.filter(
            Q(owner=user)
            | Q(organization=user.organization)
            | Q(shares__shared_with_user=user)
            | Q(shares__shared_with_team__memberships__user=user)
            | Q(is_public=True)
        ).distinct().select_related("owner", "organization").prefetch_related("widgets")

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user,
            organization=self.request.user.organization,
        )

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        """Clone a dashboard with all its widgets."""
        dashboard = self.get_object()
        new_title = request.data.get("title")
        cloned = dashboard.clone(request.user, new_title)
        return Response(
            DashboardDetailSerializer(cloned).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get", "post"])
    def widgets(self, request, pk=None):
        """List or add widgets to a dashboard."""
        dashboard = self.get_object()

        if request.method == "GET":
            widgets = dashboard.widgets.all()
            serializer = WidgetSerializer(widgets, many=True)
            return Response(serializer.data)

        serializer = WidgetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(dashboard=dashboard)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["put"], url_path="layout")
    def update_layout(self, request, pk=None):
        """Bulk update widget positions on a dashboard."""
        dashboard = self.get_object()
        serializer = BulkLayoutUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for item in serializer.validated_data["layouts"]:
            Widget.objects.filter(
                id=item["widget_id"], dashboard=dashboard
            ).update(
                position_x=item.get("x", 0),
                position_y=item.get("y", 0),
                width=item.get("w", 4),
                height=item.get("h", 3),
            )

        return Response({"detail": "Layout updated successfully."})

    @action(detail=True, methods=["get", "post"])
    def shares(self, request, pk=None):
        """List or create shares for a dashboard."""
        dashboard = self.get_object()

        if request.method == "GET":
            shares = DashboardShare.objects.filter(dashboard=dashboard)
            serializer = DashboardShareSerializer(shares, many=True)
            return Response(serializer.data)

        serializer = DashboardShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        share = serializer.save(
            dashboard=dashboard,
            created_by=request.user,
        )
        return Response(
            DashboardShareSerializer(share).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def templates(self, request, pk=None):
        """List available dashboard templates."""
        templates = Dashboard.objects.filter(is_template=True)
        serializer = DashboardListSerializer(templates, many=True)
        return Response(serializer.data)


class WidgetViewSet(viewsets.ModelViewSet):
    """Widget CRUD viewset."""

    serializer_class = WidgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Widget.objects.filter(
            dashboard__organization=self.request.user.organization
        ).select_related("dashboard", "data_source")

    @action(detail=True, methods=["post"], url_path="refresh-data")
    def refresh_data(self, request, pk=None):
        """Force refresh widget cached data."""
        widget = self.get_object()
        widget.cached_data = None
        widget.cached_at = None
        widget.save(update_fields=["cached_data", "cached_at"])
        return Response({"detail": "Widget cache cleared. Data will refresh on next load."})


class WidgetLayoutViewSet(viewsets.ModelViewSet):
    """Widget layout viewset for responsive breakpoints."""

    serializer_class = WidgetLayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WidgetLayout.objects.filter(
            dashboard__organization=self.request.user.organization
        )


class SharedDashboardView(generics.RetrieveAPIView):
    """View a shared dashboard via token (no authentication required)."""

    serializer_class = DashboardDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        token = self.kwargs["token"]
        share = DashboardShare.objects.select_related("dashboard").get(
            share_token=token
        )

        if share.expires_at and share.expires_at < timezone.now():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This share link has expired.")

        return share.dashboard
