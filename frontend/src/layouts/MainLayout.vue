<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <el-icon size="24" color="#fff"><Grid /></el-icon>
        <span v-if="!collapsed" class="logo-text">ERP 系统</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        router
        background-color="#001529"
        text-color="#ffffffa0"
        active-text-color="#fff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon><template #title>首页</template>
        </el-menu-item>

        <el-sub-menu index="system">
          <template #title><el-icon><Setting /></el-icon><span>系统管理</span></template>
          <el-menu-item index="/system/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
          <el-menu-item index="/system/roles"><el-icon><UserFilled /></el-icon>角色管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="product">
          <template #title><el-icon><Goods /></el-icon><span>产品管理</span></template>
          <el-menu-item index="/products/categories"><el-icon><Menu /></el-icon>产品分类</el-menu-item>
          <el-menu-item index="/products"><el-icon><Box /></el-icon>产品列表</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="purchase">
          <template #title><el-icon><ShoppingCart /></el-icon><span>采购管理</span></template>
          <el-menu-item index="/purchase/suppliers"><el-icon><OfficeBuilding /></el-icon>供应商</el-menu-item>
          <el-menu-item index="/purchase/orders"><el-icon><Document /></el-icon>采购订单</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="sales">
          <template #title><el-icon><Sell /></el-icon><span>销售管理</span></template>
          <el-menu-item index="/sales/customers"><el-icon><Avatar /></el-icon>客户管理</el-menu-item>
          <el-menu-item index="/sales/orders"><el-icon><Document /></el-icon>销售订单</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="inventory">
          <template #title><el-icon><Shop /></el-icon><span>库存管理</span></template>
          <el-menu-item index="/inventory/warehouses"><el-icon><House /></el-icon>仓库管理</el-menu-item>
          <el-menu-item index="/inventory/stocks"><el-icon><DataLine /></el-icon>库存查询</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="finance">
          <template #title><el-icon><Money /></el-icon><span>财务管理</span></template>
          <el-menu-item index="/finance/accounts"><el-icon><List /></el-icon>会计科目</el-menu-item>
          <el-menu-item index="/finance/vouchers"><el-icon><Tickets /></el-icon>财务凭证</el-menu-item>
          <el-menu-item index="/finance/receivables"><el-icon><CreditCard /></el-icon>应收账款</el-menu-item>
          <el-menu-item index="/finance/payables"><el-icon><Wallet /></el-icon>应付账款</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="hr">
          <template #title><el-icon><PieChart /></el-icon><span>人力资源</span></template>
          <el-menu-item index="/hr/employees"><el-icon><User /></el-icon>员工管理</el-menu-item>
          <el-menu-item index="/hr/attendances"><el-icon><Calendar /></el-icon>考勤管理</el-menu-item>
          <el-menu-item index="/hr/salaries"><el-icon><Coin /></el-icon>薪资管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" /><Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" style="background:#1a73e8">{{ userInitial }}</el-avatar>
              <span style="margin-left:8px">{{ auth.user?.real_name || auth.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
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
import { useAuthStore } from '@/stores/auth'
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const collapsed = ref(false)

const userInitial = computed(() => {
  const name = auth.user?.real_name || auth.user?.username || '?'
  return name.charAt(0).toUpperCase()
})

async function handleCommand(cmd) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    await auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout { height: 100vh; }
.sidebar {
  background: #001529;
  transition: width 0.2s;
  overflow-x: hidden;
  overflow-y: auto;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #ffffff15;
}
.logo-text { color: #fff; font-size: 16px; font-weight: 700; white-space: nowrap; }
.header {
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn { font-size: 20px; cursor: pointer; color: #666; }
.header-right { display: flex; align-items: center; }
.user-info { display: flex; align-items: center; cursor: pointer; color: #333; }
.main { background: #f5f7fa; padding: 20px; }
</style>
