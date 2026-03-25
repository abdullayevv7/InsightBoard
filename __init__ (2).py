"""
Account models: User, Organization, Team with role-based access.
"""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """
    Top-level tenant for multi-tenancy. All data is scoped to an organization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to="org_logos/", blank=True, null=True)
    website = models.URLField(blank=True, default="")
    plan = models.CharField(
        max_length=20,
        choices=[
            ("free", "Free"),
            ("starter", "Starter"),
            ("professional", "Professional"),
            ("enterprise", "Enterprise"),
        ],
        default="free",
    )
    max_users = models.PositiveIntegerField(default=5)
    max_dashboards = models.PositiveIntegerField(default=10)
    max_datasources = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()


class User(AbstractUser):
    """
    Custom user model with organization membership and profile fields.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("editor", "Editor"),
            ("viewer", "Viewer"),
        ],
        default="viewer",
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    timezone = models.CharField(max_length=50, default="UTC")
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def has_org_permission(self, permission_level):
        """Check if user has at least the given permission level."""
        hierarchy = {"owner": 4, "admin": 3, "editor": 2, "viewer": 1}
        return hierarchy.get(self.role, 0) >= hierarchy.get(permission_level, 0)


class Team(models.Model):
    """
    Team within an organization for granular access control.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="teams"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TeamMembership",
        related_name="teams",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["organization", "name"]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class TeamMembership(models.Model):
    """
    Through model for team membership with role assignment.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(
        max_length=20,
        choices=[
            ("lead", "Team Lead"),
            ("member", "Member"),
        ],
        default="member",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "team"]

    def __str__(self):
        return f"{self.user.email} - {self.team.name} ({self.role})"
