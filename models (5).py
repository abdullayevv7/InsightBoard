"""
Account views: authentication, user profile, organization and team management.
"""

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Organization, Team, TeamMembership
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    OrganizationSerializer,
    TeamSerializer,
    TeamMembershipSerializer,
    InviteUserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """JWT login endpoint with user info."""

    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(generics.GenericAPIView):
    """Logout endpoint that blacklists the refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view and update."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Change user password."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class OrganizationViewSet(viewsets.ModelViewSet):
    """Organization management viewset."""

    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(
            id=self.request.user.organization_id
        )

    def perform_create(self, serializer):
        org = serializer.save()
        self.request.user.organization = org
        self.request.user.role = "owner"
        self.request.user.save()

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """List organization members."""
        org = self.get_object()
        members = User.objects.filter(organization=org)
        serializer = UserSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        """Invite a user to the organization."""
        org = self.get_object()

        if not request.user.has_org_permission("admin"):
            return Response(
                {"detail": "You do not have permission to invite users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = InviteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]
        team_ids = serializer.validated_data.get("team_ids", [])

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "organization": org,
                "role": role,
            },
        )

        if not created:
            if user.organization and user.organization != org:
                return Response(
                    {"detail": "User belongs to another organization."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.organization = org
            user.role = role
            user.save()

        for team_id in team_ids:
            try:
                team = Team.objects.get(id=team_id, organization=org)
                TeamMembership.objects.get_or_create(user=user, team=team)
            except Team.DoesNotExist:
                continue

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, pk=None):
        """Remove a member from the organization."""
        org = self.get_object()

        if not request.user.has_org_permission("admin"):
            return Response(
                {"detail": "You do not have permission to remove members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = request.data.get("user_id")
        try:
            user = User.objects.get(id=user_id, organization=org)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found in this organization."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role == "owner":
            return Response(
                {"detail": "Cannot remove the organization owner."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.organization = None
        user.role = "viewer"
        user.save()

        TeamMembership.objects.filter(user=user, team__organization=org).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamViewSet(viewsets.ModelViewSet):
    """Team management viewset."""

    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Team.objects.filter(
            organization=self.request.user.organization
        ).prefetch_related("memberships")

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """List team members."""
        team = self.get_object()
        memberships = TeamMembership.objects.filter(team=team).select_related("user")
        serializer = TeamMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, pk=None):
        """Add a member to the team."""
        team = self.get_object()
        user_id = request.data.get("user_id")
        role = request.data.get("role", "member")

        try:
            user = User.objects.get(
                id=user_id, organization=team.organization
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found in this organization."},
                status=status.HTTP_404_NOT_FOUND,
            )

        membership, created = TeamMembership.objects.get_or_create(
            user=user, team=team, defaults={"role": role}
        )

        if not created:
            return Response(
                {"detail": "User is already a member of this team."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            TeamMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, pk=None):
        """Remove a member from the team."""
        team = self.get_object()
        user_id = request.data.get("user_id")

        deleted, _ = TeamMembership.objects.filter(
            user_id=user_id, team=team
        ).delete()

        if not deleted:
            return Response(
                {"detail": "User is not a member of this team."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
