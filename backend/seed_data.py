"""
数据库填充脚本 — 生成跨模块关联的真实业务数据

用法:
    DJANGO_SECRET_KEY=xxx python seed_data.py
"""
import os, sys, random, datetime, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
if "DJANGO_SECRET_KEY" not in os.environ:
    os.environ["DJANGO_SECRET_KEY"] = "seed-data-temp-key"

import django
django.setup()

from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from system.models import User, Role, Permission, UserRole, RolePermission
from product.models import Unit, Category, Product, SKU
from purchase.models import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseReceipt, PurchaseReceiptItem
from sales.models import Customer, SalesOrder, SalesOrderItem, Delivery, DeliveryItem
from inventory.models import Warehouse, Stock, StockTransaction
from finance.models import Account, Voucher, VoucherItem, Receivable, Payable
from hr.models import Employee, Attendance, Salary
from common.services import (
    adjust_stock,
    ensure_payable_from_purchase,
    ensure_receivable_from_sales,
    make_doc_no,
    quantize_qty,
)

NOW = timezone.now()
TODAY = NOW.date()
R = random.Random(42)  # 固定种子，保证可重现


def p(msg):
    print(f"  {msg}")


# ============================================================
# 1. 系统管理 — 角色 & 权限 & 用户
# ============================================================
def create_permissions():
    p("创建权限...")
    perms = {
        "system": [
            ("system:user:list", "用户查询", 2), ("system:user:create", "用户创建", 3),
            ("system:user:update", "用户编辑", 3), ("system:user:delete", "用户删除", 3),
            ("system:user:assign-role", "分配角色", 3), ("system:user:status", "启用禁用", 3),
            ("system:role:list", "角色查询", 2), ("system:role:create", "角色创建", 3),
            ("system:role:update", "角色编辑", 3), ("system:role:delete", "角色删除", 3),
            ("system:role:assign-permission", "分配权限", 3),
            ("system:permission:list", "权限查询", 2), ("system:permission:create", "权限创建", 3),
            ("system:permission:update", "权限编辑", 3), ("system:permission:delete", "权限删除", 3),
        ],
        "product": [
            ("product:unit:list", "单位查询", 2), ("product:unit:create", "单位创建", 3),
            ("product:unit:update", "单位编辑", 3), ("product:unit:delete", "单位删除", 3),
            ("product:category:list", "分类查询", 2), ("product:category:create", "分类创建", 3),
            ("product:category:update", "分类编辑", 3), ("product:category:delete", "分类删除", 3),
            ("product:product:list", "产品查询", 2), ("product:product:create", "产品创建", 3),
            ("product:product:update", "产品编辑", 3), ("product:product:delete", "产品删除", 3),
            ("product:sku:list", "SKU查询", 2), ("product:sku:create", "SKU创建", 3),
        ],
        "purchase": [
            ("purchase:supplier:list", "供应商查询", 2), ("purchase:supplier:create", "供应商创建", 3),
            ("purchase:supplier:update", "供应商编辑", 3), ("purchase:supplier:delete", "供应商删除", 3),
            ("purchase:order:list", "采购订单查询", 2), ("purchase:order:create", "采购订单创建", 3),
            ("purchase:order:update", "采购订单编辑", 3), ("purchase:order:delete", "采购订单删除", 3),
            ("purchase:order:submit", "采购订单提交", 3), ("purchase:order:approve", "采购订单审批", 3),
        ],
        "sales": [
            ("sales:customer:list", "客户查询", 2), ("sales:customer:create", "客户创建", 3),
            ("sales:customer:update", "客户编辑", 3), ("sales:customer:delete", "客户删除", 3),
            ("sales:order:list", "销售订单查询", 2), ("sales:order:create", "销售订单创建", 3),
            ("sales:order:update", "销售订单编辑", 3), ("sales:order:delete", "销售订单删除", 3),
            ("sales:order:submit", "销售订单提交", 3), ("sales:order:approve", "销售订单审批", 3),
        ],
        "inventory": [
            ("inventory:warehouse:list", "仓库查询", 2), ("inventory:warehouse:create", "仓库创建", 3),
            ("inventory:warehouse:update", "仓库编辑", 3), ("inventory:warehouse:delete", "仓库删除", 3),
            ("inventory:stock:list", "库存查询", 2), ("inventory:transaction:list", "流水查询", 2),
        ],
        "finance": [
            ("finance:account:list", "科目查询", 2), ("finance:account:create", "科目创建", 3),
            ("finance:account:update", "科目编辑", 3), ("finance:account:delete", "科目删除", 3),
            ("finance:voucher:list", "凭证查询", 2), ("finance:voucher:create", "凭证创建", 3),
            ("finance:voucher:delete", "凭证删除", 3), ("finance:voucher:review", "凭证审核", 3),
            ("finance:voucher:post", "凭证过账", 3),
            ("finance:receivable:list", "应收查询", 2), ("finance:receivable:create", "应收创建", 3),
            ("finance:receivable:update", "应收编辑", 3), ("finance:receivable:delete", "应收删除", 3),
            ("finance:receivable:payment", "收款登记", 3),
            ("finance:payable:list", "应付查询", 2), ("finance:payable:create", "应付创建", 3),
            ("finance:payable:update", "应付编辑", 3), ("finance:payable:delete", "应付删除", 3),
            ("finance:payable:payment", "付款登记", 3),
        ],
        "hr": [
            ("hr:employee:list", "员工查询", 2), ("hr:employee:create", "员工创建", 3),
            ("hr:employee:update", "员工编辑", 3), ("hr:employee:delete", "员工删除", 3),
            ("hr:attendance:list", "考勤查询", 2), ("hr:attendance:create", "考勤创建", 3),
            ("hr:attendance:update", "考勤编辑", 3), ("hr:attendance:delete", "考勤删除", 3),
            ("hr:salary:list", "薪资查询", 2), ("hr:salary:create", "薪资创建", 3),
            ("hr:salary:update", "薪资编辑", 3), ("hr:salary:delete", "薪资删除", 3),
            ("hr:salary:review", "薪资审核", 3), ("hr:salary:generate", "薪资生成", 3),
            ("hr:salary:batch-pay", "薪资发放", 3),
        ],
    }
    perm_map = {}
    sort = 0
    for module, module_perms in perms.items():
        sort += 1
        parent = Permission.objects.create(
            parent_id=0, perm_name=module, perm_code="",
            perm_type=1, icon="el-icon-menu", sort_order=sort,
            created_by=0,
        )
        for code, name, ptype in module_perms:
            sort += 1
            obj = Permission.objects.create(
                parent_id=parent.id, perm_name=name, perm_code=code,
                perm_type=ptype, sort_order=sort, created_by=0,
            )
            perm_map[code] = obj
    return perm_map


