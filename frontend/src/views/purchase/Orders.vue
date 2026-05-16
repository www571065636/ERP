<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><ShoppingCart /></el-icon>
        </div>
        <div>
          <div class="page-header-title">采购订单</div>
          <div class="page-header-sub">管理采购申请、审批与收货流程</div>
        </div>
      </div>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增采购单
      </el-button>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="关键词">
          <el-input v-model="query.search" placeholder="单号/供应商" clearable style="width:200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:110px">
            <el-option v-for="(label, val) in statusLabels" :key="val" :label="label" :value="Number(val)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">采购订单列表</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="采购单号" width="160">
          <template #default="{ row }">
            <el-tag effect="light" type="warning" size="small">{{ row.order_no }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商" min-width="140" />
        <el-table-column prop="order_date" label="订单日期" width="100" />
        <el-table-column prop="total_amount" label="总金额" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#1a73e8;font-weight:500">¥{{ row.total_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="statusTypes[row.status]" size="small">
              {{ statusLabels[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button text type="primary" size="small" @click="viewDetail(row)">查看</el-button>
              <template v-if="row.status === 0">
                <span class="action-sep">|</span>
                <el-button text type="primary" size="small" @click="submitOrder(row)">提交</el-button>
                <span class="action-sep">|</span>
                <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </template>
              <template v-if="row.status === 1">
                <span class="action-sep">|</span>
                <el-button text type="success" size="small" @click="approveOrder(row)">审批</el-button>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
          :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px"
        class="dialog-form" :disabled="viewMode">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="供应商" prop="supplier">
              <el-select v-model="form.supplier" filterable style="width:100%" placeholder="选择供应商">
                <el-option v-for="s in suppliers" :key="s.id" :label="s.supplier_name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="订单日期" prop="order_date">
              <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计到货">
              <el-date-picker v-model="form.expected_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="仓库">
              <el-select v-model="form.warehouse_id" style="width:100%" placeholder="选择仓库">
                <el-option v-for="w in warehouses" :key="w.id" :label="w.warehouse_name" :value="w.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="items-header">
          <span style="font-weight:600">采购明细</span>
          <el-button v-if="!viewMode" size="small" @click="addItem">
            <el-icon><Plus /></el-icon>添加行
          </el-button>
        </div>
        <el-table :data="form.items" border size="small" style="margin-bottom:8px">
          <el-table-column label="产品" min-width="180">
            <template #default="{ row }">
              <el-select v-if="!viewMode" v-model="row.product_id" filterable size="small"
                style="width:100%" @change="onProductChange(row)">
                <el-option v-for="p in products" :key="p.id" :label="p.product_name" :value="p.id" />
              </el-select>
              <span v-else>{{ row.product_name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="110">
            <template #default="{ row }">
              <el-input-number v-if="!viewMode" v-model="row.qty" :min="1"
                :step="1" :precision="0" size="small" style="width:100%" @change="calcRow(row)" />
              <span v-else>{{ row.qty }}</span>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="130">
            <template #default="{ row }">
              <el-input-number v-if="!viewMode" v-model="row.unit_price" :min="0"
                :precision="2" size="small" style="width:100%" @change="calcRow(row)" />
              <span v-else>{{ row.unit_price }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="110">
            <template #default="{ row }">
              <span style="color:#1a73e8">¥{{ row.amount || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="!viewMode" label="" width="55" align="center">
            <template #default="{ $index }">
              <el-button text type="danger" size="small" @click="form.items.splice($index, 1)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="text-align:right;padding:8px 0;font-weight:600;font-size:15px">
          合计：<span style="color:#1a73e8">¥{{ totalAmount }}</span>
        </div>
      </el-form>
      <template #footer v-if="!viewMode">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import http from '@/utils/http'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const viewMode = ref(false)
const formRef = ref()
const form = ref({ items: [] })
const suppliers = ref([])
const warehouses = ref([])
const products = ref([])
const query = reactive({ search: '', status: '', page: 1, page_size: 20 })
const statusLabels = { 0: '草稿', 1: '待审批', 2: '已审批', 3: '部分收货', 4: '全部收货', 9: '已取消' }
const statusTypes = { 0: 'info', 1: 'warning', 2: 'success', 3: 'primary', 4: 'success', 9: 'danger' }
const rules = {
  supplier: [{ required: true, message: '请选择供应商' }],
  order_date: [{ required: true, message: '请选择订单日期' }],
}

const dialogTitle = computed(() =>
  viewMode.value ? `采购单 ${form.value.order_no}` : (form.value.id ? '编辑采购单' : '新增采购单')
)
const totalAmount = computed(() =>
  form.value.items.reduce((s, i) => s + (Number(i.amount) || 0), 0).toFixed(2)
)

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/purchase/orders/', { params })
    list.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { search: '', status: '', page: 1 })
  loadData()
}

async function loadOptions() {
  const [s, w, p] = await Promise.all([
    http.get('/purchase/suppliers/', { params: { page_size: 999 } }),
    http.get('/inventory/warehouses/', { params: { page_size: 999 } }),
    http.get('/products/', { params: { page_size: 999 } }),
  ])
  suppliers.value = s.data.list
  warehouses.value = w.data.list
  products.value = p.data.list
}

function openDialog(row = {}) {
  viewMode.value = false
  form.value = { order_date: dayjs().format('YYYY-MM-DD'), items: [], ...row }
  dialogVisible.value = true
  loadOptions()
}

function viewDetail(row) {
  viewMode.value = true
  form.value = { ...row, items: row.items || [] }
  dialogVisible.value = true
  if (!row.items) {
    http.get(`/purchase/orders/${row.id}/`).then(res => { form.value = res.data })
  }
}

function addItem() {
  form.value.items.push({ product_id: null, unit_id: 1, qty: 1, unit_price: 0, amount: 0 })
}

function onProductChange(row) {
  const p = products.value.find(x => x.id === row.product_id)
  if (p) {
    row.product_name = p.product_name
    row.unit_price = p.purchase_price || 0
    calcRow(row)
  }
}

function calcRow(row) {
  row.amount = ((row.qty || 0) * (row.unit_price || 0)).toFixed(2)
}

async function handleSave() {
  await formRef.value.validate()
  if (!form.value.items.length) return ElMessage.warning('请添加采购明细')
  if (form.value.items.some(i => !i.product_id)) return ElMessage.warning('请为所有明细行选择产品')
  saving.value = true
  try {
    const payload = { ...form.value, total_amount: totalAmount.value }
    if (form.value.id) {
      await http.put(`/purchase/orders/${form.value.id}/`, payload)
    } else {
      await http.post('/purchase/orders/', payload)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function submitOrder(row) {
  await http.post(`/purchase/orders/${row.id}/submit/`)
  ElMessage.success('提交成功')
  loadData()
}

async function approveOrder(row) {
  await ElMessageBox.confirm('确认审批通过？', '审批', { type: 'warning' })
  await http.post(`/purchase/orders/${row.id}/approve/`)
  ElMessage.success('审批成功')
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除采购单 "${row.order_no}"？`, '提示', { type: 'warning' })
  await http.delete(`/purchase/orders/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0 8px;
}
</style>
