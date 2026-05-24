from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseReceipt, PurchaseReceiptItem
from common.permissions import HasPermCode
from common.response import ok, fail
from common.services import (
    ZERO_QTY,
    adjust_stock,
    ensure_payable_from_purchase,
    make_doc_no,
    quantize_amount,
    quantize_qty,
)
from product.models import Product

from .serializers import (
    SupplierSerializer,
    OrderItemSerializer,
    PurchaseOrderSerializer,
    ReceiptItemSerializer,
    PurchaseReceiptSerializer,
    PurchaseOrderWriteSerializer,
)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.filter(is_deleted=False)
    serializer_class = SupplierSerializer
    filter_backends = [SearchFilter]
    search_fields = ["supplier_code", "supplier_name", "contact_person"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "purchase:supplier:list",
        "retrieve": "purchase:supplier:list",
        "create": "purchase:supplier:create",
        "update": "purchase:supplier:update",
        "partial_update": "purchase:supplier:update",
        "destroy": "purchase:supplier:delete",
    }

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
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "purchase:order:list",
        "retrieve": "purchase:order:list",
        "create": "purchase:order:create",
        "update": "purchase:order:update",
        "partial_update": "purchase:order:update",
        "destroy": "purchase:order:delete",
        "submit": "purchase:order:submit",
        "approve": "purchase:order:approve",
        "receipts": ["purchase:order:approve"],
        "confirm_receipt": ["purchase:order:approve"],
    }

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PurchaseOrderWriteSerializer
        return PurchaseOrderSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action in ("list", "retrieve"):
            product_ids = set()
            if self.action == "retrieve":
                order = self.get_object()
                for item in order.items.all():
                    product_ids.add(item.product_id)
            elif self.action == "list":
                qs = self.filter_queryset(self.get_queryset())
                page = self.paginate_queryset(qs)
                data_source = page if page is not None else qs
                order_ids = [o.id for o in data_source]
                for pid, in PurchaseOrderItem.objects.filter(
                    order_id__in=order_ids
                ).values_list("product_id").distinct():
                    product_ids.add(pid)
            prods = Product.objects.filter(id__in=product_ids, is_deleted=False).only("id", "product_code", "product_name")
            ctx["product_map"] = {p.id: {"product_code": p.product_code, "product_name": p.product_name} for p in prods}
        return ctx

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id, buyer_id=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.id)

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
        action = request.data.get("action")
        if action not in ("approve", "reject"):
            return fail("action 必须为 approve 或 reject")
        if action == "approve":
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

    @action(detail=True, methods=["get", "post"])
    def receipts(self, request, pk=None):
        order = self.get_object()
        if request.method == "GET":
            data = PurchaseReceiptSerializer(order.receipts.order_by("-created_at"), many=True).data
            return ok(data)
        if order.status not in [2, 3]:
            return fail("只有已审批或部分收货状态可以创建收货单")
        serializer = drf_serializers.ListSerializer(
            child=ReceiptItemSerializer(), data=request.data.get("items", [])
        )
        serializer.is_valid(raise_exception=True)
        items = serializer.validated_data
        if not items:
            return fail("收货明细不能为空")
        with transaction.atomic():
            order_items = {item.id: item for item in order.items.all()}
            receipt = PurchaseReceipt.objects.create(
                receipt_no=make_doc_no("PR"),
                order=order,
                warehouse_id=order.warehouse_id,
                receipt_date=timezone.now(),
                operator_id=request.user.id,
                status=0,
                remark=request.data.get("remark", ""),
                created_by=request.user.id,
            )
            for payload in items:
                order_item = order_items.get(payload["order_item_id"])
                if not order_item:
                    raise drf_serializers.ValidationError(f"订单明细 {payload['order_item_id']} 不存在")
                qty = quantize_qty(payload["qty"])
                remaining = quantize_qty(order_item.qty) - quantize_qty(order_item.received_qty)
                if qty <= 0:
                    raise drf_serializers.ValidationError("收货数量必须大于0")
                if qty > remaining:
                    raise drf_serializers.ValidationError(f"明细 {order_item.line_no} 收货数量超过未收数量")
                PurchaseReceiptItem.objects.create(
                    receipt=receipt,
                    order_item=order_item,
                    product_id=order_item.product_id,
                    sku_id=order_item.sku_id,
                    unit_id=order_item.unit_id,
                    qty=qty,
                    remark=payload.get("remark", ""),
                )
        return ok(PurchaseReceiptSerializer(receipt).data, msg="收货单创建成功")

    @action(detail=True, methods=["post"], url_path="receipts/(?P<receipt_id>[^/.]+)/confirm")
    def confirm_receipt(self, request, pk=None, receipt_id=None):
        order = self.get_object()
        try:
            receipt = order.receipts.prefetch_related("items").get(id=receipt_id)
        except PurchaseReceipt.DoesNotExist:
            return fail("收货单不存在", 404)
        if receipt.status == 1:
            return fail("收货单已确认")
        with transaction.atomic():
            total_received = ZERO_QTY
            for item in receipt.items.select_related("order_item"):
                order_item = item.order_item
                new_received = quantize_qty(order_item.received_qty) + quantize_qty(item.qty)
                if new_received > quantize_qty(order_item.qty):
                    return fail(f"明细 {order_item.line_no} 累计收货数量超限")
                order_item.received_qty = new_received
                order_item.save(update_fields=["received_qty"])
                total_received += new_received
                adjust_stock(
                    warehouse_id=receipt.warehouse_id,
                    product_id=item.product_id,
                    sku_id=item.sku_id,
                    qty_delta=item.qty,
                    unit_cost=order_item.unit_price,
                    operator_id=request.user.id,
                    txn_type="PURCHASE_IN",
                    ref_type="PURCHASE_RECEIPT",
                    ref_id=receipt.id,
                    remark=f"采购收货 {receipt.receipt_no}",
                )

            total_order_qty = quantize_qty(order.total_qty)
            order.status = 4 if total_received >= total_order_qty else 3
            order.updated_by = request.user.id
            order.save(update_fields=["status", "updated_by", "updated_at"])
            receipt.status = 1
            receipt.updated_by = request.user.id
            receipt.save(update_fields=["status", "updated_by", "updated_at"])
            ensure_payable_from_purchase(order)
        return ok(msg="收货确认成功")
