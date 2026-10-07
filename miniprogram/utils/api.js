const { request } = require('./request')

module.exports = {
  health: () => request({ url: '/health/', auth: false }),
  login: (data) => request({ url: '/auth/login/', method: 'POST', data, auth: false }),
  register: (data) => request({ url: '/auth/register/', method: 'POST', data, auth: false }),
  me: () => request({ url: '/users/me/' }),
  updateMe: (data) => request({ url: '/users/me/', method: 'PATCH', data }),
  categories: (type) =>
    request({
      url: '/categories/' + (type ? '?type=' + type + '&nested=1' : '?nested=1'),
    }),
  expenses: (params) => {
    const q = Object.keys(params || {})
      .map((k) => `${k}=${encodeURIComponent(params[k])}`)
      .join('&')
    return request({ url: '/expenses/' + (q ? '?' + q : '') })
  },
  createExpense: (data) => request({ url: '/expenses/', method: 'POST', data }),
  updateExpense: (id, data) => request({ url: `/expenses/${id}/`, method: 'PATCH', data }),
  deleteExpense: (id) => request({ url: `/expenses/${id}/`, method: 'DELETE' }),
  statsSummary: (userId) =>
    request({ url: '/stats/summary/' + (userId ? '?user_id=' + userId : '') }),
  statsDaily: (date, userId) => request({ url: `/stats/daily/?date=${date}` + (userId ? '&user_id=' + userId : '') }),
  statsWeekly: (weekStart, userId) => request({ url: `/stats/weekly/?week_start=${weekStart}` + (userId ? '&user_id=' + userId : '') }),
  statsMonthly: (month, userId) => request({ url: `/stats/monthly/?month=${month}` + (userId ? '&user_id=' + userId : '') }),
  statsAnnual: (year, userId) => request({ url: `/stats/annual/?year=${year}` + (userId ? '&user_id=' + userId : '') }),
  aiChat: (question) => request({ url: '/ai/chat/', method: 'POST', data: { question } }),
  aiAdvice: () => request({ url: '/ai/advice/', method: 'POST', data: {} }),
  aiHistory: (page = 1) => request({ url: `/ai/history/?page=${page}&page_size=20` }),
  voiceParse: (text) =>
    request({ url: '/voice/parse/', method: 'POST', data: { text, reference_date: new Date().toISOString().slice(0, 10) } }),
  budgets: (month) => request({ url: `/budgets/?month=${month}` }),
  createBudget: (data) => request({ url: '/budgets/', method: 'POST', data }),
  updateBudget: (id, data) => request({ url: `/budgets/${id}/`, method: 'PATCH', data }),
  deleteBudget: (id) => request({ url: `/budgets/${id}/`, method: 'DELETE' }),
  // 借贷
  loanSummary: () => request({ url: '/loans/summary/' }),
  loans: (params) => {
    const q = Object.keys(params || {}).map(k => `${k}=${encodeURIComponent(params[k])}`).join('&')
    return request({ url: '/loans/' + (q ? '?' + q : '') })
  },
  createLoan: (data) => request({ url: '/loans/', method: 'POST', data }),
  updateLoan: (id, data) => request({ url: `/loans/${id}/`, method: 'PATCH', data }),
  deleteLoan: (id) => request({ url: `/loans/${id}/`, method: 'DELETE' }),
  repayLoan: (id, amount) => request({ url: `/loans/${id}/repay/`, method: 'POST', data: { amount } }),
  // 钱包
  wallets: () => request({ url: '/wallets/' }),
  updateWallet: (method, balance) => request({ url: '/wallets/', method: 'PATCH', data: { method, balance } }),
  // 家庭
  family: () => request({ url: '/family/' }),
  createFamily: (name) => request({ url: '/family/', method: 'POST', data: { name } }),
  joinFamily: (code) => request({ url: '/family/join/', method: 'POST', data: { code } }),
  leaveFamily: () => request({ url: '/family/leave/', method: 'POST' }),
  // 周期账单
  recurring: () => request({ url: '/recurring/' }),
  createRecurring: (data) => request({ url: '/recurring/', method: 'POST', data }),
  updateRecurring: (id, data) => request({ url: `/recurring/${id}/`, method: 'PATCH', data }),
  deleteRecurring: (id) => request({ url: `/recurring/${id}/`, method: 'DELETE' }),
  generateRecurring: () => request({ url: '/recurring/generate/', method: 'POST' }),
}
