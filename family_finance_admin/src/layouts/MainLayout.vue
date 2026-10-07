<template>
  <el-container class="layout">
    <el-aside width="200px">
      <div class="logo">家庭资产</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/dashboard">数据看板</el-menu-item>
        <el-menu-item index="/users">用户管理</el-menu-item>
        <el-menu-item index="/expenses">账单管理</el-menu-item>
        <el-sub-menu index="/settings-group">
          <template #title>设置中心</template>
          <el-menu-item index="/settings/categories">分类与标签</el-menu-item>
          <el-menu-item index="/settings">AI / 语音配置</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <span>{{ user?.nickname || user?.username }}</span>
        <el-button link type="danger" @click="onLogout">退出</el-button>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const router = useRouter()
const user = computed(() => store.user)

function onLogout() {
  store.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { min-height: 100vh; }
.logo { padding: 20px; font-weight: bold; color: #1677ff; }
.el-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }
</style>
