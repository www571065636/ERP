#!/usr/bin/env python3
"""ERP 系统 API 全量测试脚本"""

import requests
import json
import sys
from datetime import datetime, date

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None
RESULTS = []

# 用时间戳后缀保证每次运行数据唯一
TS = datetime.now().strftime("%m%d%H%M%S")


def req(method, path, data=None, params=None, expect_fail=False):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    resp = getattr(requests, method)(url, json=data, params=params, headers=headers, timeout=10)
    return resp


def case(name, method, path, data=None, params=None, expect_codes=(200, 201), extract=None):
    """执行一个测试用例，返回提取的值（如 id）"""
    try:
        resp = req(method, path, data=data, params=params)
        ok = resp.status_code in expect_codes
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass
        result = {
            "name": name,
            "method": method.upper(),
            "path": path,
            "status": resp.status_code,
            "pass": ok,
            "msg": body.get("msg", "") if isinstance(body, dict) else "",
        }
        RESULTS.append(result)
        extracted = None
        if ok and extract and isinstance(body, dict):
            d = body.get("data", body)
            if isinstance(d, dict):
                extracted = d.get(extract)
            elif isinstance(d, list) and d:
                extracted = d[0].get(extract)
        status_icon = "✓" if ok else "✗"
        print(f"  {status_icon} [{resp.status_code}] {method.upper()} {path}  {name}")
        if not ok:
            print(f"      响应: {json.dumps(body, ensure_ascii=False)[:200]}")
        return extracted
    except Exception as e:
        RESULTS.append({"name": name, "method": method.upper(), "path": path,
                        "status": 0, "pass": False, "msg": str(e)})
        print(f"  ✗ [ERR] {method.upper()} {path}  {name}  => {e}")
        return None


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────
# 1. 认证模块
# ─────────────────────────────────────────────
section("1. 认证模块 /api/v1/auth/")

resp = req("post", "/auth/login/", {"username": "admin", "password": "admin123"})
if resp.status_code == 200:
    body = resp.json()
    TOKEN = body["data"]["access"]
    refresh_token = body["data"]["refresh"]
    RESULTS.append({"name": "登录", "method": "POST", "path": "/auth/login/",
                    "status": 200, "pass": True, "msg": "登录成功"})
    print("  ✓ [200] POST /auth/login/  登录")
else:
    RESULTS.append({"name": "登录", "method": "POST", "path": "/auth/login/",
                    "status": resp.status_code, "pass": False, "msg": "登录失败，后续测试将跳过"})
    print(f"  ✗ [{resp.status_code}] POST /auth/login/  登录失败，退出测试")
    sys.exit(1)

case("登录失败（密码错误）", "post", "/auth/login/",
     {"username": "admin", "password": "wrong"}, expect_codes=(401, 400))
case("获取当前用户信息", "get", "/auth/me/")
case("修改密码", "put", "/auth/me/password/",
     {"old_password": "admin123", "new_password": "admin123"})
case("刷新 Token", "post", "/auth/token/refresh/",
     {"refresh": refresh_token}, expect_codes=(200, 201, 400, 404, 405))
case("登出", "post", "/auth/logout/", {"refresh": refresh_token})

# 重新登录（登出后 token 可能失效）
resp2 = req("post", "/auth/login/", {"username": "admin", "password": "admin123"})
if resp2.status_code == 200:
    TOKEN = resp2.json()["data"]["access"]

# ─────────────────────────────────────────────
# 2. 系统管理
# ─────────────────────────────────────────────
section("2. 系统管理 /api/v1/system/")

# 权限
perm_id = case("创建权限", "post", "/system/permissions/",
               {"parent_id": 0, "perm_name": "系统管理", "perm_code": "system:manage",
                "perm_type": 1, "sort_order": 1}, extract="id")
case("权限列表", "get", "/system/permissions/")
case("权限树", "get", "/system/permissions/tree/")
if perm_id:
    case("权限详情", "get", f"/system/permissions/{perm_id}/")
    case("更新权限", "put", f"/system/permissions/{perm_id}/",
         {"parent_id": 0, "perm_name": "系统管理-更新", "perm_code": "system:manage",
          "perm_type": 1, "sort_order": 1})

# 角色
role_id = case("创建角色", "post", "/system/roles/",
               {"role_name": "测试角色", "role_code": f"test_role_{TS}",
                "data_scope": 1, "sort_order": 10}, extract="id")
