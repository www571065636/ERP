from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import datetime

from .models import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseReceipt, PurchaseReceiptItem
from common.response import ok, fail


class SupplierSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "supplier_code", "supplier_name", "short_name", "contact_person",
                  "contact_phone", "email", "address", "bank_name", "bank_account",
                  "tax_no", "payment_terms", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrderItemSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ["id", "line_no", "product_id", "sku_id", "unit_id",
                  "qty", "unit_price", "tax_rate", "tax_amount", "amount", "received_qty", "remark"]
        read_only_fields = ["id", "line_no", "received_qty"]


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


class PurchaseOrderCreateSerializer(drf_serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "warehouse_id", "order_date", "expected_date",
                  "currency", "remark", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order_no = f"PO{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        order = PurchaseOrder.objects.create(order_no=order_no, **validated_data)
        total_qty = total_amount = tax_amount = 0
        for i, item_data in enumerate(items_data, 1):
            item_data["line_no"] = i
            item_data["tax_amount"] = round(
                float(item_data["qty"]) * float(item_data["unit_price"]) *
                float(item_data.get("tax_rate", 0)) / 100, 2
            )
            item_data["amount"] = round(float(item_data["qty"]) * float(item_data["unit_price"]), 2)
            PurchaseOrderItem.objects.create(order=order, **item_data)
            total_qty += float(item_data["qty"])
            total_amount += item_data["amount"]
            tax_amount += item_data["tax_amount"]
        order.total_qty = total_qty
        order.total_amount = total_amount
        order.tax_amount = tax_amount
        order.save(update_fields=["total_qty", "total_amount", "tax_amount"])
        return order


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.filter(is_deleted=False)
    serializer_class = SupplierSerializer
    filter_backends = [SearchFilter]
    search_fields = ["supplier_code", "supplier_name", "contact_person"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.filter(is_deleted=False).select_related("supplier").order_by("-created_at")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status", "supplier"]
    search_fields = ["order_no"]

    def get_serializer_class(self):
        if self.action == "create":
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id, buyer_id=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 0:
            return fail("只有草稿状态可以删除")
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        order = self.get_object()
        if order.status != 0:
            return fail("只有草稿状态可以提交")
        order.status = 1
        order.save(update_fields=["status"])
        return ok(msg="提交成功")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        order = self.get_object()
        if order.status != 1:
            return fail("只有待审批状态可以审批")
        if request.data.get("action", "approve") == "approve":
            order.status = 2
            order.approve_by = request.user.id
            order.approve_at = timezone.now()
            order.approve_remark = request.data.get("remark", "")
            order.save(update_fields=["status", "approve_by", "approve_at", "approve_remark"])
            return ok(msg="审批通过")
        order.status = 0
        order.approve_remark = request.data.get("remark", "")
        order.save(update_fields=["status", "approve_remark"])
        return ok(msg="已驳回")
