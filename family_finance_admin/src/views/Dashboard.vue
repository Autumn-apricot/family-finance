<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col :span="6" v-for="item in cards" :key="item.label">
        <el-card><div class="num">{{ item.value }}</div><div class="label">{{ item.label }}</div></el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="16">
        <el-card>
          <template #header>近 6 月支出趋势</template>
          <div ref="trendRef" class="chart" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>当月分类占比</template>
          <div ref="pieRef" class="chart" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card>
          <template #header>成员消费排行</template>
          <div ref="barRef" class="chart chart-tall" />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header>语音记账统计</template>
      <p>总解析次数：{{ voice.total_parses }}</p>
      <p>确认入账率：{{ voice.confirm_rate }}%</p>
      <p>本月语音占比：{{ dash.voice_ratio_percent ?? 0 }}%</p>
    </el-card>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { getDashboard, getStatsMonthly, getVoiceStats } from '@/api'

const loading = ref(true)
const dash = ref({})
const voice = ref({})
const cards = ref([])
const trendRef = ref(null)
const pieRef = ref(null)
const barRef = ref(null)
let trendChart
let pieChart
let barChart

function lastMonths(n = 6) {
  const arr = []
  const d = new Date()
  for (let i = n - 1; i >= 0; i--) {
    const x = new Date(d.getFullYear(), d.getMonth() - i, 1)
    arr.push(`${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}`)
  }
  return arr
}

function renderTrend(months, amounts) {
  if (!trendRef.value) return
  trendChart = trendChart || echarts.init(trendRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, data: amounts, areaStyle: { opacity: 0.15 } }],
  })
}

function renderPie(items) {
  if (!pieRef.value) return
  pieChart = pieChart || echarts.init(pieRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: (items || []).map((i) => ({ name: i.name, value: parseFloat(i.amount) })),
    }],
  })
}

function renderBar(items) {
  if (!barRef.value) return
  barChart = barChart || echarts.init(barRef.value)
  const sorted = [...(items || [])].sort(
    (a, b) => parseFloat(b.expense) - parseFloat(a.expense),
  )
  barChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: sorted.map((i) => i.nickname) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: sorted.map((i) => parseFloat(i.expense)) }],
  })
}

function onResize() {
  trendChart?.resize()
  pieChart?.resize()
  barChart?.resize()
}

onMounted(async () => {
  try {
    const monthNow = lastMonths(1)[0]
    const months = lastMonths(6)
    const monthlyRes = await Promise.all(months.map((m) => getStatsMonthly(m)))
    const trendAmounts = monthlyRes.map((r) => parseFloat(r.data?.total_expense || 0))

    const [d, v, cur] = await Promise.all([
      getDashboard(),
      getVoiceStats(),
      getStatsMonthly(monthNow),
    ])
    dash.value = d.data || {}
    voice.value = v.data || {}
    cards.value = [
      { label: '活跃用户', value: d.data.user_count },
      { label: '本月支出', value: `¥${d.data.month_expense}` },
      { label: '本月记账', value: d.data.month_expense_count },
      { label: '语音占比', value: `${d.data.voice_ratio_percent}%` },
    ]
    await nextTick()
    renderTrend(months, trendAmounts)
    renderPie(cur.data?.by_category || d.data.by_category)
    renderBar(cur.data?.by_member || d.data.by_member)
    window.addEventListener('resize', onResize)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  trendChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
})
</script>

<style scoped>
.num { font-size: 28px; font-weight: bold; color: #1677ff; }
.label { color: #999; margin-top: 8px; }
.chart { height: 280px; }
.chart-tall { height: 320px; }
</style>
