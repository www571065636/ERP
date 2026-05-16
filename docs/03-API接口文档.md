# ERP系统 API 接口文档

## 接口规范

### 基础信息

- **Base URL：** `http://your-domain/api/v1`
- **协议：** HTTPS（生产环境）
- **数据格式：** JSON
- **字符编码：** UTF-8

### 认证方式

所有接口（除登录外）需在请求头携带 JWT Token：

```
Authorization: Bearer <access_token>
```

Token 过期后使用 Refresh Token 换取新 Token，无需重新登录。

### 统一响应格式

**成功响应：**
```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

**分页响应：**
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "list": [],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

**错误响应：**
```json
{
  "code": 400,
  "msg": "参数错误：order_date 不能为空",
  "data": null
}
```

### 错误码规范

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未认证或 Token 过期 |
| 403 | 403 | 无操作权限 |
| 404 | 404 | 资源不存在 |
| 409 | 409 | 业务冲突（如库存不足、单号重复） |
| 422 | 422 | 业务规则校验失败（如订单状态不允许操作） |
| 500 | 500 | 服务器内部错误 |

### 分页参数约定

所有列表接口支持以下查询参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页条数，最大100 |
| `ordering` | string | `-created_at` | 排序字段，`-` 前缀表示降序 |

---

## 一、认证模块 `/api/v1/auth`

### 1.1 用户登录

`POST /api/v1/auth/login`

**请求体：**
```json
{
  "username": "admin",
  "password": "Admin@123"
}
```

**响应：**
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access_expires_in": 3600,
    "user": {
      "id": 1,
      "username": "admin",
      "real_name": "系统管理员",
      "avatar": "https://example.com/avatar.png",
      "permissions": ["system:user:list", "purchase:order:approve"]
    }
  }
}
```

### 1.2 刷新 Token

`POST /api/v1/auth/token/refresh`

```json
{ "refresh": "<refresh_token>" }
```

### 1.3 登出

`POST /api/v1/auth/logout`

将 Refresh Token 加入黑名单。

### 1.4 获取当前用户信息

`GET /api/v1/auth/me`

### 1.5 修改密码

`PUT /api/v1/auth/me/password`

```json
{
  "old_password": "Admin@123",
  "new_password": "NewPass@456",
  "confirm_password": "NewPass@456"
}
```

---

## 二、用户管理 `/api/v1/system`

### 2.1 用户列表

