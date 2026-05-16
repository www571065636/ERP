from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Unit, Category, Product, SKU
from .serializers import UnitSerializer, CategorySerializer, ProductSerializer, SKUSerializer
from common.response import ok


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.filter(is_deleted=False)
    serializer_class = UnitSerializer

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return ok(msg="删除成功")


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_deleted=False).order_by("sort_order")
    serializer_class = CategorySerializer

    @action(detail=False, methods=["get"])
    def tree(self, request):
        all_cats = list(self.get_queryset())
        roots = [c for c in all_cats if c.parent_id == 0]
        data = CategorySerializer(roots, many=True, context={"all_cats": all_cats}).data
        return ok(data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_deleted=False).select_related("category", "unit")
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["category", "product_type", "status"]
    search_fields = ["product_code", "product_name", "brand"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return ok(msg="删除成功")

    @action(detail=True, methods=["get", "post"])
    def skus(self, request, pk=None):
        product = self.get_object()
        if request.method == "GET":
            qs = SKU.objects.filter(product=product, is_deleted=False)
            return ok(SKUSerializer(qs, many=True).data)
        serializer = SKUSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, created_by=request.user.id)
        return ok(serializer.data)
