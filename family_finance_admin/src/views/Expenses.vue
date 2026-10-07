<template>
  <el-card>
    <el-form inline>
      <el-form-item label="月份">
        <el-input v-model="month" placeholder="2026-05" style="width: 120px" />
      </el-form-item>
      <el-form-item label="来源">
        <el-select v-model="source" clearable placeholder="全部" style="width: 120px">
          <el-option label="手动" value="manual" />
          <el-option label="语音" value="voice" />
        </el-select>
      </el-form-item>
      <el-form-item label="用户ID">
        <el-input v-model="userId" placeholder="可选" style="width: 100px" />
      </el-form-item>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button @click="exportCsv">导出 CSV</el-button>
    </el-form>
    <el-table :data="list" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="user_nickname" label="用户" />
      <el-table-column label="分类">
        <template #default="{ row }">{{ row.category_icon }} {{ row.category_name }}</template>
      </el-table-column>
      <el-table-column prop="amount" label="金额" />
      <el-table-column prop="expense_date" label="日期" />
      <el-table-column prop="source" label="来源" />
      <el-table-column prop="description" label="备注" show-overflow-tooltip />
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteExpense, getExpenses } from '@/api'

const list = ref([])
const loading = ref(false)
const month = ref(new Date().toISOString().slice(0, 7))
const source = ref('')
const userId = ref('')

async function load() {
  loading.value = true
  try {
    const params = { month: month.value, page_size: 100 }
    if (source.value) params.source = source.value
    if (userId.value) params.user_id = userId.value
    const res = await getExpenses(params)
    list.value = res.data.results || []
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  const headers = ['ID', '用户', '分类', '金额', '日期', '来源', '备注']
  const rows = list.value.map((r) => [
    r.id,
    r.user_nickname,
    r.category_name,
    r.amount,
    r.expense_date,
    r.source,
    (r.description || '').replace(/"/g, '""'),
  ])
  const lines = [headers.join(',')]
  rows.forEach((row) => {
    lines.push(row.map((c) => `"${c}"`).join(','))
  })
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `expenses_${month.value}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出')
}

async function remove(row) {
  await ElMessageBox.confirm('确认删除该账单？')
  await deleteExpense(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
