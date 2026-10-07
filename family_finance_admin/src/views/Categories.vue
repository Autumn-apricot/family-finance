<template>
  <el-card>
    <template #header>
      <div class="header-row">
        <span>分类与标签</span>
        <el-button type="primary" @click="openCreate">新增分类</el-button>
      </div>
    </template>
    <el-table :data="list" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="图标" width="80">
        <template #default="{ row }">{{ row.icon }}</template>
      </el-table-column>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="系统" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.is_system" type="info">是</el-tag>
          <span v-else>否</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="!row.is_system" link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑分类' : '新增分类'" width="420px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="emoji" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type">
            <el-option label="支出" value="expense" />
            <el-option label="收入" value="income" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCategory, deleteCategory, getCategories, updateCategory } from '@/api'

const list = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ name: '', icon: '💰', type: 'expense', sort_order: 0 })

async function load() {
  loading.value = true
  try {
    const res = await getCategories()
    list.value = res.data || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, { name: '', icon: '💰', type: 'expense', sort_order: 0 })
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, {
    name: row.name,
    icon: row.icon,
    type: row.type,
    sort_order: row.sort_order,
  })
  dialogVisible.value = true
}

async function save() {
  const payload = { ...form }
  if (editing.value) {
    await updateCategory(editing.value.id, payload)
    ElMessage.success('已更新')
  } else {
    await createCategory(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`删除分类「${row.name}」？`)
  await deleteCategory(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.header-row { display: flex; justify-content: space-between; align-items: center; }
</style>
