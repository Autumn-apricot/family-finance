<template>
  <el-card v-loading="loading">
    <template #header>系统配置（LLM / 语音）</template>
    <el-form label-width="140px">
      <el-form-item v-for="(item, key) in config" :key="key" :label="key">
        <el-input
          v-model="form[key]"
          :type="item.is_secret ? 'password' : 'text'"
          :placeholder="item.description"
        />
      </el-form-item>
      <el-button type="primary" @click="save">保存</el-button>
    </el-form>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, putConfig } from '@/api'

const config = ref({})
const form = reactive({})
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getConfig()
    config.value = res.data || {}
    Object.keys(config.value).forEach((k) => {
      const v = config.value[k]
      form[k] = v.is_secret ? '' : v.value
    })
  } finally {
    loading.value = false
  }
})

async function save() {
  const payload = {}
  Object.keys(form).forEach((k) => {
    payload[k] = { value: form[k], is_secret: config.value[k]?.is_secret }
  })
  await putConfig(payload)
  ElMessage.success('已保存')
}
</script>
