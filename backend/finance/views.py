from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from decimal import Decimal
import datetime

from .models import Account, Voucher, Receivable, Payable
from .serializers import AccountSerializer, VoucherItemSerializer, VoucherSerializer, VoucherCreateSerializer, ReceivableSerializer, PayableSerializer
from common.permissions import HasPermCode
from common.response import ok, fail


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.filter(is_deleted=False).order_by("account_code")
    serializer_class = AccountSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["account_code", "account_name"]
    filterset_fields = ["account_type", "status", "is_leaf"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "finance:account:list",
        "retrieve": "finance:account:list",
        "tree": "finance:account:list",
        "create": "finance:account:create",
        "update": "finance:account:update",
        "partial_update": "finance:account:update",
        "destroy": "finance:account:delete",
    }

    @action(detail=False, methods=["get"])
    def tree(self, request):
        accounts = Account.objects.filter(is_deleted=False, status=True).order_by("account_code")
        data = [AccountSerializer(a).data for a in accounts]
        tree = self._build_tree(data)
        return ok(data=tree)

    def _build_tree(self, items):
        """O(n) 树构建：先按 parent_id 分组，再递归组装"""
        by_parent = {}
        for item in items:
            by_parent.setdefault(item["parent_id"], []).append(item)
        result = []
        stack = [(item, result) for item in by_parent.get(0, [])]
        for item, parent_children in stack:
            parent_children.append(item)
            children = by_parent.get(item["id"], [])
            item["children"] = children
            stack.extend((child, children) for child in children)
        return result

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.filter(is_deleted=False).order_by("-voucher_date", "-created_at")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status", "voucher_type", "period"]
    search_fields = ["voucher_no"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "finance:voucher:list",
        "retrieve": "finance:voucher:list",
        "create": "finance:voucher:create",
        "destroy": "finance:voucher:delete",
        "review": "finance:voucher:review",
        "post_voucher": "finance:voucher:post",
    }

    def get_serializer_class(self):
        if self.action == "create":
            return VoucherCreateSerializer
        return VoucherSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id, preparer_id=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 0:
            return fail("只有草稿状态可以删除")
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        voucher = self.get_object()
        if voucher.status != 0:
            return fail("只有草稿状态可以审核")
        voucher.status = 1
        voucher.reviewer_id = request.user.id
        voucher.review_at = timezone.now()
        voucher.save(update_fields=["status", "reviewer_id", "review_at"])
        return ok(msg="审核成功")

    @action(detail=True, methods=["post"])
    def post_voucher(self, request, pk=None):
        voucher = self.get_object()
        if voucher.status != 1:
            return fail("只有已审核状态可以过账")
        voucher.status = 2
        voucher.save(update_fields=["status"])
        return ok(msg="过账成功")


class ReceivableViewSet(viewsets.ModelViewSet):
    queryset = Receivable.objects.filter(is_deleted=False).order_by("-created_at")
    serializer_class = ReceivableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["customer_id", "status"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "finance:receivable:list",
        "retrieve": "finance:receivable:list",
        "create": "finance:receivable:create",
        "update": "finance:receivable:update",
        "partial_update": "finance:receivable:update",
        "destroy": "finance:receivable:delete",
        "payments": "finance:receivable:payment",
    }

    def perform_create(self, serializer):
        no = f"AR{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        serializer.save(created_by=self.request.user.id, receivable_no=no)

    @action(detail=True, methods=["post"])
    def payments(self, request, pk=None):
        with transaction.atomic():
            receivable = Receivable.objects.select_for_update().get(pk=pk, is_deleted=False)
            amount = Decimal(str(request.data.get("amount", 0)))
            if amount <= 0:
                return fail("收款金额必须大于0")
            receivable_amount = Decimal(str(receivable.amount))
            received = Decimal(str(receivable.received_amount))
            balance = receivable_amount - received
            if amount > balance:
                return fail(f"收款金额不能超过未收余额 {float(balance):.2f}")
            received = received + amount
            receivable.received_amount = received
            receivable.status = 2 if received >= receivable_amount else 1
            receivable.save(update_fields=["received_amount", "status"])
        return ok(msg="收款登记成功")


class PayableViewSet(viewsets.ModelViewSet):
    queryset = Payable.objects.filter(is_deleted=False).order_by("-created_at")
    serializer_class = PayableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["supplier_id", "status"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "finance:payable:list",
        "retrieve": "finance:payable:list",
        "create": "finance:payable:create",
        "update": "finance:payable:update",
        "partial_update": "finance:payable:update",
        "destroy": "finance:payable:delete",
        "payments": "finance:payable:payment",
    }

    def perform_create(self, serializer):
        no = f"AP{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        serializer.save(created_by=self.request.user.id, payable_no=no)

    @action(detail=True, methods=["post"])
    def payments(self, request, pk=None):
        with transaction.atomic():
            payable = Payable.objects.select_for_update().get(pk=pk, is_deleted=False)
            amount = Decimal(str(request.data.get("amount", 0)))
            if amount <= 0:
                return fail("付款金额必须大于0")
            payable_amount = Decimal(str(payable.amount))
            paid = Decimal(str(payable.paid_amount))
            balance = payable_amount - paid
            if amount > balance:
                return fail(f"付款金额不能超过未付余额 {float(balance):.2f}")
            paid = paid + amount
            payable.paid_amount = paid
            payable.status = 2 if paid >= payable_amount else 1
            payable.save(update_fields=["paid_amount", "status"])
        return ok(msg="付款登记成功")
