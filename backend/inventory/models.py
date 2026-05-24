from django.db import models
from common.models import BaseModel


class Warehouse(BaseModel):
    TYPES = [(1, "原料仓"), (2, "成品仓"), (3, "在途仓"), (4, "退货仓")]
    warehouse_code = models.CharField(max_length=32, unique=True)
    warehouse_name = models.CharField(max_length=64)
    warehouse_type = models.SmallIntegerField(default=1, choices=TYPES, db_index=True)
    manager_id = models.BigIntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, default="")
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "inv_warehouse"
        verbose_name = "仓库"

    def __str__(self):
        return self.warehouse_name


class Stock(BaseModel):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    product_id = models.BigIntegerField(db_index=True)
    sku_id = models.BigIntegerField(null=True, blank=True)
    qty_available = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    qty_reserved = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    qty_in_transit = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    avg_cost = models.DecimalField(max_digits=15, decimal_places=6, default=0)

    class Meta:
        db_table = "inv_stock"
        verbose_name = "库存台账"
        unique_together = ("warehouse", "product_id", "sku_id")


class StockTransaction(models.Model):
    TXN_TYPES = [
        ("PURCHASE_IN", "采购入库"), ("SALE_OUT", "销售出库"),
        ("TRANSFER_IN", "调拨入库"), ("TRANSFER_OUT", "调拨出库"),
        ("ADJUST_IN", "盘盈调整"), ("ADJUST_OUT", "盘亏调整"),
        ("RETURN_IN", "销售退货入库"), ("RETURN_OUT", "采购退货出库"),
    ]
    txn_no = models.CharField(max_length=32, unique=True)
    txn_type = models.CharField(max_length=32, choices=TXN_TYPES, db_index=True)
    ref_type = models.CharField(max_length=32, blank=True, default="")
    ref_id = models.BigIntegerField(null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    product_id = models.BigIntegerField(db_index=True)
    sku_id = models.BigIntegerField(null=True, blank=True)
    qty_change = models.DecimalField(max_digits=15, decimal_places=4)
    qty_before = models.DecimalField(max_digits=15, decimal_places=4)
    qty_after = models.DecimalField(max_digits=15, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    operator_id = models.BigIntegerField()
    txn_time = models.DateTimeField(db_index=True)
    remark = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "inv_transaction"
        verbose_name = "库存流水"
        indexes = [
            models.Index(fields=["ref_type", "ref_id"]),
            models.Index(fields=["warehouse", "product_id"]),
        ]
