#!/bin/bash
# API 全量测试 - 通过前端代理
BASE="http://localhost:5173/api/v1"
PASS=0; FAIL=0; echo "">/tmp/test_log.txt

log() { echo "[$1] $2" >> /tmp/test_log.txt; }
check() { if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  PASS: $1"; else FAIL=$((FAIL+1)); echo "  FAIL: $1 (got $2, expected $3)"; fi; log "$1" "$2"; }
check_ok() { if [ "$2" = "200" ] || [ "$2" = "201" ]; then PASS=$((PASS+1)); echo "  PASS: $1"; else FAIL=$((FAIL+1)); echo "  FAIL: $1 (got $2, expected 200/201)"; fi; log "$1" "$2"; }

# 获取 token
T=$(curl -sf "$BASE/auth/login/" -H "Content-Type: application/json" -d '{"username":"admin","password":"Admin@2024"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access'])")
T2=$(curl -sf "$BASE/auth/login/" -H "Content-Type: application/json" -d '{"username":"zhangwei","password":"Zhang@2024"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access'])")
T3=$(curl -sf "$BASE/auth/login/" -H "Content-Type: application/json" -d '{"username":"liming","password":"Li@2024"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access'])")
T4=$(curl -sf "$BASE/auth/login/" -H "Content-Type: application/json" -d '{"username":"wangfang","password":"Wang@2024"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access'])")
T5=$(curl -sf "$BASE/auth/login/" -H "Content-Type: application/json" -d '{"username":"zhaomin","password":"Zhao@2024"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access'])")
T6=$(curl -sf "$BASE/auth/login/" -H "Content-Type: application/json" -d '{"username":"chenjie","password":"Chen@2024"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access'])")
echo "Tokens obtained for all 6 users"

code() { if [ -n "$2" ]; then curl -s -o /dev/null -w "%{http_code}" "$1" -H "Authorization: Bearer $2"; else curl -s -o /dev/null -w "%{http_code}" "$1"; fi; }
code_d() { if [ -n "$2" ]; then curl -s -o /dev/null -w "%{http_code}" "$1" -H "Authorization: Bearer $2" -H "Content-Type: application/json" -d "$3"; else curl -s -o /dev/null -w "%{http_code}" "$1" -H "Content-Type: application/json" -d "$3"; fi; }
put_d() { if [ -n "$2" ]; then curl -s -o /dev/null -w "%{http_code}" -X PUT "$1" -H "Authorization: Bearer $2" -H "Content-Type: application/json" -d "$3"; else curl -s -o /dev/null -w "%{http_code}" -X PUT "$1" -H "Content-Type: application/json" -d "$3"; fi; }

echo ""
echo "━━━ 1. 认证 ━━━"
check "登录-正确" "$(code_d "$BASE/auth/login/" "" '{"username":"admin","password":"Admin@2024"}')" 200
check "登录-错误" "$(code_d "$BASE/auth/login/" "" '{"username":"admin","password":"x"}')" 401
check "获取当前用户" "$(code "$BASE/auth/me/" "$T")" 200
check "刷新Token" "$(code_d "$BASE/auth/token/refresh/" "" "{\"refresh\":\"x\"}")" 401

echo ""
echo "━━━ 2. 系统管理 ━━━"
check "用户列表" "$(code "$BASE/system/users/" "$T")" 200
check "角色列表" "$(code "$BASE/system/roles/" "$T")" 200
check "权限列表" "$(code "$BASE/system/permissions/" "$T")" 200
check "权限树" "$(code "$BASE/system/permissions/tree/" "$T")" 200
check "Dashboard" "$(code "$BASE/system/dashboard/stats/" "$T")" 200

# 用户 CRUD
USR_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/system/users/" -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{\"username\":\"test$(date +%s)\",\"password\":\"TestApi@2026!\",\"real_name\":\"APITest\",\"email\":\"t@t.com\",\"mobile\":\"13900000008\"}")
check_ok "创建用户" "$USR_CODE"
if [ "$USR_CODE" = "201" ]; then
  USR_ID=$(curl -s "$BASE/system/users/?search=test" -H "Authorization: Bearer $T" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'])" 2>/dev/null)
  [ -n "$USR_ID" ] && check "查看用户" "$(code "$BASE/system/users/$USR_ID/" "$T")" 200
  [ -n "$USR_ID" ] && check "更新用户" "$(put_d "$BASE/system/users/$USR_ID/" "$T" '{"username":"testput","real_name":"Updated","email":"up@t.com","mobile":"13900000009","dept_id":null}')" 200
  [ -n "$USR_ID" ] && check "禁用用户" "$(put_d "$BASE/system/users/$USR_ID/status/" "$T" '{"status":false}')" 200
  [ -n "$USR_ID" ] && check "删除用户" "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/system/users/$USR_ID/" -H "Authorization: Bearer $T")" 200
fi

