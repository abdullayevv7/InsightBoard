"""
Account serializers for registration, login, user/org/team management.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Organization, Team, TeamMembership

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT token serializer that includes user info in the response."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True, validators=[validate_password], style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    organization_name = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = User
        fields = [
            "email", "username", "first_name", "last_name",
            "password", "password_confirm", "organization_name",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name", "")
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)

        if org_name:
            slug = org_name.lower().replace(" ", "-")
            org, _ = Organization.objects.get_or_create(
                slug=slug, defaults={"name": org_name}
            )
            user.organization = org
            user.role = "owner"

        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""

    full_name = serializers.ReadOnlyField()
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name", "full_name",
            "role", "avatar", "job_title", "phone", "timezone",
            "email_notifications", "organization", "organization_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "email", "organization", "created_at", "updated_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "job_title", "phone",
            "timezone", "email_notifications", "avatar",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, validators=[validate_password]
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organization management."""

    member_count = serializers.ReadOnlyField()

    class Meta:
        model = Organization
        fields = [
            "id", "name", "slug", "logo", "website", "plan",
            "max_users", "max_dashboards", "max_datasources",
            "is_active", "member_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "plan", "max_users", "max_dashboards", "max_datasources", "created_at", "updated_at"]


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for team management."""

    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id", "name", "description", "organization",
            "member_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]

    def get_member_count(self, obj):
        return obj.memberships.count()


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Serializer for team membership."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = TeamMembership
        fields = ["id", "user", "team", "role", "user_email", "user_name", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class InviteUserSerializer(serializers.Serializer):
    """Serializer for inviting a user to an organization."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[("admin", "Admin"), ("editor", "Editor"), ("viewer", "Viewer")]
    )
    team_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
