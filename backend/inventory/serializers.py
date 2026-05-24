from rest_framework import serializers as drf_serializers

from .models import Warehouse, Stock, StockTransaction


class WarehouseSerializer(drf_serializers.ModelSerializer):
    manager_name = drf_serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = ["id", "warehouse_code", "warehouse_name", "warehouse_type",
                  "manager_id", "manager_name", "address", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_manager_name(self, obj):
        from system.models import User
        if obj.manager_id:
            user = User.objects.filter(id=obj.manager_id, is_deleted=False).only("real_name").first()
            if user:
                return user.real_name
        return ""


class StockSerializer(drf_serializers.ModelSerializer):
    warehouse_name = drf_serializers.CharField(source="warehouse.warehouse_name", read_only=True)
    qty_total = drf_serializers.SerializerMethodField()
    product_code = drf_serializers.SerializerMethodField()
    product_name = drf_serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = ["id", "warehouse", "warehouse_name", "product_id", "sku_id",
                  "qty_available", "qty_reserved", "qty_in_transit", "qty_total", "avg_cost",
                  "product_code", "product_name"]

    def get_qty_total(self, obj):
        return obj.qty_available + obj.qty_reserved

    def get_product_code(self, obj):
        return self.context.get("product_map", {}).get(obj.product_id, {}).get("product_code", "")

    def get_product_name(self, obj):
        return self.context.get("product_map", {}).get(obj.product_id, {}).get("product_name", "")


class StockTransactionSerializer(drf_serializers.ModelSerializer):
    warehouse_name = drf_serializers.CharField(source="warehouse.warehouse_name", read_only=True)

    class Meta:
        model = StockTransaction
        fields = ["id", "txn_no", "txn_type", "ref_type", "ref_id", "warehouse", "warehouse_name",
                  "product_id", "sku_id", "qty_change", "qty_before", "qty_after",
                  "unit_cost", "operator_id", "txn_time", "remark"]
