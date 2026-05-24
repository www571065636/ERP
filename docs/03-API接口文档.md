# ERP系统 API 接口文档

## 文档说明

本文档描述**当前版本已实现或已在代码中可确认的接口**。

> 说明：历史文档中出现的采购收货、销售发货、库存盘点、通用上传/导出/任务接口等内容，当前版本尚未完整落地，本文统一标记为“未实现接口”，避免联调时误用。

---

## 接口规范

### 基础信息

- **Base URL：** `/api/v1`
- **数据格式：** JSON
- **字符编码：** UTF-8

### 认证方式

除登录接口外，其余接口默认需要在请求头中携带 JWT Token：

```http
Authorization: Bearer <access_token>
```

当前代码已启用：
- JWT 认证
- Refresh Token 黑名单

相关配置文件：
- `backend/config/settings.py`

### 统一响应格式

项目后端统一通过 `common.response.ok` / `common.response.fail` 返回数据，典型格式如下：

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
  "msg": "参数错误",
  "data": null
}
```

### 分页约定

当前默认分页配置：
- `page` 默认 1
- `page_size` 默认 20

相关文件：
- `backend/config/settings.py`
- `backend/common/pagination.py`

---

## 一、认证模块 `/api/v1/auth`

相关文件：
- `backend/system/urls/auth.py`
- `backend/system/views.py`

### 1.1 用户登录

`POST /api/v1/auth/login/`

请求体：
```json
{
  "username": "admin",
  "password": "Admin@123"
}
```

当前返回内容：
- `access`
- `refresh`
- `user.id`
- `user.username`
- `user.real_name`
- `user.avatar`
- `user.permissions`

说明：
- 当前接口**不返回** `access_expires_in`

### 1.2 登出

`POST /api/v1/auth/logout/`

请求体：
```json
{
  "refresh": "<refresh_token>"
}
```

说明：
- 会尝试将 refresh token 加入黑名单

### 1.3 获取当前用户信息

`GET /api/v1/auth/me/`

说明：
- 当前实现会返回当前用户基础信息
- 如后续权限控制增强，建议与登录接口保持一致返回 `permissions`

### 1.4 修改密码

`PUT /api/v1/auth/me/password/`

请求体：
```json
{
  "old_password": "Admin@123",
  "new_password": "NewPass@456"
}
```

说明：
- 当前代码仅校验旧密码和新密码长度，不校验 `confirm_password`

### 1.5 刷新 Token

当前文档不将其列为项目自定义接口。

说明：
- `backend/config/urls.py` 当前未显式挂载 `token/refresh` 路由
- 如需启用，请以后端实际接入为准

---

## 二、系统管理 `/api/v1/system`

相关文件：
- `backend/system/urls/system.py`
- `backend/system/views.py`

### 2.1 用户管理

已实现接口：
- `GET /api/v1/system/users/`
- `POST /api/v1/system/users/`
- `GET /api/v1/system/users/{id}/`
- `PUT /api/v1/system/users/{id}/`
- `DELETE /api/v1/system/users/{id}/`
- `PUT /api/v1/system/users/{id}/roles/`
- `PUT /api/v1/system/users/{id}/status/`

当前列表支持的主要过滤：
- `status`
- `dept_id`
- 搜索字段：`username`、`real_name`、`mobile`

说明：
- 当前列表接口并未严格按历史文档中的 `username`/`real_name` 独立参数实现，更接近 DRF SearchFilter

### 2.2 角色管理

已实现接口：
- `GET /api/v1/system/roles/`
- `POST /api/v1/system/roles/`
- `GET /api/v1/system/roles/{id}/`
- `PUT /api/v1/system/roles/{id}/`
- `DELETE /api/v1/system/roles/{id}/`
- `PUT /api/v1/system/roles/{id}/permissions/`

### 2.3 权限管理

已实现接口：
- `GET /api/v1/system/permissions/`
- `POST /api/v1/system/permissions/`
- `GET /api/v1/system/permissions/{id}/`
- `PUT /api/v1/system/permissions/{id}/`
- `DELETE /api/v1/system/permissions/{id}/`
- `GET /api/v1/system/permissions/tree/`

---

## 三、产品管理 `/api/v1/products`

相关文件：
- `backend/product/urls.py`
- `backend/product/views.py`

### 3.1 计量单位

已实现接口：
- `GET /api/v1/products/units/`
- `POST /api/v1/products/units/`
- `GET /api/v1/products/units/{id}/`
- `PUT /api/v1/products/units/{id}/`
- `DELETE /api/v1/products/units/{id}/`

### 3.2 产品分类

已实现接口：
- `GET /api/v1/products/categories/`
- `POST /api/v1/products/categories/`
- `GET /api/v1/products/categories/{id}/`
- `PUT /api/v1/products/categories/{id}/`
- `DELETE /api/v1/products/categories/{id}/`
- `GET /api/v1/products/categories/tree/`

### 3.3 产品

已实现接口：
- `GET /api/v1/products/`
- `POST /api/v1/products/`
- `GET /api/v1/products/{id}/`
- `PUT /api/v1/products/{id}/`
- `DELETE /api/v1/products/{id}/`
- `GET /api/v1/products/{id}/skus/`
- `POST /api/v1/products/{id}/skus/`

当前列表支持的主要过滤：
- `category`
- `product_type`
- `status`
- 搜索字段：`product_code`、`product_name`、`brand`

---

## 四、采购管理 `/api/v1/purchase`

相关文件：
- `backend/purchase/urls.py`
- `backend/purchase/views.py`

### 4.1 供应商管理

已实现接口：
- `GET /api/v1/purchase/suppliers/`
- `POST /api/v1/purchase/suppliers/`
- `GET /api/v1/purchase/suppliers/{id}/`
- `PUT /api/v1/purchase/suppliers/{id}/`
- `DELETE /api/v1/purchase/suppliers/{id}/`

### 4.2 采购订单管理

已实现接口：
- `GET /api/v1/purchase/orders/`
- `POST /api/v1/purchase/orders/`
- `GET /api/v1/purchase/orders/{id}/`
- `PUT /api/v1/purchase/orders/{id}/`
- `DELETE /api/v1/purchase/orders/{id}/`
- `POST /api/v1/purchase/orders/{id}/submit/`
- `POST /api/v1/purchase/orders/{id}/approve/`

当前列表支持：
- `status`
- `supplier`
- 搜索字段：`order_no`

说明：
- 创建采购订单时支持提交 `items`
- 当前代码中收货单模型已存在，但以下接口**尚未实现**：
  - `POST /api/v1/purchase/orders/{id}/receipts/`
  - `POST /api/v1/purchase/receipts/{id}/confirm/`

---

## 五、销售管理 `/api/v1/sales`

相关文件：
- `backend/sales/urls.py`
- `backend/sales/views.py`

### 5.1 客户管理

已实现接口：
- `GET /api/v1/sales/customers/`
- `POST /api/v1/sales/customers/`
- `GET /api/v1/sales/customers/{id}/`
- `PUT /api/v1/sales/customers/{id}/`
- `DELETE /api/v1/sales/customers/{id}/`

### 5.2 销售订单管理

已实现接口：
- `GET /api/v1/sales/orders/`
- `POST /api/v1/sales/orders/`
- `GET /api/v1/sales/orders/{id}/`
- `PUT /api/v1/sales/orders/{id}/`
- `DELETE /api/v1/sales/orders/{id}/`
- `POST /api/v1/sales/orders/{id}/submit/`
- `POST /api/v1/sales/orders/{id}/approve/`

当前列表支持：
- `status`
- `customer`
- 搜索字段：`order_no`

说明：
- 创建销售订单时支持提交 `items`
- 当前代码中发货单模型已存在，但以下接口**尚未实现**：
  - `POST /api/v1/sales/orders/{id}/deliveries/`
  - `POST /api/v1/sales/deliveries/{id}/confirm/`

---

## 六、库存管理 `/api/v1/inventory`

相关文件：
- `backend/inventory/urls.py`
- `backend/inventory/views.py`

### 6.1 仓库管理

已实现接口：
- `GET /api/v1/inventory/warehouses/`
- `POST /api/v1/inventory/warehouses/`
- `GET /api/v1/inventory/warehouses/{id}/`
- `PUT /api/v1/inventory/warehouses/{id}/`
- `DELETE /api/v1/inventory/warehouses/{id}/`

### 6.2 库存查询

已实现接口：
- `GET /api/v1/inventory/stocks/`

当前主要过滤：
- `warehouse`
- `product_id`

### 6.3 库存流水查询

已实现接口：
- `GET /api/v1/inventory/transactions/`

当前主要过滤：
- `warehouse`
- `product_id`
- `txn_type`

### 6.4 库存盘点

以下接口当前**未实现**：
- `POST /api/v1/inventory/stocktakes/`
- `PUT /api/v1/inventory/stocktakes/{id}/items/`
- `POST /api/v1/inventory/stocktakes/{id}/submit/`
- `POST /api/v1/inventory/stocktakes/{id}/approve/`

---

## 七、财务管理 `/api/v1/finance`

相关文件：
- `backend/finance/urls.py`
- `backend/finance/views.py`

### 7.1 会计科目

已实现接口：
- `GET /api/v1/finance/accounts/`
- `POST /api/v1/finance/accounts/`
- `GET /api/v1/finance/accounts/{id}/`
- `PUT /api/v1/finance/accounts/{id}/`
- `DELETE /api/v1/finance/accounts/{id}/`
- `GET /api/v1/finance/accounts/tree/`

### 7.2 财务凭证

已实现接口：
- `GET /api/v1/finance/vouchers/`
- `POST /api/v1/finance/vouchers/`
- `GET /api/v1/finance/vouchers/{id}/`
- `PUT /api/v1/finance/vouchers/{id}/`
- `DELETE /api/v1/finance/vouchers/{id}/`
- `POST /api/v1/finance/vouchers/{id}/review/`
- `POST /api/v1/finance/vouchers/{id}/post_voucher/`

说明：
- 当前过账路径为 `/post_voucher/`，不是历史文档中的 `/post/`
- 新增凭证时会校验借贷方合计必须相等

### 7.3 应收管理

已实现接口：
- `GET /api/v1/finance/receivables/`
- `POST /api/v1/finance/receivables/`
- `GET /api/v1/finance/receivables/{id}/`
- `PUT /api/v1/finance/receivables/{id}/`
- `DELETE /api/v1/finance/receivables/{id}/`
- `POST /api/v1/finance/receivables/{id}/payments/`

### 7.4 应付管理

已实现接口：
- `GET /api/v1/finance/payables/`
- `POST /api/v1/finance/payables/`
- `GET /api/v1/finance/payables/{id}/`
- `PUT /api/v1/finance/payables/{id}/`
- `DELETE /api/v1/finance/payables/{id}/`
- `POST /api/v1/finance/payables/{id}/payments/`

---

## 八、人力资源 `/api/v1/hr`

相关文件：
- `backend/hr/urls.py`
- `backend/hr/views.py`

### 8.1 员工管理

已实现接口：
- `GET /api/v1/hr/employees/`
- `POST /api/v1/hr/employees/`
- `GET /api/v1/hr/employees/{id}/`
- `PUT /api/v1/hr/employees/{id}/`
- `DELETE /api/v1/hr/employees/{id}/`

### 8.2 考勤管理

已实现接口：
- `GET /api/v1/hr/attendances/`
- `POST /api/v1/hr/attendances/`
- `GET /api/v1/hr/attendances/{id}/`
- `PUT /api/v1/hr/attendances/{id}/`
- `DELETE /api/v1/hr/attendances/{id}/`

### 8.3 薪资管理

已实现接口：
- `GET /api/v1/hr/salaries/`
- `POST /api/v1/hr/salaries/`
- `GET /api/v1/hr/salaries/{id}/`
- `PUT /api/v1/hr/salaries/{id}/`
- `DELETE /api/v1/hr/salaries/{id}/`
- `POST /api/v1/hr/salaries/{id}/review/`
- `POST /api/v1/hr/salaries/generate/`
- `POST /api/v1/hr/salaries/batch_pay/`

说明：
- `generate` 当前为同步执行
- 返回内容为生成数量与提示信息，不是异步 `task_id`

---

## 九、当前未实现的通用接口

以下接口当前版本未在根路由中接入，不应直接使用：

- `/api/v1/common/dicts/{dict_type}`
- `/api/v1/common/tasks/{task_id}`
- `/api/v1/common/upload`
- 基于 `export=true` 的统一导出接口

参考文件：
- `backend/config/urls.py`

---

## 十、接口使用提醒

1. 当前项目中很多业务流程只实现到“单据管理 + 状态流转”，尚未打通库存和财务联动。
2. 文档中列出的“未实现接口”需要以后端路由和视图真实接入后再开放联调。
3. 若后续补齐 RBAC，部分接口的可访问性会从“登录即可访问”收紧为“具备权限码才可访问”。
