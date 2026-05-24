from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Customer, SalesOrder, SalesOrderItem, Delivery, DeliveryItem
from common.permissions import HasPermCode
from common.response import ok, fail
from common.services import (
    ZERO_QTY,
    adjust_stock,
    ensure_receivable_from_sales,
    make_doc_no,
    quantize_amount,
    quantize_qty,
)
from product.models import Product

from .serializers import (
    CustomerSerializer,
    SalesOrderItemSerializer,
    SalesOrderSerializer,
    DeliveryItemSerializer,
    DeliverySerializer,
    SalesOrderWriteSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.filter(is_deleted=False)
    serializer_class = CustomerSerializer
    filter_backends = [SearchFilter]
    search_fields = ["customer_code", "customer_name", "contact_person"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "sales:customer:list",
        "retrieve": "sales:customer:list",
        "create": "sales:customer:create",
        "update": "sales:customer:update",
        "partial_update": "sales:customer:update",
        "destroy": "sales:customer:delete",
    }

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.filter(is_deleted=False).select_related("customer").order_by("-created_at")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status", "customer"]
    search_fields = ["order_no"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "sales:order:list",
        "retrieve": "sales:order:list",
        "create": "sales:order:create",
        "update": "sales:order:update",
        "partial_update": "sales:order:update",
        "destroy": "sales:order:delete",
        "submit": "sales:order:submit",
        "approve": "sales:order:approve",
        "deliveries": ["sales:order:approve"],
        "confirm_delivery": ["sales:order:approve"],
    }

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SalesOrderWriteSerializer
        return SalesOrderSerializer

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
                for pid, in SalesOrderItem.objects.filter(
                    order_id__in=order_ids
                ).values_list("product_id").distinct():
                    product_ids.add(pid)
            prods = Product.objects.filter(id__in=product_ids, is_deleted=False).only("id", "product_code", "product_name")
            ctx["product_map"] = {p.id: {"product_code": p.product_code, "product_name": p.product_name} for p in prods}
        return ctx

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id, salesperson_id=self.request.user.id)

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
            order.save(update_fields=["status", "approve_by", "approve_at"])
            return ok(msg="审批通过")
        order.status = 0
        order.save(update_fields=["status"])
        return ok(msg="已驳回")

    @action(detail=True, methods=["get", "post"])
    def deliveries(self, request, pk=None):
        order = self.get_object()
        if request.method == "GET":
            data = DeliverySerializer(order.deliveries.order_by("-created_at"), many=True).data
            return ok(data)
        if order.status not in [2, 3]:
            return fail("只有已审批或部分发货状态可以创建发货单")
        serializer = drf_serializers.ListSerializer(
            child=DeliveryItemSerializer(), data=request.data.get("items", [])
        )
        serializer.is_valid(raise_exception=True)
        items = serializer.validated_data
        if not items:
            return fail("发货明细不能为空")
        with transaction.atomic():
            order_items = {item.id: item for item in order.items.all()}
            delivery = Delivery.objects.create(
                delivery_no=make_doc_no("DO"),
                order=order,
                customer=order.customer,
                warehouse_id=order.warehouse_id,
                delivery_date=timezone.now(),
                logistics_co=request.data.get("logistics_co", ""),
                tracking_no=request.data.get("tracking_no", ""),
                receiver_name=request.data.get("receiver_name", ""),
                receiver_phone=request.data.get("receiver_phone", ""),
                receiver_addr=request.data.get("receiver_addr", ""),
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
                remaining = quantize_qty(order_item.qty) - quantize_qty(order_item.delivered_qty)
                if qty <= 0:
                    raise drf_serializers.ValidationError("发货数量必须大于0")
                if qty > remaining:
                    raise drf_serializers.ValidationError(f"明细 {order_item.line_no} 发货数量超过未发数量")
                DeliveryItem.objects.create(
                    delivery=delivery,
                    order_item=order_item,
                    product_id=order_item.product_id,
                    sku_id=order_item.sku_id,
                    unit_id=order_item.unit_id,
                    qty=qty,
                    remark=payload.get("remark", ""),
                )
        return ok(DeliverySerializer(delivery).data, msg="发货单创建成功")

    @action(detail=True, methods=["post"], url_path="deliveries/(?P<delivery_id>[^/.]+)/confirm")
    def confirm_delivery(self, request, pk=None, delivery_id=None):
        order = self.get_object()
        try:
            delivery = order.deliveries.prefetch_related("items").get(id=delivery_id)
        except Delivery.DoesNotExist:
            return fail("发货单不存在", 404)
        if delivery.status == 1:
            return fail("发货单已确认")
        with transaction.atomic():
            total_delivered = ZERO_QTY
            for item in delivery.items.select_related("order_item"):
                order_item = item.order_item
                new_delivered = quantize_qty(order_item.delivered_qty) + quantize_qty(item.qty)
                if new_delivered > quantize_qty(order_item.qty):
                    return fail(f"明细 {order_item.line_no} 累计发货数量超限")
                adjust_stock(
                    warehouse_id=delivery.warehouse_id,
                    product_id=item.product_id,
                    sku_id=item.sku_id,
                    qty_delta=-quantize_qty(item.qty),
                    unit_cost=order_item.unit_price,
                    operator_id=request.user.id,
                    txn_type="SALE_OUT",
                    ref_type="SALES_DELIVERY",
                    ref_id=delivery.id,
                    remark=f"销售发货 {delivery.delivery_no}",
                )
                order_item.delivered_qty = new_delivered
                order_item.save(update_fields=["delivered_qty"])
                total_delivered += new_delivered

            total_order_qty = quantize_qty(order.total_qty)
            order.status = 4 if total_delivered >= total_order_qty else 3
            order.updated_by = request.user.id
            order.save(update_fields=["status", "updated_by", "updated_at"])
            delivery.status = 1
            delivery.updated_by = request.user.id
            delivery.save(update_fields=["status", "updated_by", "updated_at"])
            ensure_receivable_from_sales(order)
        return ok(msg="发货确认成功")
