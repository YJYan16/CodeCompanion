import { reactive } from 'vue'

const presetUsers = {
  '2024001': { password: '123456', role: 'student', name: '张三', class: '默认班级' },
  '2024002': { password: '123456', role: 'student', name: '李四', class: '默认班级' },
  '2024003': { password: '123456', role: 'student', name: '王五', class: '默认班级' },
  'admin': { password: 'admin123', role: 'admin', name: '管理员', class: '' },
}

const authStore = reactive({
  isLoggedIn: false,
  userId: '',
  role: '',
  name: '',
  className: '',

  login(userId, password) {
    const userInfo = presetUsers[userId]
    if (userInfo && userInfo.password === password) {
      this.isLoggedIn = true
      this.userId = userId
      this.role = userInfo.role
      this.name = userInfo.name
      this.className = userInfo.class
      localStorage.setItem('auth', JSON.stringify({
        userId: userId,
        role: userInfo.role,
        name: userInfo.name,
        className: userInfo.class
      }))
      return { success: true, role: userInfo.role }
    }
    return { success: false, role: '' }
  },

  logout() {
    this.isLoggedIn = false
    this.userId = ''
    this.role = ''
    this.name = ''
    this.className = ''
    localStorage.removeItem('auth')
  },

  checkLogin() {
    const saved = localStorage.getItem('auth')
    if (saved) {
      const data = JSON.parse(saved)
      this.isLoggedIn = true
      this.userId = data.userId
      this.role = data.role
      this.name = data.name || data.userId
      this.className = data.className || '默认班级'
      return true
    }
    return false
  }
})

export function useAuthStore() {
  return authStore
}

export { authStore }