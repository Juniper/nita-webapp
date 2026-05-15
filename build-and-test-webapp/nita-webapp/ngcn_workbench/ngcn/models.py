# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from django.db import models
from django.utils.translation import gettext as _

# Create your models here.


class ActionCategory(models.Model):
    category_name = models.CharField(
        max_length=255, verbose_name="Category Name", unique=True
    )

    def __str__(self):
        return self.category_name


class Role(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name", unique=True)


class Resource(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name", unique=True)


class CampusType(models.Model):
    name = models.CharField(
        max_length=255, verbose_name=_("network_type_heading") + " Name", unique=True
    )
    description = models.CharField(max_length=255, verbose_name="Description")
    app_zip_name = models.CharField(max_length=255, unique=True)
    roles = models.ManyToManyField(Role)
    resources = models.ManyToManyField(Resource)

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
    dynamic_ansible_workspace = models.BooleanField(
        verbose_name="Dynamic Ansible workspace", default=True
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
