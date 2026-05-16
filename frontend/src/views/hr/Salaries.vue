<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Coin /></el-icon>
        </div>
        <div>
          <div class="page-header-title">薪资管理</div>
          <div class="page-header-sub">管理员工薪资核算、审核与发放</div>
        </div>
      </div>
      <div style="display:flex;gap:8px">
        <el-button @click="generateVisible = true">批量生成薪资</el-button>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon>新增薪资单
        </el-button>
      </div>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="期间">
          <el-date-picker v-model="query.period" type="month" value-format="YYYY-MM"
            placeholder="选择期间" clearable style="width:140px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:110px">
            <el-option label="草稿" :value="0" />
            <el-option label="已审核" :value="1" />
            <el-option label="已发放" :value="2" />
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
        <span class="table-toolbar-title">薪资单列表</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="salary_no" label="薪资单号" min-width="160">
          <template #default="{ row }">
            <el-tag effect="light" type="info" size="small">{{ row.salary_no }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="员工" min-width="160">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:6px">
              <el-avatar :size="28" style="background:#eb2f96;flex-shrink:0;font-size:12px">
                {{ row.employee_name?.charAt(0) }}
              </el-avatar>
              <div>
                <div style="font-size:13px;font-weight:500">{{ row.employee_name }}</div>
                <div style="font-size:11px;color:#999">{{ row.employee_no }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="period" label="期间" width="80" />
        <el-table-column prop="gross_salary" label="应发工资" width="110" align="right">
          <template #default="{ row }">
            <span style="font-weight:500">¥{{ row.gross_salary }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_salary" label="实发工资" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#eb2f96;font-weight:600">¥{{ row.net_salary }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="statusTypes[row.status]" size="small">
              {{ row.status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button text type="primary" size="small" @click="openDialog(row)">查看</el-button>
              <template v-if="row.status === 0">
                <span class="action-sep">|</span>
                <el-button text type="success" size="small" @click="reviewSalary(row)">审核</el-button>
                <span class="action-sep">|</span>
                <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? `薪资单 ${form.salary_no}` : '新增薪资单'"
      width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="员工" prop="employee">
              <el-select v-model="form.employee" filterable style="width:100%" :disabled="!!form.id">
                <el-option v-for="e in employees" :key="e.id"
                  :label="`${e.employee_no} ${e.real_name}`" :value="e.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="薪资期间" prop="period">
              <el-date-picker v-model="form.period" type="month" value-format="YYYY-MM"
                style="width:100%" :disabled="!!form.id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="基本工资">
              <el-input-number v-model="form.base_salary" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="加班费">
              <el-input-number v-model="form.overtime_pay" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="奖金">
              <el-input-number v-model="form.bonus" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="扣款">
              <el-input-number v-model="form.deduction" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="社保(个人)">
              <el-input-number v-model="form.social_security" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="个人所得税">
              <el-input-number v-model="form.income_tax" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer v-if="!form.id">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="generateVisible" title="批量生成薪资单" width="400px" destroy-on-close>
      <el-form :model="genForm" label-width="90px" class="dialog-form">
        <el-form-item label="薪资期间">
          <el-date-picker v-model="genForm.period" type="month" value-format="YYYY-MM" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import http from '@/utils/http'

const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const list = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const generateVisible = ref(false)
const formRef = ref()
const form = ref({})
const employees = ref([])
const genForm = ref({ period: dayjs().format('YYYY-MM') })
const query = reactive({ period: '', status: '', page: 1, page_size: 20 })
const statusTypes = { 0: 'info', 1: 'warning', 2: 'success' }
const rules = {
  employee: [{ required: true, message: '请选择员工' }],
  period: [{ required: true, message: '请选择薪资期间' }],
}

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/hr/salaries/', { params })
    list.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { period: '', status: '', page: 1 })
  loadData()
}

function openDialog(row = {}) {
  form.value = { base_salary: 0, overtime_pay: 0, bonus: 0, deduction: 0, social_security: 0, income_tax: 0, ...row }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    await http.post('/hr/salaries/', form.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function reviewSalary(row) {
  await http.post(`/hr/salaries/${row.id}/review/`)
  ElMessage.success('审核成功')
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除薪资单 "${row.salary_no}"？`, '提示', { type: 'warning' })
  await http.delete(`/hr/salaries/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

async function handleGenerate() {
  if (!genForm.value.period) return ElMessage.warning('请选择薪资期间')
  generating.value = true
  try {
    const res = await http.post('/hr/salaries/generate/', genForm.value)
    ElMessage.success(res.data.msg)
    generateVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    generating.value = false
  }
}

async function loadEmployees() {
  const res = await http.get('/hr/employees/', { params: { page_size: 999 } })
  employees.value = res.data.list
}

onMounted(() => { loadEmployees(); loadData() })
</script>