def create_roles(perm_map):
    p("创建角色...")
    roles = {}

    # 超级管理员 — 全部权限
    admin = Role.objects.create(
        role_name="超级管理员", role_code="super_admin",
        data_scope=1, sort_order=1, remark="系统超级管理员", created_by=0,
    )
    admin.permissions.set(Permission.objects.filter(perm_type__gt=1))
    roles["super_admin"] = admin

    # 采购经理
    purchase = Role.objects.create(
        role_name="采购经理", role_code="purchase_mgr",
        data_scope=2, sort_order=2, remark="管理采购业务", created_by=0,
    )
    purchase_perms = [p for p in perm_map if p.startswith("purchase:") or p.startswith("product:") or p == "system:user:list"]
    purchase.permissions.set([perm_map[c] for c in purchase_perms if c in perm_map])
    roles["purchase_mgr"] = purchase

    # 销售经理
    sales = Role.objects.create(
        role_name="销售经理", role_code="sales_mgr",
        data_scope=2, sort_order=3, remark="管理销售业务", created_by=0,
    )
    sales_perms = [p for p in perm_map if p.startswith("sales:") or p.startswith("product:") or p == "system:user:list"]
    sales.permissions.set([perm_map[c] for c in sales_perms if c in perm_map])
    roles["sales_mgr"] = sales

    # 仓库管理员
    wh = Role.objects.create(
        role_name="仓库管理员", role_code="warehouse_admin",
        data_scope=2, sort_order=4, remark="管理库存", created_by=0,
    )
    wh_perms = [p for p in perm_map if p.startswith("inventory:") or p.startswith("product:product:list") or p.startswith("product:unit:list") or p == "system:user:list"]
    wh.permissions.set([perm_map[c] for c in wh_perms if c in perm_map])
    roles["warehouse_admin"] = wh

    # 财务主管
    fin = Role.objects.create(
        role_name="财务主管", role_code="finance_mgr",
        data_scope=1, sort_order=5, remark="管理财务", created_by=0,
    )
    fin_perms = [p for p in perm_map if p.startswith("finance:") or p == "system:user:list"]
    fin.permissions.set([perm_map[c] for c in fin_perms if c in perm_map])
    roles["finance_mgr"] = fin

    # HR 主管
    hr_role = Role.objects.create(
        role_name="HR主管", role_code="hr_mgr",
        data_scope=2, sort_order=6, remark="管理人力资源", created_by=0,
    )
    hr_perms = [p for p in perm_map if p.startswith("hr:") or p == "system:user:list"]
    hr_role.permissions.set([perm_map[c] for c in hr_perms if c in perm_map])
    roles["hr_mgr"] = hr_role

    return roles


def create_users(roles):
    p("创建用户...")
    users = {}
    data = [
        ("admin", "Admin@2024", "系统管理员", "13800000001", "admin@erp.local", "超级管理员"),
        ("zhangwei", "Zhang@2024", "张伟", "13800000002", "zhangwei@erp.local", "采购经理"),
        ("liming", "Li@2024", "李明", "13800000003", "liming@erp.local", "销售经理"),
        ("wangfang", "Wang@2024", "王芳", "13800000004", "wangfang@erp.local", "仓库管理员"),
        ("zhaomin", "Zhao@2024", "赵敏", "13800000005", "zhaomin@erp.local", "财务主管"),
        ("chenjie", "Chen@2024", "陈洁", "13800000006", "chenjie@erp.local", "HR主管"),
    ]
    role_keys = ["super_admin", "purchase_mgr", "sales_mgr", "warehouse_admin", "finance_mgr", "hr_mgr"]

    for i, (uname, pwd, rname, mobile, email, _) in enumerate(data):
        user = User.objects.create_user(
            username=uname, password=pwd, real_name=rname,
            email=email, mobile=mobile, is_superuser=(uname == "admin"),
            is_staff=(uname == "admin"), created_by=0,
        )
        if i > 0:
            UserRole.objects.create(user=user, role=roles[role_keys[i]])
        if uname == "admin":
            UserRole.objects.create(user=user, role=roles["super_admin"])
        users[uname] = user
    return users


