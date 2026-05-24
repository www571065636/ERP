# ERP 企业资源管理系统

Django + Vue3 全栈 ERP 系统，覆盖进销存、财务、人力资源等核心业务领域。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Django 4.2 LTS + Django REST Framework |
| 认证 | SimpleJWT (Access/Refresh Token) |
| 权限 | RBAC 自定义权限码 + 前端路由/按钮级控制 |
| 前端 | Vue 3 + Element Plus + Pinia + Axios |
| 数据库 | SQLite (开发) / MySQL 8.0 (生产) |
| 部署 | Docker + Docker Compose |

## 快速开始

### Docker 部署（推荐）

```bash
# 启动全部服务
docker compose up -d

# 后端: http://localhost:8002
# 前端: http://localhost:5173
```

首次启动会自动执行数据库迁移并创建管理员账号（密码由 `DJANGO_ADMIN_PASSWORD` 环境变量指定，未设置则随机生成）。

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
export DJANGO_SECRET_KEY=your-secret-key   # 必填
export DJANGO_DEBUG=true
python manage.py migrate
python manage.py runserver

# 前端
cd frontend
npm install
npm run dev
```

## 业务模块

| 模块 | 功能 | 核心能力 |
|------|------|---------|
| **系统管理** | 用户/角色/权限管理 | RBAC 权限体系，管理员面板 |
| **产品管理** | 产品/分类/SKU/计量单位 | 多级分类树、SKU 规格管理 |
| **采购管理** | 供应商/采购订单/收货 | 订单审批流、收货→入库→自动生成应付 |
| **销售管理** | 客户/销售订单/发货 | 订单审批流、发货→出库→自动生成应收 |
| **库存管理** | 仓库/库存台账/流水 | 移动加权平均成本、出入库流水追踪 |
| **财务管理** | 会计科目/凭证/应收应付 | 借贷平衡校验、收款/付款登记 |
| **人力资源** | 员工/考勤/薪资 | 薪资自动计算、批量生成/发放 |

### 跨模块联动

```
采购收货确认 → 库存自动入库(PURCHASE_IN) + 自动生成应付账款
销售发货确认 → 库存自动出库(SALE_OUT)   + 自动生成应收账款
```

## 项目结构

```
ERP/
├── backend/
│   ├── config/          # Django 配置
│   ├── common/          # 公共模块：权限、分页、响应、工具函数
│   ├── system/          # 系统管理：用户/角色/权限/认证
│   ├── product/         # 产品管理
│   ├── purchase/        # 采购管理
│   ├── sales/           # 销售管理
│   ├── inventory/       # 库存管理
│   ├── finance/         # 财务管理
│   ├── hr/              # 人力资源管理
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── views/       # 页面组件（17个业务页面）
│   │   ├── stores/      # Pinia 状态管理
│   │   ├── router/      # 路由配置
│   │   └── utils/       # HTTP 请求工具
│   └── Dockerfile
├── docs/                # 设计文档
├── docker-compose.yml
└── .gitignore
```

## API 概览

- 认证接口：登录/登出/Token刷新/修改密码
- 系统管理：用户/角色/权限 CRUD + 分配 + 权限树
- 产品管理：单位/分类/产品 CRUD + SKU + 分类树
- 采购管理：供应商/订单 CRUD + 审批 + 收货
- 销售管理：客户/订单 CRUD + 审批 + 发货
- 库存管理：仓库 CRUD + 库存台账 + 流水查询
- 财务管理：科目/凭证 CRUD + 审核/过账 + 应收应付/收款付款
- 人力资源：员工/考勤 CRUD + 薪资 CRUD + 批量生成/发放

所有 API 基于 `/api/v1/` 前缀，完整定义见 `docs/03-API接口文档.md`。

## 文档

- [系统设计文档](docs/01-系统设计文档.md)
- [数据库设计文档](docs/02-数据库设计文档.md)
- [API 接口文档](docs/03-API接口文档.md)
