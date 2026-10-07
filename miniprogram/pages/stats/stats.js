const api = require('../../utils/api')

const COLORS = [
  '#ff4d4f', '#fa8c16', '#fadb14', '#a0d911', '#52c41a',
  '#13c2c2', '#1677ff', '#722ed1', '#eb2f96', '#fa541c',
  '#2f54eb', '#9254de', '#36cfc9', '#d4380d', '#d4b106',
]

const INCOME_COLORS = [
  '#52c41a', '#1677ff', '#722ed1', '#13c2c2', '#fa8c16',
  '#eb2f96', '#2f54eb', '#a0d911', '#36cfc9', '#9254de',
  '#07c160', '#1890ff', '#f5222d', '#faad14', '#597ef7',
]

function mondayOf(date) {
  const d = new Date(date)
  const day = d.getDay() || 7
  d.setDate(d.getDate() - day + 1)
  return d.toISOString().slice(0, 10)
}

/** 将 by_category 转为图表数据，子分类合并到父分类 */
function toChartData(byCategory, categories) {
  if (!categories || !categories.length) {
    return (byCategory || []).map((item, i) => ({
      label: item.name, value: parseFloat(item.amount) || 0,
      color: COLORS[i % COLORS.length], percent: item.percent,
    }))
  }
  const childToParent = {}
  const parentNames = new Set()
  categories.forEach(p => {
    parentNames.add(p.name)
    if (p.children) p.children.forEach(c => { childToParent[c.id] = p.name })
  })
  const merged = {}
  byCategory.forEach(item => {
    const pName = childToParent[item.category_id]
    if (pName) {
      if (!merged[pName]) merged[pName] = { name: pName, value: 0 }
      merged[pName].value += parseFloat(item.amount) || 0
    } else if (parentNames.has(item.name)) {
      if (!merged[item.name]) merged[item.name] = { name: item.name, value: 0 }
      merged[item.name].value += parseFloat(item.amount) || 0
    } else {
      merged[item.name] = { name: item.name, value: parseFloat(item.amount) || 0 }
    }
  })
  const total = Object.values(merged).reduce((s, m) => s + m.value, 0) || 1
  return Object.values(merged).map((m, i) => ({
    label: m.name, value: m.value,
    color: COLORS[i % COLORS.length],
    percent: (m.value / total * 100).toFixed(1),
  }))
}

/** 收入数据用绿色/蓝色系，子分类合并到父分类 */
function toIncomeChartData(byCategory, categories) {
  if (!categories || !categories.length) {
    return (byCategory || []).map((item, i) => ({
      label: item.name, value: parseFloat(item.amount) || 0,
      color: INCOME_COLORS[i % INCOME_COLORS.length], percent: item.percent,
    }))
  }
  // 建立子分类→父分类映射
  const childToParent = {}
  const parentNames = new Set()
  categories.forEach(p => {
    parentNames.add(p.name)
    if (p.children) p.children.forEach(c => { childToParent[c.id] = p.name })
  })
  // 合并：子分类金额加到父分类，父分类自身有数据也保留
  const merged = {}
  const parentHasOwn = new Set()
  byCategory.forEach(item => {
    const pName = childToParent[item.category_id]
    if (pName) {
      // 这是子分类，合并到父分类
      if (!merged[pName]) merged[pName] = { name: pName, value: 0 }
      merged[pName].value += parseFloat(item.amount) || 0
    } else if (parentNames.has(item.name)) {
      // 这是父分类自身的数据（没有子分类，或有人直接选了父分类记账）
      parentHasOwn.add(item.name)
      if (!merged[item.name]) merged[item.name] = { name: item.name, value: 0 }
      merged[item.name].value += parseFloat(item.amount) || 0
    } else {
      // 既不是父也不是子，直接显示
      merged[item.name] = { name: item.name, value: parseFloat(item.amount) || 0 }
    }
  })
  const total = Object.values(merged).reduce((s, m) => s + m.value, 0) || 1
  return Object.values(merged).map((m, i) => ({
    label: m.name, value: m.value,
    color: INCOME_COLORS[i % INCOME_COLORS.length],
    percent: (m.value / total * 100).toFixed(1),
  }))
}

/** 将 daily_trend 转为柱状图数据 */
function toTrendData(trend) {
  return (trend || []).map((item, i) => ({
    label: item.date.slice(5),
    value: parseFloat(item.expense) || 0,
    color: '#1677ff',
  }))
}

