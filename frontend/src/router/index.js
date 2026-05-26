import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '@/store/auth.js'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue')
  },
  {
    path: '/',
    name: 'Student',
    component: () => import('../views/StudentView.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/profile',
    name: 'StudentProfile',
    component: () => import('../views/StudentProfile.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/admin',
    component: () => import('../views/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      { path: '', redirect: '/admin/questions' },
      { path: 'questions', name: 'AdminQuestions', component: () => import('../views/admin/AdminQuestions.vue') },
      { path: 'batch', name: 'AdminBatchGrade', component: () => import('../views/admin/AdminBatchGrade.vue') },
      { path: 'reports', name: 'AdminReports', component: () => import('../views/admin/AdminReports.vue') },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('../views/admin/AdminDashboard.vue') },
      { path: 'plagiarism', name: 'AdminPlagiarism', component: () => import('../views/admin/AdminPlagiarism.vue') },
      { path: 'knowledge', name: 'AdminKnowledge', component: () => import('../views/admin/AdminKnowledge.vue') },
      { path: 'sandbox', name: 'AdminSandbox', component: () => import('../views/admin/AdminSandbox.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = authStore.checkLogin()

  if (to.path === '/login') {
    if (isLoggedIn) {
      next(authStore.role === 'admin' ? '/admin' : '/')
    } else {
      next()
    }
    return
  }

  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
    return
  }

  if (to.meta.role && isLoggedIn && authStore.role !== to.meta.role) {
    next(authStore.role === 'admin' ? '/admin' : '/')
    return
  }

  next()
})

export default router