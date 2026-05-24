from django.db import models
from common.models import BaseModel


class Account(BaseModel):
    TYPES = [(1, "资产"), (2, "负债"), (3, "权益"), (4, "收入"), (5, "费用")]
    BALANCE_DIRS = [(1, "借"), (2, "贷")]

    parent_id = models.BigIntegerField(default=0, db_index=True)
    account_code = models.CharField(max_length=32)
    account_name = models.CharField(max_length=64)
    account_type = models.SmallIntegerField(choices=TYPES, db_index=True)
    balance_dir = models.SmallIntegerField(choices=BALANCE_DIRS)
    level = models.SmallIntegerField(default=1)
    is_leaf = models.BooleanField(default=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "fin_account"
        verbose_name = "会计科目"

    def __str__(self):
        return f"{self.account_code} {self.account_name}"


class Voucher(BaseModel):
    TYPES = [("GENERAL", "记账凭证"), ("RECEIVE", "收款凭证"), ("PAY", "付款凭证"), ("TRANSFER", "转账凭证")]
    STATUS = [(0, "草稿"), (1, "已审核"), (2, "已过账"), (9, "已作废")]

    voucher_no = models.CharField(max_length=32, unique=True)
    voucher_type = models.CharField(max_length=16, choices=TYPES, default="GENERAL")
    voucher_date = models.DateField()
    period = models.CharField(max_length=7, db_index=True)
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.SmallIntegerField(choices=STATUS, default=0, db_index=True)
    ref_type = models.CharField(max_length=32, blank=True, default="")
    ref_id = models.BigIntegerField(null=True, blank=True)
    preparer_id = models.BigIntegerField()
    reviewer_id = models.BigIntegerField(null=True, blank=True)
    review_at = models.DateTimeField(null=True, blank=True)
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "fin_voucher"
        verbose_name = "财务凭证"


class VoucherItem(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name="items")
    line_no = models.IntegerField()
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    summary = models.CharField(max_length=255)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = "fin_voucher_item"
        verbose_name = "凭证明细"


class Receivable(BaseModel):
    STATUS = [(0, "未收"), (1, "部分收"), (2, "全部收"), (9, "已核销")]

    receivable_no = models.CharField(max_length=32, unique=True)
    customer_id = models.BigIntegerField(db_index=True)
    ref_type = models.CharField(max_length=32, blank=True, default="")
    ref_id = models.BigIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    received_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.SmallIntegerField(choices=STATUS, default=0, db_index=True)
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "fin_receivable"
        verbose_name = "应收账款"
        indexes = [
            models.Index(fields=["ref_type", "ref_id"]),
        ]


class Payable(BaseModel):
    STATUS = [(0, "未付"), (1, "部分付"), (2, "全部付"), (9, "已核销")]

    payable_no = models.CharField(max_length=32, unique=True)
    supplier_id = models.BigIntegerField(db_index=True)
    ref_type = models.CharField(max_length=32, blank=True, default="")
    ref_id = models.BigIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.SmallIntegerField(choices=STATUS, default=0, db_index=True)
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "fin_payable"
        verbose_name = "应付账款"
        indexes = [
            models.Index(fields=["ref_type", "ref_id"]),
        ]
