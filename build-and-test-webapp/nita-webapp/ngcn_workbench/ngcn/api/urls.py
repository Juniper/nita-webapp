# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""URL configuration for the NITA Webapp REST API.

All endpoints are registered under the ``/api/v1/`` prefix (wired in
``ngcn_workbench.urls``) via a DRF ``DefaultRouter``:

=========================  =====================================
URL prefix                 ViewSet
=========================  =====================================
``network-types/``         :class:`~ngcn.api.views.CampusTypeViewSet`
``networks/``              :class:`~ngcn.api.views.CampusNetworkViewSet`
``actions/``               :class:`~ngcn.api.views.ActionViewSet`
``action-categories/``     :class:`~ngcn.api.views.ActionCategoryViewSet`
``action-history/``        :class:`~ngcn.api.views.ActionHistoryViewSet`
=========================  =====================================

Session auth (no authentication required for csrf/login):

=========================  ==========================================
URL                        View
=========================  ==========================================
``auth/csrf/``             :func:`~ngcn.api.views.csrf_view`
``auth/login/``            :func:`~ngcn.api.views.login_view`
``auth/logout/``           :func:`~ngcn.api.views.logout_view`
``auth/me/``               :func:`~ngcn.api.views.me_view`
=========================  ==========================================
"""

from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    ActionCategoryViewSet,
    ActionHistoryViewSet,
    ActionViewSet,
    CampusNetworkViewSet,
    CampusTypeViewSet,
    JenkinsJobStreamView,
    LifecycleRunViewSet,
    csrf_view,
    login_view,
    logout_view,
    me_view,
)

router = DefaultRouter()
router.register(r"network-types", CampusTypeViewSet, basename="campustype")
router.register(r"networks", CampusNetworkViewSet, basename="campusnetwork")
router.register(r"actions", ActionViewSet, basename="action")
router.register(r"action-categories", ActionCategoryViewSet, basename="actioncategory")
router.register(r"action-history", ActionHistoryViewSet, basename="actionhistory")
router.register(r"lifecycle-runs", LifecycleRunViewSet, basename="lifecyclerun")

urlpatterns = router.urls + [
    re_path(
        r"^jenkins/jobs/(?P<job_name>[A-Za-z0-9_.\-]+)/(?P<build_no>[0-9]+)/stream/$",
        JenkinsJobStreamView.as_view(),
        name="jenkins-job-stream",
    ),
    path("auth/csrf/", csrf_view, name="auth-csrf"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
    path("auth/me/", me_view, name="auth-me"),
]
