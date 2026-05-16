from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, StockViewSet, StockTransactionViewSet

router = DefaultRouter()
router.register("warehouses", WarehouseViewSet, basename="warehouse")
router.register("stocks", StockViewSet, basename="stock")
router.register("transactions", StockTransactionViewSet, basename="stock-transaction")
urlpatterns = router.urls