# ============================================================
# 2. 产品管理 — 单位 & 分类 & 产品 & SKU
# ============================================================
def create_units():
    p("创建计量单位...")
    units = {}
    for name, code in [("个", "PCS"), ("箱", "BOX"), ("千克", "KG"),
                        ("克", "G"), ("米", "M"), ("升", "L"), ("套", "SET"), ("台", "TAI")]:
        units[code] = Unit.objects.create(unit_name=name, unit_code=code, created_by=0)
    return units


def create_categories():
    p("创建产品分类...")
    cats = {}

    # 一级分类
    for name, code in [("电子产品", "ELEC"), ("原材料", "RAW"),
                        ("成品", "FIN"), ("办公用品", "OFFICE"),
                        ("食品饮料", "FOOD"), ("包装材料", "PACK")]:
        cats[code] = Category.objects.create(
            parent_id=0, cat_name=name, cat_code=code, level=1, sort_order=len(cats)+1, created_by=0,
        )

    # 二级分类
    sub = [
        ("ELEC", "手机配件", "ELEC01"), ("ELEC", "电脑配件", "ELEC02"),
        ("RAW", "金属材料", "RAW01"), ("RAW", "塑料材料", "RAW02"),
        ("FIN", "日用成品", "FIN01"), ("FIN", "电子成品", "FIN02"),
        ("OFFICE", "文具", "OFF01"), ("OFFICE", "办公设备", "OFF02"),
        ("FOOD", "饮料", "FOOD01"), ("FOOD", "零食", "FOOD02"),
        ("PACK", "纸箱", "PACK01"), ("PACK", "塑料袋", "PACK02"),
    ]
    for parent_code, name, code in sub:
        parent = cats[parent_code]
        cats[code] = Category.objects.create(
            parent_id=parent.id, cat_name=name, cat_code=code,
            level=2, sort_order=len(cats)+1, created_by=0,
        )
    return cats


def create_products(units, categories):
    p("创建产品...")
    products = {}
    data = [
        # code, name, cat_code, unit_code, type, purchase_price, sale_price, min/max_stock
        ("P001", "iPhone 15 手机壳", "ELEC01", "PCS", 1, Decimal("15.00"), Decimal("39.90"), Decimal("50"), Decimal("500")),
        ("P002", "USB-C 数据线 1米", "ELEC01", "PCS", 1, Decimal("8.50"), Decimal("25.00"), Decimal("100"), Decimal("1000")),
        ("P003", "铝合金板材 6061", "RAW01", "KG", 2, Decimal("28.00"), Decimal("0"), Decimal("200"), Decimal("2000")),
        ("P004", "ABS 塑料颗粒", "RAW02", "KG", 2, Decimal("12.50"), Decimal("0"), Decimal("500"), Decimal("5000")),
        ("P005", "LED 台灯", "FIN02", "PCS", 1, Decimal("45.00"), Decimal("129.00"), Decimal("30"), Decimal("300")),
        ("P006", "无线蓝牙耳机", "FIN02", "PCS", 1, Decimal("85.00"), Decimal("249.00"), Decimal("20"), Decimal("200")),
        ("P007", "不锈钢保温杯", "FIN01", "PCS", 1, Decimal("32.00"), Decimal("89.00"), Decimal("40"), Decimal("400")),
        ("P008", "A4 打印纸 500张", "OFF01", "BOX", 1, Decimal("18.00"), Decimal("28.00"), Decimal("100"), Decimal("500")),
        ("P009", "矿泉水 550ml×24", "FOOD01", "BOX", 1, Decimal("18.00"), Decimal("36.00"), Decimal("50"), Decimal("300")),
        ("P010", "牛皮纸箱 30×20×15cm", "PACK01", "PCS", 3, Decimal("2.50"), Decimal("5.00"), Decimal("500"), Decimal("5000")),
    ]
    for code, name, cat_code, unit_code, ptype, pp, sp, mins, maxs in data:
        cat = categories[cat_code]
        unit = units[unit_code]
        tax_rate = Decimal("13") if ptype != 4 else Decimal("6")
        products[code] = Product.objects.create(
            product_code=code, product_name=name, category=cat, unit=unit,
            product_type=ptype, tax_rate=tax_rate,
            purchase_price=pp, sale_price=sp,
            min_stock=mins, max_stock=maxs, created_by=0,
        )
    return products


def create_skus(products):
    p("创建SKU...")
    skus = {}
    sku_data = {
        "P001": [("P001-BK", "黑色"), ("P001-WH", "白色"), ("P001-BL", "蓝色")],
        "P002": [("P002-1M", "1米"), ("P002-2M", "2米")],
        "P003": [("P003-2MM", "2mm厚"), ("P003-5MM", "5mm厚")],
        "P004": [("P004-BLK", "黑色"), ("P004-WHT", "乳白色")],
        "P005": [("P005-WH", "白色"), ("P005-BK", "黑色")],
        "P006": [("P006-BK", "黑色"), ("P006-WH", "白色")],
        "P007": [("P007-500", "500ml"), ("P007-350", "350ml")],
        "P008": [("P008-A4", "A4 70g")],
        "P009": [("P009-550", "550ml×24")],
        "P010": [("P010-STD", "标准型")],
    }
    for product_code, variants in sku_data.items():
        product = products[product_code]
        for sku_code, sku_name in variants:
            skus[sku_code] = SKU.objects.create(
                product=product, sku_code=sku_code, sku_name=sku_name,
                price=product.sale_price, created_by=0,
            )
    return skus


