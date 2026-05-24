<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><Tickets /></el-icon>
        </div>
        <div>
          <div class="page-header-title">财务凭证</div>
          <div class="page-header-sub">管理记账凭证的录入、审核与过账</div>
        </div>
      </div>
      <el-button v-if="auth.hasPermission('finance:voucher:create')" type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新增凭证
      </el-button>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
        <el-form-item label="期间">
          <el-date-picker v-model="query.period" type="month" value-format="YYYY-MM"
            placeholder="选择期间" clearable style="width:140px" />
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
        <span class="table-toolbar-title">凭证列表</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="voucher_no" label="凭证号" width="160">
          <template #default="{ row }">
            <el-tag effect="light" type="warning" size="small">{{ row.voucher_no }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="voucher_date" label="凭证日期" width="100" />
        <el-table-column prop="period" label="期间" width="80" />
        <el-table-column prop="total_debit" label="借方合计" width="120" align="right">
          <template #default="{ row }">
            <span style="color:#faad14;font-weight:500">¥{{ row.total_debit }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="摘要" min-width="140" />
        <el-table-column prop="status" label="状态" width="80" align="center">
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
              <template v-if="row.status === 0 && auth.hasPermission('finance:voucher:review')">
                <span class="action-sep">|</span>
                <el-button text type="success" size="small" @click="reviewVoucher(row)">审核</el-button>
              </template>
              <template v-if="row.status === 0 && auth.hasPermission('finance:voucher:delete')">
                <span class="action-sep">|</span>
                <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </template>
              <template v-if="row.status === 1 && auth.hasPermission('finance:voucher:post')">
                <span class="action-sep">|</span>
                <el-button text type="primary" size="small" @click="postVoucher(row)">过账</el-button>
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

    <el-dialog v-model="dialogVisible" :title="viewMode ? `凭证 ${form.voucher_no}` : '新增凭证'"
      width="800px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px"
        class="dialog-form" :disabled="viewMode">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="凭证日期" prop="voucher_date">
              <el-date-picker v-model="form.voucher_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="凭证类型">
              <el-select v-model="form.voucher_type" style="width:100%">
                <el-option label="记账凭证" value="GENERAL" />
                <el-option label="收款凭证" value="RECEIVE" />
                <el-option label="付款凭证" value="PAY" />
                <el-option label="转账凭证" value="TRANSFER" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="摘要">
              <el-input v-model="form.remark" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="items-header">
          <span style="font-weight:600">凭证明细</span>
          <el-button v-if="!viewMode" size="small" @click="addItem">
            <el-icon><Plus /></el-icon>添加行
          </el-button>
        </div>
        <el-table :data="form.items" border size="small" style="margin-bottom:8px">
          <el-table-column label="科目" min-width="160">
            <template #default="{ row }">
              <el-select v-if="!viewMode" v-model="row.account" filterable size="small" style="width:100%">
                <el-option v-for="a in leafAccounts" :key="a.id"
                  :label="`${a.account_code} ${a.account_name}`" :value="a.id" />
              </el-select>
              <span v-else>{{ row.account_code }} {{ row.account_name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="摘要" min-width="120">
            <template #default="{ row }">
              <el-input v-if="!viewMode" v-model="row.summary" size="small" />
              <span v-else>{{ row.summary }}</span>
            </template>
          </el-table-column>
          <el-table-column label="借方金额" width="130">
            <template #default="{ row }">
              <el-input-number v-if="!viewMode" v-model="row.debit_amount" :min="0"
                :precision="2" size="small" style="width:100%" />
              <span v-else>{{ row.debit_amount > 0 ? row.debit_amount : '' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="贷方金额" width="130">
            <template #default="{ row }">
              <el-input-number v-if="!viewMode" v-model="row.credit_amount" :min="0"
                :precision="2" size="small" style="width:100%" />
              <span v-else>{{ row.credit_amount > 0 ? row.credit_amount : '' }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="!viewMode" label="删除" width="60">
            <template #default="{ $index }">
              <el-button text type="danger" size="small" @click="form.items.splice($index, 1)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="text-align:right;padding:8px 0;font-weight:600">
          借方合计：<span style="color:#faad14">¥{{ totalDebit }}</span>
          &nbsp;&nbsp;
          贷方合计：<span style="color:#52c41a">¥{{ totalCredit }}</span>
          <el-tag v-if="!balanced" type="danger" size="small" style="margin-left:8px">借贷不平</el-tag>
        </div>
      </el-form>
      <template #footer v-if="!viewMode">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
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
const accounts = ref([])
const query = reactive({ period: '', status: '', page: 1, page_size: 20 })
const statusLabels = { 0: '草稿', 1: '已审核', 2: '已过账', 9: '已作废' }
const statusTypes = { 0: 'info', 1: 'warning', 2: 'success', 9: 'danger' }
const rules = { voucher_date: [{ required: true, message: '请选择凭证日期' }] }

const leafAccounts = computed(() => accounts.value.filter(a => a.is_leaf))
const totalDebit = computed(() =>
  form.value.items.reduce((s, i) => s + (Number(i.debit_amount) || 0), 0).toFixed(2)
)
const totalCredit = computed(() =>
  form.value.items.reduce((s, i) => s + (Number(i.credit_amount) || 0), 0).toFixed(2)
)
const balanced = computed(() =>
  Math.abs(Number(totalDebit.value) - Number(totalCredit.value)) < 0.001
)

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/finance/vouchers/', { params })
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

async function loadAccounts() {
  const res = await http.get('/finance/accounts/', { params: { page_size: 999 } })
  accounts.value = res.data.list || res.data
}

function openDialog() {
  viewMode.value = false
  form.value = { voucher_date: dayjs().format('YYYY-MM-DD'), voucher_type: 'GENERAL', items: [] }
  dialogVisible.value = true
  loadAccounts()
}

function viewDetail(row) {
  viewMode.value = true
  form.value = { ...row, items: row.items || [] }
  dialogVisible.value = true
  if (!row.items?.length) {
    http.get(`/finance/vouchers/${row.id}/`).then(res => { form.value = res })
  }
}

function addItem() {
  form.value.items.push({ account: null, summary: '', debit_amount: 0, credit_amount: 0 })
}

async function handleSave() {
  await formRef.value.validate()
  if (!form.value.items.length) return ElMessage.warning('请添加凭证明细')
  if (!balanced.value) return ElMessage.warning('借贷方合计必须相等')
  saving.value = true
  try {
    await http.post('/finance/vouchers/', form.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function reviewVoucher(row) {
  await http.post(`/finance/vouchers/${row.id}/review/`)
  ElMessage.success('审核成功')
  loadData()
}

async function postVoucher(row) {
  await ElMessageBox.confirm('确认过账？过账后不可修改。', '过账', { type: 'warning' })
  await http.post(`/finance/vouchers/${row.id}/post_voucher/`)
  ElMessage.success('过账成功')
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除凭证 "${row.voucher_no}"？`, '提示', { type: 'warning' })
  await http.delete(`/finance/vouchers/${row.id}/`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0 8px;
}
</style>
