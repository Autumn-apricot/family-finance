/**
 * chart-box 组件 — 纯 Canvas 2D 图表
 *
 * 属性：
 *   type   : 'ring' (环形图) | 'bar' (横向柱状图)
 *   data   : [{label, value, color}, ...]
 *   width  : 画布逻辑宽度 (px, 默认 300)
 *   height : 画布逻辑高度 (px, 默认 240)
 */

const COLORS = [
  '#ff4d4f', '#fa8c16', '#fadb14', '#a0d911', '#52c41a',
  '#13c2c2', '#1677ff', '#722ed1', '#eb2f96', '#fa541c',
  '#2f54eb', '#9254de', '#36cfc9', '#d4380d', '#d4b106',
]

Component({
  properties: {
    type: { type: String, value: 'ring' },
    data: { type: Array, value: [], observer: 'draw' },
    width: { type: Number, value: 300 },
    height: { type: Number, value: 240 },
  },

  data: {
    legendData: [],
  },

  lifetimes: {
    attached() {
      this._dpr = 0
    },
  },

  methods: {
    async draw() {
      const items = (this.properties.data || []).filter(d => d.value > 0)
      if (!items.length) return

      const { type, width, height } = this.properties
      const query = this.createSelectorQuery()
      query.select('#chart-canvas').fields({ node: true, size: true }).exec((res) => {
        if (!res || !res[0] || !res[0].node) return
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getSystemInfoSync().pixelRatio
        canvas.width = width * dpr
        canvas.height = height * dpr
        ctx.scale(dpr, dpr)

        if (type === 'ring') this._drawRing(ctx, items, width, height)
        else if (type === 'bar') this._drawBar(ctx, items, width, height)
      })
    },

    /** 环形图 */
    _drawRing(ctx, items, w, h) {
      const total = items.reduce((s, d) => s + d.value, 0)
      const cx = w / 2
      const cy = h / 2
      const outerR = Math.min(cx, cy) - 8
      const innerR = outerR * 0.58
      let startAngle = -Math.PI / 2

      // 给没颜色的项自动分配
      const colored = items.map((d, i) => ({ ...d, color: d.color || COLORS[i % COLORS.length] }))

      // 绘制扇形
      colored.forEach(d => {
        const sweep = (d.value / total) * Math.PI * 2
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, outerR, startAngle, startAngle + sweep)
        ctx.closePath()
        ctx.fillStyle = d.color
        ctx.fill()
        startAngle += sweep
      })

      // 内圆镂空
      ctx.beginPath()
      ctx.arc(cx, cy, innerR, 0, Math.PI * 2)
      ctx.fillStyle = '#fff'
      ctx.fill()

      // 中心文字
      ctx.fillStyle = '#333'
      ctx.font = 'bold 28rpx sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(`¥${total.toFixed(0)}`, cx, cy - 6)
      ctx.font = '22rpx sans-serif'
      ctx.fillStyle = '#999'
      ctx.fillText('总计', cx, cy + 18)

      // legend
      const legend = colored.map(d => ({
        label: d.label, color: d.color,
        percent: ((d.value / total) * 100).toFixed(1),
      }))
      this.setData({ legendData: legend })
    },

    /** 横向柱状图 */
    _drawBar(ctx, items, w, h) {
      const pad = { top: 8, right: 70, bottom: 8, left: 8 }
      const barH = 28
      const gap = 10
      const chartW = w - pad.left - pad.right
      const maxVal = Math.max(...items.map(d => d.value), 1)

      const colored = items.map((d, i) => ({ ...d, color: d.color || COLORS[i % COLORS.length] }))
      const visible = colored.slice(0, Math.min(colored.length, Math.floor((h - pad.top - pad.bottom) / (barH + gap))))

      visible.forEach((d, i) => {
        const y = pad.top + i * (barH + gap)
        const barW = Math.max((d.value / maxVal) * chartW, 4)

        // bar
        ctx.fillStyle = d.color
        ctx.beginPath()
        this._roundRect(ctx, pad.left, y, barW, barH, 4)
        ctx.fill()

        // label on bar
        ctx.fillStyle = '#fff'
        ctx.font = '22rpx sans-serif'
        ctx.textBaseline = 'middle'
        ctx.textAlign = 'left'
        if (barW > 40) {
          ctx.fillText(d.label, pad.left + 6, y + barH / 2)
        }

        // value on right
        ctx.fillStyle = '#333'
        ctx.textAlign = 'left'
        ctx.fillText(`¥${d.value.toFixed(0)}`, pad.left + barW + 6, y + barH / 2)
      })
    },

    _roundRect(ctx, x, y, w, h, r) {
      ctx.moveTo(x + r, y)
      ctx.lineTo(x + w - r, y)
      ctx.arcTo(x + w, y, x + w, y + r, r)
      ctx.lineTo(x + w, y + h - r)
      ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
      ctx.lineTo(x + r, y + h)
      ctx.arcTo(x, y + h, x, y + h - r, r)
      ctx.lineTo(x, y + r)
      ctx.arcTo(x, y, x + r, y, r)
      ctx.closePath()
    },
  },
})