# ============================================================
# 3. 仓库
# ============================================================
def create_warehouses():
    p("创建仓库...")
    whs = {}
    for name, code, wtype in [
        ("原料仓", "WH-RAW", 1), ("成品仓", "WH-FIN", 2),
        ("在途仓", "WH-TRANSIT", 3),
    ]:
        whs[code] = Warehouse.objects.create(
            warehouse_code=code, warehouse_name=name,
            warehouse_type=wtype, address=f"上海市浦东新区{name}路{100+R.randint(1,99)}号",
            created_by=0,
        )
    return whs


# ============================================================
# 4. 供应商 & 客户
# ============================================================
def create_suppliers():
    p("创建供应商...")
    suppliers = {}
    data = [
        ("SUP001", "深圳鸿发电子有限公司", "鸿发电子", "刘建国", "13810001001", "liujg@hongfa.cn",
         "招商银行深圳分行", "6225880123456789", "91440300123456789X", "30"),
        ("SUP002", "上海鑫达金属材料有限公司", "鑫达金属", "陈志强", "13810001002", "chenzq@xinda-metal.cn",
         "工商银行上海徐汇支行", "6222021001234567890", "91310104123456789A", "45"),
        ("SUP003", "广州明辉塑胶制品有限公司", "明辉塑胶", "黄志明", "13810001003", "huangzm@minghui.cn",
         "建设银行广州天河支行", "6227003321234567890", "91440101123456789B", "30"),
        ("SUP004", "苏州永昌纸业包装有限公司", "永昌纸业", "周永昌", "13810001004", "zhouyc@yongchang.cn",
         "农业银行苏州园区支行", "6228480401234567890", "91320594123456789C", "60"),
        ("SUP005", "北京中科创新科技有限公司", "中科创新", "王海峰", "13810001005", "wanghf@zhongke.cn",
         "中国银行北京海淀支行", "6217580001234567890", "91110108123456789D", "30"),
    ]
    for code, full_name, short_name, contact, phone, email, bank, account, tax, terms in data:
        suppliers[code] = Supplier.objects.create(
            supplier_code=code, supplier_name=full_name, short_name=short_name,
            contact_person=contact, contact_phone=phone, email=email,
            bank_name=bank, bank_account=account, tax_no=tax,
            payment_terms=terms, created_by=0,
        )
    return suppliers


def create_customers():
    p("创建客户...")
    customers = {}
    data = [
        ("CUST001", "上海华联商贸有限公司", "华联商贸", 1, "赵经理", "13920001001",
         "zhaojl@hualian.cn", "上海市静安区南京西路 1688 号",
         Decimal("500000"), Decimal("0"), "30"),
        ("CUST002", "北京新世界百货有限公司", "新世界百货", 1, "钱经理", "13920001002",
         "qianxy@newworld.cn", "北京市朝阳区建国路 88 号",
         Decimal("300000"), Decimal("0"), "45"),
        ("CUST003", "广州优品汇电子商务有限公司", "优品汇", 2, "孙经理", "13920001003",
         "sunyp@youpin.cn", "广州市天河区天河路 385 号",
         Decimal("200000"), Decimal("0"), "30"),
        ("CUST004", "深圳鹏程科技有限公司", "鹏程科技", 1, "吴经理", "13920001004",
         "wupc@pengcheng.cn", "深圳市南山区科技园 1 号",
         Decimal("400000"), Decimal("0"), "60"),
        ("CUST005", "杭州银泰百货有限公司", "银泰百货", 1, "郑经理", "13920001005",
         "zhengl@yintai.cn", "杭州市上城区延安路 530 号",
         Decimal("600000"), Decimal("0"), "30"),
    ]
    for code, full_name, short_name, ctype, contact, phone, email, addr, climit, cused, terms in data:
        customers[code] = Customer.objects.create(
            customer_code=code, customer_name=full_name, customer_type=ctype,
            contact_person=contact, contact_phone=phone, email=email, address=addr,
            credit_limit=climit, credit_used=cused, payment_terms=terms, created_by=0,
        )
    return customers


# ============================================================
# 5. 会计科目
# ============================================================
def create_accounts():
    p("创建会计科目...")
    accounts = {}
    chart = {
        "1001": ("库存现金", 1, 1),
        "1002": ("银行存款", 1, 1),
        "1122": ("应收账款", 1, 1),
        "1403": ("原材料", 1, 1),
        "1405": ("库存商品", 1, 1),
        "2201": ("应付票据", 2, 2),
        "2202": ("应付账款", 2, 2),
        "2221": ("应交税费", 2, 2),
        "4001": ("实收资本", 3, 2),
        "4101": ("未分配利润", 3, 2),
        "5001": ("主营业务收入", 4, 2),
        "5401": ("主营业务成本", 5, 1),
        "5601": ("管理费用", 5, 1),
        "5602": ("销售费用", 5, 1),
    }
    for code, (name, atype, bdir) in chart.items():
        accounts[code] = Account.objects.create(
            parent_id=0, account_code=code, account_name=name,
            account_type=atype, balance_dir=bdir, level=1, is_leaf=True,
            created_by=0,
        )
    return accounts


