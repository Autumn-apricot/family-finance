const api = require('../../utils/api')
const voice = require('../../utils/voice')

Page({
  data: {
    // 录音
    recording: false,
    recordSeconds: 0,
    _recorder: null,
    _recordTimer: null,
    // 类型切换
    expenseType: 'expense',    // 'expense' | 'income'
    categories: [],            // 一级分类（包含 children）
    subCategories: [],         // 当前选中的一级分类下的子分类
    parentIndex: 0,
    subIndex: 0,
    // 表单
    amount: '',
    description: '',
    expenseDate: '',
    paymentMethod: 'wechat',
    paymentIndex: 0,
    paymentOptions: ['💚 微信', '💙 支付宝', '💵 现金', '💳 银行卡', '💎 信用卡', '💰 其他'],
    paymentValues: ['wechat', 'alipay', 'cash', 'bank_card', 'credit_card', 'other'],
    // 文字智能
    voiceText: '',
    textParseInput: '',
    parseResult: null,
    // 账单列表
    expenses: [],
    // 筛选
    filterVisible: false,
    filterDateFrom: '',
    filterDateTo: '',
    filterCategoryId: '',
    filterCategoryName: '全部',
    filterCategoryOptions: ['全部'],
    filterCategoryIdx: 0,
    filterSearch: '',
    // 编辑弹窗
    editModalVisible: false,
    editId: null,
    editParentIndex: 0,
    editSubIndex: 0,
    editSubCategories: [],
    editAmount: '',
    editDescription: '',
    editDate: '',
    editPaymentMethod: 'wechat',
    editPaymentIndex: 0,
    // 分页
    page: 1,
    hasMore: true,
    // 滑动删除
    swipedId: null,
    swipeStartX: 0,
    swipeStartY: 0,
  },

  onShow() {
    if (!getApp().globalData.token) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    const today = new Date().toISOString().slice(0, 10)
    this.setData({ expenseDate: today, page: 1, hasMore: true })
    this._initRecorder()
    this.loadCategories()
    this.loadExpenses()
  },

  _initRecorder() {
    const rm = wx.getRecorderManager()
    rm.onStop((res) => {
      this.setData({ recording: false, recordSeconds: 0 })
      if (this.data._recordTimer) { clearInterval(this.data._recordTimer); this.data._recordTimer = null }
      if (res.tempFilePath) {
        this._processAudio(res.tempFilePath)
      }
    })
    rm.onError((res) => {
      this.setData({ recording: false, recordSeconds: 0 })
      if (this.data._recordTimer) { clearInterval(this.data._recordTimer); this.data._recordTimer = null }
      console.error('录音错误:', res)
      wx.showToast({ title: res.errMsg || '录音失败，请授权麦克风', icon: 'none' })
    })
    this.data._recorder = rm
  },

  startRecord() {
    const rm = this.data._recorder
    if (!rm) {
      wx.showToast({ title: '录音组件未就绪', icon: 'none' })
      return
    }
    // 直接启动，录音管理器会自动请求权限
    rm.start({
      duration: 30000,
      sampleRate: 16000,
      format: 'wav',
      numberOfChannels: 1,
    })
    this.setData({ recording: true, recordSeconds: 0 })
    const timer = setInterval(() => {
      this.setData({ recordSeconds: this.data.recordSeconds + 1 })
    }, 1000)
    this.data._recordTimer = timer
  },

  stopRecord() {
    if (!this.data.recording) return
    this.data._recorder.stop()
  },

  async _processAudio(filePath) {
    wx.showLoading({ title: 'AI 识别中...' })
    try {
      const textRes = await voice.transcribeAudio(filePath)
      const text = (textRes.data && textRes.data.text) || ''
      wx.hideLoading()
      if (text) {
        this.setData({ textParseInput: text.trim() })
        await this.parseByText()
      } else {
        // 识别为空，打开手动输入
        this._showVoiceInputFallback()
      }
    } catch (e) {
      wx.hideLoading()
      // ASR 失败，手动输入兜底
      this._showVoiceInputFallback()
    }
  },

  _showVoiceInputFallback() {
    wx.showModal({
      title: '录音完成',
      editable: true,
      placeholderText: '请输入刚说的内容，如：午饭35元',
      content: '',
      success: async (res) => {
        if (res.confirm && res.content) {
          this.setData({ textParseInput: res.content.trim() })
          await this.parseByText()
        }
      },
    })
  },

  getUserId() {
    const fv = getApp().globalData.familyView
    if (!fv && getApp().globalData.userInfo) return getApp().globalData.userInfo.id
    return null
  },

  // ==================== 分类 ====================

  async loadCategories() {
    // 缓存：同类型不重复加载
    if (this._cachedCats && this._cachedType === this.data.expenseType) {
      const categories = this._cachedCats
      const filterCategoryOptions = ['全部', ...categories.map(c => c.icon + ' ' + c.name)]
      this.setData({ categories, filterCategoryOptions })
      if (categories.length > 0) this.updateSubCategories(0)
      return
    }
    const res = await api.categories(this.data.expenseType)
    const categories = res.data || []
    const filterCategoryOptions = ['全部', ...categories.map(c => c.icon + ' ' + c.name)]
    this._cachedCats = categories
    this._cachedType = this.data.expenseType
    this.setData({ categories, filterCategoryOptions })
    if (categories.length > 0) {
      this.updateSubCategories(0)
    }
  },

  updateSubCategories(parentIndex) {
    const parent = this.data.categories[parentIndex]
    const subCategories = (parent && parent.children) ? parent.children : []
    this.setData({ parentIndex, subCategories, subIndex: 0 })
  },

  onParentCategory(e) {
    this.updateSubCategories(Number(e.detail.value))
  },

  onSubCategory(e) {
    this.setData({ subIndex: Number(e.detail.value) })
  },

  /** 支出/收入切换 */
  onToggleType(e) {
    const type = e.currentTarget.dataset.type
    if (type === this.data.expenseType) return
    this.setData({ expenseType: type, parentIndex: 0, subIndex: 0, subCategories: [] })
    this.loadCategories()
  },

  getSelectedCategoryId() {
    const { categories, parentIndex, subCategories, subIndex } = this.data
    if (subCategories.length > 0) return subCategories[subIndex].id
    if (categories[parentIndex]) return categories[parentIndex].id
    return null
  },

  getCategoryPath(categoryId) {
    const { categories } = this.data
    for (const p of categories) {
      if (p.id === categoryId) return { parentIndex: categories.indexOf(p), subIndex: 0, subCategories: [] }
      if (p.children) {
        for (const c of p.children) {
          if (c.id === categoryId) return { parentIndex: categories.indexOf(p), subIndex: p.children.indexOf(c), subCategories: p.children }
        }
      }
    }
    return null
  },

  // ==================== 账单列表 ====================

  async loadExpenses(append = false) {
    const params = { page: this.data.page, page_size: 20 }
    const uid = this.getUserId(); if (uid) params.user_id = uid
    if (this.data.filterDateFrom) params.date_from = this.data.filterDateFrom
    if (this.data.filterDateTo) params.date_to = this.data.filterDateTo
    if (this.data.filterCategoryId) params.category_id = this.data.filterCategoryId
    if (this.data.filterSearch) params.search = this.data.filterSearch

    try {
      const res = await api.expenses(params)
      const results = (res.data && res.data.results) || []
      const next = res.data && res.data.next
      this.setData({
        expenses: append ? [...this.data.expenses, ...results] : results,
        hasMore: !!next,
      })
    } catch (e) {
      console.error(e)
    }
  },

  loadMore() {
    if (!this.data.hasMore) return
    this.setData({ page: this.data.page + 1 })
    this.loadExpenses(true)
  },

  // ==================== 筛选 ====================

  toggleFilter() {
    this.setData({ filterVisible: !this.data.filterVisible })
  },

  onFilterDateFrom(e) { this.setData({ filterDateFrom: e.detail.value }) },
  onFilterDateTo(e) { this.setData({ filterDateTo: e.detail.value }) },

  onFilterCategory(e) {
    const idx = Number(e.detail.value)
    if (idx === 0) {
      this.setData({ filterCategoryIdx: 0, filterCategoryId: '', filterCategoryName: '全部' })
    } else {
      const catIdx = idx - 1
      const cat = this.data.categories[catIdx]
      if (cat) {
        this.setData({ filterCategoryIdx: idx, filterCategoryId: cat.id, filterCategoryName: cat.name })
      }
    }
  },

  applyFilter() {
    this.setData({ page: 1, filterVisible: false })
    this.loadExpenses()
  },

  onFilterSearch(e) { this.setData({ filterSearch: e.detail.value }) },

  resetFilter() {
    this.setData({
      filterDateFrom: '', filterDateTo: '', filterCategoryId: '', filterCategoryName: '全部',
      filterCategoryIdx: 0, filterSearch: '', page: 1, filterVisible: false,
    })
    this.loadExpenses()
  },

  // ==================== 表单 ====================

  onAmount(e) { this.setData({ amount: e.detail.value }) },
  onDesc(e) { this.setData({ description: e.detail.value }) },
  onDate(e) { this.setData({ expenseDate: e.detail.value }) },
  onPayment(e) {
    const idx = Number(e.detail.value)
    this.setData({ paymentMethod: this.data.paymentValues[idx], paymentIndex: idx })
  },

  onTextParseInput(e) { this.setData({ textParseInput: e.detail.value }) },

  async parseByText() {
    const text = (this.data.textParseInput || '').trim()
    if (!text) return wx.showToast({ title: '请输入一句话', icon: 'none' })
    wx.showLoading({ title: '解析中' })
    try {
      const res = await api.voiceParse(text)
      this.onVoiceResult({ detail: res.data })
      wx.showToast({ title: '已填入表单', icon: 'success' })
    } catch (e) {
      wx.showToast({ title: (e && e.message) || '解析失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  async onVoiceResult(e) {
    const r = e.detail
    const isIncome = r.type === 'income'
    // 类型不一致时先切换并加载分类
    if (isIncome !== (this.data.expenseType === 'income')) {
      this.setData({ expenseType: isIncome ? 'income' : 'expense' })
      await this.loadCategories()
    }
    this.setData({
      voiceText: r.raw_text || '',
      parseResult: r,
      amount: r.amount != null ? String(r.amount) : this.data.amount,
      expenseDate: r.expense_date || this.data.expenseDate,
    })
    if (r.category_id) {
      const { categories } = this.data
      const rawText = (r.raw_text || '').toLowerCase()
      for (let i = 0; i < categories.length; i++) {
        const parent = categories[i]
        if (parent.children && parent.children.length > 0) {
          const sorted = [...parent.children].sort((a, b) => b.name.length - a.name.length)
          for (let j = 0; j < sorted.length; j++) {
            if (rawText.includes(sorted[j].name)) {
              this.updateSubCategories(i)
              this.setData({ subIndex: parent.children.indexOf(sorted[j]) })
              return
            }
          }
          for (let j = 0; j < parent.children.length; j++) {
            if (parent.children[j].id === r.category_id) {
              this.updateSubCategories(i)
              this.setData({ subIndex: j })
              return
            }
          }
        }
        if (parent.id === r.category_id) {
          this.updateSubCategories(i)
          if (parent.children && parent.children.length > 0) {
            this.setData({ subIndex: this._guessSubIndex(rawText, parent.children) })
          }
          return
        }
      }
    }
  },

  _guessSubIndex(text, children) {
    const lower = text.toLowerCase()
    const sorted = children.map((c, i) => ({ ...c, origIndex: i }))
      .sort((a, b) => b.name.length - a.name.length)
    for (const c of sorted) {
      if (lower.includes(c.name)) return c.origIndex
    }
    return 0
  },

  async submit() {
    const { categories } = this.data
    if (!categories.length) return wx.showToast({ title: '无分类', icon: 'none' })
    const catId = this.getSelectedCategoryId()
    if (!catId) return wx.showToast({ title: '请选择分类', icon: 'none' })
    const amount = parseFloat(this.data.amount)
    if (!amount || amount <= 0) return wx.showToast({ title: '请输入有效金额', icon: 'none' })
    const fromVoice = !!(this.data.parseResult || this.data.voiceText)
    try {
      await api.createExpense({
        category: catId, amount,
        description: this.data.description || this.data.voiceText,
        expense_date: this.data.expenseDate,
        source: fromVoice ? 'voice' : 'manual',
        payment_method: this.data.paymentMethod,
      })
      wx.showToast({ title: '记账成功' })
      this.setData({ amount: '', description: '', voiceText: '', parseResult: null, textParseInput: '' })
      this.setData({ page: 1 })
      this.loadExpenses()
    } catch (e) {
      wx.showToast({ title: (e && e.message) || '失败', icon: 'none' })
    }
  },

  // ==================== 编辑 ====================

  async editExpense(e) {
    const id = e.currentTarget.dataset.id
    const exp = this.data.expenses.find(x => x.id === id)
    if (!exp) return

    // 记录当前类型，编辑完恢复
    this._editPrevType = this.data.expenseType
    const needType = exp.category_type || 'expense'
    if (this.data.expenseType !== needType) {
      this.setData({ expenseType: needType })
      await this.loadCategories()
    }

    const path = this.getCategoryPath(exp.category)
    this.setData({
      editModalVisible: true,
      editId: id,
      editParentIndex: path ? path.parentIndex : 0,
      editSubIndex: path ? path.subIndex : 0,
      editSubCategories: path ? path.subCategories : [],
      editAmount: String(exp.amount),
      editDescription: exp.description || '',
      editDate: exp.expense_date || '',
      editPaymentMethod: exp.payment_method || 'wechat',
      editPaymentIndex: this.data.paymentValues.indexOf(exp.payment_method || 'wechat'),
    })
  },

  onEditParentCategory(e) {
    const idx = Number(e.detail.value)
    const parent = this.data.categories[idx]
    const subs = (parent && parent.children) ? parent.children : []
    this.setData({ editParentIndex: idx, editSubIndex: 0, editSubCategories: subs })
  },

  onEditSubCategory(e) {
    this.setData({ editSubIndex: Number(e.detail.value) })
  },

  onEditAmount(e) { this.setData({ editAmount: e.detail.value }) },
  onEditDesc(e) { this.setData({ editDescription: e.detail.value }) },
  onEditDate(e) { this.setData({ editDate: e.detail.value }) },
  onEditPayment(e) {
    const idx = Number(e.detail.value)
    this.setData({ editPaymentMethod: this.data.paymentValues[idx], editPaymentIndex: idx })
  },

  async closeEditModal() {
    this.setData({ editModalVisible: false })
    await this._restoreEditType()
  },

  async _restoreEditType() {
    if (this._editPrevType && this.data.expenseType !== this._editPrevType) {
      this.setData({ expenseType: this._editPrevType })
      await this.loadCategories()
    }
    this._editPrevType = null
  },

  async submitEdit() {
    const { editId, categories, editParentIndex, editSubCategories, editSubIndex, editAmount, editDescription, editDate } = this.data
    let catId
    if (editSubCategories.length > 0) {
      catId = editSubCategories[editSubIndex].id
    } else if (categories[editParentIndex]) {
      catId = categories[editParentIndex].id
    }
    if (!catId) return wx.showToast({ title: '请选择分类', icon: 'none' })
    const amount = parseFloat(editAmount)
    if (!amount || amount <= 0) return wx.showToast({ title: '请输入有效金额', icon: 'none' })
    try {
      await api.updateExpense(editId, {
        category: catId, amount, description: editDescription,
        expense_date: editDate, payment_method: this.data.editPaymentMethod,
      })
      wx.showToast({ title: '修改成功' })
      this.setData({ editModalVisible: false })
      await this._restoreEditType()
      this.loadExpenses()
    } catch (e) {
      wx.showToast({ title: (e && e.message) || '修改失败', icon: 'none' })
    }
  },

  // ==================== 滑动删除 ====================

  onTouchStart(e) {
    if (e.touches.length !== 1) return
    this.setData({ swipeStartX: e.touches[0].clientX, swipeStartY: e.touches[0].clientY })
  },

  onTouchMove(e) {
    const id = e.currentTarget.dataset.id
    if (!this.data.swipeStartX) return
    const dx = e.touches[0].clientX - this.data.swipeStartX
    const dy = Math.abs(e.touches[0].clientY - this.data.swipeStartY)
    // 水平滑动 > 垂直，才激活
    if (Math.abs(dx) < Math.abs(dy) || Math.abs(dx) < 10) return
    // 关闭其他已打开的
    if (this.data.swipedId && this.data.swipedId !== id) {
      this.setData({ swipedId: null })
    }
    // 只允许左滑，最大 160rpx → 约 80px
    const x = Math.max(-80, Math.min(0, dx * 0.6))
    this.setData({ swipeId: id, swipeX: x })
  },

  onTouchEnd(e) {
    const id = e.currentTarget.dataset.id
    if (!this.data.swipeX || this.data.swipeX > -20) {
      // 滑动不够，归位
      this.setData({ swipedId: null, swipeStartX: 0, swipeStartY: 0, swipeX: 0 })
      return
    }
    // 锁定打开
    this.setData({ swipedId: id, swipeStartX: 0, swipeStartY: 0, swipeX: 0 })
  },

  onTapRow(e) {
    const id = e.currentTarget.dataset.id
    if (this.data.swipedId) {
      // 有划开的行，先收起
      this.setData({ swipedId: null })
    } else {
      // 直接编辑
      this.editExpense(e)
    }
  },

  // ==================== 删除 ====================

  async removeExpense(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ swipedId: null })
    const res = await wx.showModal({ title: '确认删除该账单？' })
    if (!res.confirm) return
    try {
      await api.deleteExpense(id)
      wx.showToast({ title: '已删除' })
      this.loadExpenses()
    } catch (err) {
      wx.showToast({ title: (err && err.message) || '删除失败', icon: 'none' })
    }
  },

  // ==================== 下拉刷新 / 触底 ====================

  onPullDownRefresh() {
    this.setData({ page: 1 })
    this.loadExpenses().finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    this.loadMore()
  },
})
