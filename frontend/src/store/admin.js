import { reactive } from 'vue'

// 默认班级数据
const defaultClasses = ['默认班级']

// 默认学生数据
const defaultStudents = [
  { userId: '2024001', name: '张三', class: '默认班级' },
  { userId: '2024002', name: '李四', class: '默认班级' },
  { userId: '2024003', name: '王五', class: '默认班级' },
]

// 默认题目数据
const defaultQuestions = [
  {
    id: 'q1',
    title: '找最大值',
    description: '编写函数，接收整数列表/数组，返回最大值。不能使用内置排序/max函数。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 find_max(numbers)，接收整数列表，返回最大值。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `# 题目：找最大值\ndef find_max(numbers):\n    pass`,
      practices: []
    },
    java: {
      description: '编写 findMax 方法，接收整数数组，返回最大值。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `// 找最大值 (Java)\npublic class Main {\n    public static int findMax(int[] numbers) {\n        return 0;\n    }\n}`,
      practices: []
    }
  }
]

const adminStore = reactive({
  classes: defaultClasses,
  currentClass: '默认班级',
  allReports: { '默认班级': [] },
  questions: [],
  students: defaultStudents,
  grades: [],

  init() {
    const saved = localStorage.getItem('admin_classes')
    if (saved) {
      const data = JSON.parse(saved)
      this.classes = data.classes || defaultClasses
      this.currentClass = data.currentClass || '默认班级'
      this.allReports = data.allReports || { '默认班级': [] }
      this.students = data.students || defaultStudents
    } else {
      this.allReports = { '默认班级': [] }
    }
    this.loadStudentReports()
    this.loadQuestions()
  },

  loadStudentReports() {
    const savedReports = localStorage.getItem('admin_reports')
    if (savedReports) {
      const reports = JSON.parse(savedReports)
      reports.forEach(r => {
        const className = r.class || '默认班级'
        if (!this.allReports[className]) this.allReports[className] = []
        if (!this.allReports[className].find(report => report.id === r.id)) {
          this.allReports[className].push(r)
        }
      })
    }
    this.saveToStorage()
  },

  async loadQuestions() {
    try {
      const response = await fetch('http://localhost:8001/api/questions')
      const result = await response.json()
      if (result.questions) {
        const questionMap = {}
        result.questions.forEach(q => {
          questionMap[q.id] = {
            ...q,
            languages: ['python', 'java'],
            python: {
              description: q.description,
              rubrics: q.rubrics,
              template: q.python
            },
            java: {
              description: q.description,
              rubrics: q.rubrics,
              template: q.java
            }
          }
        })
        this.questions = Object.values(questionMap)
        this.saveQuestions()
        return
      }
    } catch (error) {
      console.error('从API加载题目失败:', error)
    }
    
    const saved = localStorage.getItem('admin_questions')
    if (saved) {
      this.questions = JSON.parse(saved)
    } else {
      this.questions = JSON.parse(JSON.stringify(defaultQuestions))
      this.saveQuestions()
    }
  },

  getQuestionsForStudent() {
    const result = {}
    this.questions.forEach(q => {
      result[q.id] = q
    })
    return result
  },

  getQuestionById(id) {
    return this.questions.find(q => q.id === id)
  },

  addQuestion(question) {
    const defaultPython = { description: '', rubrics: '', template: '', practices: [] }
    const defaultJava = { description: '', rubrics: '', template: '', practices: [] }
    
    if (!question.python) question.python = { ...defaultPython }
    if (!question.java) question.java = { ...defaultJava }
    if (!question.python.practices) question.python.practices = []
    if (!question.java.practices) question.java.practices = []
    if (!question.description) question.description = question.python.description || ''
    
    const idx = this.questions.findIndex(q => q.id === question.id)
    if (idx >= 0) this.questions[idx] = question
    else this.questions.push(question)
    this.saveQuestions()
  },

  deleteQuestion(id) {
    this.questions = this.questions.filter(q => q.id !== id)
    this.saveQuestions()
  },

  saveQuestions() {
    try { localStorage.setItem('admin_questions', JSON.stringify(this.questions)) } catch (e) {}
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

  addGrade(gradeData) {
    this.grades.push({
      ...gradeData,
      id: Date.now(),
      submittedAt: gradeData.submittedAt || new Date().toLocaleString()
    })
    localStorage.setItem('adminGrades', JSON.stringify(this.grades))
  },

  getGrades() {
    const saved = localStorage.getItem('adminGrades')
    if (saved) {
      this.grades = JSON.parse(saved)
    }
    return this.grades
  },

  clearGrades() {
    this.grades = []
    localStorage.removeItem('adminGrades')
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
  },

  getStats() {
    const reports = this.reports
    const stats = {
      total: reports.length,
      averageScore: 0,
      passed: 0,
      failed: 0,
      questionStats: {},
      studentStats: {}
    }

    if (reports.length === 0) return stats

    let totalScore = 0
    reports.forEach(r => {
      const score = r.overall_score || 0
      totalScore += score
      
      if (score >= 60) stats.passed++
      else stats.failed++

      const q = r.question || '未知'
      if (!stats.questionStats[q]) {
        stats.questionStats[q] = { total: 0, sum: 0, count: 0 }
      }
      stats.questionStats[q].total += score
      stats.questionStats[q].count++

      const student = r.student_name || r.userId || '未知'
      if (!stats.studentStats[student]) {
        stats.studentStats[student] = { total: 0, count: 0, best: 0 }
      }
      stats.studentStats[student].total += score
      stats.studentStats[student].count++
      if (score > stats.studentStats[student].best) {
        stats.studentStats[student].best = score
      }
    })

    stats.averageScore = Math.round(totalScore / reports.length * 10) / 10

    Object.keys(stats.questionStats).forEach(q => {
      stats.questionStats[q].avg = Math.round(stats.questionStats[q].total / stats.questionStats[q].count * 10) / 10
    })

    Object.keys(stats.studentStats).forEach(s => {
      stats.studentStats[s].avg = Math.round(stats.studentStats[s].total / stats.studentStats[s].count * 10) / 10
    })

    return stats
  }
})

// 初始化
adminStore.init()

export function useAdminStore() {
  return adminStore
}