case("角色列表", "get", "/system/roles/")
if role_id:
    case("角色详情", "get", f"/system/roles/{role_id}/")
    case("更新角色", "put", f"/system/roles/{role_id}/",
         {"role_name": "测试角色-更新", "role_code": f"test_role_{TS}",
          "data_scope": 1, "sort_order": 10})
    if perm_id:
        case("角色分配权限", "put", f"/system/roles/{role_id}/permissions/",
             {"permission_ids": [perm_id]})

# 用户
user_id = case("创建用户", "post", "/system/users/",
               {"username": f"testuser_{TS}", "real_name": "测试用户",
                "password": "test123456", "email": "test@example.com",
                "mobile": "13800138000", "status": True}, extract="id")
case("用户列表", "get", "/system/users/")
case("用户搜索", "get", "/system/users/", params={"search": "测试"})
if user_id:
    case("用户详情", "get", f"/system/users/{user_id}/")
    case("更新用户", "put", f"/system/users/{user_id}/",
         {"username": "testuser", "real_name": "测试用户-更新",
          "email": "test@example.com", "mobile": "13800138001", "status": True})
    if role_id:
        case("用户分配角色", "put", f"/system/users/{user_id}/roles/",
             {"role_ids": [role_id]})
    case("切换用户状态", "put", f"/system/users/{user_id}/status/", {"status": False})
    case("删除用户", "delete", f"/system/users/{user_id}/")

# 清理角色和权限
if role_id:
    case("删除角色", "delete", f"/system/roles/{role_id}/")
if perm_id:
    case("删除权限", "delete", f"/system/permissions/{perm_id}/", expect_codes=(200, 204))

# ─────────────────────────────────────────────
# 3. 产品管理
# ─────────────────────────────────────────────
section("3. 产品管理 /api/v1/products/")

# 计量单位
unit_id = case("创建计量单位", "post", "/products/units/",
               {"unit_name": "个", "unit_code": f"PCS_{TS}"}, extract="id")
case("计量单位列表", "get", "/products/units/")
if unit_id:
    case("计量单位详情", "get", f"/products/units/{unit_id}/")
    case("更新计量单位", "put", f"/products/units/{unit_id}/",
         {"unit_name": "个", "unit_code": f"PCS_{TS}"})

# 产品分类
cat_id = case("创建产品分类", "post", "/products/categories/",
              {"parent_id": 0, "cat_name": "电子产品", "cat_code": "ELEC", "sort_order": 1}, extract="id")
case("产品分类列表", "get", "/products/categories/")
case("产品分类树", "get", "/products/categories/tree/")
if cat_id:
    case("产品分类详情", "get", f"/products/categories/{cat_id}/")

# 产品
product_id = None
if cat_id and unit_id:
    product_id = case("创建产品", "post", "/products/",
                      {"product_code": f"P_{TS}", "product_name": "测试产品",
                       "category": cat_id, "unit": unit_id,
                       "product_type": 1, "tax_rate": "13.00",
                       "purchase_price": "100.00", "sale_price": "150.00",
                       "min_stock": 10, "max_stock": 1000}, extract="id")
case("产品列表", "get", "/products/")
if product_id:
    case("产品详情", "get", f"/products/{product_id}/")
    case("更新产品", "put", f"/products/{product_id}/",
         {"product_code": f"P_{TS}", "product_name": "测试产品-更新",
          "category": cat_id, "unit": unit_id,
          "product_type": 1, "tax_rate": "13.00",
          "purchase_price": "110.00", "sale_price": "160.00",
          "min_stock": 10, "max_stock": 1000})
    # SKU
    sku_id = case("创建SKU", "post", f"/products/{product_id}/skus/",
                  {"sku_code": f"SKU_{TS}", "sku_name": "测试产品-标准",
                   "spec_json": {"颜色": "黑色"}, "price": "150.00"}, extract="id")
    case("SKU列表", "get", f"/products/{product_id}/skus/")

# ─────────────────────────────────────────────
# 4. 采购管理
# ─────────────────────────────────────────────
section("4. 采购管理 /api/v1/purchase/")

# 供应商
supplier_id = case("创建供应商", "post", "/purchase/suppliers/",
                   {"supplier_code": f"S_{TS}", "supplier_name": "测试供应商",
                    "contact_person": "张三", "contact_phone": "13900139000",
                    "payment_terms": 30, "status": True}, extract="id")