# ============================================================
# 6. 员工
# ============================================================
def create_employees(users):
    p("创建员工档案...")
    emps = {}
    emp_data = [
        ("EMP001", "zhangwei", "张伟", 1, "1985-03-15", "采购部", "采购经理",
         "2020-01-01", Decimal("15000")),
        ("EMP002", "liming", "李明", 1, "1988-07-22", "销售部", "销售经理",
         "2020-03-01", Decimal("16000")),
        ("EMP003", "wangfang", "王芳", 2, "1992-11-08", "仓储部", "仓库主管",
         "2021-06-01", Decimal("11000")),
        ("EMP004", "zhaomin", "赵敏", 2, "1987-05-30", "财务部", "财务主管",
         "2019-08-01", Decimal("18000")),
        ("EMP005", "chenjie", "陈洁", 2, "1990-01-12", "人力资源部", "HR主管",
         "2020-09-01", Decimal("14000")),
    ]
    for eno, uname, rname, gender, birth, dept, pos, entry, salary in emp_data:
        user = users[uname]
        emps[eno] = Employee.objects.create(
            employee_no=eno, user_id=user.id, real_name=rname,
            gender=gender, birth_date=datetime.date.fromisoformat(birth),
            mobile=user.mobile, email=user.email,
            dept_id=hash(dept) % 100 + 1, position=pos,
            entry_date=datetime.date.fromisoformat(entry),
            base_salary=salary, created_by=0,
        )
    return emps


# ============================================================
# 7. 采购流程 — 订单 → 收货 → 库存 + 应付
# ============================================================
def create_purchase_orders(users, suppliers, products, warehouses):
    p("创建采购订单...")
    buyer = users["zhangwei"]
    orders = []

    po_data = [
        # supplier, warehouse, items: [(product, sku, qty, price)]
        ("SUP001", "WH-RAW", [
            ("P002", "P002-1M", Decimal("500"), Decimal("8.20")),
            ("P002", "P002-2M", Decimal("300"), Decimal("10.50")),
        ]),
        ("SUP002", "WH-RAW", [
            ("P003", "P003-2MM", Decimal("1000"), Decimal("27.50")),
            ("P003", "P003-5MM", Decimal("800"), Decimal("28.00")),
        ]),
        ("SUP003", "WH-RAW", [
            ("P004", "P004-BLK", Decimal("2000"), Decimal("12.00")),
            ("P004", "P004-WHT", Decimal("1500"), Decimal("12.50")),
        ]),
        ("SUP001", "WH-FIN", [
            ("P005", "P005-WH", Decimal("200"), Decimal("43.00")),
            ("P005", "P005-BK", Decimal("150"), Decimal("44.00")),
            ("P006", "P006-BK", Decimal("100"), Decimal("82.00")),
        ]),
        ("SUP004", "WH-FIN", [
            ("P010", "P010-STD", Decimal("3000"), Decimal("2.40")),
            ("P008", "P008-A4", Decimal("200"), Decimal("17.50")),
        ]),
    ]

    for i, (sup_code, wh_code, items_data) in enumerate(po_data):
        supplier = suppliers[sup_code]
        wh = warehouses[wh_code]
        po_date = TODAY - datetime.timedelta(days=R.randint(5, 45))
        po_no = f"PO{po_date.strftime('%Y%m%d')}{i+1:04d}"

        with transaction.atomic():
            order = PurchaseOrder.objects.create(
                order_no=po_no, supplier=supplier, warehouse_id=wh.id,
                buyer_id=buyer.id, order_date=po_date,
                expected_date=po_date + datetime.timedelta(days=15),
                status=2,  # 已审批
                approve_by=users["admin"].id,
                approve_at=po_date + datetime.timedelta(days=1),
                created_by=buyer.id,
            )
            total_qty = Decimal("0")
            total_amount = Decimal("0")
            for j, (pcode, sku_code, qty, price) in enumerate(items_data, 1):
                product = products[pcode]
                sku = SKU.objects.get(sku_code=sku_code, product=product)
                line_amt = (qty * price).quantize(Decimal("0.01"))
                tax_amt = (line_amt * Decimal("13") / Decimal("100")).quantize(Decimal("0.01"))
                PurchaseOrderItem.objects.create(
                    order=order, line_no=j,
                    product_id=product.id, sku_id=sku.id, unit_id=product.unit_id,
                    qty=qty, unit_price=price, tax_rate=Decimal("13"),
                    tax_amount=tax_amt, amount=line_amt,
                )
                total_qty += qty
                total_amount += line_amt
            order.total_qty = total_qty
            order.total_amount = total_amount
            order.tax_amount = (total_amount * Decimal("13") / Decimal("100")).quantize(Decimal("0.01"))
            order.save(update_fields=["total_qty", "total_amount", "tax_amount"])
            orders.append(order)
    return orders


def create_purchase_receipts(users, purchase_orders, warehouses):
    p("创建采购收货...")
    operator = users["wangfang"]
    wh_fin = warehouses["WH-FIN"]
    wh_raw = warehouses["WH-RAW"]

    for order in purchase_orders:
        with transaction.atomic():
            wh_id = order.warehouse_id
            receipt = PurchaseReceipt.objects.create(
                receipt_no=f"PR{TODAY.strftime('%Y%m%d')}{order.id:04d}",
                order=order, warehouse_id=wh_id,
                receipt_date=NOW - datetime.timedelta(days=R.randint(1, 10)),
                operator_id=operator.id, status=1,
                created_by=operator.id,
            )
            for item in order.items.all():
                # 收货 80%-100%
                received_qty = quantize_qty(item.qty * Decimal(str(R.randint(80, 100))) / Decimal("100"))
                PurchaseReceiptItem.objects.create(
                    receipt=receipt, order_item=item,
                    product_id=item.product_id, sku_id=item.sku_id,
                    unit_id=item.unit_id, qty=received_qty,
                )
                # 更新订单明细已收数量
                item.received_qty = received_qty
                item.save(update_fields=["received_qty"])

                # 调整库存
                time.sleep(0.001)
                adjust_stock(
                    warehouse_id=wh_id,
                    product_id=item.product_id,
                    sku_id=item.sku_id,
                    qty_delta=received_qty,
                    unit_cost=item.unit_price,
                    operator_id=operator.id,
                    txn_type="PURCHASE_IN",
                    ref_type="PURCHASE_RECEIPT",
                    ref_id=receipt.id,
                    remark=f"采购收货 {receipt.receipt_no}",
                )

            # 更新订单状态
            total_received = sum((quantize_qty(i.received_qty) for i in order.items.all()), Decimal("0"))
            if total_received >= quantize_qty(order.total_qty):
                order.status = 4
            else:
                order.status = 3
            order.save(update_fields=["status"])

            # 生成应付
            ensure_payable_from_purchase(order)

    p(f"    已创建 {len(purchase_orders)} 笔采购收货，库存和应付已联动")