`GET /api/v1/system/users`

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `username` | string | 账号（模糊） |
| `real_name` | string | 姓名（模糊） |
| `dept_id` | int | 部门ID |
| `status` | int | 状态 1/0 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "list": [
      {
        "id": 1,
        "username": "zhangsan",
        "real_name": "张三",
        "email": "zhangsan@example.com",
        "mobile": "13800138000",
        "dept_id": 5,
        "dept_name": "采购部",
        "status": 1,
        "last_login_at": "2024-01-15T09:30:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

### 2.2 新增用户

`POST /api/v1/system/users`

```json
{
  "username": "lisi",
  "password": "Init@123",
  "real_name": "李四",
  "email": "lisi@example.com",
  "mobile": "13900139000",
  "dept_id": 5,
  "role_ids": [2, 3]
}
```

### 2.3 修改用户

`PUT /api/v1/system/users/{id}`

### 2.4 删除用户

`DELETE /api/v1/system/users/{id}`

### 2.5 分配角色

`PUT /api/v1/system/users/{id}/roles`

```json
{ "role_ids": [1, 2, 3] }
```

### 2.6 启用/禁用用户

`PUT /api/v1/system/users/{id}/status`

```json
{ "status": 0 }
```

---

### 2.7 角色列表

`GET /api/v1/system/roles`

### 2.8 新增角色

`POST /api/v1/system/roles`

```json
{
  "role_name": "采购专员",
  "role_code": "purchase_staff",
  "data_scope": 2,
  "permission_ids": [10, 11, 12, 13]
}
```

### 2.9 分配权限

`PUT /api/v1/system/roles/{id}/permissions`

```json
{ "permission_ids": [10, 11, 12, 13, 14] }
```

### 2.10 权限菜单树

`GET /api/v1/system/permissions/tree`

**响应：**
```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "perm_name": "系统管理",
      "perm_type": 1,
      "icon": "setting",
      "children": [
        {
          "id": 2,
          "perm_name": "用户管理",
          "perm_type": 2,
          "path": "/system/users",
          "children": [
            { "id": 3, "perm_name": "新增用户", "perm_type": 3, "perm_code": "system:user:create" }
          ]
        }
      ]
    }
  ]
}
```

---

## 三、产品管理 `/api/v1/products`

### 3.1 产品分类树

`GET /api/v1/products/categories/tree`

### 3.2 产品列表

`GET /api/v1/products`

| 参数 | 类型 | 说明 |
|------|------|------|
| `product_code` | string | 产品编码（模糊） |
| `product_name` | string | 产品名称（模糊） |
| `category_id` | int | 分类ID |
| `product_type` | int | 产品类型 |
| `status` | int | 状态 |

### 3.3 新增产品

`POST /api/v1/products`

```json
{
  "product_code": "P001",
  "product_name": "不锈钢螺丝M6",
  "category_id": 3,
  "brand": "国标",
  "unit_id": 1,
  "product_type": 2,
  "tax_rate": 13.00,
  "purchase_price": 0.5000,
  "sale_price": 0.8000,
  "min_stock": 1000,
  "description": "M6×20mm 不锈钢螺丝"
}
```

### 3.4 产品详情

`GET /api/v1/products/{id}`

响应包含产品基本信息及 SKU 列表。

### 3.5 修改产品

`PUT /api/v1/products/{id}`

### 3.6 SKU 管理

`GET /api/v1/products/{id}/skus` — SKU列表

`POST /api/v1/products/{id}/skus` — 新增SKU

```json
{
  "sku_code": "P001-RED-XL",
  "sku_name": "不锈钢螺丝M6-红色-XL",
  "spec_json": {"颜色": "红色", "规格": "XL"},
  "barcode": "6901234567890",
  "price": 0.9000
}
```

---

## 四、采购管理 `/api/v1/purchase`

### 4.1 供应商列表

`GET /api/v1/purchase/suppliers`

### 4.2 新增供应商

`POST /api/v1/purchase/suppliers`

```json
{
  "supplier_code": "S001",
  "supplier_name": "上海钢铁有限公司",
  "contact_person": "王经理",
  "contact_phone": "021-12345678",
  "email": "wang@steel.com",
  "address": "上海市浦东新区XX路1号",
  "bank_name": "中国工商银行",
  "bank_account": "6222021234567890",
  "tax_no": "91310000XXXXXXXXXX",
  "payment_terms": "月结30天"
}
```

### 4.3 采购订单列表

`GET /api/v1/purchase/orders`

| 参数 | 类型 | 说明 |
|------|------|------|
| `order_no` | string | 采购单号 |
| `supplier_id` | int | 供应商ID |
| `status` | int | 状态 |
| `order_date_start` | date | 订单日期起 |
| `order_date_end` | date | 订单日期止 |

### 4.4 新增采购订单

`POST /api/v1/purchase/orders`

```json
{
  "supplier_id": 1,
  "warehouse_id": 1,
  "order_date": "2024-01-15",
  "expected_date": "2024-01-25",
  "currency": "CNY",
  "remark": "紧急采购",
  "items": [
    {
      "product_id": 1,
      "sku_id": null,
      "unit_id": 1,
      "qty": 1000,
      "unit_price": 0.5500,
      "tax_rate": 13.00
    }
  ]
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": 101,
    "order_no": "PO20240115001",
    "status": 0,
    "total_amount": 621.50
  }
}
```

### 4.5 采购订单详情

`GET /api/v1/purchase/orders/{id}`

### 4.6 提交审批

`POST /api/v1/purchase/orders/{id}/submit`

### 4.7 审批采购订单

`POST /api/v1/purchase/orders/{id}/approve`

```json
{
  "action": "approve",
  "remark": "同意采购"
}
```

`action` 取值：`approve`（通过）/ `reject`（驳回）

### 4.8 创建收货单

`POST /api/v1/purchase/orders/{id}/receipts`

```json
{
  "warehouse_id": 1,
  "receipt_date": "2024-01-25T14:30:00",
  "items": [
    {
      "order_item_id": 201,
      "qty": 800
    }
  ],
  "remark": "部分到货"
}
```

### 4.9 确认收货（触发入库）

`POST /api/v1/purchase/receipts/{id}/confirm`

---

## 五、销售管理 `/api/v1/sales`

### 5.1 客户列表

`GET /api/v1/sales/customers`

### 5.2 新增客户

`POST /api/v1/sales/customers`

```json
{
  "customer_code": "C001",
  "customer_name": "北京机械制造有限公司",
  "customer_type": 1,
  "contact_person": "李总",
  "contact_phone": "010-87654321",
  "credit_limit": 500000.00,
  "payment_terms": "月结60天",
  "salesperson_id": 5
}
```

### 5.3 销售订单列表

`GET /api/v1/sales/orders`

### 5.4 新增销售订单

`POST /api/v1/sales/orders`

```json
{
  "customer_id": 1,
  "warehouse_id": 2,
  "order_date": "2024-01-16",
  "delivery_date": "2024-01-30",
  "items": [
    {
      "product_id": 1,
      "sku_id": null,
      "unit_id": 1,
      "qty": 500,
      "unit_price": 0.8000,
      "tax_rate": 13.00
    }
  ]
}
```

### 5.5 提交审批

`POST /api/v1/sales/orders/{id}/submit`

### 5.6 审批销售订单

`POST /api/v1/sales/orders/{id}/approve`

```json
{ "action": "approve", "remark": "" }
```

### 5.7 创建发货单

`POST /api/v1/sales/orders/{id}/deliveries`

```json
{
  "warehouse_id": 2,
  "delivery_date": "2024-01-28T10:00:00",
  "logistics_co": "顺丰速运",
  "tracking_no": "SF1234567890",
  "receiver_name": "李总",
  "receiver_phone": "13800138001",
  "receiver_addr": "北京市朝阳区XX路1号",
  "items": [
    { "order_item_id": 301, "qty": 500 }
  ]
}
```

### 5.8 确认出库（触发库存扣减）

`POST /api/v1/sales/deliveries/{id}/confirm`

---

## 六、库存管理 `/api/v1/inventory`

### 6.1 仓库列表

`GET /api/v1/inventory/warehouses`

### 6.2 库存查询

`GET /api/v1/inventory/stocks`

| 参数 | 类型 | 说明 |
|------|------|------|
| `warehouse_id` | int | 仓库ID |
| `product_id` | int | 产品ID |
| `product_name` | string | 产品名称（模糊） |
| `low_stock` | bool | 仅显示低于预警值的 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "list": [
      {
        "id": 1,
        "warehouse_id": 1,
        "warehouse_name": "原料仓",
        "product_id": 1,
        "product_code": "P001",
        "product_name": "不锈钢螺丝M6",
        "qty_available": 1800.0000,
        "qty_reserved": 500.0000,
        "qty_in_transit": 800.0000,
        "qty_total": 2300.0000,
        "avg_cost": 0.550000,
        "min_stock": 1000.0000,
        "is_low_stock": false
      }
    ],
    "total": 120
  }
}
```

### 6.3 库存流水查询

`GET /api/v1/inventory/transactions`

| 参数 | 类型 | 说明 |
|------|------|------|
| `warehouse_id` | int | 仓库ID |
| `product_id` | int | 产品ID |
| `txn_type` | string | 事务类型 |
| `date_start` | datetime | 开始时间 |
| `date_end` | datetime | 结束时间 |

### 6.4 创建盘点单

`POST /api/v1/inventory/stocktakes`

```json
{
  "warehouse_id": 1,
  "stocktake_date": "2024-01-31",
  "remark": "月末盘点"
}
```

系统自动将当前库存快照写入盘点明细。

### 6.5 录入实盘数量

`PUT /api/v1/inventory/stocktakes/{id}/items`

```json
{
  "items": [
    { "item_id": 1, "actual_qty": 1795.0000 },
    { "item_id": 2, "actual_qty": 320.0000 }
  ]
}
```

### 6.6 提交盘点审批

`POST /api/v1/inventory/stocktakes/{id}/submit`

### 6.7 审批并生成调整流水

`POST /api/v1/inventory/stocktakes/{id}/approve`

审批通过后自动生成 `ADJUST_IN` / `ADJUST_OUT` 库存流水，更新库存台账。

---

## 七、财务管理 `/api/v1/finance`

### 7.1 会计科目树

`GET /api/v1/finance/accounts/tree`

### 7.2 凭证列表

`GET /api/v1/finance/vouchers`

| 参数 | 类型 | 说明 |
|------|------|------|
| `voucher_no` | string | 凭证号 |
| `period` | string | 会计期间，如 2024-01 |
| `status` | int | 状态 |
| `date_start` | date | 凭证日期起 |
| `date_end` | date | 凭证日期止 |

### 7.3 新增凭证

`POST /api/v1/finance/vouchers`

```json
{
  "voucher_type": "GENERAL",
  "voucher_date": "2024-01-31",
  "remark": "1月采购入库",
  "items": [
    {
      "account_id": 101,
      "summary": "采购原材料",
      "debit_amount": 621.50,
      "credit_amount": 0
    },
    {
      "account_id": 220,
      "summary": "应付账款-上海钢铁",
      "debit_amount": 0,
      "credit_amount": 621.50
    }
  ]
}
```

> 借贷方合计必须相等，否则返回 400 错误。

### 7.4 审核凭证

`POST /api/v1/finance/vouchers/{id}/review`

### 7.5 过账

`POST /api/v1/finance/vouchers/{id}/post`

### 7.6 应收账款列表

`GET /api/v1/finance/receivables`

| 参数 | 类型 | 说明 |
|------|------|------|
| `customer_id` | int | 客户ID |
| `status` | int | 状态 |
| `overdue` | bool | 仅显示逾期 |

### 7.7 应付账款列表

`GET /api/v1/finance/payables`

### 7.8 收款登记

`POST /api/v1/finance/receivables/{id}/payments`

```json
{
  "amount": 400.00,
  "pay_date": "2024-02-05",
  "remark": "客户转账"
}
```

### 7.9 付款登记

`POST /api/v1/finance/payables/{id}/payments`

---

## 八、人力资源 `/api/v1/hr`

### 8.1 员工列表

`GET /api/v1/hr/employees`

| 参数 | 类型 | 说明 |
|------|------|------|
| `employee_no` | string | 工号 |
| `real_name` | string | 姓名（模糊） |
| `dept_id` | int | 部门ID |
| `emp_status` | int | 状态 |

### 8.2 新增员工

`POST /api/v1/hr/employees`

```json
{
  "employee_no": "EMP001",
  "real_name": "王五",
  "gender": 1,
  "birth_date": "1990-05-20",
  "id_card": "310000199005200001",
  "mobile": "13700137000",
  "dept_id": 3,
  "position": "采购专员",
  "entry_date": "2024-01-08",
  "base_salary": 8000.00,
  "bank_name": "招商银行",
  "bank_account": "6225880123456789"
}
```

### 8.3 员工详情

`GET /api/v1/hr/employees/{id}`

### 8.4 考勤记录列表

`GET /api/v1/hr/attendances`

| 参数 | 类型 | 说明 |
|------|------|------|
| `employee_id` | int | 员工ID |
| `date_start` | date | 日期起 |
| `date_end` | date | 日期止 |
| `attend_type` | int | 考勤类型 |

### 8.5 录入考勤

`POST /api/v1/hr/attendances`

```json
{
  "employee_id": 1,
  "attend_date": "2024-01-15",
  "check_in_time": "2024-01-15T08:55:00",
  "check_out_time": "2024-01-15T18:10:00",
  "attend_type": 1,
  "overtime_hours": 0
}
```

### 8.6 薪资单列表

`GET /api/v1/hr/salaries`

| 参数 | 类型 | 说明 |
|------|------|------|
| `period` | string | 薪资期间，如 2024-01 |
| `employee_id` | int | 员工ID |
| `status` | int | 状态 |

### 8.7 批量生成薪资单

`POST /api/v1/hr/salaries/generate`

```json
{
  "period": "2024-01",
  "dept_ids": [1, 2, 3]
}
```

系统根据考勤记录和基本工资自动计算，异步执行（Celery），返回任务ID。

**响应：**
```json
{
  "code": 200,
  "data": {
    "task_id": "abc123",
    "msg": "薪资核算任务已提交，请稍后查看结果"
  }
}
```

### 8.8 审核薪资单

`POST /api/v1/hr/salaries/{id}/review`

### 8.9 发放薪资

`POST /api/v1/hr/salaries/batch-pay`

```json
{
  "period": "2024-01",
  "pay_date": "2024-02-05"
}
```

---

## 九、通用接口

### 9.1 数据字典

`GET /api/v1/common/dicts/{dict_type}`

获取指定类型的字典项，如 `product_type`、`order_status` 等。

### 9.2 异步任务状态查询

`GET /api/v1/common/tasks/{task_id}`

```json
{
  "code": 200,
  "data": {
    "task_id": "abc123",
    "status": "SUCCESS",
    "result": { "generated": 45, "failed": 0 }
  }
}
```

`status` 取值：`PENDING` / `STARTED` / `SUCCESS` / `FAILURE`

### 9.3 文件上传

`POST /api/v1/common/upload`

`Content-Type: multipart/form-data`

```
file: <binary>
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "url": "https://minio.example.com/erp/2024/01/filename.xlsx",
    "filename": "filename.xlsx",
    "size": 102400
  }
}
```

### 9.4 导出接口约定

所有列表接口支持导出，在 URL 后追加 `?export=true`，返回文件下载链接（异步生成）：

```json
{
  "code": 200,
  "data": {
    "task_id": "export_xyz",
    "msg": "导出任务已提交"
  }
}
```
