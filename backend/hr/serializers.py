from rest_framework import serializers as drf_serializers
from decimal import Decimal, ROUND_HALF_UP

from .models import Employee, Attendance, Salary


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
        gross = (Decimal(str(data.get("base_salary", 0))) + Decimal(str(data.get("overtime_pay", 0))) +
                 Decimal(str(data.get("bonus", 0))) - Decimal(str(data.get("deduction", 0))))
        net = gross - Decimal(str(data.get("social_security", 0))) - Decimal(str(data.get("income_tax", 0)))
        data["gross_salary"] = gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        data["net_salary"] = net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return data
