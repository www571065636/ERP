from rest_framework import serializers
from .models import Unit, Category, Product, SKU


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "unit_name", "unit_code"]


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "parent_id", "cat_name", "cat_code", "level", "sort_order", "children"]

    def get_children(self, obj):
        all_cats = self.context.get("all_cats", [])
        children = [c for c in all_cats if c.parent_id == obj.id]
        return CategorySerializer(children, many=True, context=self.context).data


class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ["id", "sku_code", "sku_name", "spec_json", "barcode", "weight", "price", "status"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.cat_name", read_only=True)
    unit_name = serializers.CharField(source="unit.unit_name", read_only=True)
    skus = SKUSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "product_code", "product_name", "category", "category_name",
                  "brand", "unit", "unit_name", "product_type", "tax_rate",
                  "purchase_price", "sale_price", "min_stock", "max_stock",
                  "description", "image_url", "status", "created_at", "skus"]
        read_only_fields = ["id", "created_at"]
