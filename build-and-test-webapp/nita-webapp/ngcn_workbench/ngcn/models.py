# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _

# Create your models here.


class User(AbstractUser):
    """Custom user model with a three-tier application role.

    ``role`` drives all application-level access control (see
    ``ngcn.api.permissions``). Django's ``is_staff`` / ``is_superuser`` flags are
    retained for the admin panel only and are NOT used for API role checks.
    """

    ROLE_USER = "user"
    ROLE_POWER_USER = "power_user"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_POWER_USER, "Power user"),
        (ROLE_ADMIN, "Admin"),
    )

    role = models.CharField(
        max_length=16,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        verbose_name="Role",
    )


class Team(models.Model):
    """A collaborative group. Power users create teams and manage membership;
    networks can be shared with a team so all members gain read access."""

    name = models.CharField(max_length=255, unique=True, verbose_name="Team Name")
    description = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Description"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_teams",
        verbose_name="Created By",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="teams",
        blank=True,
        verbose_name="Members",
    )

    def __str__(self):
        return self.name


class ActionCategory(models.Model):
    category_name = models.CharField(
        max_length=255, verbose_name="Category Name", unique=True
    )

    def __str__(self):
        return self.category_name


class CampusType(models.Model):
    name = models.CharField(
        max_length=255, verbose_name=_("network_type_heading") + " Name", unique=True
    )
    description = models.CharField(max_length=255, verbose_name="Description")
    app_zip_name = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_types",
        verbose_name="Created By",
    )

    def __str__(self):
        return self.name


class ActionProperty(models.Model):
    shell_command = models.TextField(max_length=255, verbose_name="Shell Command")
    output_path = models.CharField(
        max_length=255, verbose_name="Output Path", null=True
    )
    custom_workspace = models.CharField(
        max_length=255, verbose_name="Output Path", null=True
    )

    def __str__(self):
        return self.shell_command


class Action(models.Model):
    action_name = models.CharField(max_length=255, verbose_name="Action Name")
    jenkins_url = models.CharField(max_length=255, verbose_name="Jenkins Action Url")
    # description = models.CharField(max_length=100,D)
    action_category = models.ForeignKey(
        ActionCategory, on_delete=models.CASCADE, verbose_name="Action Category"
    )
    campus_type_id = models.ForeignKey(
        CampusType, on_delete=models.CASCADE, verbose_name="Campus Type Id"
    )
    action_property = models.OneToOneField(
        ActionProperty, on_delete=models.CASCADE, verbose_name="Action Property"
    )

    def __str__(self):
        return self.action_name


class CampusNetwork(models.Model):
    name = models.CharField(
        max_length=255, verbose_name=_("network_heading") + " Name", unique=True
    )
    status = models.CharField(max_length=255, verbose_name="Status")
    description = models.CharField(max_length=255, verbose_name="Description")
    host_file = models.TextField()
    campus_type = models.ForeignKey(
        CampusType, on_delete=models.CASCADE, verbose_name=_("network_type_heading")
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="owned_networks",
        verbose_name="Owner",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="networks",
        verbose_name="Team",
    )

    # class Meta:
    #    unique_together = ("campus_type","name",)
    def __str__(self):
        return self.name


class ActionHistory(models.Model):
    action_id = models.ForeignKey(
        Action, verbose_name="Action Id", on_delete=models.CASCADE
    )
    # description = models.CharField(max_length=100,verbose_name="Description")
    timestamp = models.DateTimeField(verbose_name="Timestamp")
    status = models.CharField(max_length=255, verbose_name="Status")
    jenkins_job_build_no = models.IntegerField(verbose_name="Jenkins Job Id")
    category_id = models.ForeignKey(
        ActionCategory, on_delete=models.CASCADE, verbose_name="Category Id"
    )
    campus_network_id = models.ForeignKey(
        CampusNetwork, on_delete=models.CASCADE, verbose_name="Campus Network Id"
    )

    def __str__(self):
        return self.action_id.action_name


# class JobStatus(models.Model):
#    status=models.CharField(max_length=100, verbose_name="Status")


class Workbook(models.Model):
    name = models.CharField(max_length=255, null=False)
    campus_network_id = models.ForeignKey(
        CampusNetwork, on_delete=models.CASCADE, verbose_name=_("network_heading")
    )

    class Meta:
        unique_together = (
            "campus_network_id",
            "name",
        )


class Worksheets(models.Model):
    name = models.CharField(max_length=255)
    data = models.TextField()
    workbook_id = models.ForeignKey(Workbook, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            "workbook_id",
            "name",
        )

    def __str__(self):
        return self.name


class LifecycleRun(models.Model):
    """Record of a network lifecycle Jenkins job (create/delete/type-load).

    Stored independently of ``ActionHistory`` so that a run survives the
    deletion of its network row. ``subject`` is a plain string (the network or
    network-type name) rather than a foreign key for the same reason.
    """

    KIND_NETWORK_CREATE = "network_create"
    KIND_NETWORK_DELETE = "network_delete"
    KIND_NETWORK_TYPE_LOAD = "network_type_load"
    KIND_CHOICES = (
        (KIND_NETWORK_CREATE, "Network create"),
        (KIND_NETWORK_DELETE, "Network delete"),
        (KIND_NETWORK_TYPE_LOAD, "Network type load"),
    )

    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    subject = models.CharField(max_length=255)
    job_name = models.CharField(max_length=255)
    build_no = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.kind}:{self.subject} ({self.job_name}#{self.build_no})"
