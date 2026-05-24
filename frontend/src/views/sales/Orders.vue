<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Sell /></el-icon>
        </div>
        <div>
          <div class="page-header-title">销售订单</div>
          <div class="page-header-sub">管理销售申请、审批与发货流程</div>
        </div>
      </div>
      <el-button v-if="auth.hasPermission('sales:order:create')" type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增销售单
      </el-button>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="关键词">
          <el-input v-model="query.search" placeholder="单号/客户" clearable style="width:200px" />
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
        <span class="table-toolbar-title">销售订单列表</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="销售单号" width="160">
          <template #default="{ row }">
            <el-tag effect="light" type="success" size="small">{{ row.order_no }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" min-width="140" />
        <el-table-column prop="order_date" label="订单日期" width="100" />
        <el-table-column prop="total_amount" label="总金额" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#13c2c2;font-weight:500">¥{{ row.total_amount }}</span>
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
              <template v-if="row.status === 0 && auth.hasPermission('sales:order:submit')">
                <span class="action-sep">|</span>
                <el-button text type="warning" size="small" @click="submitOrder(row)">提交</el-button>
              </template>
              <template v-if="row.status === 0 && auth.hasPermission('sales:order:update')">
                <span class="action-sep">|</span>
                <el-button text type="primary" size="small" @click="editOrder(row)">编辑</el-button>
              </template>
              <template v-if="row.status === 0 && auth.hasPermission('sales:order:delete')">
                <span class="action-sep">|</span>
                <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </template>
              <template v-if="row.status === 1 && auth.hasPermission('sales:order:approve')">
                <span class="action-sep">|</span>
                <el-button text type="success" size="small" @click="approveOrder(row)">审批</el-button>
              </template>
              <template v-if="[2, 3].includes(row.status) && auth.hasPermission('sales:order:approve')">
                <span class="action-sep">|</span>
                <el-button text type="success" size="small" @click="openDeliveryDialog(row)">发货</el-button>
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
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px"
        class="dialog-form" :disabled="viewMode">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户" prop="customer">
              <el-select v-model="form.customer" filterable style="width:100%" placeholder="选择客户">
                <el-option v-for="c in customers" :key="c.id" :label="c.customer_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="订单日期" prop="order_date">
              <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="交货日期">
              <el-date-picker v-model="form.delivery_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
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
          <span style="font-weight:600">销售明细</span>
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
              <span style="color:#13c2c2">¥{{ row.amount || 0 }}</span>
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
          合计：<span style="color:#13c2c2">¥{{ totalAmount }}</span>
        </div>
      </el-form>
      <template #footer v-if="!viewMode">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="deliveryVisible" title="销售发货" width="780px" destroy-on-close>
      <el-table :data="deliveryItems" border size="small">
        <el-table-column prop="product_name" label="产品" min-width="180" />
        <el-table-column prop="qty" label="订单数量" width="110" align="right" />
        <el-table-column prop="delivered_qty" label="已发数量" width="110" align="right" />
        <el-table-column label="本次发货" width="140">
          <template #default="{ row }">
            <el-input-number v-model="row.confirm_qty" :min="0" :max="row.remaining_qty" :precision="4" style="width:100%" />
          </template>
        </el-table-column>
        <el-table-column prop="remaining_qty" label="未发数量" width="110" align="right" />
      </el-table>
      <template #footer>
        <el-button @click="deliveryVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingDelivery" @click="handleDelivery">创建并确认发货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import http from '@/utils/http'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const viewMode = ref(false)
const formRef = ref()
const form = ref({ items: [] })
const customers = ref([])
const warehouses = ref([])
const products = ref([])
const deliveryVisible = ref(false)
const deliveryItems = ref([])
const currentDeliveryOrder = ref(null)
const savingDelivery = ref(false)
const query = reactive({ search: '', status: '', page: 1, page_size: 20 })
const statusLabels = { 0: '草稿', 1: '待审批', 2: '已审批', 3: '部分发货', 4: '全部发货', 9: '已取消' }
const statusTypes = { 0: 'info', 1: 'warning', 2: 'success', 3: 'primary', 4: 'success', 9: 'danger' }
const rules = {
  customer: [{ required: true, message: '请选择客户' }],
  order_date: [{ required: true, message: '请选择订单日期' }],
}

const dialogTitle = computed(() =>
  viewMode.value ? `销售单 ${form.value.order_no}` : (form.value.id ? '编辑销售单' : '新增销售单')
)
const totalAmount = computed(() =>
  form.value.items.reduce((s, i) => s + (Number(i.amount) || 0), 0).toFixed(2)
)

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/sales/orders/', { params })
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
  const [c, w, p] = await Promise.all([
    http.get('/sales/customers/', { params: { page_size: 999 } }),
    http.get('/inventory/warehouses/', { params: { page_size: 999 } }),
    http.get('/products/', { params: { page_size: 999 } }),
  ])
  customers.value = c.data.list
  warehouses.value = w.data.list
  products.value = p.data.list
}

