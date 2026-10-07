const api = require('../../utils/api')

const STATUS_MAP = { pending: '待还', partial: '部分还', settled: '已结清', overdue: '逾期' }

Page({
  data: {
    summary: { total_lend: 0, total_borrow: 0, outstanding_lend: 0, outstanding_borrow: 0, net: 0, overdue_count: 0 },
    loans: [],
    filter: 'all',
    // 弹窗
    modalVisible: false,
    modalTitle: '添加借贷',
    editingId: null,
    form: { counterparty: '', direction: 'lend', amount: '', loan_date: '', due_date: '', description: '' },
    // 还款弹窗
    repayVisible: false,
    repayLoanId: null,
    repayAmount: '',
    repayName: '',
  },

  onShow() {
    if (!getApp().globalData.token) { wx.reLaunch({ url: '/pages/login/login' }); return }
    this.load()
  },

  async load() {
    try {
      const [s, l] = await Promise.all([
        api.loanSummary(),
        api.loans(this.data.filter !== 'all' ? { direction: this.data.filter } : {}),
      ])
      this.setData({ summary: s.data || {}, loans: (l.data && l.data.results) || [] })
    } catch (e) { console.error(e) }
  },

  setFilter(e) {
    const f = e.currentTarget.dataset.filter
    this.setData({ filter: f })
    this.load()
  },

  // 表单
  openAdd() {
    const today = new Date().toISOString().slice(0, 10)
    this.setData({
      modalVisible: true, modalTitle: '添加借贷', editingId: null,
      form: { counterparty: '', direction: 'lend', amount: '', loan_date: today, due_date: '', description: '' },
    })
  },

  openEdit(e) {
    const id = e.currentTarget.dataset.id
    const loan = this.data.loans.find(l => l.id === id)
    if (!loan) return
    this.setData({
      modalVisible: true, modalTitle: '编辑借贷', editingId: id,
      form: {
        counterparty: loan.counterparty, direction: loan.direction,
        amount: String(loan.amount), loan_date: loan.loan_date,
        due_date: loan.due_date || '', description: loan.description || '',
      },
    })
  },

  onFormField(e) {
    const field = e.currentTarget.dataset.field
    // tap 事件用 dataset.value，change 事件用 detail.value
    const value = e.detail.value !== undefined ? e.detail.value : e.currentTarget.dataset.value
    if (value === undefined || value === null) return
    const form = this.data.form
    form[field] = value
    this.setData({ form })
  },

  closeModal() { this.setData({ modalVisible: false }) },

  async submitForm() {
    const f = this.data.form
    if (!f.counterparty.trim()) return wx.showToast({ title: '请输入对方姓名', icon: 'none' })
    if (!f.amount || parseFloat(f.amount) <= 0) return wx.showToast({ title: '请输入有效金额', icon: 'none' })
    if (!f.loan_date) return wx.showToast({ title: '请选择日期', icon: 'none' })
    const data = { ...f, amount: parseFloat(f.amount), due_date: f.due_date || null }
    try {
      if (this.data.editingId) {
        await api.updateLoan(this.data.editingId, data)
      } else {
        await api.createLoan(data)
      }
      wx.showToast({ title: '保存成功' })
      this.closeModal()
      this.load()
    } catch (e) { wx.showToast({ title: (e && e.message) || '失败', icon: 'none' }) }
  },

  async deleteLoan(e) {
    const id = e.currentTarget.dataset.id
    const res = await wx.showModal({ title: '确认删除？' })
    if (!res.confirm) return
    try {
      await api.deleteLoan(id)
      wx.showToast({ title: '已删除' })
      this.load()
    } catch (e) { wx.showToast({ title: '失败', icon: 'none' }) }
  },

  // 还款
  openRepay(e) {
    const id = e.currentTarget.dataset.id
    const loan = this.data.loans.find(l => l.id === id)
    if (!loan || loan.status === 'settled') return
    this.setData({ repayVisible: true, repayLoanId: id, repayAmount: '', repayName: loan.counterparty })
  },

  onRepayInput(e) { this.setData({ repayAmount: e.detail.value }) },
  closeRepay() { this.setData({ repayVisible: false }) },

  async submitRepay() {
    const amount = parseFloat(this.data.repayAmount)
    if (!amount || amount <= 0) return wx.showToast({ title: '请输入还款金额', icon: 'none' })
    try {
      await api.repayLoan(this.data.repayLoanId, amount)
      wx.showToast({ title: '还款记录成功' })
      this.closeRepay()
      this.load()
    } catch (e) { wx.showToast({ title: (e && e.message) || '失败', icon: 'none' }) }
  },
})
