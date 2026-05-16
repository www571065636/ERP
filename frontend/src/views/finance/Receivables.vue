<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">
          <el-icon><CreditCard /></el-icon>
        </div>
        <div>
          <div class="page-header-title">应收账款</div>
          <div class="page-header-sub">跟踪客户应收款项与收款进度</div>
        </div>
      </div>
    </div>

    <div class="search-card">
      <el-form inline @submit.prevent="loadData">
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
        <span class="table-toolbar-title">应收账款列表</span>
        <el-tag effect="light" type="info">共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="receivable_no" label="应收单号" min-width="160">
          <template #default="{ row }">
            <el-tag effect="light" type="warning" size="small">{{ row.receivable_no }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_id" label="客户ID" width="80" align="center" />
        <el-table-column prop="amount" label="应收金额" width="110" align="right">
          <template #default="{ row }">
            <span style="font-weight:500">¥{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="received_amount" label="已收金额" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#52c41a">¥{{ row.received_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="balance" label="未收余额" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#f5222d;font-weight:500">¥{{ row.balance }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="到期日" width="100" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag effect="light" :type="statusTypes[row.status]" size="small">
              {{ statusLabels[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button text type="primary" size="small"
                :disabled="row.balance <= 0"
                @click="openPayment(row)">
                收款
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
          :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
      </div>
    </div>

    <el-dialog v-model="paymentVisible" title="收款登记" width="400px" destroy-on-close>
      <el-form ref="payFormRef" :model="payForm" label-width="90px" class="dialog-form">
        <el-form-item label="应收单号">
          <span style="color:#faad14;font-weight:500">{{ payForm.receivable_no }}</span>
        </el-form-item>
        <el-form-item label="未收余额">
          <span style="color:#f5222d;font-weight:600;font-size:16px">¥{{ payForm.balance }}</span>
        </el-form-item>
        <el-form-item label="收款金额" prop="amount">
          <el-input-number v-model="payForm.amount" :min="0.01" :max="payForm.balance"
            :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="收款日期">
          <el-date-picker v-model="payForm.pay_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="payForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paymentVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handlePayment">确认收款</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import http from '@/utils/http'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const paymentVisible = ref(false)
const payFormRef = ref()
const payForm = ref({})
const query = reactive({ status: '', page: 1, page_size: 20 })
const statusLabels = { 0: '未收', 1: '部分收', 2: '全部收', 9: '已核销' }
const statusTypes = { 0: 'danger', 1: 'warning', 2: 'success', 9: 'info' }

async function loadData() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== ''))
    const res = await http.get('/finance/receivables/', { params })
    list.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { status: '', page: 1 })
  loadData()
}

function openPayment(row) {
  payForm.value = { ...row, amount: row.balance, pay_date: dayjs().format('YYYY-MM-DD') }
  paymentVisible.value = true
}

async function handlePayment() {
  saving.value = true
  try {
    await http.post(`/finance/receivables/${payForm.value.id}/payments/`, payForm.value)
    ElMessage.success('收款登记成功')
    paymentVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>
