<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><el-icon><User /></el-icon></div>
        <div>
          <div class="page-header-title">用户管理</div>
          <div class="page-header-sub">管理系统登录账号与权限</div>
        </div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增用户</el-button>
    </div>
    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="账号/姓名">
          <el-input v-model="query.search" placeholder="账号或姓名" clearable style="width:200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:100px">
            <el-option label="启用" :value="1" /><el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div class="table-card">
      <div class="table-toolbar">
        <span class="table-toolbar-title">用户列表</span>
        <el-tag type="info" effect="plain">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" style="width:100%">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column label="用户" min-width="160">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:10px">
              <el-avatar :size="32" class="user-avatar-badge">
                {{ (row.real_name||row.username||'?').charAt(0) }}
              </el-avatar>
              <div>
                <div style="font-weight:500;color:#1a1a2e">{{ row.real_name }}</div>
                <div style="font-size:12px;color:#999">{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'" effect="light">{{ row.status ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="160">
          <template #default="{ row }">
            <span style="color:#666;font-size:13px">{{ row.last_login_at ? row.last_login_at.slice(0,16).replace('T',' ') : '从未登录' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <span class="action-sep">|</span>
              <el-button text :type="row.status ? 'warning' : 'success'" size="small" @click="toggleStatus(row)">{{ row.status ? '禁用' : '启用' }}</el-button>
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
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用户' : '新增用户'" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" class="dialog-form">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" placeholder="登录账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!form.id">
          <el-input v-model="form.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="电子邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="mobile">
          <el-input v-model="form.mobile" placeholder="手机号码" />
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
import { Plus, Search } from '@element-plus/icons-vue'
import http from '@/utils/http'
const loading = ref(false), saving = ref(false)
const list = ref([]), total = ref(0)
const dialogVisible = ref(false), formRef = ref()
const query = reactive({ search: '', status: '', page: 1, page_size: 20 })
const form = ref({})
const rules = {
  username: [{ required: true, message: '请输入账号' }],
  password: [{ required: true, message: '请输入密码' }],
  real_name: [{ required: true, message: '请输入姓名' }],
  email: [{ pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '请输入有效的邮箱地址', trigger: 'blur' }],
  mobile: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号（11位数字）', trigger: 'blur' }],
}
async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/system/users/', { params })
    list.value = res.data.list; total.value = res.data.total
  } catch (e) { ElMessage.error(e.message) } finally { loading.value = false }
}
function resetQuery() { Object.assign(query, { search: '', status: '', page: 1 }); loadData() }
function openDialog(row = {}) { form.value = { ...row }; dialogVisible.value = true }
async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    form.value.id ? await http.put(`/system/users/${form.value.id}/`, form.value)
                  : await http.post('/system/users/', form.value)
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error(e.message) } finally { saving.value = false }
}
async function toggleStatus(row) {
  await http.put(`/system/users/${row.id}/status/`, { status: row.status ? 0 : 1 })
  ElMessage.success('操作成功'); loadData()
}
async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除用户 "${row.real_name}"？`, '提示', { type: 'warning' })
  await http.delete(`/system/users/${row.id}/`)
  ElMessage.success('删除成功'); loadData()
}
onMounted(loadData)
</script>
