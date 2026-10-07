<template>
  <el-card>
    <el-table :data="list" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="nickname" label="昵称" />
      <el-table-column prop="role" label="角色" />
      <el-table-column label="状态">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button
            v-if="row.is_active"
            link
            type="danger"
            @click="disable(row)"
          >禁用</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, patchUser } from '@/api'

const list = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const res = await getUsers()
    list.value = res.data.results || res.data || []
  } finally {
    loading.value = false
  }
}

async function disable(row) {
  await ElMessageBox.confirm(`禁用用户 ${row.username}？`)
  await patchUser(row.id, { is_active: false })
  ElMessage.success('已禁用')
  load()
}

onMounted(load)
</script>
