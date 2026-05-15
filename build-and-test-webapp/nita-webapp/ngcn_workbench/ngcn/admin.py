# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from django.contrib import admin

from ngcn.models import (
    Action,
    ActionCategory,
    ActionHistory,
    CampusNetwork,
    CampusType,
    Workbook,
    Worksheets,
)

# Register your models here.
admin.site.register(ActionCategory)
admin.site.register(Action)
admin.site.register(CampusType)
admin.site.register(CampusNetwork)
admin.site.register(ActionHistory)
admin.site.register(Workbook)
admin.site.register(Worksheets)
# admin.site.register(JenkinsJobProperty)