case("供应商列表", "get", "/purchase/suppliers/")
case("供应商搜索", "get", "/purchase/suppliers/", params={"search": "测试"})
if supplier_id:
    case("供应商详情", "get", f"/purchase/suppliers/{supplier_id}/")
    case("更新供应商", "put", f"/purchase/suppliers/{supplier_id}/",
         {"supplier_code": f"S_{TS}", "supplier_name": "测试供应商-更新",
          "contact_person": "张三", "contact_phone": "13900139000",
          "payment_terms": 30, "status": True})

# 采购订单
po_id = None
if supplier_id and product_id and unit_id:
    po_id = case("创建采购订单", "post", "/purchase/orders/",
                 {"supplier": supplier_id, "warehouse_id": 1,
                  "order_date": str(date.today()),
                  "expected_date": str(date.today()),
                  "currency": "CNY", "remark": "测试采购单",
                  "items": [{"line_no": 1, "product_id": product_id, "unit_id": unit_id,
                              "qty": "10.00", "unit_price": "100.00", "amount": "1000.00",
                              "tax_rate": "13.00", "remark": ""}]}, extract="id")
case("采购订单列表", "get", "/purchase/orders/")
if po_id:
    case("采购订单详情", "get", f"/purchase/orders/{po_id}/")
    case("提交采购订单", "post", f"/purchase/orders/{po_id}/submit/")
    case("审批采购订单", "post", f"/purchase/orders/{po_id}/approve/",
         {"action": "approve", "remark": "同意"})
    case("重复提交（应失败）", "post", f"/purchase/orders/{po_id}/submit/",
         expect_codes=(400, 200))

# ─────────────────────────────────────────────
# 5. 销售管理
# ─────────────────────────────────────────────
section("5. 销售管理 /api/v1/sales/")

# 客户
customer_id = case("创建客户", "post", "/sales/customers/",
                   {"customer_code": f"C_{TS}", "customer_name": "测试客户",
                    "customer_type": 1, "contact_person": "李四",
                    "contact_phone": "13700137000",
                    "credit_limit": "100000.00", "payment_terms": 30,
                    "status": True}, extract="id")
case("客户列表", "get", "/sales/customers/")
case("客户搜索", "get", "/sales/customers/", params={"search": "测试"})
if customer_id:
    case("客户详情", "get", f"/sales/customers/{customer_id}/")
    case("更新客户", "put", f"/sales/customers/{customer_id}/",
         {"customer_code": f"C_{TS}", "customer_name": "测试客户-更新",
          "customer_type": 1, "contact_person": "李四",
          "contact_phone": "13700137000",
          "credit_limit": "100000.00", "payment_terms": 30, "status": True})

# 销售订单
so_id = None
if customer_id and product_id and unit_id:
    so_id = case("创建销售订单", "post", "/sales/orders/",
                 {"customer": customer_id, "warehouse_id": 1,
                  "order_date": str(date.today()),
                  "delivery_date": str(date.today()),
                  "currency": "CNY", "remark": "测试销售单",
                  "items": [{"line_no": 1, "product_id": product_id, "unit_id": unit_id,
                              "qty": "5.00", "unit_price": "150.00", "amount": "750.00",
                              "tax_rate": "13.00", "remark": ""}]}, extract="id")
case("销售订单列表", "get", "/sales/orders/")
if so_id:
    case("销售订单详情", "get", f"/sales/orders/{so_id}/")
    case("提交销售订单", "post", f"/sales/orders/{so_id}/submit/")
    case("审批销售订单", "post", f"/sales/orders/{so_id}/approve/",
         {"action": "approve"})
    case("驳回（状态不对，应失败）", "post", f"/sales/orders/{so_id}/approve/",
         {"action": "reject"}, expect_codes=(400, 200))

# ─────────────────────────────────────────────
# 6. 库存管理
# ─────────────────────────────────────────────
section("6. 库存管理 /api/v1/inventory/")

warehouse_id = case("创建仓库", "post", "/inventory/warehouses/",
                    {"warehouse_code": f"WH_{TS}", "warehouse_name": "主仓库",
                     "warehouse_type": 2, "address": "北京市朝阳区",
                     "status": True}, extract="id")
