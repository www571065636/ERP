from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from decimal import Decimal
import datetime

from .models import Employee, Attendance, Salary
from .serializers import EmployeeSerializer, AttendanceSerializer, SalarySerializer
from common.permissions import HasPermCode
from common.response import ok, fail


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.filter(is_deleted=False).order_by("employee_no")
    serializer_class = EmployeeSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["employee_no", "real_name", "mobile"]
    filterset_fields = ["dept_id", "emp_status"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "hr:employee:list",
        "retrieve": "hr:employee:list",
        "create": "hr:employee:create",
        "update": "hr:employee:update",
        "partial_update": "hr:employee:update",
        "destroy": "hr:employee:delete",
    }

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.filter(is_deleted=False).select_related("employee").order_by("-attend_date")
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "attend_type"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "hr:attendance:list",
        "retrieve": "hr:attendance:list",
        "create": "hr:attendance:create",
        "update": "hr:attendance:update",
        "partial_update": "hr:attendance:update",
        "destroy": "hr:attendance:delete",
    }

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")


class SalaryViewSet(viewsets.ModelViewSet):
    queryset = Salary.objects.filter(is_deleted=False).select_related("employee").order_by("-period", "-created_at")
    serializer_class = SalarySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "period", "status"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "hr:salary:list",
        "retrieve": "hr:salary:list",
        "create": "hr:salary:create",
        "update": "hr:salary:update",
        "partial_update": "hr:salary:update",
        "destroy": "hr:salary:delete",
        "review": "hr:salary:review",
        "generate": "hr:salary:generate",
        "batch_pay": "hr:salary:batch-pay",
    }

    def perform_create(self, serializer):
        no = f"SAL{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        serializer.save(created_by=self.request.user.id, salary_no=no)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 0:
            return fail("只有草稿状态可以删除")
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        salary = self.get_object()
        if salary.status != 0:
            return fail("只有草稿状态可以审核")
        salary.status = 1
        salary.save(update_fields=["status"])
        return ok(msg="审核成功")

    @action(detail=False, methods=["post"])
    def generate(self, request):
        period = request.data.get("period")
        dept_ids = request.data.get("dept_ids", [])
        if not period:
            return fail("请指定薪资期间")
        qs = Employee.objects.filter(is_deleted=False, emp_status__in=[1, 3])
        if dept_ids:
            qs = qs.filter(dept_id__in=dept_ids)
        created = 0
        with transaction.atomic():
            for emp in qs:
                if Salary.objects.filter(employee=emp, period=period).exists():
                    continue
                no = f"SAL{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}{emp.id}"
                gross = Decimal(str(emp.base_salary or 0))
                Salary.objects.create(
                    salary_no=no, employee=emp, period=period,
                    base_salary=emp.base_salary or 0,
                    gross_salary=gross, net_salary=gross,
                    created_by=request.user.id
                )
                created += 1
        return ok(data={"generated": created, "msg": f"已生成 {created} 条薪资单"})

    @action(detail=False, methods=["post"])
    def batch_pay(self, request):
        period = request.data.get("period")
        pay_date = request.data.get("pay_date")
        if not period:
            return fail("请指定薪资期间")
        count = Salary.objects.filter(period=period, status=1, is_deleted=False).update(
            status=2, pay_date=pay_date
        )
        return ok(data={"paid": count, "msg": f"已发放 {count} 条薪资单"})
