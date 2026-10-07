import { defineStore } from 'pinia'
import { login as loginApi, getMe } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('ff_token') || '',
    user: JSON.parse(localStorage.getItem('ff_user') || 'null'),
  }),
  getters: {
    isAdmin: (s) => s.user?.role === 'admin',
  },
  actions: {
    async login(form) {
      const res = await loginApi(form)
      this.token = res.data.access
      this.user = res.data.user
      localStorage.setItem('ff_token', this.token)
      localStorage.setItem('ff_user', JSON.stringify(this.user))
      if (this.user.role !== 'admin') {
        this.logout()
        throw new Error('仅管理员可登录管理后台')
      }
    },
    async fetchMe() {
      const res = await getMe()
      this.user = res.data
      localStorage.setItem('ff_user', JSON.stringify(this.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('ff_token')
      localStorage.removeItem('ff_user')
    },
  },
})
