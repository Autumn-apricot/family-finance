/**
 * 网络请求封装
 * @param {boolean} auth 默认 true；登录/注册/health 等公开接口传 auth: false，避免携带过期 token 导致 401
 */
function request({ url, method = 'GET', data, auth = true, timeout = 15000 }) {
  const app = getApp()
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = wx.getStorageSync('token') || ''
    if (token) headers.Authorization = 'Bearer ' + token
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: app.globalData.apiBase + url,
      method,
      data,
      timeout,
      header: headers,
      success(res) {
        if (res.statusCode === 401) {
          const body = res.data || { message: '未授权' }
          if (auth) {
            app.clearSession()
            const pages = getCurrentPages()
            const route = pages.length ? pages[pages.length - 1].route : ''
            if (route !== 'pages/login/login') {
              wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
              wx.reLaunch({ url: '/pages/login/login' })
            }
          }
          reject(body)
          return
        }
        const body = res.data
        // 兼容 code=0 与 code=200
        if (res.statusCode >= 200 && res.statusCode < 300) {
          if (body.code === 0 || body.code === 200) {
            resolve(body)
          } else if (body.code === 40002) {
            // 部分解析（如无金额）仍 resolve，由调用方处理
            resolve(body)
          } else {
            reject(body)
          }
        } else {
          reject(body || { message: '请求失败' })
        }
      },
      fail(err) {
        const errMsg = (err && err.errMsg) || ''
        let message = '网络请求失败'
        if (/url not in domain|合法域名|domain list/i.test(errMsg)) {
          message = '域名校验未关闭：详情→本地设置→勾选不校验合法域名'
        } else if (/timeout/i.test(errMsg)) {
          message = '连接后端超时：请确认 runserver 0.0.0.0:8000 已启动，浏览器能打开 /api/health/'
        } else if (/connect|fail/i.test(errMsg)) {
          message = '无法连接后端，请确认 Django 已启动（runserver 0.0.0.0:8000）'
        } else if (errMsg) {
          message = errMsg
        }
        reject({ message, errMsg })
      },
    })
  })
}

module.exports = { request }
