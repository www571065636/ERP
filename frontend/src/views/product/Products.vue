<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Box /></el-icon>
        </div>
        <div>
          <div class="page-header-title">产品管理</div>
          <div class="page-header-sub">管理产品信息、价格与库存参数</div>
        </div>
      </div>
      <el-button v-if="auth.hasPermission('product:product:create')" type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增产品
      </el-button>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="关键词">
          <el-input v-model="query.search" placeholder="编码/名称" clearable style="width:200px" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="query.product_type" placeholder="全部" clearable style="width:110px">
            <el-option v-for="(label, val) in typeLabels" :key="val" :label="label" :value="Number(val)" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:90px">
            <el-option label="启用" :value="1" /><el-option label="停用" :value="0" />
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
        <span class="table-toolbar-title">产品列表</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="product_code" label="产品编码" width="130">
          <template #default="{ row }">
            <el-tag effect="light" type="info" size="small">{{ row.product_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="产品名称" min-width="160" />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="product_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag effect="light" :type="typeColors[row.product_type]" size="small">
              {{ typeLabels[row.product_type] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sale_price" label="销售价" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#1a73e8;font-weight:500">{{ row.sale_price ? `¥${row.sale_price}` : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="row.status ? 'success' : 'danger'" size="small">
              {{ row.status ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button v-if="auth.hasPermission('product:product:update')" text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <span v-if="auth.hasPermission('product:product:update') && auth.hasPermission('product:product:delete')" class="action-sep">|</span>
              <el-button v-if="auth.hasPermission('product:product:delete')" text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
          :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑产品' : '新增产品'"
      width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品编码" prop="product_code">
              <el-input v-model="form.product_code" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品名称" prop="product_name">
              <el-input v-model="form.product_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品类型">
              <el-select v-model="form.product_type" style="width:100%">
                <el-option v-for="(label, val) in typeLabels" :key="val" :label="label" :value="Number(val)" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌">
              <el-input v-model="form.brand" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="采购价">
              <el-input-number v-model="form.purchase_price" :precision="4" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="销售价">
              <el-input-number v-model="form.sale_price" :precision="4" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率(%)">
              <el-input-number v-model="form.tax_rate" :precision="2" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最低库存">
              <el-input-number v-model="form.min_stock" :precision="4" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/utils/http'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const formRef = ref()
const form = ref({})
const typeLabels = { 1: '成品', 2: '原材料', 3: '半成品', 4: '服务' }
const typeColors = { 1: 'success', 2: 'primary', 3: 'warning', 4: 'info' }
const query = reactive({ search: '', product_type: '', status: '', page: 1, page_size: 20 })
const rules = {
  product_code: [{ required: true, message: '请输入产品编码' }],
  product_name: [{ required: true, message: '请输入产品名称' }],
}

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/products/', { params })
    list.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { search: '', product_type: '', status: '', page: 1 })
  loadData()
}

function openDialog(row = {}) {
  form.value = { product_type: 1, tax_rate: 0, min_stock: 0, ...row }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await http.put(`/products/${form.value.id}/`, form.value)
    } else {
      await http.post('/products/', form.value)
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

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除产品 "${row.product_name}"？`, '提示', { type: 'warning' })
  await http.delete(`/products/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
