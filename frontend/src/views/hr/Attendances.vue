<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Calendar /></el-icon>
        </div>
        <div>
          <div class="page-header-title">考勤管理</div>
          <div class="page-header-sub">记录员工每日签到签退与考勤状态</div>
        </div>
      </div>
      <el-button v-if="auth.hasPermission('hr:attendance:create')" type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>录入考勤
      </el-button>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="员工">
          <el-select v-model="query.employee" filterable clearable placeholder="选择员工" style="width:160px">
            <el-option v-for="e in employees" :key="e.id" :label="e.real_name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD"
            start-placeholder="开始" end-placeholder="结束" style="width:220px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">考勤记录</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
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
        <el-table-column prop="attend_date" label="考勤日期" width="100" />
        <el-table-column label="签到时间" min-width="160">
          <template #default="{ row }">
            {{ row.check_in_time ? row.check_in_time.slice(0, 16).replace('T', ' ') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="签退时间" min-width="160">
          <template #default="{ row }">
            {{ row.check_out_time ? row.check_out_time.slice(0, 16).replace('T', ' ') : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="attend_type_label" label="考勤类型" width="100">
          <template #default="{ row }">
            <el-tag effect="light" :type="typeColors[row.attend_type]" size="small">
              {{ row.attend_type_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overtime_hours" label="加班工时" width="100" align="center" />
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button v-if="auth.hasPermission('hr:attendance:update')" text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <span v-if="auth.hasPermission('hr:attendance:update') && auth.hasPermission('hr:attendance:delete')" class="action-sep">|</span>
              <el-button v-if="auth.hasPermission('hr:attendance:delete')" text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
          :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑考勤' : '录入考勤'"
      width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
        <el-form-item label="员工" prop="employee">
          <el-select v-model="form.employee" filterable style="width:100%">
            <el-option v-for="e in employees" :key="e.id"
              :label="`${e.employee_no} ${e.real_name}`" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="考勤日期" prop="attend_date">
          <el-date-picker v-model="form.attend_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="考勤类型">
          <el-select v-model="form.attend_type" style="width:100%">
            <el-option label="正常" :value="1" />
            <el-option label="迟到" :value="2" />
            <el-option label="早退" :value="3" />
            <el-option label="缺勤" :value="4" />
            <el-option label="请假" :value="5" />
            <el-option label="出差" :value="6" />
          </el-select>
        </el-form-item>
        <el-form-item label="签到时间">
          <el-date-picker v-model="form.check_in_time" type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="签退时间">
          <el-date-picker v-model="form.check_out_time" type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="加班工时">
          <el-input-number v-model="form.overtime_hours" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
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
import dayjs from 'dayjs'
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
const employees = ref([])
const dateRange = ref([])
const query = reactive({ employee: '', page: 1, page_size: 20 })
const typeColors = { 1: 'success', 2: 'warning', 3: 'warning', 4: 'danger', 5: 'info', 6: 'primary' }
const rules = {
  employee: [{ required: true, message: '请选择员工' }],
  attend_date: [{ required: true, message: '请选择考勤日期' }],
}

async function loadData() {
  loading.value = true
  try {
    const params = { ...query }
    if (dateRange.value?.length === 2) {
      params.date_start = dateRange.value[0]
      params.date_end = dateRange.value[1]
    }
    const filtered = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== ''))
    const res = await http.get('/hr/attendances/', { params: filtered })
    list.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { employee: '', page: 1 })
  dateRange.value = []
  loadData()
}

function openDialog(row = {}) {
  form.value = { attend_type: 1, overtime_hours: 0, attend_date: dayjs().format('YYYY-MM-DD'), ...row }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await http.put(`/hr/attendances/${form.value.id}/`, form.value)
    } else {
      await http.post('/hr/attendances/', form.value)
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
  await ElMessageBox.confirm('确认删除该考勤记录？', '提示', { type: 'warning' })
  await http.delete(`/hr/attendances/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

async function loadEmployees() {
  const res = await http.get('/hr/employees/', { params: { page_size: 999 } })
  employees.value = res.data.list
}

onMounted(() => { loadEmployees(); loadData() })
</script>
