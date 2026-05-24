from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Warehouse, Stock, StockTransaction
from .serializers import WarehouseSerializer, StockSerializer, StockTransactionSerializer
from common.permissions import HasPermCode
from common.response import ok
from product.models import Product


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.filter(is_deleted=False)
    serializer_class = WarehouseSerializer
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "inventory:warehouse:list",
        "retrieve": "inventory:warehouse:list",
        "create": "inventory:warehouse:create",
        "update": "inventory:warehouse:update",
        "partial_update": "inventory:warehouse:update",
        "destroy": "inventory:warehouse:delete",
    }

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
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "inventory:stock:list",
        "retrieve": "inventory:stock:list",
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        if not search:
            return queryset
        product_ids = list(Product.objects.filter(
            Q(product_code__icontains=search) | Q(product_name__icontains=search),
            is_deleted=False,
        ).values_list("id", flat=True))
        if not product_ids:
            return queryset.none()
        return queryset.filter(product_id__in=product_ids)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        data_source = page if page is not None else queryset
        product_ids = {item.product_id for item in data_source}
        product_map = {
            product.id: {"product_code": product.product_code, "product_name": product.product_name}
            for product in Product.objects.filter(id__in=product_ids, is_deleted=False).only("id", "product_code", "product_name")
        }
        serializer = self.get_serializer(data_source, many=True, context={"product_map": product_map})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return ok(serializer.data)


class StockTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockTransaction.objects.select_related("warehouse").order_by("-txn_time")
    serializer_class = StockTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["warehouse", "product_id", "txn_type"]
    permission_classes = [HasPermCode]
    permission_map = {
        "list": "inventory:transaction:list",
        "retrieve": "inventory:transaction:list",
    }
