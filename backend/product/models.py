from django.db import models
from common.models import BaseModel


class Unit(BaseModel):
    unit_name = models.CharField(max_length=32, verbose_name="单位名称")
    unit_code = models.CharField(max_length=32, unique=True, verbose_name="单位编码")

    class Meta:
        db_table = "prd_unit"
        verbose_name = "计量单位"

    def __str__(self):
        return self.unit_name


class Category(BaseModel):
    parent_id = models.BigIntegerField(default=0, verbose_name="父分类ID")
    cat_name = models.CharField(max_length=64, verbose_name="分类名称")
    cat_code = models.CharField(max_length=64, blank=True, default="")
    level = models.SmallIntegerField(default=1)
    tree_path = models.CharField(max_length=500, blank=True, default="")
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "prd_category"
        verbose_name = "产品分类"

    def __str__(self):
        return self.cat_name


class Product(BaseModel):
    PRODUCT_TYPES = [(1, "成品"), (2, "原材料"), (3, "半成品"), (4, "服务")]

    product_code = models.CharField(max_length=64, unique=True, verbose_name="产品编码")
    product_name = models.CharField(max_length=128, verbose_name="产品名称")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)
    brand = models.CharField(max_length=64, blank=True, default="")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, null=True, blank=True)
    product_type = models.SmallIntegerField(default=1, choices=PRODUCT_TYPES)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    purchase_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    min_stock = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    max_stock = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    description = models.TextField(blank=True, default="")
    image_url = models.CharField(max_length=255, blank=True, default="")
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "prd_product"
        verbose_name = "产品"

    def __str__(self):
        return self.product_name


class SKU(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="skus")
    sku_code = models.CharField(max_length=64, unique=True)
    sku_name = models.CharField(max_length=128)
    spec_json = models.JSONField(null=True, blank=True)
    barcode = models.CharField(max_length=64, blank=True, default="")
    weight = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "prd_sku"
        verbose_name = "SKU"

    def __str__(self):
        return self.sku_name
