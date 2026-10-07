const api = require('../../utils/api')

Page({
  data: {
    input: '',
    messages: [],
    loadingHistory: false,
    hasMoreHistory: true,
    historyPage: 1,
  },

  onShow() {
    if (!getApp().globalData.token) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    // 首次打开显示欢迎语
    if (this.data.messages.length === 0) {
      this.setData({
        messages: [{ role: 'ai', text: '您好，有什么想问的？', isWelcome: true }],
        hasMoreHistory: true,
        historyPage: 1,
      })
    }
  },

  async loadHistory() {
    if (this.data.loadingHistory || !this.data.hasMoreHistory) return
    this.setData({ loadingHistory: true })
    try {
      const res = await api.aiHistory(this.data.historyPage)
      const results = (res.data && res.data.results) || []
      if (results.length === 0) {
        this.setData({ hasMoreHistory: false })
        return
      }
      // 后端按时间倒序返回，反转得到正序
      const older = []
      results.reverse().forEach(item => {
        older.push({ role: 'user', text: item.question, time: item.created_at })
        older.push({ role: 'ai', text: item.answer, time: item.created_at })
      })
      // 把历史插入到消息列表最前面（欢迎语之后）
      const current = this.data.messages
      const welcome = current.length > 0 && current[0].isWelcome ? current.slice(0, 1) : []
      const rest = current.length > 0 && current[0].isWelcome ? current.slice(1) : current
      this.setData({
        messages: [...welcome, ...older, ...rest],
        historyPage: this.data.historyPage + 1,
        hasMoreHistory: results.length >= 20,
      })
    } catch (e) {
      console.error('加载AI历史失败', e)
    } finally {
      this.setData({ loadingHistory: false })
    }
  },

  onInput(e) { this.setData({ input: e.detail.value }) },

  sendQuick(e) {
    const text = e.currentTarget.dataset.text
    if (!text) return
    this.setData({ input: text })
    this.send()
  },

  async send() {
    const q = this.data.input.trim()
    if (!q) return
    const msgs = this.data.messages.concat([{ role: 'user', text: q }])
    this.setData({ messages: msgs, input: '' }, () => this.scrollToBottom())
    try {
      const res = await api.aiChat(q)
      this.setData({
        messages: this.data.messages.concat([{ role: 'ai', text: res.data.answer }]),
      }, () => this.scrollToBottom())
    } catch (e) {
      wx.showToast({ title: (e && e.message) || '失败', icon: 'none' })
    }
  },

  scrollToBottom() {
    this.setData({ scrollToView: `msg-${this.data.messages.length - 1}` })
  },

  async advice() {
    wx.showLoading({ title: '分析中' })
    try {
      const res = await api.aiAdvice()
      wx.hideLoading()
      this.setData({
        messages: this.data.messages.concat([
          { role: 'ai', text: res.data.advice },
        ]),
      }, () => this.scrollToBottom())
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '失败', icon: 'none' })
    }
  },
})
