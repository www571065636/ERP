<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><List /></el-icon>
        </div>
        <div>
          <div class="page-header-title">会计科目</div>
          <div class="page-header-sub">管理财务会计科目层级结构</div>
        </div>
      </div>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增科目
      </el-button>
    </div>

    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">科目列表</span>
        <el-tag effect="light" type="info">树形结构</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" row-key="id" default-expand-all
        :tree-props="{ children: 'children' }">
        <el-table-column prop="account_code" label="科目编码" width="150">
          <template #default="{ row }">
            <el-tag effect="light" type="warning" size="small">{{ row.account_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="account_name" label="科目名称" min-width="180" />
        <el-table-column prop="account_type_label" label="科目类型" width="100">
          <template #default="{ row }">
            <el-tag effect="light" :type="typeColors[row.account_type]" size="small">
              {{ row.account_type_label || typeLabels[row.account_type] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="balance_dir" label="余额方向" width="100" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="row.balance_dir === 1 ? 'primary' : 'success'" size="small">
              {{ row.balance_dir === 1 ? '借' : '贷' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="层级" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="row.status ? 'success' : 'danger'" size="small">
              {{ row.status ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <span class="action-sep">|</span>
              <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
                <el-button text type="primary" size="small">
                  更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="addChild">添加子科目</el-dropdown-item>
                    <el-dropdown-item command="delete" style="color:var(--el-color-danger)">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑科目' : '新增科目'"
      width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
        <el-form-item label="科目编码" prop="account_code">
          <el-input v-model="form.account_code" />
        </el-form-item>
        <el-form-item label="科目名称" prop="account_name">
          <el-input v-model="form.account_name" />
        </el-form-item>
        <el-form-item label="科目类型" prop="account_type">
          <el-select v-model="form.account_type" style="width:100%">
            <el-option v-for="(label, val) in typeLabels" :key="val" :label="label" :value="Number(val)" />
          </el-select>
        </el-form-item>
        <el-form-item label="余额方向">
          <el-radio-group v-model="form.balance_dir">
            <el-radio :value="1">借</el-radio>
            <el-radio :value="2">贷</el-radio>
          </el-radio-group>
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
import { ArrowDown } from '@element-plus/icons-vue'
import http from '@/utils/http'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const formRef = ref()
const form = ref({})
const typeLabels = { 1: '资产', 2: '负债', 3: '权益', 4: '收入', 5: '费用' }
const typeColors = { 1: 'primary', 2: 'danger', 3: 'success', 4: 'warning', 5: 'info' }
const rules = {
  account_code: [{ required: true, message: '请输入科目编码' }],
  account_name: [{ required: true, message: '请输入科目名称' }],
  account_type: [{ required: true, message: '请选择科目类型' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/finance/accounts/tree/')
    list.value = res.data
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openDialog(row = {}, parentId = 0) {
  form.value = { balance_dir: 1, account_type: 1, parent_id: parentId, ...row }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await http.put(`/finance/accounts/${form.value.id}/`, form.value)
    } else {
      await http.post('/finance/accounts/', form.value)
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

function handleCommand(cmd, row) {
  if (cmd === 'addChild') openDialog({}, row.id)
  else if (cmd === 'delete') handleDelete(row)
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除科目 "${row.account_name}"？`, '提示', { type: 'warning' })
  await http.delete(`/finance/accounts/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
