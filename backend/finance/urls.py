from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, VoucherViewSet, ReceivableViewSet, PayableViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("vouchers", VoucherViewSet, basename="voucher")
router.register("receivables", ReceivableViewSet, basename="receivable")
router.register("payables", PayableViewSet, basename="payable")

urlpatterns = router.urls
