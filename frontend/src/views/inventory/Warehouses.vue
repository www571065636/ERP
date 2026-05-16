<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Shop /></el-icon>
        </div>
        <div>
          <div class="page-header-title">仓库管理</div>
          <div class="page-header-sub">管理仓库基本信息与负责人</div>
        </div>
      </div>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增仓库
      </el-button>
    </div>

    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">仓库列表</span>
        <el-tag effect="light" type="info">共 {{ list.length }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="warehouse_code" label="仓库编码" width="140">
          <template #default="{ row }">
            <el-tag effect="light" type="info" size="small">{{ row.warehouse_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="warehouse_name" label="仓库名称" min-width="160" />
        <el-table-column prop="warehouse_type" label="类型" width="110">
          <template #default="{ row }">
            <el-tag effect="light" :type="typeColors[row.warehouse_type]" size="small">
              {{ typeLabels[row.warehouse_type] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="manager_name" label="负责人" width="100" />
        <el-table-column prop="address" label="地址" min-width="160" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="row.status ? 'success' : 'danger'" size="small">
              {{ row.status ? '启用' : '禁用' }}
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
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑仓库' : '新增仓库'"
      width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="dialog-form">
        <el-form-item label="仓库编码" prop="warehouse_code">
          <el-input v-model="form.warehouse_code" />
        </el-form-item>
        <el-form-item label="仓库名称" prop="warehouse_name">
          <el-input v-model="form.warehouse_name" />
        </el-form-item>
        <el-form-item label="仓库类型">
          <el-select v-model="form.warehouse_type" style="width:100%">
            <el-option v-for="(label, val) in typeLabels" :key="val" :label="label" :value="Number(val)" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="form.manager_name" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/utils/http'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const formRef = ref()
const form = ref({})
const typeLabels = { 1: '原材料仓', 2: '成品仓', 3: '半成品仓', 4: '退货仓' }
const typeColors = { 1: 'primary', 2: 'success', 3: 'warning', 4: 'danger' }
const rules = {
  warehouse_code: [{ required: true, message: '请输入仓库编码' }],
  warehouse_name: [{ required: true, message: '请输入仓库名称' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/inventory/warehouses/', { params: { page_size: 999 } })
    list.value = res.data.list
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openDialog(row = {}) {
  form.value = { warehouse_type: 1, ...row }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await http.put(`/inventory/warehouses/${form.value.id}/`, form.value)
    } else {
      await http.post('/inventory/warehouses/', form.value)
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
  await ElMessageBox.confirm(`确认删除仓库 "${row.warehouse_name}"？`, '提示', { type: 'warning' })
  await http.delete(`/inventory/warehouses/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
