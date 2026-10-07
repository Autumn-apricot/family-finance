/**
 * 语音输入组件 — 微信同声传译插件 + 后端 /voice/parse/
 *
 * 启用语音需在 app.json 声明插件并在公众平台授权，见 miniprogram/README.md
 */
const { parseVoiceText } = require('../../utils/voice')

/** 未在 app.json 配置或未授权时 manager 为 null，模拟器可正常启动 */
function createRecordManager() {
  try {
    const plugin = requirePlugin('WechatSI')
    return plugin.getRecordRecognitionManager()
  } catch (e) {
    return null
  }
}

Component({
  properties: {
    /** hold 长按说话 | tap 点击切换 */
    mode: {
      type: String,
      value: 'hold',
    },
    disabled: {
      type: Boolean,
      value: false,
    },
    /** 参考日期 YYYY-MM-DD，默认今天 */
    referenceDate: {
      type: String,
      value: '',
    },
  },

  data: {
    status: 'idle', // idle | recording | processing | preview | error
    partialText: '',
    finalText: '',
    recordSeconds: 0,
    errorMessage: '',
    preview: null,
    timerId: null,
    pluginReady: false,
  },

  lifetimes: {
    attached() {
      this._manager = createRecordManager()
      this.setData({ pluginReady: !!this._manager })
      if (this._manager) this._bindManager()
    },
    detached() {
      this._clearTimer()
      try {
        if (this._manager) this._manager.stop()
      } catch (e) {
        /* ignore */
      }
    },
  },

  methods: {
    _bindManager() {
      const manager = this._manager
      manager.onRecognize = (res) => {
        this.setData({
          partialText: res.result || '',
        })
      }

      manager.onStop = (res) => {
        this._clearTimer()
        const text = (res.result || '').trim()
        this.setData({ finalText: text, recordSeconds: 0 })
        if (!text) {
          this._setError('没听清，请再说一次')
          return
        }
        this._parseText(text)
      }

      manager.onError = (res) => {
        this._clearTimer()
        const msg = res.msg || res.errMsg || '录音识别失败'
        this._setError(msg)
        this.triggerEvent('error', { message: msg })
      }
    },

    _setError(message) {
      this.setData({
        status: 'error',
        errorMessage: message,
      })
    },

    _clearTimer() {
      if (this.data.timerId) {
        clearInterval(this.data.timerId)
        this.setData({ timerId: null })
      }
    },

    /** 检查麦克风权限 */
    async _ensureRecordAuth() {
      return new Promise((resolve, reject) => {
        wx.getSetting({
          success: (res) => {
            if (res.authSetting['scope.record']) {
              resolve()
              return
            }
            wx.authorize({
              scope: 'scope.record',
              success: resolve,
              fail: () => {
                wx.showModal({
                  title: '需要麦克风权限',
                  content: '请在设置中开启录音权限以使用语音记账',
                  confirmText: '去设置',
                  success: (m) => {
                    if (m.confirm) wx.openSetting()
                  },
                })
                reject(new Error('scope.record denied'))
              },
            })
          },
        })
      })
    },

    async onTouchStart() {
      if (this.properties.disabled || this.properties.mode !== 'hold') return
      await this.startRecord()
    },

    onTouchEnd() {
      if (this.properties.mode !== 'hold') return
      this.stopRecord()
    },

    async onTapMic() {
      if (this.properties.disabled || this.properties.mode !== 'tap') return
      if (this.data.status === 'recording') {
        this.stopRecord()
      } else {
        await this.startRecord()
      }
    },

    async startRecord() {
      if (!this._manager) {
        wx.showToast({
          title: '语音插件未配置，请用手动记账',
          icon: 'none',
          duration: 2500,
        })
        return
      }
      try {
        await this._ensureRecordAuth()
      } catch (e) {
        return
      }

      this.setData({
        status: 'recording',
        partialText: '',
        finalText: '',
        errorMessage: '',
        preview: null,
        recordSeconds: 0,
      })

      const timerId = setInterval(() => {
        this.setData({ recordSeconds: this.data.recordSeconds + 1 })
      }, 1000)
      this.setData({ timerId })

      this._manager.start({
        lang: 'zh_CN',
        duration: 60000,
      })
    },

    stopRecord() {
      if (this.data.status !== 'recording') return
      this.setData({ status: 'processing' })
      try {
        this._manager.stop()
      } catch (e) {
        this._setError('结束录音失败')
      }
    },

    async _parseText(text) {
      this.setData({ status: 'processing' })
      const ref = this.properties.referenceDate || ''

      try {
        const res = await parseVoiceText(text, ref || undefined)
        const data = res.data

        if (res.code === 40002) {
          // 无金额等部分解析
          this.setData({
            status: 'preview',
            preview: data,
            errorMessage: res.message || '未识别到金额，请补充',
          })
          this.triggerEvent('parsed', { ...data, partial: true })
          return
        }

        this.setData({
          status: 'preview',
          preview: data,
          errorMessage: '',
        })
        this.triggerEvent('parsed', data)
      } catch (err) {
        const msg = (err && err.message) || '解析失败，请重试或改用手动记账'
        this._setError(msg)
        this.triggerEvent('error', { message: msg })
      }
    },

    /** 外部传入文本（手动输入降级） */
    parseManualText(text) {
      return this._parseText(text)
    },

    onRetry() {
      this.setData({
        status: 'idle',
        partialText: '',
        finalText: '',
        preview: null,
        errorMessage: '',
      })
    },

    /** 父页面修改预览后同步 */
    updatePreview(preview) {
      this.setData({ preview })
    },
  },
})
