<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon" style="background:linear-gradient(135deg,#52c41a,#237804)">
          <el-icon><Menu /></el-icon>
        </div>
        <div>
          <div class="page-header-title">产品分类</div>
          <div class="page-header-sub">管理产品的层级分类结构</div>
        </div>
      </div>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增分类
      </el-button>
    </div>

    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">分类列表</span>
        <el-tag effect="light" type="info">树形结构</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" row-key="id" default-expand-all
        :tree-props="{ children: 'children' }">
        <el-table-column prop="cat_name" label="分类名称" min-width="200" />
        <el-table-column prop="cat_code" label="分类编码" width="150">
          <template #default="{ row }">
            <el-tag effect="light" type="info" size="small">{{ row.cat_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="层级" width="80" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="['', 'primary', 'success', 'warning'][row.level] || 'info'" size="small">
              L{{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <el-divider direction="vertical" />
              <el-button text type="primary" size="small" @click="openDialog({}, row.id)">添加子级</el-button>
              <el-divider direction="vertical" />
              <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑分类' : '新增分类'"
      width="440px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" class="dialog-form">
        <el-form-item label="分类名称" prop="cat_name">
          <el-input v-model="form.cat_name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="分类编码" prop="cat_code">
          <el-input v-model="form.cat_code" placeholder="请输入分类编码" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" style="width:100%" />
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
const rules = {
  cat_name: [{ required: true, message: '请输入分类名称' }],
  cat_code: [{ required: true, message: '请输入分类编码' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/products/categories/tree/')
    list.value = res.data
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openDialog(row = {}, parentId = 0) {
  form.value = { sort_order: 0, parent_id: parentId, ...row }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await http.put(`/products/categories/${form.value.id}/`, form.value)
    } else {
      await http.post('/products/categories/', form.value)
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
  await ElMessageBox.confirm(`确认删除分类 "${row.cat_name}"？`, '提示', { type: 'warning' })
  await http.delete(`/products/categories/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
