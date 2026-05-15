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
