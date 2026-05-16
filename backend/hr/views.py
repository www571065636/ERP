from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
import datetime

from .models import Employee, Attendance, Salary
from common.response import ok, fail


class EmployeeSerializer(drf_serializers.ModelSerializer):
    emp_status_label = drf_serializers.CharField(source="get_emp_status_display", read_only=True)
    gender_label = drf_serializers.CharField(source="get_gender_display", read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "employee_no", "user_id", "real_name", "gender", "gender_label",
                  "birth_date", "id_card", "mobile", "email", "dept_id", "position",
                  "entry_date", "leave_date", "emp_status", "emp_status_label",
                  "base_salary", "bank_name", "bank_account", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"id_card": {"write_only": True}, "bank_account": {"write_only": True}}


class AttendanceSerializer(drf_serializers.ModelSerializer):
    employee_name = drf_serializers.CharField(source="employee.real_name", read_only=True)
    employee_no = drf_serializers.CharField(source="employee.employee_no", read_only=True)
    attend_type_label = drf_serializers.CharField(source="get_attend_type_display", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "employee", "employee_name", "employee_no", "attend_date",
                  "check_in_time", "check_out_time", "attend_type", "attend_type_label",
                  "work_hours", "overtime_hours", "remark", "created_at"]
        read_only_fields = ["id", "created_at"]


class SalarySerializer(drf_serializers.ModelSerializer):
    employee_name = drf_serializers.CharField(source="employee.real_name", read_only=True)
    employee_no = drf_serializers.CharField(source="employee.employee_no", read_only=True)
    status_label = drf_serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Salary
        fields = ["id", "salary_no", "employee", "employee_name", "employee_no", "period",
                  "base_salary", "overtime_pay", "bonus", "deduction", "social_security",
                  "income_tax", "gross_salary", "net_salary", "status", "status_label",
                  "pay_date", "remark", "created_at"]
        read_only_fields = ["id", "salary_no", "gross_salary", "net_salary", "created_at"]

    def validate(self, data):
        gross = (float(data.get("base_salary", 0)) + float(data.get("overtime_pay", 0)) +
                 float(data.get("bonus", 0)) - float(data.get("deduction", 0)))
        net = gross - float(data.get("social_security", 0)) - float(data.get("income_tax", 0))
        data["gross_salary"] = round(gross, 2)
        data["net_salary"] = round(net, 2)
        return data


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.filter(is_deleted=False).order_by("employee_no")
    serializer_class = EmployeeSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["employee_no", "real_name", "mobile"]
    filterset_fields = ["dept_id", "emp_status"]

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
        for emp in qs:
            if Salary.objects.filter(employee=emp, period=period).exists():
                continue
            no = f"SAL{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}{emp.id}"
            gross = float(emp.base_salary or 0)
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
