from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from inventory.models import Stock, Warehouse
from product.models import Category, Product, Unit
from purchase.models import PurchaseOrder, Supplier
from sales.models import Customer, SalesOrder
from system.models import Permission, Role


class BusinessFlowTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="admin", password="admin123", real_name="管理员", is_superuser=True, is_staff=True)
        self.client.force_authenticate(self.user)

        self.unit = Unit.objects.create(unit_name="个", unit_code="PCS", created_by=self.user.id)
        self.category = Category.objects.create(parent_id=0, cat_name="测试分类", created_by=self.user.id)
        self.product = Product.objects.create(
            product_code="P001",
            product_name="测试产品",
            category=self.category,
            unit=self.unit,
            purchase_price="100.0000",
            sale_price="150.0000",
            min_stock="2.0000",
            created_by=self.user.id,
        )
        self.warehouse = Warehouse.objects.create(
            warehouse_code="WH001",
            warehouse_name="主仓",
            warehouse_type=2,
            created_by=self.user.id,
        )
        self.supplier = Supplier.objects.create(
            supplier_code="S001",
            supplier_name="供应商A",
            payment_terms="30",
            created_by=self.user.id,
        )
        self.customer = Customer.objects.create(
            customer_code="C001",
            customer_name="客户A",
            payment_terms="15",
            created_by=self.user.id,
        )

    def test_purchase_receipt_updates_stock_and_payable(self):
        create_resp = self.client.post("/api/v1/purchase/orders/", {
            "supplier": self.supplier.id,
            "warehouse_id": self.warehouse.id,
            "order_date": "2026-05-24",
            "expected_date": "2026-05-25",
            "currency": "CNY",
            "items": [{
                "product_id": self.product.id,
                "sku_id": None,
                "unit_id": self.unit.id,
                "qty": "10.0000",
                "unit_price": "100.0000",
                "tax_rate": "13.00",
                "remark": "",
            }],
        }, format="json")
        self.assertEqual(create_resp.status_code, 201)
        order_id = create_resp.data["id"]

        self.assertEqual(self.client.post(f"/api/v1/purchase/orders/{order_id}/submit/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/purchase/orders/{order_id}/approve/", {"action": "approve"}, format="json").status_code, 200)

        detail = self.client.get(f"/api/v1/purchase/orders/{order_id}/").data
        item_id = detail["items"][0]["id"]
        receipt = self.client.post(f"/api/v1/purchase/orders/{order_id}/receipts/", {
            "items": [{"order_item_id": item_id, "qty": "10.0000"}]
        }, format="json")
        self.assertEqual(receipt.status_code, 200)
        receipt_id = receipt.data["data"]["id"]

        confirm = self.client.post(f"/api/v1/purchase/orders/{order_id}/receipts/{receipt_id}/confirm/")
        self.assertEqual(confirm.status_code, 200)

        stock = Stock.objects.get(warehouse=self.warehouse, product_id=self.product.id, sku_id=None)
        self.assertEqual(str(stock.qty_available), "10.0000")
        order = PurchaseOrder.objects.get(id=order_id)
        self.assertEqual(order.status, 4)

    def test_sales_delivery_updates_stock_and_receivable(self):
        Stock.objects.create(
            warehouse=self.warehouse,
            product_id=self.product.id,
            sku_id=None,
            qty_available="8.0000",
            qty_reserved="0.0000",
            qty_in_transit="0.0000",
            avg_cost="100.000000",
            created_by=self.user.id,
        )
        create_resp = self.client.post("/api/v1/sales/orders/", {
            "customer": self.customer.id,
            "warehouse_id": self.warehouse.id,
            "order_date": "2026-05-24",
            "delivery_date": "2026-05-25",
            "currency": "CNY",
            "items": [{
                "product_id": self.product.id,
                "sku_id": None,
                "unit_id": self.unit.id,
                "qty": "5.0000",
                "unit_price": "150.0000",
                "tax_rate": "13.00",
                "remark": "",
            }],
        }, format="json")
        self.assertEqual(create_resp.status_code, 201)
        order_id = create_resp.data["id"]

        self.assertEqual(self.client.post(f"/api/v1/sales/orders/{order_id}/submit/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/sales/orders/{order_id}/approve/", {"action": "approve"}, format="json").status_code, 200)

        detail = self.client.get(f"/api/v1/sales/orders/{order_id}/").data
        item_id = detail["items"][0]["id"]
        delivery = self.client.post(f"/api/v1/sales/orders/{order_id}/deliveries/", {
            "items": [{"order_item_id": item_id, "qty": "5.0000"}]
        }, format="json")
        self.assertEqual(delivery.status_code, 200)
        delivery_id = delivery.data["data"]["id"]

        confirm = self.client.post(f"/api/v1/sales/orders/{order_id}/deliveries/{delivery_id}/confirm/")
        self.assertEqual(confirm.status_code, 200)

        stock = Stock.objects.get(warehouse=self.warehouse, product_id=self.product.id, sku_id=None)
        self.assertEqual(str(stock.qty_available), "3.0000")
        order = SalesOrder.objects.get(id=order_id)
        self.assertEqual(order.status, 4)

    def test_dashboard_stats_endpoint(self):
        response = self.client.get("/api/v1/system/dashboard/stats/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("stat_cards", response.data["data"])