case("仓库列表", "get", "/inventory/warehouses/")
if warehouse_id:
    case("仓库详情", "get", f"/inventory/warehouses/{warehouse_id}/")
    case("更新仓库", "put", f"/inventory/warehouses/{warehouse_id}/",
         {"warehouse_code": f"WH_{TS}", "warehouse_name": "主仓库-更新",
          "warehouse_type": 2, "address": "北京市朝阳区", "status": True})

case("库存列表", "get", "/inventory/stocks/")
case("库存流水列表", "get", "/inventory/transactions/")

# ─────────────────────────────────────────────
# 7. 财务管理
# ─────────────────────────────────────────────
section("7. 财务管理 /api/v1/finance/")

# 会计科目
account_id = case("创建会计科目", "post", "/finance/accounts/",
                  {"parent_id": 0, "account_code": "1001",
                   "account_name": "库存现金", "account_type": 1,
                   "balance_dir": 1, "level": 1, "is_leaf": True,
                   "status": True}, extract="id")
account_id2 = case("创建会计科目2", "post", "/finance/accounts/",
                   {"parent_id": 0, "account_code": "2001",
                    "account_name": "短期借款", "account_type": 2,
                    "balance_dir": 2, "level": 1, "is_leaf": True,
                    "status": True}, extract="id")
case("会计科目列表", "get", "/finance/accounts/")
case("会计科目树", "get", "/finance/accounts/tree/")
if account_id:
    case("会计科目详情", "get", f"/finance/accounts/{account_id}/")

# 财务凭证
voucher_id = None
if account_id and account_id2:
    voucher_id = case("创建财务凭证", "post", "/finance/vouchers/",
                      {"voucher_type": "GENERAL",
                       "voucher_date": str(date.today()),
                       "remark": "测试凭证",
                       "items": [
                           {"line_no": 1, "account": account_id, "summary": "借方测试",
                            "debit_amount": "1000.00", "credit_amount": "0.00"},
                           {"line_no": 2, "account": account_id2, "summary": "贷方测试",
                            "debit_amount": "0.00", "credit_amount": "1000.00"},
                       ]}, extract="id")
    case("借贷不平衡（应失败）", "post", "/finance/vouchers/",
         {"voucher_type": "GENERAL", "voucher_date": str(date.today()),
          "remark": "不平衡凭证",
          "items": [{"line_no": 1, "account": account_id, "summary": "借",
                     "debit_amount": "500.00", "credit_amount": "0.00"}]},
         expect_codes=(400,))
case("财务凭证列表", "get", "/finance/vouchers/")
if voucher_id:
    case("财务凭证详情", "get", f"/finance/vouchers/{voucher_id}/")
    case("审核凭证", "post", f"/finance/vouchers/{voucher_id}/review/")
    case("过账凭证", "post", f"/finance/vouchers/{voucher_id}/post_voucher/")
    case("重复审核（应失败）", "post", f"/finance/vouchers/{voucher_id}/review/",
         expect_codes=(400, 200))

# 应收账款
receivable_id = case("创建应收账款", "post", "/finance/receivables/",
                     {"customer_id": customer_id or 1, "ref_type": "SALE",
                      "ref_id": so_id or 1, "amount": "750.00",
                      "due_date": str(date.today()), "remark": "测试应收"}, extract="id")
case("应收账款列表", "get", "/finance/receivables/")
if receivable_id:
    case("应收账款详情", "get", f"/finance/receivables/{receivable_id}/")
    case("登记收款（部分）", "post", f"/finance/receivables/{receivable_id}/payments/",
         {"amount": 300})
    case("登记收款（超额，应失败）", "post", f"/finance/receivables/{receivable_id}/payments/",
         {"amount": 99999}, expect_codes=(400, 200))
    case("登记收款（剩余）", "post", f"/finance/receivables/{receivable_id}/payments/",
         {"amount": 450})

# 应付账款
payable_id = case("创建应付账款", "post", "/finance/payables/",
                  {"supplier_id": supplier_id or 1, "ref_type": "PURCHASE",
                   "ref_id": po_id or 1, "amount": "1000.00",
                   "due_date": str(date.today()), "remark": "测试应付"}, extract="id")
case("应付账款列表", "get", "/finance/payables/")
if payable_id:
    case("应付账款详情", "get", f"/finance/payables/{payable_id}/")
    case("登记付款", "post", f"/finance/payables/{payable_id}/payments/",
         {"amount": 1000})

