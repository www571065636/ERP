<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon" style="background:linear-gradient(135deg,#722ed1,#531dab)">
          <el-icon><DataLine /></el-icon>
        </div>
        <div>
          <div class="page-header-title">库存查询</div>
          <div class="page-header-sub">实时查看各仓库产品库存与成本</div>
        </div>
      </div>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="仓库">
          <el-select v-model="query.warehouse" placeholder="全部仓库" clearable style="width:150px" @change="loadData">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.warehouse_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.search" placeholder="产品编码/名称" clearable style="width:200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">库存明细</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="warehouse_name" label="仓库" width="120">
          <template #default="{ row }">
            <el-tag effect="light" type="info" size="small">{{ row.warehouse_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_code" label="产品编码" width="120" />
        <el-table-column prop="product_name" label="产品名称" min-width="160" />
        <el-table-column prop="quantity" label="库存数量" width="100" align="right">
          <template #default="{ row }">
            <span style="font-weight:500">{{ row.quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="locked_qty" label="锁定数量" width="100" align="right">
          <template #default="{ row }">
            <span style="color:#faad14">{{ row.locked_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column label="可用数量" width="100" align="right">
          <template #default="{ row }">
            <span style="color:#52c41a;font-weight:500">
              {{ (Number(row.quantity) - Number(row.locked_qty)).toFixed(4) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_cost" label="平均成本" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#722ed1">{{ row.avg_cost ? `¥${row.avg_cost}` : '-' }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
          :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/utils/http'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const warehouses = ref([])
const query = reactive({ warehouse: '', search: '', page: 1, page_size: 20 })

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/inventory/stocks/', { params })
    list.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { warehouse: '', search: '', page: 1 })
  loadData()
}

async function loadWarehouses() {
  const res = await http.get('/inventory/warehouses/', { params: { page_size: 999 } })
  warehouses.value = res.data.list
}

onMounted(() => { loadWarehouses(); loadData() })
</script>
