# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from ngcn.models import (
    Action,
    ActionCategory,
    ActionHistory,
    CampusNetwork,
    CampusType,
    Team,
    User,
    Workbook,
    Worksheets,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin for the custom User model, exposing the ``role`` field."""

    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Role", {"fields": ("role",)}),)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by")
    filter_horizontal = ("members",)


# Register your models here.
admin.site.register(ActionCategory)
admin.site.register(Action)
admin.site.register(CampusType)
admin.site.register(CampusNetwork)
admin.site.register(ActionHistory)
admin.site.register(Workbook)
admin.site.register(Worksheets)
# admin.site.register(JenkinsJobProperty)