# ============================================================
# 8. 销售流程 — 订单 → 发货 → 库存 + 应收
# ============================================================
def create_sales_orders(users, customers, products, warehouses):
    p("创建销售订单...")
    salesperson = users["liming"]
    orders = []

    so_data = [
        ("CUST001", "WH-FIN", [
            ("P005", "P005-WH", Decimal("50"), Decimal("129.00")),
            ("P006", "P006-BK", Decimal("30"), Decimal("249.00")),
            ("P007", "P007-500", Decimal("40"), Decimal("89.00")),
        ]),
        ("CUST002", "WH-FIN", [
            ("P005", "P005-BK", Decimal("30"), Decimal("129.00")),
            ("P001", "P001-BK", Decimal("100"), Decimal("39.90")),
            ("P001", "P001-WH", Decimal("80"), Decimal("39.90")),
        ]),
        ("CUST003", "WH-FIN", [
            ("P006", "P006-WH", Decimal("20"), Decimal("249.00")),
            ("P002", "P002-1M", Decimal("200"), Decimal("25.00")),
            ("P008", "P008-A4", Decimal("50"), Decimal("28.00")),
            ("P009", "P009-550", Decimal("30"), Decimal("36.00")),
        ]),
        ("CUST004", "WH-FIN", [
            ("P006", "P006-BK", Decimal("25"), Decimal("249.00")),
            ("P007", "P007-350", Decimal("60"), Decimal("79.00")),
            ("P010", "P010-STD", Decimal("500"), Decimal("5.00")),
        ]),
        ("CUST005", "WH-FIN", [
            ("P005", "P005-WH", Decimal("60"), Decimal("129.00")),
            ("P005", "P005-BK", Decimal("40"), Decimal("129.00")),
            ("P006", "P006-WH", Decimal("35"), Decimal("249.00")),
            ("P007", "P007-500", Decimal("50"), Decimal("89.00")),
            ("P001", "P001-BL", Decimal("120"), Decimal("39.90")),
        ]),
    ]

    for i, (cust_code, wh_code, items_data) in enumerate(so_data):
        customer = customers[cust_code]
        wh = warehouses[wh_code]
        so_date = TODAY - datetime.timedelta(days=R.randint(1, 30))
        so_no = f"SO{so_date.strftime('%Y%m%d')}{i+1:04d}"

        with transaction.atomic():
            order = SalesOrder.objects.create(
                order_no=so_no, customer=customer, warehouse_id=wh.id,
                salesperson_id=salesperson.id, order_date=so_date,
                delivery_date=so_date + datetime.timedelta(days=7),
                status=2,  # 已审批
                approve_by=users["admin"].id,
                approve_at=so_date + datetime.timedelta(days=1),
                created_by=salesperson.id,
            )
            total_qty = Decimal("0")
            total_amount = Decimal("0")
            for j, (pcode, sku_code, qty, price) in enumerate(items_data, 1):
                product = products[pcode]
                sku = SKU.objects.get(sku_code=sku_code, product=product)
                line_amt = (qty * price).quantize(Decimal("0.01"))
                tax_amt = (line_amt * Decimal("13") / Decimal("100")).quantize(Decimal("0.01"))
                SalesOrderItem.objects.create(
                    order=order, line_no=j,
                    product_id=product.id, sku_id=sku.id, unit_id=product.unit_id,
                    qty=qty, unit_price=price, tax_rate=Decimal("13"),
                    tax_amount=tax_amt, amount=line_amt,
                )
                total_qty += qty
                total_amount += line_amt
            order.total_qty = total_qty
            order.total_amount = total_amount
            order.tax_amount = (total_amount * Decimal("13") / Decimal("100")).quantize(Decimal("0.01"))
            order.save(update_fields=["total_qty", "total_amount", "tax_amount"])
            orders.append(order)
    return orders


