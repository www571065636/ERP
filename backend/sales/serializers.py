from rest_framework import serializers as drf_serializers
from django.db import transaction
from decimal import Decimal
import datetime

from .models import Customer, SalesOrder, SalesOrderItem, Delivery, DeliveryItem
from common.services import quantize_qty, quantize_amount, make_doc_no


class CustomerSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "customer_code", "customer_name", "customer_type", "contact_person",
                  "contact_phone", "email", "address", "credit_limit", "credit_used",
                  "payment_terms", "salesperson_id", "status", "created_at"]
        read_only_fields = ["id", "created_at", "credit_used"]


class SalesOrderItemSerializer(drf_serializers.ModelSerializer):
    product_name = drf_serializers.SerializerMethodField()
    product_code = drf_serializers.SerializerMethodField()

    class Meta:
        model = SalesOrderItem
        fields = ["id", "line_no", "product_id", "product_code", "product_name",
                  "sku_id", "unit_id", "qty", "unit_price", "tax_rate",
                  "tax_amount", "amount", "delivered_qty", "remark"]
        read_only_fields = ["id", "line_no", "delivered_qty", "product_code", "product_name"]

    def get_product_name(self, obj):
        return self.context.get("product_map", {}).get(obj.product_id, {}).get("product_name", "")

    def get_product_code(self, obj):
        return self.context.get("product_map", {}).get(obj.product_id, {}).get("product_code", "")


class SalesOrderSerializer(drf_serializers.ModelSerializer):
    customer_name = drf_serializers.CharField(source="customer.customer_name", read_only=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    status_label = drf_serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SalesOrder
        fields = ["id", "order_no", "customer", "customer_name", "salesperson_id", "warehouse_id",
                  "order_date", "delivery_date", "currency", "total_qty", "total_amount",
                  "tax_amount", "status", "status_label", "approve_by", "approve_at",
                  "remark", "created_at", "items"]
        read_only_fields = ["id", "order_no", "created_at", "total_qty", "total_amount", "tax_amount"]


class DeliveryItemSerializer(drf_serializers.Serializer):
    order_item_id = drf_serializers.IntegerField()
    qty = drf_serializers.DecimalField(max_digits=15, decimal_places=4)
    remark = drf_serializers.CharField(required=False, allow_blank=True, default="")


class DeliverySerializer(drf_serializers.ModelSerializer):
    items = drf_serializers.SerializerMethodField()
    status_label = drf_serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = ["id", "delivery_no", "order", "customer", "warehouse_id", "delivery_date",
                  "logistics_co", "tracking_no", "receiver_name", "receiver_phone", "receiver_addr",
                  "status", "status_label", "operator_id", "remark", "created_at", "items"]

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


class SalesOrderWriteSerializer(drf_serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = ["customer", "warehouse_id", "order_date", "delivery_date", "currency", "remark", "items"]

    def validate_items(self, items):
        if not items:
            raise drf_serializers.ValidationError("销售明细不能为空")
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order_no = f"SO{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        order = SalesOrder.objects.create(order_no=order_no, **validated_data)
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
                if qty < order_item.delivered_qty:
                    raise drf_serializers.ValidationError(f"第 {index} 行数量不能小于已发货数量")
                for attr, value in payload.items():
                    setattr(order_item, attr, value)
                order_item.save()
                seen_ids.add(item_id)
            else:
                SalesOrderItem.objects.create(order=order, **payload)
            total_qty += qty
            total_amount += line_amount
            tax_amount += line_tax_amount

        for item_id, order_item in existing_items.items():
            if item_id in seen_ids:
                continue
            if order_item.delivered_qty > 0:
                raise drf_serializers.ValidationError(f"第 {order_item.line_no} 行已发货，不能删除")
            order_item.delete()

        order.total_qty = total_qty
        order.total_amount = total_amount
        order.tax_amount = tax_amount
        order.save(update_fields=["total_qty", "total_amount", "tax_amount"])