function openDialog(row = {}) {
  viewMode.value = false
  form.value = { order_date: dayjs().format('YYYY-MM-DD'), currency: 'CNY', items: [], ...row }
  dialogVisible.value = true
  loadOptions()
}

async function editOrder(row) {
  viewMode.value = false
  await loadOptions()
  const res = await http.get(`/sales/orders/${row.id}/`)
  form.value = {
    id: res.data.id,
    customer: res.data.customer,
    warehouse_id: res.data.warehouse_id,
    order_date: res.data.order_date,
    delivery_date: res.data.delivery_date,
    currency: res.data.currency || 'CNY',
    remark: res.data.remark,
    items: (res.data.items || []).map(item => ({
      id: item.id,
      product_id: item.product_id,
      sku_id: item.sku_id,
      unit_id: item.unit_id,
      qty: Number(item.qty),
      unit_price: Number(item.unit_price),
      tax_rate: Number(item.tax_rate || 0),
      amount: Number(item.amount || 0),
      delivered_qty: Number(item.delivered_qty || 0),
      remark: item.remark || '',
    })),
  }
  dialogVisible.value = true
}

function viewDetail(row) {
  viewMode.value = true
  form.value = { ...row, items: row.items || [] }
  dialogVisible.value = true
  if (!row.items) {
    http.get(`/sales/orders/${row.id}/`).then(res => { form.value = res.data })
  }
}

function addItem() {
  form.value.items.push({ product_id: null, sku_id: null, unit_id: 1, qty: 1, unit_price: 0, tax_rate: 0, amount: 0, remark: '' })
}

function onProductChange(row) {
  const p = products.value.find(x => x.id === row.product_id)
  if (p) {
    row.product_name = p.product_name
    row.unit_price = p.sale_price || 0
    calcRow(row)
  }
}

function calcRow(row) {
  row.amount = ((row.qty || 0) * (row.unit_price || 0)).toFixed(2)
}

async function handleSave() {
  await formRef.value.validate()
  if (!form.value.items.length) return ElMessage.warning('请添加销售明细')
  if (form.value.items.some(i => !i.product_id)) return ElMessage.warning('请为所有明细行选择产品')
  saving.value = true
  try {
    const payload = {
      customer: form.value.customer,
      warehouse_id: form.value.warehouse_id,
      order_date: form.value.order_date,
      delivery_date: form.value.delivery_date,
      currency: form.value.currency || 'CNY',
      remark: form.value.remark || '',
      items: form.value.items.map(item => ({
        ...(item.id ? { id: item.id } : {}),
        product_id: item.product_id,
        sku_id: item.sku_id || null,
        unit_id: item.unit_id || 1,
        qty: item.qty,
        unit_price: item.unit_price,
        tax_rate: item.tax_rate || 0,
        remark: item.remark || '',
      })),
    }
    if (form.value.id) {
      await http.put(`/sales/orders/${form.value.id}/`, payload)
    } else {
      await http.post('/sales/orders/', payload)
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
  await ElMessageBox.confirm('确认提交销售单？提交后将进入审批。', '提示', { type: 'warning' })
  await http.post(`/sales/orders/${row.id}/submit/`)
  ElMessage.success('提交成功')
  loadData()
}

async function approveOrder(row) {
  await ElMessageBox.confirm('确认审批通过？', '审批', { type: 'warning' })
  await http.post(`/sales/orders/${row.id}/approve/`)
  ElMessage.success('审批成功')
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除销售单 "${row.order_no}"？`, '提示', { type: 'warning' })
  await http.delete(`/sales/orders/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

async function openDeliveryDialog(row) {
  const res = await http.get(`/sales/orders/${row.id}/`)
  currentDeliveryOrder.value = res.data
  deliveryItems.value = (res.data.items || []).map(item => ({
    ...item,
    product_name: products.value.find(p => p.id === item.product_id)?.product_name || `产品#${item.product_id}`,
    remaining_qty: Math.max(Number(item.qty) - Number(item.delivered_qty || 0), 0),
    confirm_qty: Math.max(Number(item.qty) - Number(item.delivered_qty || 0), 0),
  })).filter(item => item.remaining_qty > 0)
  if (!deliveryItems.value.length) {
    ElMessage.warning('该销售单已全部发货')
    return
  }
  deliveryVisible.value = true
}

async function handleDelivery() {
  const items = deliveryItems.value
    .filter(item => Number(item.confirm_qty) > 0)
    .map(item => ({ order_item_id: item.id, qty: item.confirm_qty }))
  if (!items.length) {
    ElMessage.warning('请填写本次发货数量')
    return
  }
  savingDelivery.value = true
  try {
    const delivery = await http.post(`/sales/orders/${currentDeliveryOrder.value.id}/deliveries/`, { items })
    await http.post(`/sales/orders/${currentDeliveryOrder.value.id}/deliveries/${delivery.data.id}/confirm/`)
    ElMessage.success('发货成功')
    deliveryVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    savingDelivery.value = false
  }
}

onMounted(async () => {
  await loadOptions()
  loadData()
})
</script>

<style scoped>
.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0 8px;
}
</style>
