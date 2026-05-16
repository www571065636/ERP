from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, AttendanceViewSet, SalaryViewSet

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")
router.register("attendances", AttendanceViewSet, basename="attendance")
router.register("salaries", SalaryViewSet, basename="salary")

urlpatterns = router.urls