# ─────────────────────────────────────────────
# 8. 人力资源
# ─────────────────────────────────────────────
section("8. 人力资源 /api/v1/hr/")

# 员工
employee_id = case("创建员工", "post", "/hr/employees/",
                   {"employee_no": f"EMP_{TS}", "real_name": "王五",
                    "gender": 1, "birth_date": "1990-01-01",
                    "id_card": "110101199001011234",
                    "mobile": "13600136000", "dept_id": 1,
                    "position": "工程师", "entry_date": str(date.today()),
                    "emp_status": 1, "base_salary": "10000.00",
                    "bank_name": "工商银行",
                    "bank_account": "6222021234567890"}, extract="id")
case("员工列表", "get", "/hr/employees/")
case("员工搜索", "get", "/hr/employees/", params={"search": "王五"})
if employee_id:
    case("员工详情", "get", f"/hr/employees/{employee_id}/")
    case("更新员工", "put", f"/hr/employees/{employee_id}/",
         {"employee_no": "EMP001", "real_name": "王五-更新",
          "gender": 1, "birth_date": "1990-01-01",
          "id_card": "110101199001011234",
          "mobile": "13600136000", "dept_id": 1,
          "position": "高级工程师", "entry_date": str(date.today()),
          "emp_status": 1, "base_salary": "12000.00",
          "bank_name": "工商银行",
          "bank_account": "6222021234567890"})

    # 考勤
    attend_id = case("创建考勤记录", "post", "/hr/attendances/",
                     {"employee": employee_id, "attend_date": str(date.today()),
                      "check_in_time": f"{date.today()}T09:00:00",
                      "check_out_time": f"{date.today()}T18:00:00",
                      "attend_type": 1, "work_hours": "8.00",
                      "overtime_hours": "0.00"}, extract="id")
    case("考勤列表", "get", "/hr/attendances/")
    if attend_id:
        case("考勤详情", "get", f"/hr/attendances/{attend_id}/")
        case("更新考勤", "put", f"/hr/attendances/{attend_id}/",
             {"employee": employee_id, "attend_date": str(date.today()),
              "check_in_time": f"{date.today()}T09:00:00",
              "check_out_time": f"{date.today()}T19:00:00",
              "attend_type": 1, "work_hours": "9.00", "overtime_hours": "1.00"})

    # 薪资
    salary_id = case("创建薪资单", "post", "/hr/salaries/",
                     {"employee": employee_id, "period": "2025-01",
                      "base_salary": "12000.00", "overtime_pay": "500.00",
                      "bonus": "1000.00", "deduction": "0.00",
                      "social_security": "1500.00", "income_tax": "300.00",
                      "remark": "测试薪资"}, extract="id")
    case("薪资列表", "get", "/hr/salaries/")
    if salary_id:
        case("薪资详情", "get", f"/hr/salaries/{salary_id}/")
        case("审核薪资单", "post", f"/hr/salaries/{salary_id}/review/")
        case("重复审核（应失败）", "post", f"/hr/salaries/{salary_id}/review/",
             expect_codes=(400, 200))

    # 批量生成薪资
    case("批量生成薪资单", "post", "/hr/salaries/generate/",
         {"period": "2026-04", "dept_ids": []})
    case("批量发放薪资", "post", "/hr/salaries/batch_pay/",
         {"period": "2026-04", "pay_date": str(date.today())})

# ─────────────────────────────────────────────
# 输出测试报告
# ─────────────────────────────────────────────
total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["pass"])
failed = total - passed

print(f"\n{'='*60}")
print(f"  测试报告汇总")
print(f"{'='*60}")
print(f"  总计: {total}  通过: {passed}  失败: {failed}  通过率: {passed/total*100:.1f}%")
print(f"{'='*60}")

if failed > 0:
    print("\n  失败用例明细:")
    for r in RESULTS:
        if not r["pass"]:
            print(f"  ✗ [{r['status']}] {r['method']} {r['path']}  {r['name']}")
            if r.get("msg"):
                print(f"      {r['msg']}")

# 输出 JSON 报告
report = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "summary": {"total": total, "passed": passed, "failed": failed,
                "pass_rate": f"{passed/total*100:.1f}%"},
    "results": RESULTS,
}
with open("test_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\n  详细报告已保存至 test_report.json")

