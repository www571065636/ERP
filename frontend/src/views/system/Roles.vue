<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><el-icon><UserFilled /></el-icon></div>
        <div><div class="page-header-title">角色管理</div><div class="page-header-sub">配置系统角色与数据权限</div></div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增角色</el-button>
    </div>
    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">角色列表</span>
        <el-tag type="info" effect="plain">共 {{ list.length }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" style="width:100%">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column prop="role_name" label="角色名称" min-width="140">
          <template #default="{ row }">
            <span style="font-weight:500;color:#1a1a2e">{{ row.role_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="role_code" label="角色编码" width="160">
          <template #default="{ row }">
            <el-tag type="info" effect="plain" size="small">{{ row.role_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="data_scope" label="数据权限" width="140">
          <template #default="{ row }">{{ scopeLabels[row.data_scope] || "-" }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'" effect="light">{{ row.status ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
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
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑角色' : '新增角色'" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="dialog-form">
        <el-form-item label="角色名称" prop="role_name"><el-input v-model="form.role_name" placeholder="角色名称" /></el-form-item>
        <el-form-item label="角色编码" prop="role_code"><el-input v-model="form.role_code" placeholder="英文标识" /></el-form-item>
        <el-form-item label="数据权限">
          <el-select v-model="form.data_scope" style="width:100%">
            <el-option v-for="(label, val) in scopeLabels" :key="val" :label="label" :value="Number(val)" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
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
import { Plus } from '@element-plus/icons-vue'
import http from '@/utils/http'
const loading = ref(false), saving = ref(false)
const list = ref([]), dialogVisible = ref(false), formRef = ref(), form = ref({})
const scopeLabels = { 1: '全部数据', 2: '本部门', 3: '本部门及下级', 4: '仅本人', 5: '自定义' }
const rules = { role_name: [{ required: true, message: '请输入角色名称' }], role_code: [{ required: true, message: '请输入角色编码' }] }
async function loadData() {
  loading.value = true
  try { const res = await http.get('/system/roles/'); list.value = res.data.list || res.data }
  catch (e) { ElMessage.error(e.message) } finally { loading.value = false }
}
function openDialog(row = {}) { form.value = { data_scope: 1, ...row }; dialogVisible.value = true }
async function handleSave() {
  await formRef.value.validate(); saving.value = true
  try {
    form.value.id ? await http.put(`/system/roles/${form.value.id}/`, form.value) : await http.post('/system/roles/', form.value)
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error(e.message) } finally { saving.value = false }
}
async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除角色 "${row.role_name}"？`, '提示', { type: 'warning' })
  await http.delete(`/system/roles/${row.id}/`); ElMessage.success('删除成功'); loadData()
}
onMounted(loadData)
</script>