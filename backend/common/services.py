from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
import datetime
import random

from django.utils import timezone

from finance.models import Payable, Receivable
from inventory.models import Stock, StockTransaction
from product.models import Product


ZERO_QTY = Decimal("0.0000")
ZERO_AMOUNT = Decimal("0.00")
ZERO_COST = Decimal("0.000000")


def quantize_qty(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)


def quantize_amount(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def quantize_cost(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.000000"), rounding=ROUND_HALF_UP)


def make_doc_no(prefix):
    micro = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    return f"{prefix}{micro[:16]}{random.randint(10, 99)}"


def estimate_due_date(payment_terms):
    try:
        days = int(payment_terms or 0)
    except (TypeError, ValueError):
        days = 0
    return timezone.localdate() + timedelta(days=days)


def adjust_stock(*, warehouse_id, product_id, sku_id, qty_delta, unit_cost, operator_id, txn_type, ref_type, ref_id, remark):
    qty_delta = quantize_qty(qty_delta)
    unit_cost = quantize_cost(unit_cost)
    stock = Stock.objects.select_for_update().filter(
        warehouse_id=warehouse_id,
        product_id=product_id,
        sku_id=sku_id,
    ).first()
    if not stock:
        stock = Stock.objects.create(
            warehouse_id=warehouse_id,
            product_id=product_id,
            sku_id=sku_id,
            qty_available=ZERO_QTY,
            qty_reserved=ZERO_QTY,
            qty_in_transit=ZERO_QTY,
            avg_cost=ZERO_COST,
            created_by=operator_id,
        )
    before = quantize_qty(stock.qty_available)
    after = before + qty_delta
    if after < 0:
        raise ValueError("库存不足，无法出库")

    if qty_delta > 0:
        current_value = before * quantize_cost(stock.avg_cost)
        inbound_value = qty_delta * unit_cost
        total_qty = after
        stock.avg_cost = quantize_cost((current_value + inbound_value) / total_qty) if total_qty > 0 else unit_cost
    elif after == 0:
        stock.avg_cost = ZERO_COST

    stock.qty_available = after
    stock.updated_by = operator_id
    stock.save(update_fields=["qty_available", "avg_cost", "updated_by", "updated_at"])

    StockTransaction.objects.create(
        txn_no=make_doc_no("TXN"),
        txn_type=txn_type,
        ref_type=ref_type,
        ref_id=ref_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        sku_id=sku_id,
        qty_change=qty_delta,
        qty_before=before,
        qty_after=after,
        unit_cost=unit_cost,
        operator_id=operator_id,
        txn_time=timezone.now(),
        remark=remark,
    )
    return stock


def get_product_snapshot(product_id):
    try:
        product = Product.objects.only("id", "product_code", "product_name").get(id=product_id, is_deleted=False)
        return product.product_code, product.product_name
    except Product.DoesNotExist:
        return "", ""


def ensure_receivable_from_sales(order):
    amount = ZERO_AMOUNT
    for item in order.items.all():
        qty = quantize_qty(item.delivered_qty)
        line_amount = quantize_amount(qty * quantize_cost(item.unit_price))
        line_tax = quantize_amount(line_amount * quantize_amount(item.tax_rate) / Decimal("100"))
        amount += line_amount + line_tax
    receivable = Receivable.objects.filter(ref_type="SALE_ORDER", ref_id=order.id, is_deleted=False).first()
    due_date = estimate_due_date(order.customer.payment_terms)
    if receivable:
        receivable.amount = amount
        receivable.due_date = due_date
        receivable.updated_by = order.updated_by or order.created_by
        receivable.save(update_fields=["amount", "due_date", "updated_by", "updated_at"])
        return receivable
    return Receivable.objects.create(
        receivable_no=make_doc_no("AR"),
        customer_id=order.customer_id,
        ref_type="SALE_ORDER",
        ref_id=order.id,
        amount=amount,
        received_amount=ZERO_AMOUNT,
        due_date=due_date,
        status=0,
        remark=f"销售订单 {order.order_no} 自动生成",
        created_by=order.created_by,
    )


def ensure_payable_from_purchase(order):
    amount = ZERO_AMOUNT
    for item in order.items.all():
        qty = quantize_qty(item.received_qty)
        line_amount = quantize_amount(qty * quantize_cost(item.unit_price))
        line_tax = quantize_amount(line_amount * quantize_amount(item.tax_rate) / Decimal("100"))
        amount += line_amount + line_tax
    payable = Payable.objects.filter(ref_type="PURCHASE_ORDER", ref_id=order.id, is_deleted=False).first()
    due_date = estimate_due_date(order.supplier.payment_terms)
    if payable:
        payable.amount = amount
        payable.due_date = due_date
        payable.updated_by = order.updated_by or order.created_by
        payable.save(update_fields=["amount", "due_date", "updated_by", "updated_at"])
        return payable
    return Payable.objects.create(
        payable_no=make_doc_no("AP"),
        supplier_id=order.supplier_id,
        ref_type="PURCHASE_ORDER",
        ref_id=order.id,
        amount=amount,
        paid_amount=ZERO_AMOUNT,
        due_date=due_date,
        status=0,
        remark=f"采购订单 {order.order_no} 自动生成",
        created_by=order.created_by,
    )
