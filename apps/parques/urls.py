from rest_framework.routers import DefaultRouter
from .views import ParqueViewSet

router = DefaultRouter()
router.register("", ParqueViewSet, basename="parques")
urlpatterns = router.urls
