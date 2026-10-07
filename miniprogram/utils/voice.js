/**
 * 语音解析 API 封装
 * 依赖 utils/request.js 中的 request 方法
 */
const { request } = require('./request')

/**
 * 将 ASR 文本提交后端结构化解析
 * @param {string} text
 * @param {string} [referenceDate] YYYY-MM-DD
 * @returns {Promise<object>} 信封 { code, message, data }
 */
function parseVoiceText(text, referenceDate) {
  const data = { text: (text || '').trim() }
  if (referenceDate) {
    data.reference_date = referenceDate
  }
  return request({
    url: '/voice/parse/',
    method: 'POST',
    data,
  })
}

/**
 * 确认语音日志已入账（可选，记账成功后调用）
 */
function confirmVoiceLog(logId, expenseId) {
  return request({
    url: `/voice/logs/${logId}/confirm/`,
    method: 'POST',
    data: { expense_id: expenseId },
  })
}

/**
 * 上传音频云端转写（P1 兜底，插件失败时使用）
 */
function transcribeAudio(filePath) {
  const app = getApp()
  const token = wx.getStorageSync('token') || ''
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: app.globalData.apiBase + '/voice/transcribe/',
      filePath,
      name: 'file',
      header: {
        Authorization: 'Bearer ' + token,
      },
      success(res) {
        try {
          const body = JSON.parse(res.data)
          if (body.code === 0) {
            resolve(body)
          } else {
            reject(body)
          }
        } catch (e) {
          reject({ message: '解析响应失败' })
        }
      },
      fail: reject,
    })
  })
}

module.exports = {
  parseVoiceText,
  confirmVoiceLog,
  transcribeAudio,
}