echo ""
echo "━━━ 3. 产品管理 ━━━"
check "单位列表" "$(code "$BASE/products/units/" "$T")" 200
check "分类列表" "$(code "$BASE/products/categories/" "$T")" 200
check "分类树" "$(code "$BASE/products/categories/tree/" "$T")" 200
check "产品列表" "$(code "$BASE/products/" "$T")" 200
check "产品搜索" "$(code "$BASE/products/?search=LED" "$T")" 200

PRD_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/products/" -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{\"product_code\":\"T$(date +%s)\",\"product_name\":\"APITestProduct\",\"product_type\":1,\"category\":1,\"unit\":1}")
check_ok "创建产品" "$PRD_CODE"
if [ "$PRD_CODE" = "201" ]; then
  PID=$(curl -s "$BASE/products/" -H "Authorization: Bearer $T" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'])" 2>/dev/null)
  [ -n "$PID" ] && check "删除产品" "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/products/$PID/" -H "Authorization: Bearer $T")" 200
fi

echo ""
echo "━━━ 4. 采购管理 ━━━"
check "供应商列表" "$(code "$BASE/purchase/suppliers/" "$T2")" 200
check "供应商搜索" "$(code "$BASE/purchase/suppliers/?search=SUP001" "$T2")" 200
check "采购订单列表" "$(code "$BASE/purchase/orders/" "$T2")" 200
check "订单过滤" "$(code "$BASE/purchase/orders/?status=2" "$T2")" 200

