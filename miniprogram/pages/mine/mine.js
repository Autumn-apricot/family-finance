const api = require('../../utils/api')

Page({
  data: {
    user: {},
    hideTotal: false,
    // 钱包
    wallets: [],
    walletTotal: 0,
    // 预算弹窗
    budgetVisible: false,
    budgetMonth: '',
    budgetItems: [],
    budgetSaving: false,
    // 周期账单
    recurringVisible: false,
    recurringList: [],
    recCats: [],
    recCatIdx: 0,
    recAmount: '',
    recDesc: '',
    recCycles: ['每月', '每周', '每年', '每天'],
    recCycleIdx: 0,
    recCycleVals: ['monthly', 'weekly', 'yearly', 'daily'],
    // 家庭
    family: { has_family: false },
    familyLoading: true,
    familyModalVisible: false,
    familyName: '',
    joinCode: '',
  },

  onShow() {
    if (!getApp().globalData.token) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.refreshMe()
    this.loadWallets()
    this.loadFamily()
  },

  async loadFamily() {
    this.setData({ familyLoading: true })
    try {
      const res = await api.family()
      this.setData({ family: res.data || { has_family: false }, familyLoading: false })
    } catch (e) { this.setData({ familyLoading: false }) }
  },

  openFamilyModal() { this.setData({ familyModalVisible: true, familyName: '', joinCode: '' }) },
  closeFamilyModal() { this.setData({ familyModalVisible: false }) },
  onFamilyName(e) { this.setData({ familyName: e.detail.value }) },
  onJoinCode(e) { this.setData({ joinCode: e.detail.value }) },

  async createFamily() {
    const name = this.data.familyName.trim()
    if (!name) return wx.showToast({ title: '请输入家庭名', icon: 'none' })
    try {
      await api.createFamily(name)
      wx.showToast({ title: '创建成功' })
      this.closeFamilyModal()
      this.loadFamily()
    } catch (e) { wx.showToast({ title: (e && e.message) || '失败', icon: 'none' }) }
  },

  async joinFamily() {
    const code = this.data.joinCode.trim()
    if (!code) return wx.showToast({ title: '请输入邀请码', icon: 'none' })
    try {
      await api.joinFamily(code)
      wx.showToast({ title: '加入成功' })
      this.closeFamilyModal()
      this.loadFamily()
    } catch (e) { wx.showToast({ title: (e && e.message) || '失败', icon: 'none' }) }
  },

  async leaveFamily() {
    const res = await wx.showModal({ title: '退出家庭？', content: '退出后将无法看到家人账单' })
    if (!res.confirm) return
    try {
      await api.leaveFamily()
      wx.showToast({ title: '已退出' })
      this.loadFamily()
    } catch (e) { wx.showToast({ title: '失败', icon: 'none' }) }
  },

  async refreshMe() {
    try {
      const res = await api.me()
      const user = res.data || {}
      getApp().setSession(getApp().globalData.token, user)
      this.setData({ user, hideTotal: !!user.hide_total_amount })
    } catch (e) {
      const user = getApp().globalData.userInfo || {}
      this.setData({ user, hideTotal: !!user.hide_total_amount })
    }
  },

  async loadWallets() {
    try {
      const res = await api.wallets()
      const data = res.data || {}
      const items = (data.items || []).map(w => ({
        ...w,
        balanceFmt: Number(w.balance).toFixed(2),
        isNeg: w.balance < 0,
      }))
      const total = Number(data.total || 0).toFixed(2)
      this.setData({ wallets: items, walletTotal: total })
    } catch (e) { /* ignore */ }
  },

  editWallet(e) {
    const method = e.currentTarget.dataset.method
    const wallet = this.data.wallets.find(w => w.method === method)
    const current = wallet ? String(wallet.balance) : ''
    wx.showModal({
      title: '修改余额',
      editable: true,
      placeholderText: '输入当前余额',
      content: current,
      success: async (res) => {
        if (res.confirm && res.content !== undefined) {
          const val = parseFloat(res.content)
          if (isNaN(val)) { wx.showToast({ title: '请输入数字', icon: 'none' }); return }
          try {
            await api.updateWallet(method, val)
            this.loadWallets()
          } catch (e) { wx.showToast({ title: '保存失败', icon: 'none' }) }
        }
      },
    })
  },

  async onHideTotal(e) {
    const hide = e.detail.value
    try {
      const res = await api.updateMe({ hide_total_amount: hide })
      const user = res.data || {}
      getApp().setSession(getApp().globalData.token, user)
      this.setData({ user, hideTotal: hide })
      wx.showToast({ title: hide ? '已隐藏金额' : '已显示金额', icon: 'none' })
    } catch (err) {
      wx.showToast({ title: (err && err.message) || '保存失败', icon: 'none' })
      this.setData({ hideTotal: !hide })
    }
  },

  // 预算
  async openBudget() {
    const now = new Date()
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    wx.showLoading({ title: '加载中' })
    try {
      const [catRes, budgetRes] = await Promise.all([api.categories('expense'), api.budgets(month)])
      const categories = catRes.data || []
      const budgets = budgetRes.data || []
      const budgetMap = {}
      budgets.forEach(b => { budgetMap[b.category] = { id: b.id, amount: b.amount } })
      const items = []
      categories.forEach(p => {
        if (p.children && p.children.length) {
          p.children.forEach(c => {
            const bid = budgetMap[c.id]
            items.push({ categoryId: c.id, name: p.name + '—' + c.name, icon: c.icon, budget: bid ? bid.amount : '', budgetId: bid ? bid.id : null })
          })
        } else {
          const bid = budgetMap[p.id]
          items.push({ categoryId: p.id, name: p.name, icon: p.icon, budget: bid ? bid.amount : '', budgetId: bid ? bid.id : null })
        }
      })
      this.setData({ budgetVisible: true, budgetMonth: month, budgetItems: items })
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally { wx.hideLoading() }
  },
  onBudgetInput(e) {
    const idx = e.currentTarget.dataset.idx
    const items = this.data.budgetItems
    items[idx].budget = e.detail.value
    this.setData({ budgetItems: items })
  },
  async saveBudgets() {
    this.setData({ budgetSaving: true })
    try {
      for (const item of this.data.budgetItems) {
        const amount = parseFloat(item.budget)
        if (amount > 0) {
          if (item.budgetId) await api.updateBudget(item.budgetId, { amount, month: this.data.budgetMonth, category: item.categoryId })
          else await api.createBudget({ amount, month: this.data.budgetMonth, category: item.categoryId })
        } else if (item.budgetId) await api.deleteBudget(item.budgetId)
      }
      wx.showToast({ title: '预算保存成功' })
      this.setData({ budgetVisible: false })
    } catch (e) { wx.showToast({ title: (e && e.message) || '保存失败', icon: 'none' }) }
    finally { this.setData({ budgetSaving: false }) }
  },
  closeBudget() { this.setData({ budgetVisible: false }) },

  async copyLastBudget() {
    const [y, m] = this.data.budgetMonth.split('-').map(Number)
    let lm = m - 1, ly = y
    if (lm === 0) { lm = 12; ly -= 1 }
    const lastMonth = `${ly}-${String(lm).padStart(2, '0')}`
    try {
      const res = await api.budgets(lastMonth)
      const items = this.data.budgetItems
      const lastMap = {}
      ;(res.data || []).forEach(b => { lastMap[b.category] = b.amount })
      let copied = 0
      items.forEach(item => {
        if (lastMap[item.categoryId] && !item.budget) {
          item.budget = String(lastMap[item.categoryId])
          copied++
        }
      })
      this.setData({ budgetItems: items })
      wx.showToast({ title: copied ? `已复制 ${copied} 项` : '上月无预算', icon: 'none' })
    } catch (e) { wx.showToast({ title: '加载失败', icon: 'none' }) }
  },

  // 周期账单
  async openRecurring() {
    wx.showLoading({ title: '加载中' })
    try {
      const [recRes, catRes] = await Promise.all([
        api.recurring(), api.categories('expense'),
      ])
      const cats = catRes.data || []
      // 扁平化分类
      const flatCats = []
      cats.forEach(p => {
        flatCats.push(p)
        if (p.children) p.children.forEach(c => flatCats.push(c))
      })
      this.setData({
        recurringVisible: true, recurringList: recRes.data || [],
        recCats: flatCats, recCatIdx: 0, recAmount: '', recDesc: '', recCycleIdx: 0,
      })
    } catch (e) { wx.showToast({ title: '加载失败', icon: 'none' }) }
    finally { wx.hideLoading() }
  },
  closeRecurring() { this.setData({ recurringVisible: false }) },
  onRecCat(e) { this.setData({ recCatIdx: Number(e.detail.value) }) },
  onRecAmt(e) { this.setData({ recAmount: e.detail.value }) },
  onRecDesc(e) { this.setData({ recDesc: e.detail.value }) },
  onRecCycle(e) { this.setData({ recCycleIdx: Number(e.detail.value) }) },
  async addRecurring() {
    const { recCats, recCatIdx, recAmount, recDesc, recCycleVals, recCycleIdx } = this.data
    const cat = recCats[recCatIdx]
    if (!cat) return wx.showToast({ title: '请选择分类', icon: 'none' })
    const amt = parseFloat(recAmount)
    if (!amt || amt <= 0) return wx.showToast({ title: '请输入金额', icon: 'none' })
    const today = new Date()
    const nextDate = today.toISOString().slice(0, 10)
    try {
      await api.createRecurring({
        category: cat.id, amount: amt, description: recDesc,
        cycle: recCycleVals[recCycleIdx], next_date: nextDate,
      })
      wx.showToast({ title: '已添加' })
      this.openRecurring()
    } catch (e) { wx.showToast({ title: '失败', icon: 'none' }) }
  },
  async deleteRecurring(e) {
    const id = e.currentTarget.dataset.id
    const res = await wx.showModal({ title: '确认删除？' })
    if (!res.confirm) return
    try {
      await api.deleteRecurring(id)
      wx.showToast({ title: '已删除' })
      this.openRecurring()
    } catch (e) { wx.showToast({ title: '失败', icon: 'none' }) }
  },

  logout() {
    getApp().clearSession()
    wx.reLaunch({ url: '/pages/login/login' })
  },
})
