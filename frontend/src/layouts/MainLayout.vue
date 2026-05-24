<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside :width="collapsed ? '64px' : '230px'" class="sidebar">
      <div class="logo-area" @click="router.push('/dashboard')">
        <div class="logo-icon">
          <el-icon :size="22" color="#fff"><Grid /></el-icon>
        </div>
        <div v-if="!collapsed" class="logo-text">
          <span class="logo-title">ERP 系统</span>
          <span class="logo-sub">企业资源管理</span>
        </div>
      </div>

      <div class="menu-wrapper">
        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          router
          background-color="transparent"
          text-color="#94a3b8"
          active-text-color="#fff"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <template #title>首页</template>
          </el-menu-item>

          <el-sub-menu v-for="group in menuGroups" :key="group.key" :index="group.key">
            <template #title>
              <el-icon><component :is="group.icon" /></el-icon>
              <span>{{ group.title }}</span>
            </template>
            <el-menu-item v-for="item in group.children" :key="item.index" :index="item.index">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>

      <div v-if="!collapsed" class="sidebar-footer">
        <span class="footer-text">v1.0</span>
      </div>
    </el-aside>

    <!-- 右侧主体 -->
    <el-container class="main-container">
      <el-header class="header">
        <div class="header-left">
          <div class="collapse-btn" @click="collapsed = !collapsed">
            <el-icon :size="18">
              <Fold v-if="!collapsed" />
              <Expand v-else />
            </el-icon>
          </div>
          <el-breadcrumb separator="">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">
              <el-icon><House /></el-icon>
              <span class="breadcrumb-home">首页</span>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">
              <span class="breadcrumb-current">{{ route.meta.title }}</span>
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-badge :value="0" :max="99" :hidden="true" class="header-badge">
            <el-icon :size="20" class="header-icon"><Bell /></el-icon>
          </el-badge>
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ userInitial }}
              </el-avatar>
              <span class="user-name">{{ auth.user?.real_name || auth.user?.username }}</span>
              <el-icon :size="14" class="user-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span>个人信息</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Grid, House, Setting, User, UserFilled, Goods, Menu, Box,
  ShoppingCart, OfficeBuilding, Document, Sell, Avatar, Shop,
  DataLine, Money, List, Tickets, CreditCard, Wallet, PieChart,
  Calendar, Coin, Fold, Expand, Bell, ArrowDown, SwitchButton,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const collapsed = ref(false)

const menuGroups = computed(() => [
  {
    key: 'system',
    title: '系统管理',
    icon: Setting,
    children: [
      { index: '/system/users', title: '用户管理', icon: User, permission: 'system:user:list' },
      { index: '/system/roles', title: '角色管理', icon: UserFilled, permission: 'system:role:list' },
    ],
  },
  {
    key: 'product',
    title: '产品管理',
    icon: Goods,
    children: [
      { index: '/products/categories', title: '产品分类', icon: Menu, permission: 'product:category:list' },
      { index: '/products', title: '产品列表', icon: Box, permission: 'product:product:list' },
    ],
  },
  {
    key: 'purchase',
    title: '采购管理',
    icon: ShoppingCart,
    children: [
      { index: '/purchase/suppliers', title: '供应商', icon: OfficeBuilding, permission: 'purchase:supplier:list' },
      { index: '/purchase/orders', title: '采购订单', icon: Document, permission: 'purchase:order:list' },
    ],
  },
  {
    key: 'sales',
    title: '销售管理',
    icon: Sell,
    children: [
      { index: '/sales/customers', title: '客户管理', icon: Avatar, permission: 'sales:customer:list' },
      { index: '/sales/orders', title: '销售订单', icon: Document, permission: 'sales:order:list' },
    ],
  },
  {
    key: 'inventory',
    title: '库存管理',
    icon: Shop,
    children: [
      { index: '/inventory/warehouses', title: '仓库管理', icon: House, permission: 'inventory:warehouse:list' },
      { index: '/inventory/stocks', title: '库存查询', icon: DataLine, permission: 'inventory:stock:list' },
    ],
  },
  {
    key: 'finance',
    title: '财务管理',
    icon: Money,
    children: [
      { index: '/finance/accounts', title: '会计科目', icon: List, permission: 'finance:account:list' },
      { index: '/finance/vouchers', title: '财务凭证', icon: Tickets, permission: 'finance:voucher:list' },
      { index: '/finance/receivables', title: '应收账款', icon: CreditCard, permission: 'finance:receivable:list' },
      { index: '/finance/payables', title: '应付账款', icon: Wallet, permission: 'finance:payable:list' },
    ],
  },
  {
    key: 'hr',
    title: '人力资源',
    icon: PieChart,
    children: [
      { index: '/hr/employees', title: '员工管理', icon: User, permission: 'hr:employee:list' },
      { index: '/hr/attendances', title: '考勤管理', icon: Calendar, permission: 'hr:attendance:list' },
      { index: '/hr/salaries', title: '薪资管理', icon: Coin, permission: 'hr:salary:list' },
    ],
  },
].map(group => ({
  ...group,
  children: group.children.filter(item => auth.hasPermission(item.permission)),
})).filter(group => group.children.length > 0))

