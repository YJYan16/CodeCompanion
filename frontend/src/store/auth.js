import { reactive } from 'vue'
import api from '@/api/client.js'

const authStore = reactive({
  isLoggedIn: false,
  token: '',
  userId: '',
  dbUserId: null,
  role: '',
  name: '',
  className: '',

  async login(username, password) {
    try {
      const { data } = await api.post('/login', { username, password })
      if (data.success && data.token) {
        this.isLoggedIn = true
        this.token = data.token
        this.userId = data.user.username
        this.dbUserId = data.user.id
        this.role = data.user.role
        this.name = data.user.name
        this.className = data.user.class_name || '默认班级'
        sessionStorage.setItem('auth_token', data.token)
        sessionStorage.setItem('auth_user', JSON.stringify(data.user))
        return { success: true, role: data.user.role }
      }
      return { success: false, role: '' }
    } catch {
      return { success: false, role: '' }
    }
  },

  logout() {
    this.isLoggedIn = false
    this.token = ''
    this.userId = ''
    this.dbUserId = null
    this.role = ''
    this.name = ''
    this.className = ''
    sessionStorage.removeItem('auth_token')
    sessionStorage.removeItem('auth_user')
  },

  async checkLogin() {
    const token = sessionStorage.getItem('auth_token')
    const savedUser = sessionStorage.getItem('auth_user')
    if (!token || !savedUser) {
      return false
    }

    this.token = token
    const user = JSON.parse(savedUser)
    this.isLoggedIn = true
    this.userId = user.username
    this.dbUserId = user.id
    this.role = user.role
    this.name = user.name
    this.className = user.class_name || '默认班级'

    try {
      const { data } = await api.get('/me')
      this.dbUserId = data.id
      this.name = data.name
      this.className = data.class_name || '默认班级'
      sessionStorage.setItem('auth_user', JSON.stringify(data))
      return true
    } catch {
      this.logout()
      return false
    }
  },
})

export function useAuthStore() {
  return authStore
}

export { authStore }