def create_sales_deliveries(users, sales_orders, warehouses):
    p("创建销售发货...")
    operator = users["wangfang"]

    for order in sales_orders:
        # 先确保有足够的库存（为涉及的产品补充库存）
        for item in order.items.all():
            stock = Stock.objects.filter(
                warehouse_id=order.warehouse_id,
                product_id=item.product_id,
                sku_id=item.sku_id,
            ).first()
            if not stock or stock.qty_available < item.qty:
                # 先入库保证库存充足
                time.sleep(0.001)
                adjust_stock(
                    warehouse_id=order.warehouse_id,
                    product_id=item.product_id,
                    sku_id=item.sku_id,
                    qty_delta=item.qty * Decimal("2"),  # 补充2倍订单量
                    unit_cost=item.unit_price * Decimal("0.6"),
                    operator_id=operator.id,
                    txn_type="PURCHASE_IN",
                    ref_type="INIT",
                    ref_id=0,
                    remark="初始化库存（为销售发货准备）",
                )

        with transaction.atomic():
            delivery = Delivery.objects.create(
                delivery_no=f"DO{TODAY.strftime('%Y%m%d')}{order.id:04d}",
                order=order, customer=order.customer,
                warehouse_id=order.warehouse_id,
                delivery_date=NOW - datetime.timedelta(days=R.randint(0, 5)),
                logistics_co=R.choice(["顺丰速运", "中通快递", "圆通速递"]),
                tracking_no=f"SF{R.randint(1000000000, 9999999999)}",
                receiver_name=order.customer.contact_person,
                receiver_phone=order.customer.contact_phone,
                receiver_addr=order.customer.address,
                operator_id=operator.id, status=1,
                created_by=operator.id,
            )
            for item in order.items.all():
                # 发货80%-100%
                delivered_qty = quantize_qty(item.qty * Decimal(str(R.randint(80, 100))) / Decimal("100"))
                DeliveryItem.objects.create(
                    delivery=delivery, order_item=item,
                    product_id=item.product_id, sku_id=item.sku_id,
                    unit_id=item.unit_id, qty=delivered_qty,
                )
                item.delivered_qty = delivered_qty
                item.save(update_fields=["delivered_qty"])

                # 调整库存（出库）
                time.sleep(0.001)
                adjust_stock(
                    warehouse_id=order.warehouse_id,
                    product_id=item.product_id,
                    sku_id=item.sku_id,
                    qty_delta=-delivered_qty,
                    unit_cost=item.unit_price,
                    operator_id=operator.id,
                    txn_type="SALE_OUT",
                    ref_type="SALES_DELIVERY",
                    ref_id=delivery.id,
                    remark=f"销售发货 {delivery.delivery_no}",
                )

            # 更新订单状态
            total_delivered = sum((quantize_qty(i.delivered_qty) for i in order.items.all()), Decimal("0"))
            if total_delivered >= quantize_qty(order.total_qty):
                order.status = 4
            else:
                order.status = 3
            order.save(update_fields=["status"])

            # 生成应收
            ensure_receivable_from_sales(order)

    p(f"    已创建 {len(sales_orders)} 笔销售发货，库存和应收已联动")


# ============================================================
# 9. 财务凭证
# ============================================================
def create_vouchers(users, accounts):
    p("创建财务凭证...")
    preparer = users["zhaomin"]
    reviewer = users["admin"]
    acc = accounts
    vouchers = []

    voucher_data = [
        # (日期, 期间, 类型, [(account_code, summary, debit, credit), ...])
        (TODAY - datetime.timedelta(days=25), "2024-05", "PAY", [
            ("1002", "支付原材料采购款", Decimal("35000"), Decimal("0")),
            ("2202", "支付深圳鸿发电子货款", Decimal("0"), Decimal("35000")),
        ]),
        (TODAY - datetime.timedelta(days=20), "2024-05", "RECEIVE", [
            ("1002", "收到华联商贸货款", Decimal("15000"), Decimal("0")),
            ("1122", "收回应收账款", Decimal("0"), Decimal("15000")),
        ]),
        (TODAY - datetime.timedelta(days=15), "2024-05", "GENERAL", [
            ("1403", "原材料入库", Decimal("28000"), Decimal("0")),
            ("1002", "支付鑫达金属货款", Decimal("0"), Decimal("28000")),
        ]),
        (TODAY - datetime.timedelta(days=10), "2024-05", "GENERAL", [
            ("5601", "本月办公室租金", Decimal("12000"), Decimal("0")),
            ("5602", "销售人员差旅费", Decimal("3500"), Decimal("0")),
            ("1002", "银行存款支出", Decimal("0"), Decimal("15500")),
        ]),
        (TODAY - datetime.timedelta(days=5), "2024-05", "RECEIVE", [
            ("1002", "收到新世界百货货款", Decimal("20000"), Decimal("0")),
            ("1122", "收回应收账款", Decimal("0"), Decimal("20000")),
        ]),
        (TODAY - datetime.timedelta(days=2), "2024-05", "TRANSFER", [
            ("5001", "结转本月主营业务收入", Decimal("0"), Decimal("88000")),
            ("4101", "结转收入至未分配利润", Decimal("88000"), Decimal("0")),
        ]),
    ]

    for v_date, period, vtype, items_list in voucher_data:
        with transaction.atomic():
            v_no = f"V{v_date.strftime('%Y%m%d')}{len(vouchers)+1:04d}"
            total_debit = sum(d for _, _, d, _ in items_list)
            total_credit = sum(c for _, _, _, c in items_list)
            voucher = Voucher.objects.create(
                voucher_no=v_no, voucher_type=vtype,
                voucher_date=v_date, period=period,
                total_debit=total_debit, total_credit=total_credit,
                status=2,  # 已过账
                preparer_id=preparer.id,
                reviewer_id=reviewer.id,
                review_at=v_date + datetime.timedelta(days=1),
                created_by=preparer.id,
            )
            for i, (acct_code, summary, debit, credit) in enumerate(items_list, 1):
                VoucherItem.objects.create(
                    voucher=voucher, line_no=i,
                    account=acc[acct_code], summary=summary,
                    debit_amount=debit, credit_amount=credit,
                )
            vouchers.append(voucher)
    p(f"    已创建 {len(vouchers)} 张财务凭证")


