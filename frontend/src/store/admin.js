import { reactive } from 'vue'
import api from '@/api/client.js'

const defaultClasses = ['默认班级']

const adminStore = reactive({
  classes: [...defaultClasses],
  currentClass: '默认班级',
  allReports: { '默认班级': [] },
  questions: [],
  students: [],
  grades: [],
  loading: false,

  async init() {
    this.loading = true
    try {
      await Promise.all([
        this.loadClasses(),
        this.loadStudents(),
        this.loadQuestions(),
        this.loadGrades(),
      ])
    } finally {
      this.loading = false
    }
  },

  async loadClasses() {
    try {
      const { data } = await api.get('/classes')
      const names = (data.classes || []).map((c) => c.name)
      if (names.length) {
        this.classes = names
        if (!this.classes.includes(this.currentClass)) {
          this.currentClass = this.classes[0]
        }
      }
    } catch (error) {
      console.error('加载班级失败:', error)
    }
  },

  async loadStudents() {
    try {
      const { data } = await api.get('/users')
      this.students = (data.users || [])
        .filter((u) => u.role === 'student')
        .map((u) => ({
          userId: u.username,
          name: u.name,
          class: u.class_name || '默认班级',
          dbId: u.id,
        }))
    } catch (error) {
      console.error('加载学生失败:', error)
    }
  },

  async loadGrades() {
    try {
      const { data } = await api.get('/grades')
      this.grades = (data.grades || []).map((g) => ({
        id: g.id,
        userId: g.user_id,
        userName: g.user_name,
        questionId: g.question_id,
        question: g.question_title,
        className: g.class_name,
        code: g.code,
        language: g.language,
        overall_score: g.overall_score,
        summary: g.summary,
        deductions: g.deductions || [],
        submittedAt: g.submitted_at,
      }))

      this.allReports = {}
      this.grades.forEach((g) => {
        const className = g.className || '默认班级'
        if (!this.allReports[className]) this.allReports[className] = []
        this.allReports[className].push({
          id: g.id,
          userId: g.userId,
          student_name: g.userName,
          question: g.question,
          overall_score: g.overall_score,
          summary: g.summary,
          class: className,
          submittedAt: g.submittedAt,
        })
      })
    } catch (error) {
      console.error('加载成绩失败:', error)
    }
  },

  async loadQuestions() {
    try {
      const { data } = await api.get('/questions')
      if (data.questions) {
        this.questions = data.questions.map((q) => ({
          id: q.id,
          title: q.title,
          description: q.description,
          languages: ['python', 'java'],
          rubrics: q.rubrics,
          python: {
            description: q.description,
            rubrics: q.rubrics,
            template: q.python?.template || '',
            practices: [],
          },
          java: {
            description: q.description,
            rubrics: q.rubrics,
            template: q.java?.template || '',
            practices: [],
          },
        }))
      }
    } catch (error) {
      console.error('加载题目失败:', error)
    }
  },

  getQuestionsForStudent() {
    const result = {}
    this.questions.forEach((q) => {
      result[q.id] = q
    })
    return result
  },

  getQuestionById(id) {
    return this.questions.find((q) => q.id === id)
  },

  async addQuestion(question) {
    await api.post('/questions', null, {
      params: {
        question_id: question.id,
        title: question.title,
        description: question.description || '',
        python_template: question.python?.template || '',
        java_template: question.java?.template || '',
        rubrics: question.python?.rubrics || question.rubrics || '',
        difficulty: question.difficulty || '简单',
      },
    })
    await this.loadQuestions()
  },

  async deleteQuestion(id) {
    await api.delete(`/questions/${id}`)
    await this.loadQuestions()
  },

  get reports() {
    if (!this.allReports[this.currentClass]) this.allReports[this.currentClass] = []
    return this.allReports[this.currentClass]
  },

  async addReport(report) {
    try {
      await api.post('/grades', {
        user_id: report.user_id || report.userId,
        question_id: report.question_id || report.questionId,
        code: report.code || '',
        language: report.language || 'python',
        overall_score: report.overall_score || 0,
        summary: report.summary || '',
        deductions: report.deductions || [],
        class_name: report.class_name || report.className || this.currentClass,
      })
      await this.loadGrades()
    } catch (error) {
      console.error('保存成绩失败:', error)
    }
  },

  async addGrade(gradeData) {
    const student = this.students.find((s) => s.userId === gradeData.userId)
    await this.addReport({
      ...gradeData,
      user_id: student?.dbId || gradeData.dbUserId,
      question_id: gradeData.questionId,
      class_name: gradeData.className || this.currentClass,
    })
  },

  getGrades() {
    return this.grades
  },

  async addClass(name) {
    if (!name || this.classes.includes(name)) return
    await api.post('/classes', null, { params: { name } })
    this.classes.push(name)
    this.allReports[name] = []
    this.currentClass = name
  },

  switchClass(name) {
    this.currentClass = name
  },

  handleRealtimeEvent(event, data) {
    if (event === 'grade_saved') {
      this.loadGrades()
    }
  },

  getStats() {
    const reports = this.reports
    const stats = {
      total: reports.length,
      averageScore: 0,
      passed: 0,
      failed: 0,
      questionStats: {},
      studentStats: {},
    }

    if (reports.length === 0) return stats

    let totalScore = 0
    reports.forEach((r) => {
      const score = r.overall_score || 0
      totalScore += score
      if (score >= 60) stats.passed++
      else stats.failed++

      const q = r.question || '未知'
      if (!stats.questionStats[q]) stats.questionStats[q] = { total: 0, count: 0 }
      stats.questionStats[q].total += score
      stats.questionStats[q].count++

      const student = r.student_name || r.userId || '未知'
      if (!stats.studentStats[student]) stats.studentStats[student] = { total: 0, count: 0, best: 0 }
      stats.studentStats[student].total += score
      stats.studentStats[student].count++
      if (score > stats.studentStats[student].best) stats.studentStats[student].best = score
    })

    stats.averageScore = Math.round((totalScore / reports.length) * 10) / 10
    Object.keys(stats.questionStats).forEach((q) => {
      stats.questionStats[q].avg = Math.round((stats.questionStats[q].total / stats.questionStats[q].count) * 10) / 10
    })
    Object.keys(stats.studentStats).forEach((s) => {
      stats.studentStats[s].avg = Math.round((stats.studentStats[s].total / stats.studentStats[s].count) * 10) / 10
    })
    return stats
  },
})

export function useAdminStore() {
  return adminStore
}

export { adminStore }
