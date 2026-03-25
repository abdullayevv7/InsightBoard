"""
Account admin configuration.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Organization, Team, TeamMembership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email", "username", "full_name", "organization", "role", "is_active", "created_at",
    ]
    list_filter = ["role", "is_active", "organization"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "InsightBoard",
            {
                "fields": (
                    "organization", "role", "avatar", "job_title",
                    "phone", "timezone", "email_notifications",
                ),
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "InsightBoard",
            {
                "fields": ("email", "organization", "role"),
            },
        ),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "plan", "member_count", "is_active", "created_at"]
    list_filter = ["plan", "is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0
    readonly_fields = ["joined_at"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "created_at"]
    list_filter = ["organization"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [TeamMembershipInline]
