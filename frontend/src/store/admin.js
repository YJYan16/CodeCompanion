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
          question_id: g.questionId,
          language: g.language,
          code: g.code,
          overall_score: g.overall_score,
          summary: g.summary,
          deductions: g.deductions || [],
          class: className,
          submitted_at: g.submittedAt,
          source: 'student'
        })
      })
    } catch (error) {
      console.error('加载成绩失败:', error)
    }
  },

  async loadQuestions() {
    try {
      const { data } = await api.get('/questions')
      console.log('API /questions response:', data)
      if (data.questions) {
        console.log('Questions data before mapping:', data.questions)
        this.questions = data.questions.map((q) => {
          const mapped = {
            id: q.id || q.question_id,  // 兼容后端返回的question_id字段
            title: q.title,
            description: q.description,
            languages: ['python', 'java'],
            rubrics: q.rubrics,
            python: {
              description: q.python?.description || q.description,
              rubrics: q.python?.rubrics || q.rubrics,
              template: q.python?.template || '',
              practices: [],
            },
            java: {
              description: q.java?.description || q.description,
              rubrics: q.java?.rubrics || q.rubrics,
              template: q.java?.template || '',
              practices: [],
            },
          }
          console.log('Mapped question:', mapped.id, mapped.title)
          return mapped
        })
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
    const params = {
      title: question.title,
      description: question.description || '',
      languages: question.languages || ['python', 'java'],
      python_template: question.python?.template || '',
      python_description: question.python?.description || '',
      python_rubrics: question.python?.rubrics || '',
      java_template: question.java?.template || '',
      java_description: question.java?.description || '',
      java_rubrics: question.java?.rubrics || '',
      rubrics: question.rubrics || question.python?.rubrics || '',
      difficulty: question.difficulty || '简单',
    }
    if (question.id) {
      params.question_id = question.id
    }
    const response = await api.post('/questions', null, { params })
    console.log('添加题目成功，返回的question_id:', response.data.question_id)
    await this.loadQuestions()
    return response.data.question_id
  },

  async deleteQuestion(id) {
    await api.delete(`/questions/${id}`)
    await this.loadQuestions()
  },

  async updateQuestion(question) {
    console.log('========== updateQuestion 开始 ==========')
    console.log('question:', JSON.stringify(question, null, 2))
    console.log('question.id:', question?.id, 'type:', typeof question?.id)
    console.log('Boolean(question?.id):', Boolean(question?.id))
    console.log('question.python?.template:', question.python?.template)
    console.log('question.java?.template:', question.java?.template)
    
    if (!question?.id || question?.id === '') {
      console.error('❌ 题目ID不能为空，无法更新题目')
      alert('题目ID不能为空，请刷新页面重试')
      return
    }
    
    const params = {
      title: question.title,
      description: question.description || '',
      languages: question.languages || ['python', 'java'],
      python_template: question.python?.template || '',
      python_description: question.python?.description || '',
      python_rubrics: question.python?.rubrics || '',
      java_template: question.java?.template || '',
      java_description: question.java?.description || '',
      java_rubrics: question.java?.rubrics || '',
      rubrics: question.rubrics || question.python?.rubrics || '',
      difficulty: question.difficulty || '简单',
    }
    
    console.log('发送的 params:', JSON.stringify(params, null, 2))
    console.log('python_template length:', params.python_template?.length)
    console.log('java_template length:', params.java_template?.length)
    
    try {
      const response = await api.put(`/questions/${question.id}`, undefined, { params })
      console.log('API 响应:', response.data)
    } catch (error) {
      console.error('API 错误:', error)
      console.error('API 错误响应:', error.response?.data)
    }
    
    await this.loadQuestions()
    console.log('========== updateQuestion 结束 ==========')
  },

  get reports() {
    if (!this.allReports[this.currentClass]) this.allReports[this.currentClass] = []
    return this.allReports[this.currentClass]
  },

  async addReport(report) {
    try {
      await api.post('/grades', {
        user_id: report.user_id || report.userId,
        user_name: report.user_name || report.userName || report.student_name || '',
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
    } else if (event === 'question_updated' || event === 'question_created') {
      console.log('题目更新事件收到:', event, data)
      this.handleQuestionUpdate(data)
    } else if (event === 'question_deleted') {
      console.log('题目删除事件收到:', event, data)
      this.questions = this.questions.filter(q => q.id !== data.question_id)
    }
  },

  handleQuestionUpdate(data) {
    const questionIndex = this.questions.findIndex(q => q.id === data.question_id)
    if (questionIndex !== -1) {
      this.questions[questionIndex] = {
        ...this.questions[questionIndex],
        title: data.title,
        python: {
          ...this.questions[questionIndex].python,
          template: data.python_template || '',
          description: data.python_description || '',
        },
        java: {
          ...this.questions[questionIndex].java,
          template: data.java_template || '',
          description: data.java_description || '',
        },
      }
      console.log('题目已更新:', this.questions[questionIndex])
    } else {
      console.log('未找到对应题目，将重新加载所有题目')
      this.loadQuestions()
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
