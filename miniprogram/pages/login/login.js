const api = require('../../utils/api')

Page({
  data: {
    username: 'zhangsan',
    password: '123456',
    isRegister: false,
    nickname: '',
    backendOk: true,
    backendHint: '',
  },

  onLoad() {
    getApp().clearSession()
    if (!this._checkingBackend) this.checkBackend()
  },

  async checkBackend() {
    if (this._checkingBackend) return
    this._checkingBackend = true
    try {
      await api.health()
      this.setData({ backendOk: true, backendHint: '' })
    } catch (e) {
      const hint =
        (e && e.message) ||
        '后端未连接。请先运行：cd code\\family_finance → runserver 0.0.0.0:8000'
      this.setData({ backendOk: false, backendHint: hint })
    } finally {
      this._checkingBackend = false
    }
  },

  onUsername(e) { this.setData({ username: e.detail.value }) },
  onPassword(e) { this.setData({ password: e.detail.value }) },
  onNickname(e) { this.setData({ nickname: e.detail.value }) },
  toggleMode() { this.setData({ isRegister: !this.data.isRegister }) },

  async submit() {
    const { username, password, isRegister, nickname } = this.data
    if (!username || !password) {
      wx.showToast({ title: '请填写账号密码', icon: 'none' })
      return
    }
    wx.showLoading({ title: '登录中' })
    try {
      const res = isRegister
        ? await api.register({ username, password, nickname: nickname || username })
        : await api.login({ username, password })
      const d = res.data
      getApp().setSession(d.access, d.user)
      wx.hideLoading()
      wx.switchTab({ url: '/pages/home/home' })
    } catch (e) {
      wx.hideLoading()
      const msg =
        (e && e.message) ||
        (e && e.errMsg) ||
        (typeof e === 'string' ? e : '') ||
        '登录失败'
      wx.showToast({ title: msg, icon: 'none', duration: 3000 })
      if (/后端|连接|域名|runserver/i.test(msg)) this.checkBackend()
    }
  },
})
