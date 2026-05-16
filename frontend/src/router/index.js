import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '首页' } },
      // 系统管理
      { path: 'system/users', name: 'Users', component: () => import('@/views/system/Users.vue'), meta: { title: '用户管理' } },
      { path: 'system/roles', name: 'Roles', component: () => import('@/views/system/Roles.vue'), meta: { title: '角色管理' } },
      // 产品管理
      { path: 'products', name: 'Products', component: () => import('@/views/product/Products.vue'), meta: { title: '产品管理' } },
      { path: 'products/categories', name: 'Categories', component: () => import('@/views/product/Categories.vue'), meta: { title: '产品分类' } },
      // 采购管理
      { path: 'purchase/suppliers', name: 'Suppliers', component: () => import('@/views/purchase/Suppliers.vue'), meta: { title: '供应商管理' } },
      { path: 'purchase/orders', name: 'PurchaseOrders', component: () => import('@/views/purchase/Orders.vue'), meta: { title: '采购订单' } },
      // 销售管理
      { path: 'sales/customers', name: 'Customers', component: () => import('@/views/sales/Customers.vue'), meta: { title: '客户管理' } },
      { path: 'sales/orders', name: 'SalesOrders', component: () => import('@/views/sales/Orders.vue'), meta: { title: '销售订单' } },
      // 库存管理
      { path: 'inventory/warehouses', name: 'Warehouses', component: () => import('@/views/inventory/Warehouses.vue'), meta: { title: '仓库管理' } },
      { path: 'inventory/stocks', name: 'Stocks', component: () => import('@/views/inventory/Stocks.vue'), meta: { title: '库存查询' } },
      // 财务管理
      { path: 'finance/accounts', name: 'Accounts', component: () => import('@/views/finance/Accounts.vue'), meta: { title: '会计科目' } },
      { path: 'finance/vouchers', name: 'Vouchers', component: () => import('@/views/finance/Vouchers.vue'), meta: { title: '财务凭证' } },
      { path: 'finance/receivables', name: 'Receivables', component: () => import('@/views/finance/Receivables.vue'), meta: { title: '应收账款' } },
      { path: 'finance/payables', name: 'Payables', component: () => import('@/views/finance/Payables.vue'), meta: { title: '应付账款' } },
      // 人力资源
      { path: 'hr/employees', name: 'Employees', component: () => import('@/views/hr/Employees.vue'), meta: { title: '员工管理' } },
      { path: 'hr/attendances', name: 'Attendances', component: () => import('@/views/hr/Attendances.vue'), meta: { title: '考勤管理' } },
      { path: 'hr/salaries', name: 'Salaries', component: () => import('@/views/hr/Salaries.vue'), meta: { title: '薪资管理' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return '/login'
  }
  if (to.path === '/login' && auth.isLoggedIn) {
    return '/'
  }
})

export default router