# ============================================================
# 10. 考勤 & 薪资
# ============================================================
def create_attendances(employees):
    p("创建考勤记录...")
    cnt = 0
    for emp in employees.values():
        for day_offset in range(20):
            adate = TODAY - datetime.timedelta(days=day_offset)
            if adate.weekday() >= 5:
                continue  # 跳过周末
            attend_type = R.choices([1, 1, 1, 1, 1, 2, 3, 5], weights=[20, 20, 20, 20, 20, 2, 1, 1])[0]
            check_in = datetime.datetime.combine(adate, datetime.time(8, R.randint(30, 55)))
            check_out = datetime.datetime.combine(adate, datetime.time(17, R.randint(0, 30)))
            work_hours = Decimal("8.0")
            if attend_type == 2:
                check_in = datetime.datetime.combine(adate, datetime.time(9, R.randint(10, 40)))
                work_hours = Decimal("7.5")
            elif attend_type == 3:
                check_out = datetime.datetime.combine(adate, datetime.time(16, R.randint(0, 30)))
                work_hours = Decimal("7.5")
            elif attend_type == 5:
                work_hours = Decimal("0")
                check_in = None
                check_out = None

            Attendance.objects.create(
                employee=emp, attend_date=adate,
                check_in_time=check_in, check_out_time=check_out,
                attend_type=attend_type, work_hours=work_hours,
                overtime_hours=Decimal(str(R.choice([0, 0, 0, 1.5, 2, 3]))),
                created_by=0,
            )
            cnt += 1
    p(f"    已创建 {cnt} 条考勤记录")


def create_salaries(employees):
    p("创建薪资记录...")
    cnt = 0
    for emp in employees.values():
        period = "2024-05"
        gross = Decimal(str(emp.base_salary or 0))
        bonus = Decimal(str(R.choice([0, 0, 0, 500, 1000, 2000])))
        overtime = Decimal(str(R.choice([0, 0, 200, 300, 500])))
        deduction = Decimal("0")
        social = (gross * Decimal("0.105")).quantize(Decimal("0.01"))
        tax_base = gross + bonus + overtime - social - Decimal("5000")
        tax = (tax_base * Decimal("0.03")).quantize(Decimal("0.01")) if tax_base > 0 else Decimal("0")
        net = (gross + bonus + overtime - social - tax).quantize(Decimal("0.01"))
        gross_total = gross + bonus + overtime - deduction

        Salary.objects.create(
            salary_no=f"SAL{period.replace('-','')}{emp.id:04d}",
            employee=emp, period=period,
            base_salary=gross, overtime_pay=overtime,
            bonus=bonus, deduction=deduction,
            social_security=social, income_tax=tax,
            gross_salary=gross_total, net_salary=net,
            status=2,  # 已发放
            pay_date=datetime.date(2024, 6, 5),
            created_by=0,
        )
        cnt += 1
    p(f"    已创建 {cnt} 条薪资记录")


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("ERP 数据库填充脚本")
    print("=" * 60)

    print("\n[1/10] 系统管理...")
    perm_map = create_permissions()
    roles = create_roles(perm_map)
    users = create_users(roles)

    print("\n[2/10] 产品基础数据...")
    units = create_units()
    categories = create_categories()
    products = create_products(units, categories)
    skus = create_skus(products)

    print("\n[3/10] 仓库...")
    warehouses = create_warehouses()

    print("\n[4/10] 供应商和客户...")
    suppliers = create_suppliers()
    customers = create_customers()

    print("\n[5/10] 会计科目...")
    accounts = create_accounts()

    print("\n[6/10] 员工档案...")
    employees = create_employees(users)

    print("\n[7/10] 采购流程（订单→收货→库存→应付）...")
    po_orders = create_purchase_orders(users, suppliers, products, warehouses)
    create_purchase_receipts(users, po_orders, warehouses)

    print("\n[8/10] 销售流程（订单→发货→库存→应收）...")
    so_orders = create_sales_orders(users, customers, products, warehouses)
    create_sales_deliveries(users, so_orders, warehouses)

    print("\n[9/10] 财务凭证...")
    create_vouchers(users, accounts)

    print("\n[10/10] 考勤和薪资...")
    create_attendances(employees)
    create_salaries(employees)

    # 统计
    print("\n" + "=" * 60)
    print("数据填充完成！统计如下：")
    print(f"  用户:     {User.objects.count()}")
    print(f"  角色:     {Role.objects.count()}")
    print(f"  权限:     {Permission.objects.count()}")
    print(f"  产品:     {Product.objects.count()}")
    print(f"  SKU:      {SKU.objects.count()}")
    print(f"  供应商:   {Supplier.objects.count()}")
    print(f"  客户:     {Customer.objects.count()}")
    print(f"  仓库:     {Warehouse.objects.count()}")
    print(f"  库存记录: {Stock.objects.count()}")
    print(f"  库存流水: {StockTransaction.objects.count()}")
    print(f"  采购订单: {PurchaseOrder.objects.count()}")
    print(f"  销售订单: {SalesOrder.objects.count()}")
    print(f"  会计科目: {Account.objects.count()}")
    print(f"  财务凭证: {Voucher.objects.count()}")
    print(f"  应收账款: {Receivable.objects.count()}")
    print(f"  应付账款: {Payable.objects.count()}")
    print(f"  员工:     {Employee.objects.count()}")
    print(f"  考勤:     {Attendance.objects.count()}")
    print(f"  薪资:     {Salary.objects.count()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
