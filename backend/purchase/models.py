from django.db import models
from common.models import BaseModel
from common.validators import phone_validator, email_validator


class Supplier(BaseModel):
    supplier_code = models.CharField(max_length=64, unique=True)
    supplier_name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=64, blank=True, default="")
    contact_person = models.CharField(max_length=64, blank=True, default="")
    contact_phone = models.CharField(max_length=20, blank=True, default="", validators=[phone_validator])
    email = models.EmailField(blank=True, default="", validators=[email_validator])
    address = models.CharField(max_length=255, blank=True, default="")
    bank_name = models.CharField(max_length=128, blank=True, default="")
    bank_account = models.CharField(max_length=64, blank=True, default="")
    tax_no = models.CharField(max_length=64, blank=True, default="")
    payment_terms = models.CharField(max_length=128, blank=True, default="")
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "pur_supplier"
        verbose_name = "供应商"

    def __str__(self):
        return self.supplier_name


class PurchaseOrder(BaseModel):
    STATUS_CHOICES = [
        (0, "草稿"), (1, "待审批"), (2, "已审批"),
        (3, "部分收货"), (4, "全部收货"), (5, "已关闭"), (9, "已取消"),
    ]
    order_no = models.CharField(max_length=32, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    warehouse_id = models.BigIntegerField()
    buyer_id = models.BigIntegerField()
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=8, default="CNY")
    total_qty = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.SmallIntegerField(default=0, choices=STATUS_CHOICES)
    approve_by = models.BigIntegerField(null=True, blank=True)
    approve_at = models.DateTimeField(null=True, blank=True)
    approve_remark = models.CharField(max_length=500, blank=True, default="")
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "pur_order"
        verbose_name = "采购订单"

    def __str__(self):
        return self.order_no


class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    line_no = models.IntegerField()
    product_id = models.BigIntegerField()
    sku_id = models.BigIntegerField(null=True, blank=True)
    unit_id = models.BigIntegerField()
    qty = models.DecimalField(max_digits=15, decimal_places=4)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    received_qty = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    remark = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "pur_order_item"


class PurchaseReceipt(BaseModel):
    receipt_no = models.CharField(max_length=32, unique=True)
    order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="receipts")
    warehouse_id = models.BigIntegerField()
    receipt_date = models.DateTimeField()
    operator_id = models.BigIntegerField()
    status = models.SmallIntegerField(default=0)
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "pur_receipt"
        verbose_name = "采购收货单"

    def __str__(self):
        return self.receipt_no


class PurchaseReceiptItem(models.Model):
    receipt = models.ForeignKey(PurchaseReceipt, on_delete=models.CASCADE, related_name="items")
    order_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT)
    product_id = models.BigIntegerField()
    sku_id = models.BigIntegerField(null=True, blank=True)
    unit_id = models.BigIntegerField()
    qty = models.DecimalField(max_digits=15, decimal_places=4)
    remark = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "pur_receipt_item"
