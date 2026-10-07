/**
 * 记账页集成示例 — 复制逻辑到 pages/record/record.js
 */
const { confirmVoiceLog } = require('../../utils/voice')
const { request } = require('../../utils/request')

Page({
  data: {
    voicePreview: null,
    referenceDate: '',
  },

  onLoad(options) {
    const today = this._today()
    this.setData({
      referenceDate: today,
      openVoice: options.mode === 'voice',
    })
  },

  _today() {
    const d = new Date()
    const m = `${d.getMonth() + 1}`.padStart(2, '0')
    const day = `${d.getDate()}`.padStart(2, '0')
    return `${d.getFullYear()}-${m}-${day}`
  },

  onVoiceParsed(e) {
    const preview = e.detail
    this.setData({ voicePreview: preview })
    // 可将 preview 填入表单：category_id, amount, expense_date, description, voice_log_id
  },

  onVoiceError(e) {
    wx.showToast({ title: e.detail.message || '语音失败', icon: 'none' })
  },

  async onConfirmVoiceSave() {
    const p = this.data.voicePreview
    if (!p || p.amount == null) {
      wx.showToast({ title: '请补充金额', icon: 'none' })
      return
    }

    try {
      const res = await request({
        url: '/expenses/',
        method: 'POST',
        data: {
          category: p.category_id,
          amount: p.amount,
          expense_date: p.expense_date,
          description: p.description || p.raw_text,
          source: 'voice',
          voice_log_id: p.log_id,
        },
      })
      const expenseId = res.data && (res.data.id || res.data.expense_id)
      if (p.log_id && expenseId) {
        await confirmVoiceLog(p.log_id, expenseId).catch(() => {})
      }
      wx.showToast({ title: '记账成功' })
      this.setData({ voicePreview: null })
    } catch (err) {
      wx.showToast({ title: (err && err.message) || '保存失败', icon: 'none' })
    }
  },
})
