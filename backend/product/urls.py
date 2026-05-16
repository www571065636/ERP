from rest_framework.routers import DefaultRouter
from .views import UnitViewSet, CategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register("units", UnitViewSet, basename="unit")
router.register("categories", CategoryViewSet, basename="category")
router.register("", ProductViewSet, basename="product")
urlpatterns = router.urls
