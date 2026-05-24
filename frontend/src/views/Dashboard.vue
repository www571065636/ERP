<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><House /></el-icon>
        </div>
        <div>
          <div class="page-header-title">工作台</div>
          <div class="page-header-sub">欢迎使用 ERP 管理系统，今天是 {{ today }}</div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <div class="stat-card">
          <div class="stat-bg" :style="{ background: card.gradient }" />
          <div class="stat-icon">
            <el-icon :size="24"><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.title }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">快捷入口</span>
      </div>
      <div class="shortcuts-grid">
        <div
          v-for="item in shortcuts"
          :key="item.path"
          class="shortcut-item"
          @click="router.push(item.path)"
        >
          <div class="shortcut-icon" :style="{ background: item.color + '15' }">
            <el-icon :size="22" :color="item.color">
              <component :is="item.icon" />
            </el-icon>
          </div>
          <span class="shortcut-label">{{ item.title }}</span>
        </div>
      </div>
    </div>

    <!-- 最近动态 -->
    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">系统概览</span>
      </div>
      <div class="overview-grid">
        <div class="overview-item" v-for="item in overview" :key="item.label">
          <div class="overview-dot" :style="{ background: item.color }" />
          <span class="overview-label">{{ item.label }}</span>
          <span class="overview-value">{{ item.value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import http from '@/utils/http'

const router = useRouter()
const today = dayjs().format('YYYY年MM月DD日')

const statCards = ref([
  { title: '采购订单', value: '0', icon: 'ShoppingCart', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { title: '销售订单', value: '0', icon: 'Sell', gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  { title: '库存预警', value: '0', icon: 'Warning', gradient: 'linear-gradient(135deg, #ef4444, #dc2626)' },
  { title: '员工总数', value: '0', icon: 'User', gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
])

const shortcuts = [
  { title: '采购订单', path: '/purchase/orders', icon: 'ShoppingCart', color: '#f59e0b' },
  { title: '销售订单', path: '/sales/orders', icon: 'Sell', color: '#06b6d4' },
  { title: '库存查询', path: '/inventory/stocks', icon: 'DataLine', color: '#8b5cf6' },
  { title: '员工管理', path: '/hr/employees', icon: 'User', color: '#ec4899' },
  { title: '财务凭证', path: '/finance/vouchers', icon: 'Tickets', color: '#10b981' },
  { title: '系统用户', path: '/system/users', icon: 'Setting', color: '#6366f1' },
]

const overview = ref([
  { label: '产品总数', value: '0', color: '#10b981' },
  { label: '供应商数', value: '0', color: '#f59e0b' },
  { label: '客户数', value: '0', color: '#06b6d4' },
  { label: '仓库数', value: '0', color: '#8b5cf6' },
  { label: '待审批', value: '0', color: '#ef4444' },
  { label: '本月订单', value: '0', color: '#6366f1' },
])

async function loadStats() {
  try {
    const res = await http.get('/system/dashboard/stats/')
    const cardMap = Object.fromEntries((res.data.stat_cards || []).map(item => [item.title, item.value]))
    statCards.value = statCards.value.map(item => ({ ...item, value: String(cardMap[item.title] ?? item.value) }))
    const overviewMap = Object.fromEntries((res.data.overview || []).map(item => [item.label, item.value]))
    overview.value = overview.value.map(item => ({ ...item, value: String(overviewMap[item.label] ?? item.value) }))
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(loadStats)
</script>

<style scoped>
/* 统计卡片 */
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}
.stat-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,.1);
  transform: translateY(-2px);
}
.stat-bg {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 3px;
}
.stat-icon {
  width: 48px; height: 48px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: #f8fafc;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.stat-body { flex: 1; min-width: 0; }
.stat-value {
  font-size: 28px; font-weight: 700;
  color: #1e293b; line-height: 1.2;
}
.stat-label {
  font-size: 13px; color: #94a3b8; margin-top: 4px;
}

/* 快捷入口 */
.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0;
  padding: 4px;
}
.shortcut-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}
.shortcut-item:hover { background: #f8fafc; }
.shortcut-icon {
  width: 48px; height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.shortcut-label {
  font-size: 13px; color: #475569; font-weight: 500;
}

/* 系统概览 */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0;
  padding: 16px 20px 20px;
}
.overview-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px;
  border-radius: 8px;
  transition: background 0.15s;
}
.overview-item:hover { background: #f8fafc; }
.overview-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
}
.overview-label {
  font-size: 12px; color: #94a3b8;
}
.overview-value {
  font-size: 20px; font-weight: 700; color: #1e293b;
}
</style>