const activeMenu = computed(() => route.path)

const userInitial = computed(() => {
  const name = auth.user?.real_name || auth.user?.username || '?'
  return name.charAt(0).toUpperCase()
})

async function handleCommand(cmd) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    await auth.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

/* ===== 侧边栏 ===== */
.sidebar {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-x: hidden;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

/* Logo */
.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  transition: padding 0.3s;
}
.sidebar[width="64px"] .logo-area {
  padding: 0;
  justify-content: center;
}
.logo-icon {
  width: 34px; height: 34px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35);
  flex-shrink: 0;
}
.logo-text {
  display: flex;
  flex-direction: column;
  white-space: nowrap;
  overflow: hidden;
}
.logo-title {
  font-size: 16px; font-weight: 700; color: #fff;
  line-height: 1.3;
}
.logo-sub {
  font-size: 10px; color: rgba(255,255,255,0.35);
  letter-spacing: 1px;
}

/* 菜单区域 */
.menu-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 0;
}
.menu-wrapper::-webkit-scrollbar {
  width: 4px;
}
.menu-wrapper::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.08);
  border-radius: 2px;
}

/* 菜单项覆盖 */
.menu-wrapper :deep(.el-menu) {
  border-right: none;
}
.menu-wrapper :deep(.el-menu-item),
.menu-wrapper :deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
  margin: 2px 8px;
  border-radius: 8px;
  transition: all 0.2s;
  font-size: 14px;
}
.menu-wrapper :deep(.el-menu-item:hover),
.menu-wrapper :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #e2e8f0 !important;
}
.menu-wrapper :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.25), rgba(37, 99, 235, 0.08)) !important;
  color: #fff !important;
  border-left: 3px solid #2563eb;
}
.menu-wrapper :deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  color: #fff !important;
}
.menu-wrapper :deep(.el-sub-menu .el-menu) {
  background: rgba(0, 0, 0, 0.15) !important;
}
.menu-wrapper :deep(.el-sub-menu .el-menu-item) {
  padding-left: 56px !important;
  height: 40px;
  line-height: 40px;
  font-size: 13px;
}
.menu-wrapper :deep(.el-sub-menu .el-menu-item:hover) {
  background: rgba(255,255,255,0.04) !important;
}
.menu-wrapper :deep(.el-sub-menu .el-menu-item.is-active) {
  background: rgba(37, 99, 235, 0.15) !important;
  border-left: none;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 12px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  text-align: center;
  flex-shrink: 0;
}
.footer-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.2);
}

/* ===== 头部 ===== */
.main-container {
  background: #f1f5f9;
}
.header {
  height: 56px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 折叠按钮 */
.collapse-btn {
  width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}
.collapse-btn:hover {
  background: #f1f5f9;
  color: #2563eb;
}

/* 面包屑 */
.header-left :deep(.el-breadcrumb) {
  font-size: 13px;
}
.header-left :deep(.el-breadcrumb__inner) {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #94a3b8;
  font-weight: 400;
}
.breadcrumb-home {
  margin-left: 2px;
}
.breadcrumb-current {
  color: #1e293b;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 通知图标 */
.header-badge {
  cursor: pointer;
}
.header-icon {
  color: #64748b;
  transition: color 0.2s;
}
.header-icon:hover {
  color: #2563eb;
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}
.user-info:hover {
  background: #f8fafc;
}
.user-avatar {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
}
.user-name {
  font-size: 14px; color: #334155; font-weight: 500;
}
.user-arrow {
  color: #94a3b8;
  transition: transform 0.2s;
}

/* ===== 主区域 ===== */
.main {
  background: #f1f5f9;
  padding: 20px;
  overflow-y: auto;
}
</style>
