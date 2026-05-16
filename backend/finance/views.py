from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import datetime

from .models import Account, Voucher, VoucherItem, Receivable, Payable
from common.response import ok, fail


class AccountSerializer(drf_serializers.ModelSerializer):
    account_type_label = drf_serializers.CharField(source="get_account_type_display", read_only=True)

    class Meta:
        model = Account
        fields = ["id", "parent_id", "account_code", "account_name", "account_type",
                  "account_type_label", "balance_dir", "level", "is_leaf", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class VoucherItemSerializer(drf_serializers.ModelSerializer):
    account_name = drf_serializers.CharField(source="account.account_name", read_only=True)
    account_code = drf_serializers.CharField(source="account.account_code", read_only=True)

    class Meta:
        model = VoucherItem
        fields = ["id", "line_no", "account", "account_code", "account_name",
                  "summary", "debit_amount", "credit_amount"]


class VoucherSerializer(drf_serializers.ModelSerializer):
    items = VoucherItemSerializer(many=True, read_only=True)
    status_label = drf_serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Voucher
        fields = ["id", "voucher_no", "voucher_type", "voucher_date", "period",
                  "total_debit", "total_credit", "status", "status_label",
                  "preparer_id", "reviewer_id", "review_at", "remark", "created_at", "items"]
        read_only_fields = ["id", "voucher_no", "created_at", "total_debit", "total_credit"]


class VoucherCreateSerializer(drf_serializers.ModelSerializer):
    items = VoucherItemSerializer(many=True)

    class Meta:
        model = Voucher
        fields = ["voucher_type", "voucher_date", "remark", "items"]

    def validate_items(self, items):
        if not items:
            raise drf_serializers.ValidationError("凭证明细不能为空")
        total_debit = sum(float(i.get("debit_amount", 0)) for i in items)
        total_credit = sum(float(i.get("credit_amount", 0)) for i in items)
        if round(total_debit, 2) != round(total_credit, 2):
            raise drf_serializers.ValidationError("借贷方合计必须相等")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        voucher_date = validated_data["voucher_date"]
        period = voucher_date.strftime("%Y-%m")
        voucher_no = f"V{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        total_debit = sum(float(i.get("debit_amount", 0)) for i in items_data)
        total_credit = sum(float(i.get("credit_amount", 0)) for i in items_data)
        voucher = Voucher.objects.create(
            voucher_no=voucher_no, period=period,
            total_debit=total_debit, total_credit=total_credit,
            **validated_data
        )
        for i, item in enumerate(items_data, 1):
            item["line_no"] = i
            VoucherItem.objects.create(voucher=voucher, **item)
        return voucher


class ReceivableSerializer(drf_serializers.ModelSerializer):
    status_label = drf_serializers.CharField(source="get_status_display", read_only=True)
    balance = drf_serializers.SerializerMethodField()

    class Meta:
        model = Receivable
        fields = ["id", "receivable_no", "customer_id", "ref_type", "ref_id",
                  "amount", "received_amount", "balance", "due_date",
                  "status", "status_label", "remark", "created_at"]
        read_only_fields = ["id", "receivable_no", "created_at"]

    def get_balance(self, obj):
        return float(obj.amount) - float(obj.received_amount)


class PayableSerializer(drf_serializers.ModelSerializer):
    status_label = drf_serializers.CharField(source="get_status_display", read_only=True)
    balance = drf_serializers.SerializerMethodField()

    class Meta:
        model = Payable
        fields = ["id", "payable_no", "supplier_id", "ref_type", "ref_id",
                  "amount", "paid_amount", "balance", "due_date",
                  "status", "status_label", "remark", "created_at"]
        read_only_fields = ["id", "payable_no", "created_at"]

    def get_balance(self, obj):
        return float(obj.amount) - float(obj.paid_amount)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.filter(is_deleted=False).order_by("account_code")
    serializer_class = AccountSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["account_code", "account_name"]
    filterset_fields = ["account_type", "status", "is_leaf"]

    @action(detail=False, methods=["get"])
    def tree(self, request):
        accounts = Account.objects.filter(is_deleted=False, status=True).order_by("account_code")
        data = [AccountSerializer(a).data for a in accounts]
        tree = self._build_tree(data, 0)
        return ok(data=tree)

    def _build_tree(self, items, parent_id):
        result = []
        for item in items:
            if item["parent_id"] == parent_id:
                item["children"] = self._build_tree(items, item["id"])
                result.append(item)
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

    def perform_create(self, serializer):
        no = f"AR{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        serializer.save(created_by=self.request.user.id, receivable_no=no)

    @action(detail=True, methods=["post"])
    def payments(self, request, pk=None):
        receivable = self.get_object()
        amount = float(request.data.get("amount", 0))
        if amount <= 0:
            return fail("收款金额必须大于0")
        balance = float(receivable.amount) - float(receivable.received_amount)
        if amount > balance:
            return fail(f"收款金额不能超过未收余额 {balance}")
        receivable.received_amount = float(receivable.received_amount) + amount
        if float(receivable.received_amount) >= float(receivable.amount):
            receivable.status = 2
        else:
            receivable.status = 1
        receivable.save(update_fields=["received_amount", "status"])
        return ok(msg="收款登记成功")


class PayableViewSet(viewsets.ModelViewSet):
    queryset = Payable.objects.filter(is_deleted=False).order_by("-created_at")
    serializer_class = PayableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["supplier_id", "status"]

    def perform_create(self, serializer):
        no = f"AP{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        serializer.save(created_by=self.request.user.id, payable_no=no)

    @action(detail=True, methods=["post"])
    def payments(self, request, pk=None):
        payable = self.get_object()
        amount = float(request.data.get("amount", 0))
        if amount <= 0:
            return fail("付款金额必须大于0")
        balance = float(payable.amount) - float(payable.paid_amount)
        if amount > balance:
            return fail(f"付款金额不能超过未付余额 {balance}")
        payable.paid_amount = float(payable.paid_amount) + amount
        if float(payable.paid_amount) >= float(payable.amount):
            payable.status = 2
        else:
            payable.status = 1
        payable.save(update_fields=["paid_amount", "status"])
        return ok(msg="付款登记成功")
