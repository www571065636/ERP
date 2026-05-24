from rest_framework import serializers as drf_serializers
from decimal import Decimal
import datetime

from .models import Account, Voucher, VoucherItem, Receivable, Payable


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
        read_only_fields = ["id", "line_no"]


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
        fields = ["id", "voucher_no", "voucher_type", "voucher_date", "remark", "items"]
        read_only_fields = ["id", "voucher_no"]

    def validate_items(self, items):
        if not items:
            raise drf_serializers.ValidationError("凭证明细不能为空")
        total_debit = sum(Decimal(str(i.get("debit_amount", 0))) for i in items)
        total_credit = sum(Decimal(str(i.get("credit_amount", 0))) for i in items)
        if total_debit != total_credit:
            raise drf_serializers.ValidationError("借贷方合计必须相等")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        voucher_date = validated_data["voucher_date"]
        period = voucher_date.strftime("%Y-%m")
        voucher_no = f"V{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}"
        total_debit = sum(Decimal(str(i.get("debit_amount", 0))) for i in items_data)
        total_credit = sum(Decimal(str(i.get("credit_amount", 0))) for i in items_data)
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
        return obj.amount - obj.received_amount


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
        return obj.amount - obj.paid_amount
