from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Warehouse, Stock, StockTransaction
from common.response import ok


class WarehouseSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "warehouse_code", "warehouse_name", "warehouse_type",
                  "manager_id", "address", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class StockSerializer(drf_serializers.ModelSerializer):
    warehouse_name = drf_serializers.CharField(source="warehouse.warehouse_name", read_only=True)
    qty_total = drf_serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = ["id", "warehouse", "warehouse_name", "product_id", "sku_id",
                  "qty_available", "qty_reserved", "qty_in_transit", "qty_total", "avg_cost"]

    def get_qty_total(self, obj):
        return float(obj.qty_available) + float(obj.qty_reserved)


class StockTransactionSerializer(drf_serializers.ModelSerializer):
    warehouse_name = drf_serializers.CharField(source="warehouse.warehouse_name", read_only=True)

    class Meta:
        model = StockTransaction
        fields = ["id", "txn_no", "txn_type", "ref_type", "ref_id", "warehouse", "warehouse_name",
                  "product_id", "sku_id", "qty_change", "qty_before", "qty_after",
                  "unit_cost", "operator_id", "txn_time", "remark"]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.filter(is_deleted=False)
    serializer_class = WarehouseSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.filter(is_deleted=False).select_related("warehouse")
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["warehouse", "product_id"]


class StockTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockTransaction.objects.select_related("warehouse").order_by("-txn_time")
    serializer_class = StockTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["warehouse", "product_id", "txn_type"]
