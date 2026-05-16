from django.db import models
from common.models import BaseModel
from common.validators import phone_validator, email_validator


class Employee(BaseModel):
    STATUS = [(1, "在职"), (2, "离职"), (3, "试用")]
    GENDERS = [(1, "男"), (2, "女")]

    employee_no = models.CharField(max_length=32)
    user_id = models.BigIntegerField(null=True, blank=True)
    real_name = models.CharField(max_length=64)
    gender = models.SmallIntegerField(choices=GENDERS, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    id_card = models.CharField(max_length=32, blank=True, default="")
    mobile = models.CharField(max_length=20, blank=True, default="", validators=[phone_validator])
    email = models.CharField(max_length=128, blank=True, default="", validators=[email_validator])
    dept_id = models.BigIntegerField(null=True, blank=True)
    position = models.CharField(max_length=64, blank=True, default="")
    entry_date = models.DateField(null=True, blank=True)
    leave_date = models.DateField(null=True, blank=True)
    emp_status = models.SmallIntegerField(choices=STATUS, default=1)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bank_name = models.CharField(max_length=64, blank=True, default="")
    bank_account = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "hr_employee"
        verbose_name = "员工档案"

    def __str__(self):
        return f"{self.employee_no} {self.real_name}"


class Attendance(BaseModel):
    TYPES = [(1, "正常"), (2, "迟到"), (3, "早退"), (4, "缺勤"), (5, "请假"), (6, "出差")]

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    attend_date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    attend_type = models.SmallIntegerField(choices=TYPES, default=1)
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    remark = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "hr_attendance"
        verbose_name = "考勤记录"
        unique_together = ("employee", "attend_date")


class Salary(BaseModel):
    STATUS = [(0, "草稿"), (1, "已审核"), (2, "已发放")]

    salary_no = models.CharField(max_length=32, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    period = models.CharField(max_length=7)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    social_security = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.SmallIntegerField(choices=STATUS, default=0)
    pay_date = models.DateField(null=True, blank=True)
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "hr_salary"
        verbose_name = "薪资单"
        unique_together = ("employee", "period")
