<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon" style="background:linear-gradient(135deg,#1a73e8,#0d47a1)">
          <el-icon><House /></el-icon>
        </div>
        <div>
          <div class="page-header-title">工作台</div>
          <div class="page-header-sub">欢迎使用 ERP 管理系统，今天是 {{ today }}</div>
        </div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <div class="stat-card" :style="`--card-color:${card.color}`">
          <div class="stat-icon" :style="`background:${card.color}18`">
            <el-icon :size="28" :color="card.color"><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.title }}</div>
          </div>
          <div class="stat-trend" :style="`color:${card.color}`">
            <el-icon :size="36" :color="card.color + '20'"><component :is="card.icon" /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="table-card" style="margin-top:0">
      <div class="table-toolbar">
        <span class="table-toolbar-title">快捷入口</span>
      </div>
      <div class="shortcuts-grid">
        <div v-for="item in shortcuts" :key="item.path"
          class="shortcut-item" @click="router.push(item.path)">
          <div class="shortcut-icon" :style="`background:${item.color}15`">
            <el-icon :size="24" :color="item.color"><component :is="item.icon" /></el-icon>
          </div>
          <span class="shortcut-label">{{ item.title }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'

const router = useRouter()
const today = dayjs().format('YYYY年MM月DD日')

const statCards = [
  { title: '采购订单', value: '-', icon: 'ShoppingCart', color: '#1a73e8' },
  { title: '销售订单', value: '-', icon: 'Sell', color: '#52c41a' },
  { title: '库存预警', value: '-', icon: 'Warning', color: '#faad14' },
  { title: '待审批', value: '-', icon: 'Bell', color: '#f5222d' },
]

const shortcuts = [
  { title: '新增采购单', path: '/purchase/orders', icon: 'ShoppingCart', color: '#1a73e8' },
  { title: '新增销售单', path: '/sales/orders', icon: 'Sell', color: '#52c41a' },
  { title: '库存查询', path: '/inventory/stocks', icon: 'DataLine', color: '#722ed1' },
  { title: '员工管理', path: '/hr/employees', icon: 'User', color: '#fa8c16' },
  { title: '财务凭证', path: '/finance/vouchers', icon: 'Tickets', color: '#13c2c2' },
  { title: '系统用户', path: '/system/users', icon: 'Setting', color: '#eb2f96' },
]
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  position: relative;
  overflow: hidden;
  cursor: default;
  transition: box-shadow 0.2s;
}
.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.stat-icon {
  width: 56px; height: 56px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-body { flex: 1; }
.stat-value { font-size: 28px; font-weight: 700; color: #1a1a2e; line-height: 1.2; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.stat-trend {
  position: absolute; right: 16px; bottom: 8px;
  opacity: 0.15;
}

.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  padding: 16px 20px 20px;
}
.shortcut-item {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 16px 8px; border-radius: 10px; cursor: pointer;
  transition: background 0.15s;
}
.shortcut-item:hover { background: #f5f7fa; }
.shortcut-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.shortcut-label { font-size: 13px; color: #555; font-weight: 500; }
</style>