# 订单详情
PO_ID=$(curl -s "$BASE/purchase/orders/" -H "Authorization: Bearer $T2" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'])" 2>/dev/null)
[ -n "$PO_ID" ] && check "订单详情" "$(code "$BASE/purchase/orders/$PO_ID/" "$T2")" 200
[ -n "$PO_ID" ] && check "收货单列表" "$(code "$BASE/purchase/orders/$PO_ID/receipts/" "$T2")" 200

# 创建草稿 → 提交 → 审批
PO_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/purchase/orders/" -H "Authorization: Bearer $T2" -H "Content-Type: application/json" \
  -d '{"supplier":1,"warehouse_id":1,"order_date":"2026-05-24","expected_date":"2026-06-01","currency":"CNY","items":[{"product_id":1,"sku_id":1,"unit_id":1,"qty":10,"unit_price":15,"tax_rate":13,"amount":150.00,"tax_amount":19.50}]}')
check_ok "创建采购订单" "$PO_CODE"
if [ "$PO_CODE" = "201" ]; then
  DRAFT_ID=$(curl -s "$BASE/purchase/orders/?status=0" -H "Authorization: Bearer $T2" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'] if l else '')" 2>/dev/null)
  [ -n "$DRAFT_ID" ] && check "提交审批" "$(code_d "$BASE/purchase/orders/$DRAFT_ID/submit/" "$T2" '{}')" 200
  [ -n "$DRAFT_ID" ] && check "审批通过" "$(code_d "$BASE/purchase/orders/$DRAFT_ID/approve/" "$T" '{"action":"approve"}')" 200
fi

echo ""
echo "━━━ 5. 销售管理 ━━━"
check "客户列表" "$(code "$BASE/sales/customers/" "$T3")" 200
check "客户搜索" "$(code "$BASE/sales/customers/?search=CUST001" "$T3")" 200
check "销售订单列表" "$(code "$BASE/sales/orders/" "$T3")" 200
check "订单过滤" "$(code "$BASE/sales/orders/?status=2" "$T3")" 200

SO_ID=$(curl -s "$BASE/sales/orders/" -H "Authorization: Bearer $T3" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'])" 2>/dev/null)
[ -n "$SO_ID" ] && check "订单详情" "$(code "$BASE/sales/orders/$SO_ID/" "$T3")" 200
[ -n "$SO_ID" ] && check "发货单列表" "$(code "$BASE/sales/orders/$SO_ID/deliveries/" "$T3")" 200

SO_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/sales/orders/" -H "Authorization: Bearer $T3" -H "Content-Type: application/json" \
  -d '{"customer":1,"warehouse_id":2,"order_date":"2026-05-24","delivery_date":"2026-05-30","currency":"CNY","items":[{"product_id":5,"sku_id":9,"unit_id":1,"qty":5,"unit_price":129,"tax_rate":13,"amount":645.00,"tax_amount":83.85}]}')
check_ok "创建销售订单" "$SO_CODE"
if [ "$SO_CODE" = "201" ]; then
  DRAFT_SO=$(curl -s "$BASE/sales/orders/?status=0" -H "Authorization: Bearer $T3" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'] if l else '')" 2>/dev/null)
  [ -n "$DRAFT_SO" ] && check "提交审批" "$(code_d "$BASE/sales/orders/$DRAFT_SO/submit/" "$T3" '{}')" 200
  [ -n "$DRAFT_SO" ] && check "驳回" "$(code_d "$BASE/sales/orders/$DRAFT_SO/approve/" "$T" '{"action":"reject"}')" 200
fi

echo ""
echo "━━━ 6. 库存管理 ━━━"
check "仓库列表" "$(code "$BASE/inventory/warehouses/" "$T4")" 200
check "库存列表" "$(code "$BASE/inventory/stocks/" "$T4")" 200
check "库存过滤" "$(code "$BASE/inventory/stocks/?warehouse=1" "$T4")" 200
check "库存搜索" "$(code "$BASE/inventory/stocks/?search=LED" "$T4")" 200
check "流水列表" "$(code "$BASE/inventory/transactions/" "$T4")" 200
check "流水过滤" "$(code "$BASE/inventory/transactions/?txn_type=PURCHASE_IN" "$T4")" 200

echo ""
echo "━━━ 7. 财务管理 ━━━"
check "科目列表" "$(code "$BASE/finance/accounts/" "$T5")" 200
check "科目树" "$(code "$BASE/finance/accounts/tree/" "$T5")" 200
check "凭证列表" "$(code "$BASE/finance/vouchers/" "$T5")" 200
check "凭证过滤" "$(code "$BASE/finance/vouchers/?status=2" "$T5")" 200
check "应收列表" "$(code "$BASE/finance/receivables/" "$T5")" 200
check "应付列表" "$(code "$BASE/finance/payables/" "$T5")" 200

# 创建凭证
VOUCH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/finance/vouchers/" -H "Authorization: Bearer $T5" -H "Content-Type: application/json" \
  -d '{"voucher_type":"GENERAL","voucher_date":"2026-05-24","remark":"Test","items":[{"line_no":1,"account":1,"summary":"Debit","debit_amount":500,"credit_amount":0},{"line_no":2,"account":11,"summary":"Credit","debit_amount":0,"credit_amount":500}]}')
check_ok "创建凭证" "$VOUCH_CODE"
if [ "$VOUCH_CODE" = "201" ]; then
  VID=$(curl -s "$BASE/finance/vouchers/?status=0" -H "Authorization: Bearer $T5" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'] if l else '')" 2>/dev/null)
  [ -n "$VID" ] && check "审核凭证" "$(code_d "$BASE/finance/vouchers/$VID/review/" "$T5" '{}')" 200
  [ -n "$VID" ] && check "过账凭证" "$(code_d "$BASE/finance/vouchers/$VID/post_voucher/" "$T5" '{}')" 200
fi

# 借贷不平衡
R=$(curl -s "$BASE/finance/vouchers/" -H "Authorization: Bearer $T5" -H "Content-Type: application/json" \
  -d '{"voucher_type":"GENERAL","voucher_date":"2026-05-24","items":[{"line_no":1,"account":1,"summary":"x","debit_amount":100,"credit_amount":0}]}')
check "借贷不平衡" "$(echo "$R" | python -c "import sys,json;print(json.load(sys.stdin).get('code',0))")" 400

# 收款/付款
RECV=$(curl -s "$BASE/finance/receivables/" -H "Authorization: Bearer $T5" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'])" 2>/dev/null)
[ -n "$RECV" ] && check "收款登记" "$(code_d "$BASE/finance/receivables/$RECV/payments/" "$T5" '{"amount":100}')" 200
PAYB=$(curl -s "$BASE/finance/payables/" -H "Authorization: Bearer $T5" | python -c "import sys,json;d=json.load(sys.stdin)['data'];l=d.get('list',d);print(l[0]['id'])" 2>/dev/null)
[ -n "$PAYB" ] && check "付款登记" "$(code_d "$BASE/finance/payables/$PAYB/payments/" "$T5" '{"amount":100}')" 200

echo ""
echo "━━━ 8. HR ━━━"
check "员工列表" "$(code "$BASE/hr/employees/" "$T6")" 200
check "员工搜索" "$(code "$BASE/hr/employees/?search=EMP001" "$T6")" 200
check "考勤列表" "$(code "$BASE/hr/attendances/" "$T6")" 200
check "考勤过滤" "$(code "$BASE/hr/attendances/?attend_type=1" "$T6")" 200
check "薪资列表" "$(code "$BASE/hr/salaries/" "$T6")" 200
check "薪资过滤" "$(code "$BASE/hr/salaries/?status=2" "$T6")" 200
check "批量生成" "$(code_d "$BASE/hr/salaries/generate/" "$T6" '{"period":"2026-06","dept_ids":[]}')" 200
check "批量发放" "$(code_d "$BASE/hr/salaries/batch_pay/" "$T6" '{"period":"2026-06","pay_date":"2026-06-10"}')" 200

echo ""
echo "━━━ 9. 权限 ━━━"
check "采购经理访财务(403)" "$(code "$BASE/finance/accounts/" "$T2")" 403
check "销售经理访HR(403)" "$(code "$BASE/hr/salaries/" "$T3")" 403
check "未认证(401)" "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/system/users/")" 401

echo ""
echo "==========================================="
echo "  通过: $PASS  失败: $FAIL  总计: $((PASS+FAIL))"
[ $FAIL -eq 0 ] && echo "  结论: 全部通过 ✓" || echo "  结论: $FAIL 项失败 ✗"
echo "==========================================="