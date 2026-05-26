import { reactive } from 'vue'

export const adminStore = reactive({
  classes: ['默认班级'],
  currentClass: '默认班级',
  allReports: {},  // { 班级名: [reports] }

  init() {
    const saved = sessionStorage.getItem('admin_classes')
    if (saved) {
      const data = JSON.parse(saved)
      this.classes = data.classes || ['默认班级']
      this.currentClass = data.currentClass || '默认班级'
      this.allReports = data.allReports || {}
      if (!this.allReports[this.currentClass]) {
        this.allReports[this.currentClass] = []
      }
    } else {
      this.allReports = { '默认班级': [] }
      this.saveToStorage()
    }
  },

  get reports() {
    if (!this.allReports[this.currentClass]) {
      this.allReports[this.currentClass] = []
    }
    return this.allReports[this.currentClass]
  },

  set reports(val) {
    this.allReports[this.currentClass] = val
  },

  addReport(report) {
    if (!this.allReports[this.currentClass]) {
      this.allReports[this.currentClass] = []
    }
    this.allReports[this.currentClass].push(report)
    this.saveToStorage()
  },

  addClass(name) {
    if (!this.classes.includes(name)) {
      this.classes.push(name)
      this.allReports[name] = []
      this.saveToStorage()
    }
  },

  switchClass(name) {
    this.currentClass = name
    this.saveToStorage()
  },

  saveToStorage() {
    try {
      sessionStorage.setItem('admin_classes', JSON.stringify({
        classes: this.classes,
        currentClass: this.currentClass,
        allReports: this.allReports
      }))
    } catch (e) {}
  }
})

adminStore.init()