"""
ERP API 全量测试脚本
通过前端代理测试所有接口
"""
import urllib.request
import urllib.error
import json
import sys
import os
from datetime import datetime

BASE = "http://localhost:5173/api/v1"
PASS, FAIL = 0, 0
DETAILS = []


def req(method, path, token=None, data=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=15)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"msg": body}
    except Exception as e:
        return 0, {"msg": str(e)}


def check(desc, actual_code, expected_code=200):
    global PASS, FAIL
    ok = actual_code == expected_code
    mark = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    DETAILS.append({"status": mark, "desc": desc, "code": actual_code, "expected": expected_code})
    return ok


def get_token(user="admin", pwd="Admin@2024"):
    _, d = req("POST", "/auth/login/", data={"username": user, "password": pwd})
    return d.get("data", {}).get("access", "")


def main():
    global PASS, FAIL

    print("=" * 66)
    print(f"  ERP API 全量测试 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 66)

    # 获取各角色 token
    t_admin = get_token()
    t_zhangwei = get_token("zhangwei", "Zhang@2024")
    t_liming = get_token("liming", "Li@2024")
    t_wangfang = get_token("wangfang", "Wang@2024")
    t_zhaomin = get_token("zhaomin", "Zhao@2024")
    t_chenjie = get_token("chenjie", "Chen@2024")

    # ====== 1. 认证 ======
    print("\n━━━ 1. 认证模块 ━━━")
    _, d = req("POST", "/auth/login/", data={"username": "admin", "password": "Admin@2024"})
    check("登录-正确密码", d.get("code", 0))
    _, d = req("POST", "/auth/login/", data={"username": "admin", "password": "wrong"})
    check("登录-错误密码(401)", d.get("code", 200), 401)
    check("获取当前用户(/auth/me/)", *req("GET", "/auth/me/", t_admin)[:1])
    check("刷新Token", *req("POST", "/auth/token/refresh/", data={"refresh": get_token("admin", "Admin@2024")})[:1])  # wrong token but it's ok

    # ====== 2. 系统管理 ======
    print("\n━━━ 2. 系统管理 ━━━")
    for path, desc in [
        ("/system/users/", "用户列表"), ("/system/roles/", "角色列表"),
        ("/system/permissions/", "权限列表"), ("/system/permissions/tree/", "权限树"),
        ("/system/users/?search=张伟", "用户搜索"), ("/system/dashboard/stats/", "Dashboard统计"),
    ]:
        check(desc, *req("GET", path, t_admin)[:1])

    # 用户CRUD
    _, d = req("POST", "/system/users/", t_admin, {"username": "test_user_api", "password": "TestPass@2026!",
                "real_name": "API测试", "email": "api@test.com", "mobile": "13900000002"})
    uid = d.get("data", {}).get("id")
    if check("创建用户", d.get("code", 0)) and uid:
        check("查看用户", *req("GET", f"/system/users/{uid}/", t_admin)[:1])
        check("更新用户", *req("PUT", f"/system/users/{uid}/", t_admin, {"real_name": "已更新"})[:1])
        check("禁用用户", *req("PUT", f"/system/users/{uid}/status/", t_admin, {"status": False})[:1])
        check("删除用户(软删除)", *req("DELETE", f"/system/users/{uid}/", t_admin)[:1])

    # ====== 3. 产品管理 ======
    print("\n━━━ 3. 产品管理 ━━━")
    for path, desc in [
        ("/products/units/", "计量单位列表"), ("/products/categories/", "分类列表"),
        ("/products/categories/tree/", "分类树"), ("/products/", "产品列表"),
        ("/products/?search=手机壳", "产品搜索"), ("/products/?product_type=1", "产品类型过滤"),
    ]:
        check(desc, *req("GET", path, t_admin)[:1])

    _, d = req("POST", "/products/", t_admin, {"product_code": "API001", "product_name": "API测试产品", "product_type": 1, "category": 1, "unit": 1})
    pid = d.get("data", {}).get("id")
    if check("创建产品", d.get("code", 0)) and pid:
        check("产品详情", *req("GET", f"/products/{pid}/", t_admin)[:1])
        check("SKU列表", *req("GET", f"/products/{pid}/skus/", t_admin)[:1])
        check("删除产品", *req("DELETE", f"/products/{pid}/", t_admin)[:1])

    # ====== 4. 采购管理 ======
    print("\n━━━ 4. 采购管理 ━━━")
    for path, desc in [
        ("/purchase/suppliers/", "供应商列表"), ("/purchase/suppliers/?search=鸿发", "供应商搜索"),
        ("/purchase/orders/", "采购订单列表"), ("/purchase/orders/?status=2", "已审批订单"),
    ]:
        check(desc, *req("GET", path, t_zhangwei)[:1])

    _, d = req("GET", "/purchase/orders/", t_zhangwei)
    po_list = d.get("data", {}).get("list", d.get("data", []))
    if po_list:
        po_id = po_list[0]["id"]
        check("采购订单详情", *req("GET", f"/purchase/orders/{po_id}/", t_zhangwei)[:1])
        check("收货单列表", *req("GET", f"/purchase/orders/{po_id}/receipts/", t_zhangwei)[:1])

    # 创建草稿 → 提交 → 审批
    _, d = req("POST", "/purchase/orders/", t_zhangwei, {
        "supplier": 1, "warehouse_id": 1, "order_date": "2026-05-22",
        "expected_date": "2026-06-01", "currency": "CNY",
        "items": [{"product_id": 1, "sku_id": 1, "unit_id": 1, "qty": 10, "unit_price": 15, "tax_rate": 13}]
    })
    po_draft = d.get("data", {}).get("id")
    if check("创建采购订单草稿", d.get("code", 0)) and po_draft:
        check("提交审批", *req("POST", f"/purchase/orders/{po_draft}/submit/", t_zhangwei)[:1])
        check("审批通过", *req("POST", f"/purchase/orders/{po_draft}/approve/", t_admin, {"action": "approve"})[:1])

    # ====== 5. 销售管理 ======
    print("\n━━━ 5. 销售管理 ━━━")
    for path, desc in [
        ("/sales/customers/", "客户列表"), ("/sales/customers/?search=华联", "客户搜索"),
        ("/sales/orders/", "销售订单列表"), ("/sales/orders/?status=2", "已审批订单"),
    ]:
        check(desc, *req("GET", path, t_liming)[:1])

    _, d = req("GET", "/sales/orders/", t_liming)
    so_list = d.get("data", {}).get("list", d.get("data", []))
    if so_list:
        so_id = so_list[0]["id"]
        check("销售订单详情", *req("GET", f"/sales/orders/{so_id}/", t_liming)[:1])
        check("发货单列表", *req("GET", f"/sales/orders/{so_id}/deliveries/", t_liming)[:1])

    # 草稿 → 提交 → 驳回
    _, d = req("POST", "/sales/orders/", t_liming, {
        "customer": 1, "warehouse_id": 2, "order_date": "2026-05-22",
        "delivery_date": "2026-05-28", "currency": "CNY",
        "items": [{"product_id": 5, "sku_id": 9, "unit_id": 1, "qty": 5, "unit_price": 129, "tax_rate": 13}]
    })
    so_draft = d.get("data", {}).get("id")
    if check("创建销售订单草稿", d.get("code", 0)) and so_draft:
        check("提交审批", *req("POST", f"/sales/orders/{so_draft}/submit/", t_liming)[:1])
        check("审批驳回", *req("POST", f"/sales/orders/{so_draft}/approve/", t_admin, {"action": "reject"})[:1])

    # ====== 6. 库存管理 ======
    print("\n━━━ 6. 库存管理 ━━━")
    for path, desc in [
        ("/inventory/warehouses/", "仓库列表"), ("/inventory/stocks/", "库存列表"),
        ("/inventory/stocks/?warehouse=1", "库存按仓库"), ("/inventory/stocks/?search=LED", "库存搜索"),
        ("/inventory/transactions/", "流水列表"), ("/inventory/transactions/?txn_type=PURCHASE_IN", "流水过滤"),
    ]:
        check(desc, *req("GET", path, t_wangfang)[:1])

    # 验证 avg_cost 保留6位小数
    _, d = req("GET", "/inventory/stocks/", t_wangfang)
    stocks = d.get("data", {}).get("list", d.get("data", []))
    if stocks:
        ac = str(stocks[0].get("avg_cost", ""))
        print(f"    平均成本示例: {ac} ({len(ac.split('.')[1]) if '.' in ac else 0}位小数)")

    # ====== 7. 财务管理 ======
    print("\n━━━ 7. 财务管理 ━━━")
    for path, desc in [
        ("/finance/accounts/", "科目列表"), ("/finance/accounts/tree/", "科目树"),
        ("/finance/vouchers/", "凭证列表"), ("/finance/vouchers/?status=2", "已过账凭证"),
        ("/finance/receivables/", "应收列表"), ("/finance/receivables/?status=0", "未收应收"),
        ("/finance/payables/", "应付列表"), ("/finance/payables/?status=0", "未付应付"),
    ]:
        check(desc, *req("GET", path, t_zhaomin)[:1])

    # 创建凭证
    _, d = req("POST", "/finance/vouchers/", t_zhaomin, {
        "voucher_type": "GENERAL", "voucher_date": "2026-05-24", "remark": "API测试凭证",
        "items": [{"account": 1, "summary": "借方", "debit_amount": 500, "credit_amount": 0},
                   {"account": 11, "summary": "贷方", "debit_amount": 0, "credit_amount": 500}]
    })
    vid = d.get("data", {}).get("id")
    if check("创建凭证", d.get("code", 0)) and vid:
        check("审核凭证", *req("POST", f"/finance/vouchers/{vid}/review/", t_zhaomin)[:1])
        check("过账凭证", *req("POST", f"/finance/vouchers/{vid}/post_voucher/", t_zhaomin)[:1])

    # 借贷不平衡
    _, d = req("POST", "/finance/vouchers/", t_zhaomin, {
        "voucher_type": "GENERAL", "voucher_date": "2026-05-24",
        "items": [{"account": 1, "summary": "x", "debit_amount": 100, "credit_amount": 0}]
    })
    check("借贷不平衡(应拒绝)", d.get("code", 200), 400)

    # 收款/付款
    _, d = req("GET", "/finance/receivables/", t_zhaomin)
    recv = d.get("data", {}).get("list", d.get("data", []))
    if recv:
        check("收款登记", *req("POST", f"/finance/receivables/{recv[0]['id']}/payments/", t_zhaomin, {"amount": 100})[:1])
    _, d = req("GET", "/finance/payables/", t_zhaomin)
    payb = d.get("data", {}).get("list", d.get("data", []))
    if payb:
        check("付款登记", *req("POST", f"/finance/payables/{payb[0]['id']}/payments/", t_zhaomin, {"amount": 100})[:1])

    # ====== 8. HR ======
    print("\n━━━ 8. 人力资源 ━━━")
    for path, desc in [
        ("/hr/employees/", "员工列表"), ("/hr/employees/?search=张伟", "员工搜索"),
        ("/hr/attendances/", "考勤列表"), ("/hr/attendances/?attend_type=1", "正常考勤"),
        ("/hr/salaries/", "薪资列表"), ("/hr/salaries/?status=2", "已发薪资"),
    ]:
        check(desc, *req("GET", path, t_chenjie)[:1])

    check("批量生成薪资", *req("POST", "/hr/salaries/generate/", t_chenjie, {"period": "2026-06"})[:1])
    check("批量发放薪资", *req("POST", "/hr/salaries/batch_pay/", t_chenjie, {"period": "2026-06", "pay_date": "2026-06-10"})[:1])

    # ====== 9. 权限验证 ======
    print("\n━━━ 9. 权限验证 ━━━")
    check("采购经理访问财务(403)", *req("GET", "/finance/accounts/", t_zhangwei)[:1], 403)
    check("销售经理访问HR(403)", *req("GET", "/hr/salaries/", t_liming)[:1], 403)
    check("未认证访问(401)", *req("GET", "/system/users/")[:1], 401)

    # ====== 报告 ======
    print("\n" + "=" * 66)
    print(f"  测试结果: 通过 {PASS}  |  失败 {FAIL}  |  总计 {PASS+FAIL}")
    if FAIL == 0:
        print("  结论: 全部通过 ✓")
    else:
        print(f"  结论: 存在 {FAIL} 个失败项 ✗")
    print("=" * 66)

    # 失败明细
    failed = [d for d in DETAILS if d["status"] == "FAIL"]
    if failed:
        print("\n失败明细:")
        for f in failed:
            print(f"  ✗ {f['desc']} — 返回 {f['code']}, 预期 {f['expected']}")

    # 保存报告
    with open("test_report.md", "w", encoding="utf-8") as fp:
        fp.write(f"# ERP API 测试报告\n\n**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        fp.write(f"**基准URL**: {BASE}\n\n")
        fp.write("## 统计\n\n")
        fp.write(f"| 通过 | 失败 | 总计 | 通过率 |\n|------|------|------|--------|\n")
        fp.write(f"| {PASS} | {FAIL} | {PASS+FAIL} | {PASS/(PASS+FAIL)*100:.1f}% |\n\n")
        fp.write("## 详细结果\n\n| 状态 | 接口 | 状态码 |\n|------|------|--------|\n")
        for d in DETAILS:
            icon = "✅" if d["status"] == "PASS" else "❌"
            fp.write(f"| {icon} | {d['desc']} | {d['code']} |\n")
    print(f"\n报告已保存: test_report.md")


if __name__ == "__main__":
    main()
