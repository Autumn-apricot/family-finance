import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'users', name: 'Users', component: () => import('@/views/Users.vue') },
      { path: 'expenses', name: 'Expenses', component: () => import('@/views/Expenses.vue') },
      { path: 'settings', name: 'Settings', component: () => import('@/views/Settings.vue') },
      { path: 'settings/categories', name: 'Categories', component: () => import('@/views/Categories.vue') },
    ],
  },
  { path: '/403', name: 'Forbidden', component: () => import('@/views/Forbidden.vue'), meta: { public: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFound.vue'), meta: { public: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.public) return true
  if (!store.token) return '/login'
  if (!store.isAdmin) return '/403'
  return true
})

export default router
