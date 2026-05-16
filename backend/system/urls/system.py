from rest_framework.routers import DefaultRouter
from system.views import UserViewSet, RoleViewSet, PermissionViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")
router.register("permissions", PermissionViewSet, basename="permission")
urlpatterns = router.urls