Page({
  data: {
    tab: 'month',
    month: '',
    date: '',
    weekStart: '',
    year: '',
    monthly: {},
    daily: {},
    weekly: {},
    annual: {},
    // 图表数据
    monthRingData: [],
    monthIncomeData: [],
    monthTrendData: [],
    weekTrendData: [],
  },

  onShow() {
    if (!getApp().globalData.token) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    const now = new Date()
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    const date = now.toISOString().slice(0, 10)
    const year = String(now.getFullYear())
    this.setData({ month, date, weekStart: mondayOf(now), year })
    this.loadTab(this.data.tab)  // 每次显示都刷新当前tab
  },

  getUserId() {
    const fv = getApp().globalData.familyView
    if (!fv && getApp().globalData.userInfo) return getApp().globalData.userInfo.id
    return null
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ tab })
    this.loadTab(tab)
  },

  async loadTab(tab) {
    try {
      const uid = this.getUserId()
      if (tab === 'day') {
        const res = await api.statsDaily(this.data.date, uid)
        this.setData({ daily: res.data || {} })
      } else if (tab === 'week') {
        const res = await api.statsWeekly(this.data.weekStart, uid)
        const data = res.data || {}
        this.setData({
          weekly: data,
          weekTrendData: toTrendData(data.daily_trend),
        })
      } else if (tab === 'month') {
        const [statsRes, budgetRes, incCatRes, expCatRes] = await Promise.all([
          api.statsMonthly(this.data.month, uid),
          api.budgets(this.data.month),
          api.categories('income'),
          api.categories('expense'),
        ])
        const incCats = incCatRes.data || []
        const expCats = expCatRes.data || []
        const data = statsRes.data || {}
        const budgets = budgetRes.data || []
        // 合并预算到分类
        const budgetMap = {}
        budgets.forEach(b => { budgetMap[b.category] = b.amount })
        const byCategoryWithBudget = (data.by_category || []).map(c => ({
          ...c,
          budget: budgetMap[c.category_id] || '0',
          overBudget: parseFloat(budgetMap[c.category_id] || 0) > 0 && parseFloat(c.amount) > parseFloat(budgetMap[c.category_id]),
        }))
        this.setData({
          monthly: { ...data, by_category: byCategoryWithBudget },
          monthRingData: toChartData(data.by_category, expCats),
          monthIncomeData: toIncomeChartData(data.by_income_category, incCats),
          monthTrendData: toTrendData(data.daily_trend),
        })
      } else if (tab === 'year') {
        const res = await api.statsAnnual(this.data.year, this.getUserId())
        const data = res.data || {}
        const maxExp = Math.max(...(data.monthly_trend || []).map(m => parseFloat(m.expense) || 0), 1)
        const maxInc = Math.max(...(data.monthly_trend || []).map(m => parseFloat(m.income) || 0), 1)
        const trend = (data.monthly_trend || []).map(m => ({
          ...m,
          barOut: ((parseFloat(m.expense) || 0) / maxExp * 100).toFixed(0),
          barIn: ((parseFloat(m.income) || 0) / maxInc * 100).toFixed(0),
        }))
        this.setData({ annual: { ...data, monthly_trend: trend } })
      }
    } catch (e) {
      console.error(e)
    }
  },

  onMonth(e) {
    this.setData({ month: e.detail.value.slice(0, 7) })
    this.loadTab('month')
  },
  onDate(e) {
    this.setData({ date: e.detail.value })
    this.loadTab('day')
  },
  onWeek(e) {
    this.setData({ weekStart: mondayOf(new Date(e.detail.value)) })
    this.loadTab('week')
  },
  onYear(e) {
    this.setData({ year: e.detail.value.slice(0, 4) })
    this.loadTab('year')
  },

  onPullDownRefresh() {
    this.loadTab(this.data.tab).finally(() => wx.stopPullDownRefresh())
  },

  goToMonth(e) {
    const month = e.currentTarget.dataset.month
    this.setData({ tab: 'month', month })
    this.loadTab('month')
  },

  async generateShareCard() {
    const { month, monthRingData, monthIncomeData, monthly } = this.data
    wx.showLoading({ title: '生成中' })
    try {
      const query = this.createSelectorQuery()
      query.select('#shareCanvas').fields({ node: true, size: true }).exec(async (res) => {
        if (!res || !res[0] || !res[0].node) { wx.hideLoading(); return }
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getSystemInfoSync().pixelRatio
        const W = 750, H = 1200
        canvas.width = W * dpr; canvas.height = H * dpr
        ctx.scale(dpr, dpr)

        // 背景
        const grad = ctx.createLinearGradient(0, 0, 0, H)
        grad.addColorStop(0, '#1677ff'); grad.addColorStop(0.3, '#722ed1'); grad.addColorStop(1, '#1a1a2e')
        ctx.fillStyle = grad; ctx.fillRect(0, 0, W, H)

        // 头部
        const fv = getApp().globalData.familyView
        const title = fv ? `${month} 家庭月报` : `${month} 个人月报`
        ctx.fillStyle = '#fff'; ctx.font = 'bold 52rpx sans-serif'; ctx.textAlign = 'center'
        ctx.fillText(title, W / 2, 100)
        ctx.font = '26rpx sans-serif'; ctx.fillStyle = 'rgba(255,255,255,.6)'
        ctx.fillText('家庭资产管理 · 智能记账', W / 2, 140)

        // KPI
        const kpiY = 190
        ctx.fillStyle = 'rgba(255,255,255,.1)'
        ctx.beginPath(); this._roundRect(ctx, 40, kpiY, 670, 140, 20); ctx.fill()
        const exp = monthly.total_expense || '0'; const inc = monthly.total_income || '0'; const bal = monthly.balance || '0'
        ctx.textAlign = 'center'
        ctx.font = 'bold 48rpx sans-serif'; ctx.fillStyle = '#ffd591'
        ctx.fillText(`-¥${exp}`, 170, kpiY + 55)
        ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.font = '22rpx sans-serif'
        ctx.fillText('支出', 170, kpiY + 90)
        ctx.font = 'bold 48rpx sans-serif'; ctx.fillStyle = '#b7eb8f'
        ctx.fillText(`+¥${inc}`, 375, kpiY + 55)
        ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.font = '22rpx sans-serif'
        ctx.fillText('收入', 375, kpiY + 90)
        ctx.font = 'bold 48rpx sans-serif'; ctx.fillStyle = '#91d5ff'
        ctx.fillText(`¥${bal}`, 580, kpiY + 55)
        ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.font = '22rpx sans-serif'
        ctx.fillText('结余', 580, kpiY + 90)

        // 支出分类
        let y = 370
        if (monthRingData.length) {
          ctx.fillStyle = '#fff'; ctx.font = 'bold 32rpx sans-serif'; ctx.textAlign = 'left'
          ctx.fillText('📂 支出分类', 50, y); y += 50
          const barW = 600, barH = 24
          for (let i = 0; i < Math.min(monthRingData.length, 8); i++) {
            const d = monthRingData[i]
            ctx.fillStyle = 'rgba(255,255,255,.6)'; ctx.font = '24rpx sans-serif'
            ctx.fillText(`${d.label}  ¥${d.value.toFixed(0)}`, 50, y)
            ctx.fillText(`${d.percent}%`, 670, y)
            ctx.fillStyle = 'rgba(255,255,255,.15)'
            ctx.beginPath(); this._roundRect(ctx, 50, y + 6, barW, barH, 6); ctx.fill()
            ctx.fillStyle = d.color
            ctx.beginPath(); this._roundRect(ctx, 50, y + 6, barW * (d.percent / 100), barH, 6); ctx.fill()
            y += 44
          }
        }

        // 收入来源
        if (monthIncomeData.length) {
          y += 20
          ctx.fillStyle = '#fff'; ctx.font = 'bold 32rpx sans-serif'
          ctx.fillText('💰 收入来源', 50, y); y += 50
          for (let i = 0; i < Math.min(monthIncomeData.length, 4); i++) {
            const d = monthIncomeData[i]
            ctx.fillStyle = 'rgba(255,255,255,.6)'; ctx.font = '24rpx sans-serif'
            ctx.fillText(`${d.label}  ¥${d.value.toFixed(0)}`, 50, y)
            ctx.fillText(`${d.percent}%`, 400, y)
            ctx.fillStyle = d.color; ctx.font = 'bold 28rpx sans-serif'
            ctx.fillText(`+¥${d.value.toFixed(0)}`, 550, y)
            y += 40
          }
        }

        // 成员（过滤掉没有收支的）
        const activeMembers = (monthly.by_member || []).filter(m => parseFloat(m.expense) > 0 || parseFloat(m.income) > 0)
        if (activeMembers.length) {
          y += 24
          ctx.fillStyle = '#fff'; ctx.font = 'bold 32rpx sans-serif'
          ctx.fillText('👥 成员贡献', 50, y); y += 50
          for (const m of activeMembers) {
            ctx.fillStyle = 'rgba(255,255,255,.7)'; ctx.font = '24rpx sans-serif'
            ctx.fillText(`${m.nickname}`, 50, y)
            ctx.fillStyle = '#ffd591'; ctx.fillText(`-¥${m.expense}`, 300, y)
            ctx.fillStyle = '#b7eb8f'; ctx.fillText(`+¥${m.income}`, 520, y)
            y += 36
          }
        }

        // 底部
        ctx.fillStyle = 'rgba(255,255,255,.25)'; ctx.font = '22rpx sans-serif'; ctx.textAlign = 'center'
        ctx.fillText('家庭资产 · 智能记账', W / 2, H - 30)

        // 导出
        wx.canvasToTempFilePath({
          canvas, success: (res) => {
            wx.hideLoading()
            wx.previewImage({ urls: [res.tempFilePath], current: res.tempFilePath })
          }, fail: () => { wx.hideLoading(); wx.showToast({ title: '生成失败', icon: 'none' }) }
        }, this)
      })
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '生成失败', icon: 'none' })
    }
  },

  _roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y)
    ctx.arcTo(x + w, y, x + w, y + r, r)
    ctx.lineTo(x + w, y + h - r); ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
    ctx.lineTo(x + r, y + h); ctx.arcTo(x, y + h, x, y + h - r, r)
    ctx.lineTo(x, y + r); ctx.arcTo(x, y, x + r, y, r)
    ctx.closePath()
  },
})
