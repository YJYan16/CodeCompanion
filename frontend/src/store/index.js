import { reactive } from 'vue'

export const adminStore = reactive({
  classes: ['默认班级'],
  currentClass: '默认班级',
  allReports: {},
  questions: [],
  students: [
    { userId: '2024001', name: '张三', class: '默认班级' },
    { userId: '2024002', name: '李四', class: '默认班级' },
    { userId: '2024003', name: '王五', class: '默认班级' },
  ],

  init() {
    const saved = localStorage.getItem('admin_classes')
    if (saved) {
      const data = JSON.parse(saved)
      this.classes = data.classes || ['默认班级']
      this.currentClass = data.currentClass || '默认班级'
      this.allReports = data.allReports || {}
      this.students = data.students || this.students
    } else {
      this.allReports = { '默认班级': [] }
    }
    this.loadStudentReports()
    this.loadQuestions()
    // ★ 不调用 saveToStorage()，避免覆盖学生端刚写入的数据
  },

  loadStudentReports() {
    // 数据已经在 init() 中从 admin_classes 加载了，无需额外操作
    // 学生端提交时直接写入 admin_classes.allReports
    this.saveToStorage()
  },

  loadQuestions() {
    const saved = localStorage.getItem('admin_questions')
    if (saved) {
      this.questions = JSON.parse(saved)
    } else {
      this.questions = [
        {
          id: 'q1', title: '找最大值', languages: ['python', 'java'],
          python: { description: '编写函数 find_max(numbers)，接收整数列表，返回最大值。', rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)' },
          java: { description: '编写 findMax 方法，接收整数数组，返回最大值。', rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)' }
        }
      ]
      this.saveQuestions()
    }
  },

  updateStudentClass(userId, newClass) {
    const student = this.students.find(s => s.userId === userId)
    if (student) {
      student.class = newClass
      this.saveToStorage()
    }
  },

  saveQuestions() {
    try { localStorage.setItem('admin_questions', JSON.stringify(this.questions)) } catch (e) {}
  },

  addQuestion(question) {
    const idx = this.questions.findIndex(q => q.id === question.id)
    if (idx >= 0) this.questions[idx] = question
    else this.questions.push(question)
    this.saveQuestions()
  },

  deleteQuestion(id) {
    this.questions = this.questions.filter(q => q.id !== id)
    this.saveQuestions()
  },

  get reports() {
    if (!this.allReports[this.currentClass]) this.allReports[this.currentClass] = []
    return this.allReports[this.currentClass]
  },

  addReport(report) {
    if (!this.allReports[this.currentClass]) this.allReports[this.currentClass] = []
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
      localStorage.setItem('admin_classes', JSON.stringify({
        classes: this.classes,
        currentClass: this.currentClass,
        allReports: this.allReports,
        students: this.students
      }))
    } catch (e) {}
  }
})

adminStore.init()