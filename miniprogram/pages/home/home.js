const api = require('../../utils/api')

function maskAmount(val, hide) {
  return hide ? '****' : (val || '0.00')
}

Page({
  data: {
    todayDate: '',
    summary: {},
    expenses: [],
    loanSummary: null,
    hideTotal: false,
    hasFamily: false,
    familyView: true,
    swipedId: null,
    swipeStartX: 0,
    swipeStartY: 0,
    editVisible: false, editId: null, editCategories: [],
    editParentIndex: 0, editSubIndex: 0, editSubCategories: [],
    editAmount: '', editDesc: '', editDate: '', editPayment: 'wechat', editPaymentIdx: 0,
    paymentOptions: ['💚 微信', '💙 支付宝', '💵 现金', '💳 银行卡', '💎 信用卡', '💰 其他'],
    paymentValues: ['wechat', 'alipay', 'cash', 'bank_card', 'credit_card', 'other'],
  },

  onShow() {
    if (!getApp().globalData.token) { wx.reLaunch({ url: '/pages/login/login' }); return }
    const now = new Date()
    const todayStr = `${now.getFullYear()}年${now.getMonth()+1}月${now.getDate()}日`
    const hideTotal = !!(getApp().globalData.userInfo && getApp().globalData.userInfo.hide_total_amount)
    const familyView = getApp().globalData.familyView
    this.setData({ todayDate: todayStr, hideTotal, familyView })
    this.load()
    api.generateRecurring().catch(() => {})
  },

  toggleView() {
    const fv = getApp().toggleFamilyView()
    this.setData({ familyView: fv })
    this.load()
  },

  async load() {
    try {
      const meRes = await api.me().catch(() => null)
      if (meRes && meRes.data) {
        getApp().setSession(getApp().globalData.token, meRes.data)
        const hasFamily = !!(meRes.data.family)
        getApp().globalData.familyId = meRes.data.family
        this.setData({ hideTotal: !!meRes.data.hide_total_amount, hasFamily })
      }
      const hide = this.data.hideTotal
      const fv = getApp().globalData.familyView
      const uid = (!fv && getApp().globalData.userInfo) ? getApp().globalData.userInfo.id : null
      const [s, e, loan] = await Promise.all([
        api.statsSummary(uid),
        api.expenses({ page: 1, page_size: 5, ...(uid ? { user_id: uid } : {}) }),
        api.loanSummary().catch(() => ({ data: null })),
      ])
      const raw = s.data || {}
      this.setData({
        summary: {
          today_expense: maskAmount(raw.today_expense, hide),
          today_income: maskAmount(raw.today_income, hide),
          month_expense: maskAmount(raw.month_expense, hide),
          month_income: maskAmount(raw.month_income, hide),
          month_balance: maskAmount(raw.month_balance, hide),
          budget_total: raw.budget_total || 0,
          budget_used_percent: raw.budget_used_percent || 0,
        },
        expenses: (e.data && e.data.results) || [],
        loanSummary: (loan && loan.data) || null,
      })
    } catch (err) { console.error(err) }
  },

  // 编辑
  async openEdit(e) {
    const id = e.currentTarget.dataset.id
    const exp = this.data.expenses.find(x => x.id === id)
    if (!exp) return
    wx.showLoading({ title: '加载中' })
    try {
      const catRes = await api.categories(exp.category_type || 'expense')
      const cats = catRes.data || []
      let pi = 0, si = 0, subs = []
      for (let i = 0; i < cats.length; i++) {
        if (cats[i].id === exp.category) { pi = i; break }
        if (cats[i].children) {
          for (let j = 0; j < cats[i].children.length; j++) {
            if (cats[i].children[j].id === exp.category) { pi = i; si = j; subs = cats[i].children; break }
          }
        }
      }
      this.setData({
        editVisible: true, editId: id, editCategories: cats,
        editParentIndex: pi, editSubIndex: si, editSubCategories: subs,
        editAmount: String(exp.amount), editDesc: exp.description || '', editDate: exp.expense_date || '',
        editPayment: exp.payment_method || 'wechat',
        editPaymentIdx: this.data.paymentValues.indexOf(exp.payment_method || 'wechat'),
      })
    } catch (e) { wx.showToast({ title: '加载失败', icon: 'none' }) }
    finally { wx.hideLoading() }
  },
  onEditParent(e) { const idx = Number(e.detail.value); const p = this.data.editCategories[idx]; this.setData({ editParentIndex: idx, editSubIndex: 0, editSubCategories: (p && p.children) || [] }) },
  onEditSub(e) { this.setData({ editSubIndex: Number(e.detail.value) }) },
  onEditAmt(e) { this.setData({ editAmount: e.detail.value }) },
  onEditDesc(e) { this.setData({ editDesc: e.detail.value }) },
  onEditDate(e) { this.setData({ editDate: e.detail.value }) },
  onEditPay(e) { const idx = Number(e.detail.value); this.setData({ editPayment: this.data.paymentValues[idx], editPaymentIdx: idx }) },
  closeEdit() { this.setData({ editVisible: false }) },
  async submitEdit() {
    const { editId, editCategories, editParentIndex, editSubCategories, editSubIndex, editAmount, editDesc, editDate, editPayment } = this.data
    let catId
    if (editSubCategories.length > 0) catId = editSubCategories[editSubIndex].id
    else if (editCategories[editParentIndex]) catId = editCategories[editParentIndex].id
    if (!catId) return wx.showToast({ title: '请选择分类', icon: 'none' })
    const amt = parseFloat(editAmount)
    if (!amt || amt <= 0) return wx.showToast({ title: '金额无效', icon: 'none' })
    try {
      await api.updateExpense(editId, { category: catId, amount: amt, description: editDesc, expense_date: editDate, payment_method: editPayment })
      wx.showToast({ title: '修改成功' }); this.closeEdit(); this.load()
    } catch (e) { wx.showToast({ title: (e && e.message) || '失败', icon: 'none' }) }
  },

  onTapRow(e) { if (this.data.swipedId) { this.setData({ swipedId: null }); return } this.openEdit(e) },
  onTouchStart(e) { if (e.touches.length !== 1) return; this.setData({ swipeStartX: e.touches[0].clientX, swipeStartY: e.touches[0].clientY }) },
  onTouchMove(e) {
    const id = e.currentTarget.dataset.id
    if (!this.data.swipeStartX) return
    const dx = e.touches[0].clientX - this.data.swipeStartX
    if (Math.abs(dx) < Math.abs(e.touches[0].clientY - this.data.swipeStartY) || Math.abs(dx) < 10) return
    if (this.data.swipedId && this.data.swipedId !== id) this.setData({ swipedId: null })
    this.setData({ swipeId: id, swipeX: Math.max(-80, Math.min(0, dx * 0.6)) })
  },
  onTouchEnd(e) {
    const id = e.currentTarget.dataset.id
    if (!this.data.swipeX || this.data.swipeX > -20) { this.setData({ swipedId: null, swipeStartX: 0, swipeStartY: 0, swipeX: 0 }); return }
    this.setData({ swipedId: id, swipeStartX: 0, swipeStartY: 0, swipeX: 0 })
  },
  async removeExpense(e) {
    const id = e.currentTarget.dataset.id; this.setData({ swipedId: null })
    const res = await wx.showModal({ title: '确认删除？' }); if (!res.confirm) return
    try { await api.deleteExpense(id); wx.showToast({ title: '已删除' }); this.load() }
    catch (err) { wx.showToast({ title: '失败', icon: 'none' }) }
  },

  goRecord() { wx.switchTab({ url: '/pages/record/record' }) },
  goLoan() { wx.navigateTo({ url: '/pages/loan/loan' }) },
  onPullDownRefresh() { this.load().finally(() => wx.stopPullDownRefresh()) },
})
