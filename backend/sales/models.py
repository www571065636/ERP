from django.db import models
from common.models import BaseModel


class Customer(BaseModel):
    customer_code = models.CharField(max_length=64, unique=True)
    customer_name = models.CharField(max_length=128)
    customer_type = models.SmallIntegerField(default=1)
    contact_person = models.CharField(max_length=64, blank=True, default="")
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    credit_used = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_terms = models.CharField(max_length=128, blank=True, default="")
    salesperson_id = models.BigIntegerField(null=True, blank=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "sal_customer"
        verbose_name = "客户"

    def __str__(self):
        return self.customer_name


class SalesOrder(BaseModel):
    STATUS_CHOICES = [
        (0, "草稿"), (1, "待审批"), (2, "已审批"),
        (3, "部分发货"), (4, "全部发货"), (5, "已关闭"), (9, "已取消"),
    ]
    order_no = models.CharField(max_length=32, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    salesperson_id = models.BigIntegerField()
    warehouse_id = models.BigIntegerField()
    order_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=8, default="CNY")
    total_qty = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.SmallIntegerField(default=0, choices=STATUS_CHOICES)
    approve_by = models.BigIntegerField(null=True, blank=True)
    approve_at = models.DateTimeField(null=True, blank=True)
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "sal_order"
        verbose_name = "销售订单"

    def __str__(self):
        return self.order_no


class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    line_no = models.IntegerField()
    product_id = models.BigIntegerField()
    sku_id = models.BigIntegerField(null=True, blank=True)
    unit_id = models.BigIntegerField()
    qty = models.DecimalField(max_digits=15, decimal_places=4)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    delivered_qty = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    remark = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "sal_order_item"


class Delivery(BaseModel):
    delivery_no = models.CharField(max_length=32, unique=True)
    order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name="deliveries")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    warehouse_id = models.BigIntegerField()
    delivery_date = models.DateTimeField()
    logistics_co = models.CharField(max_length=64, blank=True, default="")
    tracking_no = models.CharField(max_length=64, blank=True, default="")
    receiver_name = models.CharField(max_length=64, blank=True, default="")
    receiver_phone = models.CharField(max_length=20, blank=True, default="")
    receiver_addr = models.CharField(max_length=255, blank=True, default="")
    status = models.SmallIntegerField(default=0)
    operator_id = models.BigIntegerField()
    remark = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "sal_delivery"
        verbose_name = "发货单"

    def __str__(self):
        return self.delivery_no
