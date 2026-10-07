App({
  globalData: {
    apiBase: 'http://192.168.43.121:8000/api',
    // apiBase: 'http://127.0.0.1:8000/api',  // 模拟器用
    token: '',
    userInfo: null,
    familyView: true,  // true=全家, false=个人
    familyId: null,
  },

  onLaunch() {
    const token = wx.getStorageSync('token') || ''
    const userInfo = wx.getStorageSync('userInfo') || null
    this.globalData.token = token
    this.globalData.userInfo = userInfo
  },

  toggleFamilyView() {
    this.globalData.familyView = !this.globalData.familyView
    return this.globalData.familyView
  },

  setSession(token, userInfo) {
    this.globalData.token = token
    this.globalData.userInfo = userInfo
    wx.setStorageSync('token', token)
    wx.setStorageSync('userInfo', userInfo)
  },

  clearSession() {
    this.globalData.token = ''
    this.globalData.userInfo = null
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
  },
})
