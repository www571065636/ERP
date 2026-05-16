<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><User /></el-icon>
        </div>
        <div>
          <div class="page-header-title">员工管理</div>
          <div class="page-header-sub">管理员工档案、职位与薪资信息</div>
        </div>
      </div>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增员工
      </el-button>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="关键词">
          <el-input v-model="query.search" placeholder="工号/姓名/手机号" clearable style="width:220px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.emp_status" placeholder="全部" clearable style="width:100px">
            <el-option label="在职" :value="1" />
            <el-option label="离职" :value="2" />
            <el-option label="试用" :value="3" />
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
        <span class="table-toolbar-title">员工列表</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="员工" width="160">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <el-avatar :size="32" style="background:#eb2f96;flex-shrink:0">
                {{ row.real_name?.charAt(0) }}
              </el-avatar>
              <div>
                <div style="font-weight:500;font-size:13px">{{ row.real_name }}</div>
                <div style="font-size:11px;color:#999">{{ row.employee_no }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="gender_label" label="性别" width="70" align="center" />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column prop="position" label="职位" min-width="120" />
        <el-table-column prop="entry_date" label="入职日期" width="110" />
        <el-table-column prop="emp_status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="statusTypes[row.emp_status]" size="small">
              {{ row.emp_status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <span class="action-sep">|</span>
              <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
          :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑员工' : '新增员工'"
      width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="dialog-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="工号" prop="employee_no">
              <el-input v-model="form.employee_no" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="real_name">
              <el-input v-model="form.real_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-radio-group v-model="form.gender">
                <el-radio :value="1">男</el-radio>
                <el-radio :value="2">女</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号" prop="mobile">
              <el-input v-model="form.mobile" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-input v-model="form.position" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="入职日期">
              <el-date-picker v-model="form.entry_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="基本工资">
              <el-input-number v-model="form.base_salary" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.emp_status" style="width:100%">
                <el-option label="在职" :value="1" />
                <el-option label="离职" :value="2" />
                <el-option label="试用" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开户银行">
              <el-input v-model="form.bank_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="银行账号">
              <el-input v-model="form.bank_account" />
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

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const formRef = ref()
const form = ref({})
const query = reactive({ search: '', emp_status: '', page: 1, page_size: 20 })
const statusTypes = { 1: 'success', 2: 'danger', 3: 'warning' }
const rules = {
  employee_no: [{ required: true, message: '请输入工号' }],
  real_name: [{ required: true, message: '请输入姓名' }],
  mobile: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号（11位数字）', trigger: 'blur' }],
  email: [{ pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '请输入有效的邮箱地址', trigger: 'blur' }],
}

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/hr/employees/', { params })
    list.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { search: '', emp_status: '', page: 1 })
  loadData()
}

function openDialog(row = {}) {
  form.value = { emp_status: 1, gender: 1, ...row }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await http.put(`/hr/employees/${form.value.id}/`, form.value)
    } else {
      await http.post('/hr/employees/', form.value)
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
  await ElMessageBox.confirm(`确认删除员工 "${row.real_name}"？`, '提示', { type: 'warning' })
  await http.delete(`/hr/employees/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
