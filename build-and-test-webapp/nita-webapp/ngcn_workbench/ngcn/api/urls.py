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
"""

from rest_framework.routers import DefaultRouter

from .views import (
    ActionCategoryViewSet,
    ActionHistoryViewSet,
    ActionViewSet,
    CampusNetworkViewSet,
    CampusTypeViewSet,
)

router = DefaultRouter()
router.register(r"network-types", CampusTypeViewSet, basename="campustype")
router.register(r"networks", CampusNetworkViewSet, basename="campusnetwork")
router.register(r"actions", ActionViewSet, basename="action")
router.register(r"action-categories", ActionCategoryViewSet, basename="actioncategory")
router.register(r"action-history", ActionHistoryViewSet, basename="actionhistory")

urlpatterns = router.urls
