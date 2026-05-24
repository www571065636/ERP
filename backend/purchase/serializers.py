from rest_framework import serializers as drf_serializers
from django.db import transaction
from decimal import Decimal
import datetime

from .models import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseReceipt, PurchaseReceiptItem
from common.services import quantize_qty, quantize_amount, make_doc_no


class SupplierSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "supplier_code", "supplier_name", "short_name", "contact_person",
                  "contact_phone", "email", "address", "bank_name", "bank_account",
                  "tax_no", "payment_terms", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrderItemSerializer(drf_serializers.ModelSerializer):
    product_name = drf_serializers.SerializerMethodField()
    product_code = drf_serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderItem
        fields = ["id", "line_no", "product_id", "product_code", "product_name",
                  "sku_id", "unit_id", "qty", "unit_price", "tax_rate",
                  "tax_amount", "amount", "received_qty", "remark"]
        read_only_fields = ["id", "line_no", "received_qty", "product_code", "product_name"]

    def get_product_name(self, obj):
        return self.context.get("product_map", {}).get(obj.product_id, {}).get("product_name", "")

    def get_product_code(self, obj):
        return self.context.get("product_map", {}).get(obj.product_id, {}).get("product_code", "")


class PurchaseOrderSerializer(drf_serializers.ModelSerializer):
    supplier_name = drf_serializers.CharField(source="supplier.supplier_name", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_label = drf_serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ["id", "order_no", "supplier", "supplier_name", "warehouse_id", "buyer_id",
                  "order_date", "expected_date", "currency", "total_qty", "total_amount",
                  "tax_amount", "status", "status_label", "approve_by", "approve_at",
                  "approve_remark", "remark", "created_at", "items"]
        read_only_fields = ["id", "order_no", "created_at", "total_qty", "total_amount", "tax_amount"]


class ReceiptItemSerializer(drf_serializers.Serializer):
    order_item_id = drf_serializers.IntegerField()
    qty = drf_serializers.DecimalField(max_digits=15, decimal_places=4)
    remark = drf_serializers.CharField(required=False, allow_blank=True, default="")


class PurchaseReceiptSerializer(drf_serializers.ModelSerializer):
    items = drf_serializers.SerializerMethodField()
    status_label = drf_serializers.SerializerMethodField()

    class Meta:
        model = PurchaseReceipt
        fields = ["id", "receipt_no", "order", "warehouse_id", "receipt_date", "operator_id",
                  "status", "status_label", "remark", "created_at", "items"]

    def get_items(self, obj):
        return [{
            "id": item.id,
            "order_item_id": item.order_item_id,
            "product_id": item.product_id,
            "sku_id": item.sku_id,
            "unit_id": item.unit_id,
            "qty": item.qty,
            "remark": item.remark,
        } for item in obj.items.all()]

    def get_status_label(self, obj):
        return {0: "草稿", 1: "已确认"}.get(obj.status, "未知")


class PurchaseOrderWriteSerializer(drf_serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "warehouse_id", "order_date", "expected_date",
                  "currency", "remark", "items"]

    def validate_items(self, items):
        if not items:
            raise drf_serializers.ValidationError("采购明细不能为空")
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order_no = f"PO{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        order = PurchaseOrder.objects.create(order_no=order_no, **validated_data)
        self.sync_items(order, items_data)
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.status != 0:
            raise drf_serializers.ValidationError("只有草稿状态可以编辑")
        items_data = validated_data.pop("items")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self.sync_items(instance, items_data)
        return instance

    def sync_items(self, order, items_data):
        existing_items = {item.id: item for item in order.items.all()}
        seen_ids = set()
        total_qty = Decimal("0.0000")
        total_amount = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for index, item_data in enumerate(items_data, 1):
            item_id = item_data.get("id")
            qty = quantize_qty(item_data.get("qty"))
            unit_price = quantize_qty(item_data.get("unit_price"))
            item_tax_rate = quantize_amount(item_data.get("tax_rate"))
            line_tax_amount = quantize_amount(qty * unit_price * item_tax_rate / Decimal("100"))
            line_amount = quantize_amount(qty * unit_price)
            payload = {
                "line_no": index,
                "product_id": item_data.get("product_id"),
                "sku_id": item_data.get("sku_id"),
                "unit_id": item_data.get("unit_id"),
                "qty": qty,
                "unit_price": unit_price,
                "tax_rate": item_tax_rate,
                "tax_amount": line_tax_amount,
                "amount": line_amount,
                "remark": item_data.get("remark", ""),
            }
            if item_id:
                order_item = existing_items.get(item_id)
                if not order_item:
                    raise drf_serializers.ValidationError(f"明细项 {item_id} 不存在")
                if qty < order_item.received_qty:
                    raise drf_serializers.ValidationError(f"第 {index} 行数量不能小于已收货数量")
                for attr, value in payload.items():
                    setattr(order_item, attr, value)
                order_item.save()
                seen_ids.add(item_id)
            else:
                PurchaseOrderItem.objects.create(order=order, **payload)
            total_qty += qty
            total_amount += line_amount
            tax_amount += line_tax_amount

        for item_id, order_item in existing_items.items():
            if item_id in seen_ids:
                continue
            if order_item.received_qty > 0:
                raise drf_serializers.ValidationError(f"第 {order_item.line_no} 行已收货，不能删除")
            if PurchaseReceiptItem.objects.filter(order_item=order_item).exists():
                raise drf_serializers.ValidationError(f"第 {order_item.line_no} 行已有关联收货记录，不能删除")
            order_item.delete()

        order.total_qty = total_qty
        order.total_amount = total_amount
        order.tax_amount = tax_amount
        order.save(update_fields=["total_qty", "total_amount", "tax_amount"])
