from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SalesOrderViewSet

router = DefaultRouter()
router.register("customers", CustomerViewSet, basename="customer")
router.register("orders", SalesOrderViewSet, basename="sales-order")
urlpatterns = router.urls
