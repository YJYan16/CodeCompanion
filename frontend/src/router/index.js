import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '@/store/auth.js'
import { Document } from '@element-plus/icons-vue'

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
      { path: 'sandbox', name: 'AdminSandbox', component: () => import('../views/admin/AdminSandbox.vue') },
      { path: 'lesson-plan', name: 'AdminLessonPlan', component: () => import('../views/admin/AdminLessonPlan.vue') },
      { path: 'students', name: 'AdminStudents', component: () => import('../views/admin/AdminStudents.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

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

  // ★ 教师端路由需要管理员权限
  if (to.path.startsWith('/admin')) {
    if (!isLoggedIn) {
      next('/login')
    } else if (authStore.role !== 'admin') {
      // 如果当前登录的不是管理员，跳转到登录页让用户重新登录
      authStore.logout()
      next('/login')
    } else {
      next()
    }
    return
  }

  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
    return
  }

  next()
})

export default router