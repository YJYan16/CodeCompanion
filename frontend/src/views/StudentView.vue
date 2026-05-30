<template>
  <div class="student-container">
    <!-- 页面加载骨架屏 -->
    <SkeletonLoader v-if="pageLoading" />

    <template v-else>
      <el-header>
        <div class="header-content">
          <div class="header-left">
            <h1>🤖 码途智伴</h1>
          </div>
          <div class="header-right">
            <el-tooltip effect="dark" placement="bottom">
              <template #content>
                <div>学号: {{ authStore.userId }}</div>
                <div>班级: {{ authStore.className }}</div>
              </template>
              <span class="header-name">{{ authStore.name }}</span>
            </el-tooltip>
            <el-button @click="$router.push('/profile')" class="profile-btn" size="small">📊 档案</el-button>
            <el-button @click="handleLogout" type="danger" link size="small">退出</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <el-row :gutter="20">
        <!-- 左侧 -->
        <el-col :xs="24" :lg="12" class="left-col">
          <el-card header="📝 提交作业">
            <!-- 离线模式指示器 -->
            <div class="offline-indicator" :class="{ active: offlineMode }">
              <span class="indicator-icon">📴</span>
              <span>{{ offlineMode ? '离线模式' : '在线模式' }}</span>
              <el-switch v-model="offlineMode" @change="toggleOfflineMode" />
              <el-tooltip effect="dark" placement="top">
                <template #content>
                  <div v-if="ollamaStatus.connected" style="color: green;">✓ Ollama服务已连接</div>
                  <div v-else style="color: red;">✗ {{ ollamaStatus.error }}</div>
                  <div v-if="ollamaStatus.model_available" style="color: green;">✓ {{ ollamaStatus.model_name }}</div>
                  <div v-else-if="ollamaStatus.connected" style="color: orange;">⚠️ 模型未下载</div>
                  <div v-if="ollamaStatus.suggestion" style="font-size: 12px; margin-top: 4px;">{{ ollamaStatus.suggestion }}</div>
                </template>
                <el-button size="mini" @click="refreshOllamaStatus">🔄</el-button>
              </el-tooltip>
            </div>
            
            <!-- 推荐练习模式指示器 -->
            <div class="practice-indicator" :class="{ active: isPracticeMode }">
              <span class="indicator-icon">🎯</span>
              <span>{{ isPracticeMode ? '推荐练习模式' : '普通作业模式' }}</span>
              <el-switch :model-value="isPracticeMode" @update:model-value="togglePracticeMode" />
            </div>
            
            <!-- 练习模式内容区域（显示在标注之下） -->
            <div v-if="isPracticeMode" class="practice-content-area">
              <div class="practice-title-section">
                <h4 class="practice-section-title">📖 练习内容</h4>
                <el-divider class="practice-divider" />
              </div>
              
              <!-- 练习描述 -->
              <div class="practice-description-box">
                <el-textarea 
                  v-model="currentPracticeDescription" 
                  :rows="4" 
                  :readonly="true"
                  class="practice-description"
                  placeholder="练习题目要求..."
                ></el-textarea>
              </div>
              
              <!-- 练习目标 -->
              <div v-if="currentPractice?.detail" class="practice-objective">
                <div class="objective-label">🎯 练习目标</div>
                <div class="objective-content">{{ currentPractice.detail }}</div>
              </div>
              
              <!-- 一键填充按钮 -->
              <div class="practice-action">
                <el-button type="primary" size="small" @click="fillTemplate" class="fill-btn">
                  📋 一键填充代码模板                </el-button>
              </div>
            </div>
            
            <el-form label-width="60px" class="submit-form">
              <el-form-item label="题目">
                <el-select v-model="selectedQuestion" placeholder="请选择题目">
                  <el-option v-for="key in Object.keys(questionBank)" :key="key" :label="questionBank[key].title" :value="key" />
                </el-select>
              </el-form-item>
              <el-form-item label="语言">
                <el-select v-model="language" placeholder="选择语言" class="full-width">
                  <el-option label="Python" value="python" />
                  <el-option label="Java" value="java" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="代码">
                <div class="editor-wrapper">
                  <div style="width:100%;max-width:100%;overflow:hidden;">
                    <CodeEditor v-if="editorReady" v-model="code" :language="language" />
                    <div v-else class="editor-placeholder">加载中...</div>
                  </div>
                  
                  <!-- 无模板提示（直接填充到编辑器） -->
                  <div v-if="showNoTemplateHint && !isPracticeMode && !code.trim()" class="floating-hint">
                    <span class="hint-icon">📝</span>
                    <span class="hint-text"># 该题目没有模板，请自行编写完整代码</span>
                    <span class="hint-close" @click="showNoTemplateHint = false">×</span>
                  </div>
                </div>
                <div v-if="lastSavedTime" class="auto-save-status">
                  <span>✓ 自动保存 {{ lastSavedTime }}</span>
                </div>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="submitGrade" :loading="loading" class="submit-btn">
                  🚀 {{ isPracticeMode ? '开始练习' : '提交批改' }}
                </el-button>
                <el-button type="success" @click="runCode" :loading="running" class="run-btn" style="margin-left: 10px;">
                  ▶️ 运行代码
                </el-button>
              </el-form-item>
            </el-form>
            
            <!-- 代码运行结果区域 -->
            <el-card v-if="showOutput" header="💻 运行结果">
              <div class="output-container">
                <div v-if="running" class="running-indicator">
                  <el-icon class="is-loading" :size="24"><Loading /></el-icon>
                  <span>正在运行...</span>
                </div>
                <div v-else>
                  <div v-if="runResult.success" class="output-success">
                    <pre class="output-text">{{ runResult.output }}</pre>
                  </div>
                  <div v-else class="output-error">
                    <pre class="error-text">{{ runResult.error }}</pre>
                  </div>
                </div>
              </div>
            </el-card>
          </el-card>
        </el-col>

        <!-- 右侧 -->
        <el-col :xs="24" :lg="12" class="right-col">
          <el-card header="📊 批改报告">
            <div v-if="loading">
              <el-skeleton :rows="8" animated />
            </div>
            <GradeReport v-if="report" :report="report" :stream-content="streamContent" @ask="openTutor" />

            <!-- 提交至教师按钮（练习模式下不显示） -->
            <div v-if="report && !report.streaming && !isPracticeMode" class="submit-to-teacher">
              <el-button type="success" @click="submitToTeacher" :loading="submitting" class="teacher-btn">
                📮 提交至教师              </el-button>
              <span class="submit-hint">将最终版本提交给教师查看</span>
            </div>
            
            <!-- 练习模式提示 -->
            <div v-if="isPracticeMode && report && !report.streaming" class="practice-mode-hint">
              <el-tag type="info" size="medium">💡 练习模式 - 批改结果仅保存到个人档案，不会提交给教师</el-tag>
            </div>

            <div v-if="!report && !loading" class="placeholder-text">等待提交代码...</div>

            <WeakKnowledgeCard :knowledge-points="weakKnowledge" />

            <LearningPath :steps="learningPath" :active-step="0" @start-step="handleStartStep" />

            <!-- 推荐练习区域 -->
            <div v-if="practiceList.length > 0" class="practice-area">
              <el-divider />
              <h3>🎯 推荐练习</h3>
              <div 
                v-for="(p, i) in practiceList" 
                :key="i" 
                class="practice-item"
                :class="{ active: currentPractice?.description === p.description }"
                @click="startPractice(p)"
              >
                <div class="practice-info">
                  <div class="practice-header">
                    <span class="practice-badge">练习{{ i+1 }}</span>
                    <span class="difficulty-badge" :class="'level-' + p.difficulty">
                      {{ p.difficulty === 1 ? '简单' : p.difficulty === 2 ? '中等' : '困难' }}
                    </span>
                  </div>
                  <strong class="practice-title">{{ p.description }}</strong>
                  <p v-if="p.detail" class="practice-detail">{{ p.detail }}</p>
                </div>
                <el-button size="small" type="primary" @click.stop="startPractice(p)" :loading="practiceLoading">
                  {{ practiceLoading ? '加载中...' : '开始' }}
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <TutorChat v-model="showTutor" :report-json="reportJson" :student-code="code" />
      </el-main>
    </template>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import CodeEditor from '@/components/CodeEditor.vue'
import GradeReport from '@/components/GradeReport.vue'
import TutorChat from '@/components/TutorChat.vue'
import WeakKnowledgeCard from '@/components/WeakKnowledgeCard.vue'
import LearningPath from '@/components/LearningPath.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'

import { useAuthStore } from '@/store/auth'
import { useAdminStore } from '@/store/admin'

const authStore = useAuthStore()
const adminStore = useAdminStore()

// 页面状态
const pageLoading = ref(true)
const loading = ref(false)
const running = ref(false)
const submitting = ref(false)
const practiceLoading = ref(false)
const editorReady = ref(true)  // ★ 初始为 true
const showNoTemplateHint = ref(false)

// 表单数据
const selectedQuestion = ref('')
const language = ref('python')
const code = ref('')
const lastSavedTime = ref('')
const autoSaveTimer = ref(null)

// 报告数据
const report = ref(null)
const reportJson = ref('{}')
const streamContent = ref('')
const runResult = ref({ success: false, output: '', error: '' })
const showOutput = ref(false)

// 练习模式
const isPracticeMode = ref(false)
const currentPractice = ref(null)
const currentPracticeDescription = ref('')
const originalCode = ref('')
const isProgrammaticChange = ref(false)

// 学习数据
const weakKnowledge = ref([])
const learningPath = ref([])
const practiceList = ref([])
const showTutor = ref(false)

// 题目库
const questionBank = ref({})

// 离线模式
const offlineMode = ref(false)
const ollamaStatus = ref({
  connected: false,
  model_available: false,
  model_name: '',
  error: null,
  suggestion: ''
})

// 获取当前题目的模板
const getCurrentPractices = () => {
  const q = questionBank[selectedQuestion.value]
  if (!q) return []
  
  const lang = language.value === 'java' ? 'java' : 'python'
  const langData = q[lang]
  
  if (!langData) return []
  
  // ★ practices 可能是数组、undefined 或不存在
  const practices = langData.practices
  if (Array.isArray(practices)) return practices
  
  // 如果有 template，生成默认练习
  if (langData.template) {
    return [{
      description: `巩固练习：${q.title}`,
      difficulty: 1,
      questionId: selectedQuestion.value,
      template: langData.template
    }]
  }
  
  return []
}
// 获取当前题目的模板
const getCurrentTemplate = () => {
  const q = questionBank[selectedQuestion.value]
  if (!q) return ''
  const lang = language.value === 'java' ? 'java' : 'python'
  const langData = q[lang]
  if (langData && langData.template) return langData.template
  if (q.template) return q.template
  return ''
}

// 检测当前题目是否有模板
const hasTemplate = () => {
  const template = getCurrentTemplate()
  return template && template.trim().length > 0
}

// 获取当前题目的描述
const getCurrentDescription = () => {
  const currentQ = questionBank[selectedQuestion.value]
  return currentQ?.description || ''
}


// 填充代码模板
const fillTemplate = () => {
  if (isPracticeMode.value && currentPractice.value?.template) {
    code.value = currentPractice.value.template
  } else {
    code.value = getCurrentTemplate()
  }
}

// 加载题目列表
const loadQuestions = async () => {
  try {
    const res = await fetch('/api/questions')
    const data = await res.json()
    if (data.questions && data.questions.length > 0) {
      // 清空旧数据
      Object.keys(questionBank).forEach(k => delete questionBank[k])
      
      data.questions.forEach(q => {
        questionBank[q.id] = {
          title: q.title || '',
          description: q.python?.description || q.description || '',
          rubrics: q.python?.rubrics || q.rubrics || '',
          python: {
            template: q.python?.template || '',
            description: q.python?.description || '',
            rubrics: q.python?.rubrics || '',
            practices: []
          },
          java: {
            template: q.java?.template || '',
            description: q.java?.description || '',
            rubrics: q.java?.rubrics || '',
            practices: []
          }
        }
      })
      
      console.log('✅ 从后端加载题目成功，共', Object.keys(questionBank).length, '道')
      console.log('题目列表:', Object.keys(questionBank))
      return true
    }
  } catch (e) {
    console.error('从后端加载题目失败:', e)
  }
  
  // 后端失败，从 localStorage 兜底
  const saved = localStorage.getItem('admin_questions')
  if (saved) {
    try {
      const questions = JSON.parse(saved)
      questions.forEach(q => {
        questionBank[q.id] = {
          title: q.title,
          description: q.description || '',
          rubrics: q.rubrics || '',
          python: q.python || { template: '', practices: [] },
          java: q.java || { template: '', practices: [] }
        }
      })
      console.log('从 localStorage 加载题目成功')
      return true
    } catch (e) {}
  }
  return false
}
  

// 提交批改（SSE 流式）
const submitGrade = async () => {
  if (!selectedQuestion.value) {
    alert('请先选择题目')
    return
  }
  if (!language.value) {
    alert('请先选择语言')
    return
  }
  if (!code.value.trim()) {
    alert('请先输入代码')
    return
  }

  if (loading.value) {
    return
  }

  const currentQ = questionBank[selectedQuestion.value]
  const langKey = language.value === 'java' ? 'java' : 'python'
  const questionText = currentQ?.description || currentQ?.title || ''
  const rubrics = currentQ?.[langKey]?.rubrics || currentQ?.rubrics || ''

  if (loading.value) {
    return
  }

  loading.value = true
  report.value = { overall_score: 0, summary: '', deductions: [], streaming: true }
  streamContent.value = ''

  const controller = new AbortController()

  try {
    const response = await fetch('/api/grade/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        code: code.value,
        language: language.value,
        question: questionText,
        rubrics,
      }),
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let streamComplete = false

    while (!streamComplete) {
      try {
        const { done, value } = await reader.read()
        if (done) {
          streamComplete = true
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') {
            streamComplete = true
            loading.value = false
            break
          }
          try {
            const msg = JSON.parse(data)
            if (msg.type === 'review' || msg.type === 'content') {
              streamContent.value += msg.content
            } else if (msg.type === 'diagnosis') {
              streamContent.value += `\n${msg.content}\n`
            } else if (msg.type === 'result') {
              report.value = { ...msg.data, summary: streamContent.value || msg.data.summary, streaming: false }
              reportJson.value = JSON.stringify({ ...msg.data, summary: streamContent.value || msg.data.summary })
              generateKnowledgeAndPractices({ ...msg.data, summary: streamContent.value || msg.data.summary })
              saveToTeacherStore({ ...msg.data, summary: streamContent.value || msg.data.summary })
              loading.value = false
              streamComplete = true
              break
            } else if (msg.type === 'error') {
              report.value = { overall_score: 0, summary: msg.content || '批改出错', deductions: [], streaming: false }
              loading.value = false
              streamComplete = true
              break
            }
          } catch (e) {
            console.warn('SSE消息解析失败:', e)
          }
        }
      } catch (readErr) {
        if (readErr.name === 'AbortError') {
          console.log('请求已被取消')
          streamComplete = true
          break
        }
        throw readErr
      }
    }
    loading.value = false
  } catch (err) {
    console.error('批改请求失败:', err)
    report.value = { overall_score: 0, summary: '请求失败: ' + err.message, deductions: [], streaming: false }
    loading.value = false
  } finally {
    controller.abort()
  }
}

// 保存到教师端存储（自动提交到后端数据库）
const saveToTeacherStore = async (data) => {
  try {
    const response = await fetch('/api/grades', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        user_id: authStore.dbUserId,
        user_name: authStore.name,
        question_id: selectedQuestion.value,
        code: code.value,
        language: language.value,
        overall_score: parseFloat(data.overall_score) || 0,
        summary: data.summary || '',
        deductions: data.deductions || [],
        class_name: authStore.className,
      }),
    })
    
    if (!response.ok) {
      console.error('自动保存成绩失败:', response.statusText)
    }
  } catch (error) {
    console.error('自动保存成绩失败:', error)
  }
}

// 提交至教师
const submitToTeacher = async () => {
  if (!report.value) return

  submitting.value = true

  try {
    await fetch('/api/grades', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        user_id: authStore.dbUserId,
        user_name: authStore.name,
        question_id: selectedQuestion.value,
        code: code.value,
        language: language.value,
        overall_score: parseFloat(report.value.overall_score) || 0,
        summary: report.value.summary || '',
        deductions: report.value.deductions || [],
        class_name: authStore.className,
      }),
    })

    alert('已成功提交给教师！')
  } catch (error) {
    console.error('提交失败:', error)
    alert('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 自动保存代码到后端
const autoSaveCode = async () => {
  if (!code.value.trim() || !selectedQuestion.value || !authStore.token) return

  try {
    await fetch('/api/drafts', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        question_id: selectedQuestion.value,
        code: code.value,
        language: language.value,
      }),
    })
    lastSavedTime.value = new Date().toLocaleTimeString()
  } catch (e) {
    console.error('自动保存失败:', e)
  }
}

// 加载自动保存的代码
const loadAutoSaveCode = async () => {
  if (!selectedQuestion.value || !authStore.token) return
  try {
    const response = await fetch(`/api/drafts/${selectedQuestion.value}`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    const result = await response.json()
    if (result.draft) {
      code.value = result.draft.code
      language.value = result.draft.language
    }
  } catch (e) {
    console.error('加载自动保存代码失败:', e)
  }
}

// 更新编辑器
const updateEditor = () => {
  // ★ 确保 selectedQuestion 有值
  if (!selectedQuestion.value || !questionBank[selectedQuestion.value]) {
    const firstKey = Object.keys(questionBank)[0]
    if (firstKey) {
      selectedQuestion.value = firstKey
    }
  }
  
  const template = getCurrentTemplate()
  if (template) {
    code.value = template
  }
  
  practiceList.value = getCurrentPractices()
  report.value = null
  reportJson.value = '{}'
  weakKnowledge.value = []
  learningPath.value = []
  
  editorReady.value = false
  nextTick(() => {
    editorReady.value = true
  })
}

// 监听题目变化
watch(selectedQuestion, async (newVal, oldVal) => {
  report.value = null
  reportJson.value = '{}'
  streamContent.value = ''

  if (isPracticeMode.value && currentPractice.value) {
    const currentQ = questionBank[newVal]
    if (currentQ) {
      const lang = language.value === 'java' ? 'java' : 'python'
      currentPractice.value.template = currentQ[lang]?.template || ''
      currentPracticeDescription.value = currentQ.description || ''
      currentPractice.value.detail = currentQ.description || ''
      code.value = currentPractice.value.template
    }
  } else {
    // 普通模式：加载自动保存的代码，没有则使用模板
    if (!isProgrammaticChange.value) {
      await loadAutoSaveCode()
      if (!code.value.trim()) {
        const template = getCurrentTemplate()
        if (template && template.trim()) {
          code.value = template
          showNoTemplateHint.value = false
        } else {
          code.value = '# 该题目没有模板，请自行编写完整代码'
          showNoTemplateHint.value = true
        }
      } else {
        showNoTemplateHint.value = false
      }
    }
  }
  updateEditor()
})

// 监听语言变化
watch(language, async (newVal, oldVal) => {
  if (isPracticeMode.value && currentPractice.value) {
    const currentQ = questionBank[selectedQuestion.value]
    if (currentQ) {
      currentPractice.value.template = currentQ[newVal]?.template || ''
      code.value = currentPractice.value.template
    }
  } else {
    // 普通模式：尝试加载该语言的自动保存代码
    if (!isProgrammaticChange.value) {
      const savedCode = await getLangAutoSaveCode(newVal)
      if (savedCode) {
        code.value = savedCode
        showNoTemplateHint.value = false
      } else {
        const template = getCurrentTemplate()
        if (template && template.trim()) {
          code.value = template
          showNoTemplateHint.value = false
        } else {
          code.value = '# 该题目没有模板，请自行编写完整代码'
          showNoTemplateHint.value = true
        }
      }
    }
  }
  updateEditor()
})

// 获取指定语言的自动保存代码
const getLangAutoSaveCode = async (lang) => {
  if (!selectedQuestion.value || !authStore.token) return null
  try {
    const response = await fetch(`/api/drafts/${selectedQuestion.value}`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    const result = await response.json()
    if (result.draft && result.draft.language === lang) {
      return result.draft.code
    }
  } catch (e) {
    console.error('加载自动保存代码失败:', e)
  }
  return null
}

// 代码变化时触发自动保存
const handleCodeChange = () => {
  if (autoSaveTimer.value) {
    clearTimeout(autoSaveTimer.value)
  }
  autoSaveTimer.value = setTimeout(() => {
    autoSaveCode()
  }, 2000)
}

// 监听代码变化，触发自动保存
watch(code, (newCode) => {
  // 用户开始输入时隐藏无模板提示
  if (newCode && newCode.trim().length > 0) {
    showNoTemplateHint.value = false
  }
  handleCodeChange()
})

const handleLogout = () => {
  authStore.logout()
  window.location.href = '/login'
}

// 切换练习模式
const togglePracticeMode = (newValue) => {
  if (!newValue) {
    // 退出练习模式，恢复到练习前的状态
    
    // 0. 设置模式标志为false
    isPracticeMode.value = false
    
    // 1. 清除所有练习模式相关的数据
    currentPractice.value = null
    currentPracticeDescription.value = ''
    practiceList.value = []
    weakKnowledge.value = []
    learningPath.value = []
    
    // 2. 清除练习模式的批改报告
    report.value = null
    reportJson.value = '{}'
    streamContent.value = ''
    
    // 3. 恢复代码到练习前的状态
    if (originalCode.value && originalCode.value.trim()) {
      code.value = originalCode.value
      originalCode.value = ''
    } else {
      // 如果没有保存的代码，恢复到当前题目的模板
      code.value = getCurrentTemplate()
    }
    
    // 4. 检查当前题目是否有模板
    showNoTemplateHint.value = !hasTemplate()
    
    // 5. 强制刷新编辑器
    editorReady.value = false
    nextTick(() => {
      editorReady.value = true
      // 显示提示信息
      alert('已退出练习模式，代码已恢复到练习前的状态')
    })
  } else {
    // 进入练习模式
    if (!selectedQuestion.value) {
      alert('请先选择题目')
      isPracticeMode.value = false
      return
    }

    // 保存当前代码状态
    if (code.value && code.value.trim()) {
      originalCode.value = code.value
    } else {
      originalCode.value = getCurrentTemplate()
    }

    isPracticeMode.value = true
    const currentQ = questionBank[selectedQuestion.value]
    if (currentQ) {
      currentPracticeDescription.value = currentQ.description || ''
      currentPractice.value = {
        description: currentQ.title,
        detail: currentQ.description,
        template: getCurrentTemplate(),
        questionId: selectedQuestion.value
      }
      code.value = currentPractice.value.template
    }
    
    editorReady.value = false
    nextTick(() => {
      editorReady.value = true
      alert('已进入练习模式，原代码已保存，退出时将自动恢复')
    })
  }
}

// 运行代码
const runCode = async () => {
  if (!selectedQuestion.value) {
    alert('请先选择题目')
    return
  }
  if (!language.value) {
    alert('请先选择语言')
    return
  }
  if (!code.value.trim()) {
    alert('请先输入代码')
    return
  }
  
  running.value = true
  showOutput.value = true
  runResult.value = { success: false, output: '', error: '' }
  
  try {
    const response = await fetch('/api/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        code: code.value,
        language: language.value
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      runResult.value = {
        success: true,
        output: result.output || '运行成功，无输出',
        error: ''
      }
    } else {
      runResult.value = {
        success: false,
        output: '',
        error: result.error || '运行失败'
      }
    }
  } catch (error) {
    runResult.value = {
      success: false,
      output: '',
      error: '网络错误: ' + error.message
    }
  } finally {
    running.value = false
  }
}

// 快捷键处理
const handleKeydown = (e) => {
  if (e.ctrlKey || e.metaKey) {
    if (e.key === 'Enter') {
      e.preventDefault()
      submitGrade()
    } else if (e.key === 'r' || e.key === 'R') {
      e.preventDefault()
      runCode()
    }
  }
}

onMounted(async () => {
  await loadQuestions()
  
  // 确保有默认选中
  if (!selectedQuestion.value) {
    selectedQuestion.value = Object.keys(questionBank)[0] || 'q1'
  }
  
  // 直接设置模板
  const template = getCurrentTemplate()
  if (template) {
    code.value = template
  }
  
  editorReady.value = true
  pageLoading.value = false
})

// 监听adminStore题目变化，同步更新学生端
watch(
  () => adminStore.questions,
  () => {
    loadQuestions()
  },
  { deep: true }
)

// 检查Ollama状态
const checkOllamaStatus = async () => {
  try {
    const response = await fetch('/api/ollama/status')
    const status = await response.json()
    ollamaStatus.value = status
  } catch (error) {
    ollamaStatus.value = {
      connected: false,
      model_available: false,
      model_name: '',
      error: '无法连接到后端服务',
      suggestion: ''
    }
  }
}

// 切换离线模式
const toggleOfflineMode = async (value) => {
  if (value) {
    // 切换到离线模式前检查Ollama状态
    await checkOllamaStatus()
    
    if (!ollamaStatus.value.connected) {
      alert(`无法切换到离线模式：${ollamaStatus.value.error}\n\n${ollamaStatus.value.suggestion}`)
      offlineMode.value = false
      return
    }
    
    if (!ollamaStatus.value.model_available) {
      alert(`模型未准备好！${ollamaStatus.value.suggestion}`)
      offlineMode.value = false
      return
    }
    
    // 发送切换请求    
    try {
      await fetch('/api/model/toggle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ use_local: true })
      })
      offlineMode.value = true
      alert('已切换到离线模式！批改将使用本地Qwen2.5-7B模型。')
    } catch (error) {
      alert('切换失败，请重试')
      offlineMode.value = false
    }
  } else {
    // 切换到在线模式    
    try {
      await fetch('/api/model/toggle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ use_local: false })
      })
      offlineMode.value = false
      alert('已切换到在线模式！批改将使用云端智谱AI模型。')
    } catch (error) {
      alert('切换失败，请重试')
      offlineMode.value = true
    }
  }
}

// 刷新Ollama状态
const refreshOllamaStatus = () => {
  checkOllamaStatus()
}

// 根据薄弱知识点生成针对性练习
const generatePracticeTemplate = (weakPoint, language) => {
  const templates = {
    '边界条件处理': {
      python: `# ============================================
# 专项练习：边界条件处理# ============================================
# 练习目标：掌握常见的边界情况处理
# 薄弱点：${weakPoint}
# ============================================

def process_data(data):
    """
    处理输入数据，返回处理后的结果列表    
    参数:
        data (list): 输入的整数列表        
    返回:
        list: 处理后的列表
        
    注意: 需要处理以下边界情况
    1. data 为空列表 []
    2. data 为 None
    3. data 包含负数或零
    4. data 包含重复元素
    """
    
    # ========== 请在此处填写代码 ==========
    # 初始化结果列表
    result = []
    
    # 处理边界情况
    if data is None:
        return result
    
    # 遍历输入数据
    seen = set()
    for num in data:
        # 跳过负数和零
        if num <= 0:
            continue
        # 跳过重复元素
        if num in seen:
            continue
        seen.add(num)
        result.append(num)
    
    return result
    # ========== 代码填写结束 ==========

# ============================================
# 测试用例（无需修改）
# ============================================
test_cases = [
    [],                           # 空列表 -> []
    None,                         # None -> []
    [1, 2, 3, 4, 5],              # 正常情况 -> [1, 2, 3, 4, 5]
    [-1, 0, 1, -2, 2],           # 包含负数和零 -> [1, 2]
    [1, 1, 2, 2, 3, 3],          # 包含重复元素 -> [1, 2, 3]
]

print("测试结果:")
for tc in test_cases:
    result = process_data(tc)
    print(f"输入: {tc} -> 输出: {result}")`,
      java: `// ============================================
// 专项练习：边界条件处理
// ============================================
// 练习目标：掌握常见的边界情况处理
// 薄弱点：${weakPoint}
// ============================================

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

public class BoundaryPractice {
    
    /**
     * 处理输入数据，返回处理后的结果列表
     * 
     * @param data 输入的整数数组（可能为null）
     * @return 处理后的列表，只包含正数且无重复
     */
    public static List<Integer> processData(Integer[] data) {
        // ========== 请在此处填写代码 ==========
        List<Integer> result = new ArrayList<>();
        
        // 处理边界情况
        if (data == null) {
            return result;
        }
        
        HashSet<Integer> seen = new HashSet<>();
        for (Integer num : data) {
            // 跳过负数、零和null
            if (num == null || num <= 0) {
                continue;
            }
            // 跳过重复元素
            if (seen.contains(num)) {
                continue;
            }
            seen.add(num);
            result.add(num);
        }
        
        return result;
        // ========== 代码填写结束 ==========
    }
    
    // ============================================
    // 测试用例（无需修改）
    // ============================================
    public static void main(String[] args) {
        Integer[][] testCases = {
            {},                          // 空数组 -> []
            null,                        // null -> []
            {1, 2, 3, 4, 5},             // 正常情况 -> [1, 2, 3, 4, 5]
            {-1, 0, 1, -2, 2},          // 包含负数和零 -> [1, 2]
            {1, 1, 2, 2, 3, 3},         // 包含重复元素 -> [1, 2, 3]
        };
        
        System.out.println("测试结果:");
        for (Integer[] tc : testCases) {
            List<Integer> result = processData(tc);
            System.out.println("输入: " + java.util.Arrays.toString(tc) + " -> 输出: " + result);
        }
    }
}`
    },
    '循环逻辑': {
      python: `# ============================================
# 专项练习：循环逻辑优化
# ============================================
# 练习目标：掌握高效的循环实现方式
# 薄弱点：${weakPoint}
# ============================================

def efficient_loop(items):
    """
    高效遍历列表，同时完成多个计算任务
    
    参数:
        items (list): 输入的整数列表
        
    返回:
        tuple: (偶数和, 最大奇数, 负数个数)
    """
    # 初始化变量
    even_sum = 0      # 所有偶数的和
    max_odd = None    # 最大的奇数
    negative_count = 0 # 负数的个数
    
    # ========== 请在此处填写代码 ==========
    # 遍历列表，一次循环完成所有计算
    for num in items:
        # 判断是否为偶数
        if num % 2 == 0:
            even_sum += num
        # 判断是否为奇数
        if num % 2 != 0:
            # 更新最大奇数
            if max_odd is None or num > max_odd:
                max_odd = num
        # 判断是否为负数
        if num < 0:
            negative_count += 1
    # ========== 代码填写结束 ==========
    
    return even_sum, max_odd, negative_count

# ============================================
# 测试用例（无需修改）
# ============================================
test_list = [1, 2, -3, 4, -5, 6, 7, -8, 9]
even_sum, max_odd, negative_count = efficient_loop(test_list)
print(f"偶数和: {even_sum} (期望: 2+4+6+(-8) = 4)")
print(f"最大奇数: {max_odd} (期望: 9)")
print(f"负数个数: {negative_count} (期望: 3)")`,
      java: `// ============================================
// 专项练习：循环逻辑优化
// ============================================
// 练习目标：掌握高效的循环实现方式
// 薄弱点：${weakPoint}
// ============================================

public class LoopPractice {
    
    /**
     * 高效遍历数组，同时完成多个计算任务
     * 
     * @param items 输入的整数数组
     * @return int[]: [偶数和, 最大奇数, 负数个数]
     */
    public static int[] efficientLoop(int[] items) {
        // 初始化变量
        int evenSum = 0;       // 所有偶数的和
        Integer maxOdd = null; // 最大的奇数
        int negativeCount = 0; // 负数的个数
        
        // ========== 请在此处填写代码 ==========
        // 遍历数组，一次循环完成所有计算
        for (int num : items) {
            // 判断是否为偶数
            if (num % 2 == 0) {
                evenSum += num;
            }
            // 判断是否为奇数
            if (num % 2 != 0) {
                // 更新最大奇数
                if (maxOdd == null || num > maxOdd) {
                    maxOdd = num;
                }
            }
            // 判断是否为负数
            if (num < 0) {
                negativeCount++;
            }
        }
        // ========== 代码填写结束 ==========
        
        int maxOddValue = maxOdd != null ? maxOdd : 0;
        return new int[]{evenSum, maxOddValue, negativeCount};
    }
    
    // ============================================
    // 测试用例（无需修改）
    // ============================================
    public static void main(String[] args) {
        int[] testArray = {1, 2, -3, 4, -5, 6, 7, -8, 9};
        int[] result = efficientLoop(testArray);
        
        System.out.println("输入数组: " + java.util.Arrays.toString(testArray));
        System.out.println("偶数和: " + result[0] + " (期望: 4)");
        System.out.println("最大奇数: " + result[1] + " (期望: 9)");
        System.out.println("负数个数: " + result[2] + " (期望: 3)");
    }
}`
    },
    '代码规范': {
      python: `# ============================================
# 专项练习：代码规范
# ============================================
# 练习目标：编写符合Python编码规范的代码
# 薄弱点：${weakPoint}
# ============================================

# TODO: 重构以下代码使其符合Python编码规范
# 要求:
# 1. 变量命名使用蛇形命名法(snake_case)
# 2. 添加适当的注释和文档字符串
# 3. 保持适当的空行
# 4. 函数参数格式正确
# 5. 代码块缩进统一

# ========== 请在此处填写重构后的代码 ==========
def calculate_sum(a, b, c):
    """
    计算三个数的和或积差
    
    参数:
        a (int): 第一个整数
        b (int): 第二个整数
        c (int): 第三个整数
        
    返回:
        int: 如果 a > b 返回 a+b+c，否则返回 a*b - c
    """
    if a > b:
        return a + b + c
    else:
        product = a * b
        return product - c
# ========== 代码填写结束 ==========

# ============================================
# 测试用例（无需修改）
# ============================================
print("测试结果:")
print(f"calculate_sum(1, 2, 3) = {calculate_sum(1, 2, 3)} (期望: 1*2-3 = -1)")
print(f"calculate_sum(5, 2, 3) = {calculate_sum(5, 2, 3)} (期望: 5+2+3 = 10)")`,
      java: `// ============================================
// 专项练习：代码规范
// ============================================
// 练习目标：编写符合Java编码规范的代码
// 薄弱点：${weakPoint}
// ============================================

// TODO: 重构以下代码使其符合Java编码规范
// 要求:
// 1. 变量命名使用驼峰命名法(camelCase)
// 2. 添加适当的注释和文档注释
// 3. 保持适当的空行
// 4. 代码块格式正确
// 5. 大括号位置规范
public class CodeStylePractice {
    
    /**
     * 计算三个数的和或积差
     * 
     * @param a 第一个整数
     * @param b 第二个整数
     * @param c 第三个整数
     * @return 如果 a > b 返回 a+b+c，否则返回 a*b - c
     */
    // ========== 请在此处填写重构后的代码 ==========
    public static int calculateSum(int a, int b, int c) {
        if (a > b) {
            return a + b + c;
        } else {
            int product = a * b;
            return product - c;
        }
    }
    // ========== 代码填写结束 ==========
    
    // ============================================
    // 测试用例（无需修改）
    // ============================================
    public static void main(String[] args) {
        System.out.println("测试结果:");
        System.out.println("calculateSum(1, 2, 3) = " + calculateSum(1, 2, 3) 
            + " (期望: 1*2-3 = -1)");
        System.out.println("calculateSum(5, 2, 3) = " + calculateSum(5, 2, 3) 
            + " (期望: 5+2+3 = 10)");
    }
}`
    },
    '算法效率': {
      python: `# ============================================
# 专项练习：算法效率优化
# ============================================
# 练习目标：掌握时间复杂度优化技术
# 薄弱点：${weakPoint}
# ============================================

def find_duplicates(nums):
    """
    找出列表中的重复元素
    
    参数:
        nums (list): 输入的整数列表
        
    返回:
        list: 重复元素组成的列表
        
    优化目标:
        当前朴素实现的时间复杂度为 O(n^2)
        请优化为 O(n) 时间复杂度
    """
    # ========== 请在此处填写优化后的代码 ==========
    # 使用集合实现 O(n) 时间复杂度
    seen = set()
    duplicates = set()
    
    for num in nums:
        if num in seen:
            duplicates.add(num)
        else:
            seen.add(num)
    
    return list(duplicates)
    # ========== 代码填写结束 ==========

# ============================================
# 测试用例（无需修改）
# ============================================
test_list = [1, 2, 3, 2, 1, 5, 6, 5, 5, 5]
result = find_duplicates(test_list)

print(f"输入列表: {test_list}")
print(f"重复元素: {result} (期望: [1, 2, 5])")`,
      java: `// ============================================
// 专项练习：算法效率优化
// ============================================
// 练习目标：掌握时间复杂度优化技术
// 薄弱点：${weakPoint}
// ============================================

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

public class EfficiencyPractice {
    
    /**
     * 找出数组中的重复元素
     * 
     * @param nums 输入的整数数组
     * @return 重复元素组成的列表
     * 
     * 优化目标:
     *     当前朴素实现的时间复杂度为 O(n^2)
     *     请优化为 O(n) 时间复杂度
     */
    public static List<Integer> findDuplicates(int[] nums) {
        // ========== 请在此处填写优化后的代码 ==========
        // 使用 HashSet 实现 O(n) 时间复杂度
        HashSet<Integer> seen = new HashSet<>();
        HashSet<Integer> duplicates = new HashSet<>();
        
        for (int num : nums) {
            if (seen.contains(num)) {
                duplicates.add(num);
            } else {
                seen.add(num);
            }
        }
        
        return new ArrayList<>(duplicates);
        // ========== 代码填写结束 ==========
    }
    
    // ============================================
    // 测试用例（无需修改）
    // ============================================
    public static void main(String[] args) {
        int[] testNums = {1, 2, 3, 2, 1, 5, 6, 5, 5, 5};
        List<Integer> result = findDuplicates(testNums);
        
        System.out.println("输入数组: " + java.util.Arrays.toString(testNums));
        System.out.println("重复元素: " + result + " (期望: [1, 2, 5])");
    }
}`
    },
    '函数设计': {
      python: `# ============================================
# 专项练习：函数设计
# ============================================
# 练习目标：掌握良好的函数设计原则
# 薄弱点：${weakPoint}
# ============================================

def calculate_stats(data):
    """
    计算列表的统计信息
    
    参数:
        data (list): 数字列表
        
    返回:
        dict: 包含统计信息的字典，包含以下键:
            - count: 元素个数
            - sum: 总和
            - average: 平均值
            - max: 最大值
            - min: 最小值
            - range: 极差（最大值减最小值）
    """
    
    # ========== 请在此处填写代码 ==========
    # 处理边界情况
    if not data:
        return {
            'count': 0,
            'sum': 0,
            'average': 0.0,
            'max': None,
            'min': None,
            'range': 0
        }
    
    # 计算统计信息
    count = len(data)
    total_sum = sum(data)
    average = total_sum / count
    max_val = max(data)
    min_val = min(data)
    range_val = max_val - min_val
    
    return {
        'count': count,
        'sum': total_sum,
        'average': round(average, 2),
        'max': max_val,
        'min': min_val,
        'range': range_val
    }
    # ========== 代码填写结束 ==========

# ============================================
# 测试用例（无需修改）
# ============================================
test_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
stats = calculate_stats(test_data)

print("统计结果:")
for key, value in stats.items():
    print(f"  {key}: {value}")`,
      java: `// ============================================
// 专项练习：函数设计
// ============================================
// 练习目标：掌握良好的函数设计原则
// 薄弱点：${weakPoint}
// ============================================

import java.util.HashMap;
import java.util.Map;

public class FunctionDesignPractice {
    
    /**
     * 计算数组的统计信息
     * 
     * @param data 数字数组
     * @return Map 包含统计信息:
     *     - count: 元素个数
     *     - sum: 总和
     *     - average: 平均值
     *     - max: 最大值
     *     - min: 最小值
     *     - range: 极差
     */
    public static Map<String, Object> calculateStats(int[] data) {
        Map<String, Object> stats = new HashMap<>();
        
        // ========== 请在此处填写代码 ==========
        // 处理边界情况
        if (data == null || data.length == 0) {
            stats.put("count", 0);
            stats.put("sum", 0);
            stats.put("average", 0.0);
            stats.put("max", null);
            stats.put("min", null);
            stats.put("range", 0);
            return stats;
        }
        
        // 计算统计信息
        int count = data.length;
        int sum = 0;
        int max = data[0];
        int min = data[0];
        
        for (int num : data) {
            sum += num;
            if (num > max) max = num;
            if (num < min) min = num;
        }
        
        double average = (double) sum / count;
        int range = max - min;
        
        stats.put("count", count);
        stats.put("sum", sum);
        stats.put("average", Math.round(average * 100.0) / 100.0);
        stats.put("max", max);
        stats.put("min", min);
        stats.put("range", range);
        
        return stats;
        // ========== 代码填写结束 ==========
    }
    
    // ============================================
    // 测试用例（无需修改）
    // ============================================
    public static void main(String[] args) {
        int[] testData = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
        Map<String, Object> stats = calculateStats(testData);
        
        System.out.println("统计结果:");
        for (Map.Entry<String, Object> entry : stats.entrySet()) {
            System.out.println("  " + entry.getKey() + ": " + entry.getValue());
        }
    }
}`
    },
    '逻辑错误': {
      python: `# ============================================
# 专项练习：调试与逻辑纠错
# ============================================
# 练习目标：学会识别和修复逻辑错误
# 薄弱点：${weakPoint}
# ============================================

def find_missing_number(nums):
    """
    找出 0 到 n 之间缺失的数字
    数组包含 n 个不同的数字，范围在 [0, n] 之间
    
    参数:
        nums (list): 输入的整数列表
        
    返回:
        int: 缺失的数字
    """
    n = len(nums)
    
    # 计算 0 到 n 的和（高斯公式）
    total = n * (n + 1) // 2
    
    # 计算数组中所有元素的和
    sum_nums = sum(nums)
    
    # ========== 找出并修复逻辑错误 ==========
    # 错误分析: 当前返回 sum_nums - total，但正确应该是 total - sum_nums
    # 因为 total 是 0..n 的完整和，sum_nums 是缺少一个数的和
    # 所以缺失的数字 = total - sum_nums
    return total - sum_nums
    # ========== 修复结束 ==========

# ============================================
# 测试用例（无需修改）
# ============================================
test_cases = [
    [3, 0, 1],      # 应返回 2
    [0, 1],         # 应返回 2
    [9,6,4,2,3,5,7,0,1],  # 应返回 8
    [0]             # 应返回 1
]

print("测试结果:")
for tc in test_cases:
    result = find_missing_number(tc)
    print(f"输入: {tc} -> 缺失: {result}")`,
      java: `// ============================================
// 专项练习：调试与逻辑纠错
// ============================================
// 练习目标：学会识别和修复逻辑错误
// 薄弱点：${weakPoint}
// ============================================

public class LogicFixPractice {
    
    /**
     * 找出 0 到 n 之间缺失的数字
     * 数组包含 n 个不同的数字，范围在 [0, n] 之间
     * 
     * @param nums 输入的整数数组
     * @return 缺失的数字
     */
    public static int findMissingNumber(int[] nums) {
        int n = nums.length;
        
        // 计算 0 到 n 的和（高斯公式）
        int total = n * (n + 1) / 2;
        
        // 计算数组中所有元素的和
        int sumNums = 0;
        for (int num : nums) {
            sumNums += num;
        }
        
        // ========== 找出并修复逻辑错误 ==========
        // 错误分析: 当前返回 sumNums - total，但正确应该是 total - sumNums
        // 因为 total 是 0..n 的完整和，sumNums 是缺少一个数的和
        // 所以缺失的数字 = total - sumNums
        return total - sumNums;
        // ========== 修复结束 ==========
    }
    
    // ============================================
    // 测试用例（无需修改）
    // ============================================
    public static void main(String[] args) {
        int[][] testCases = {
            {3, 0, 1},                    // 应返回 2
            {0, 1},                       // 应返回 2
            {9, 6, 4, 2, 3, 5, 7, 0, 1},  // 应返回 8
            {0}                           // 应返回 1
        };
        
        System.out.println("测试结果:");
        for (int[] tc : testCases) {
            int result = findMissingNumber(tc);
            System.out.println("输入: " + java.util.Arrays.toString(tc) + " -> 缺失: " + result);
        }
    }
}`
    }
  }
  
  const lang = language === 'java' ? 'java' : 'python'
  return templates[weakPoint]?.[lang] || generateDefaultPractice(language)
}

// 生成默认练习模板
const generateDefaultPractice = (language) => {
  if (language === 'java') {
    return `// 巩固练习
// 练习目标：复习当前知识点

public class Practice {
    public static void main(String[] args) {
        // 在此编写你的练习代码
        System.out.println("开始练习...");
    }
}`
  } else {
    return `# 巩固练习
# 练习目标：复习当前知识点

def practice():
    # 在此编写你的练习代码
    print("开始练习...")

if __name__ == "__main__":
    practice()`
  }
}

const generateKnowledgeAndPractices = (evaluationData) => {
  const deductions = evaluationData.deductions || []
  
  weakKnowledge.value = deductions.map(d => ({
    name: d.type,
    explanation: `${d.reason}\n\n改进建议: ${d.suggestion}`,
    common_mistake: d.reason
  }))
  
  // 根据薄弱知识点生成有针对性的练习
  const newPractices = deductions.map((d, index) => ({
    description: `练习${index + 1}：${d.type}专项训练`,
    detail: d.reason,
    difficulty: Math.min(d.severity || 1, 3),
    questionId: selectedQuestion.value,
    template: generatePracticeTemplate(d.type, language.value)
  }))
  
  // 如果没有扣分，生成巩固练习
  if (newPractices.length === 0) {
    newPractices.push({
      description: '巩固练习：复习当前知识点',
      detail: '完成当前题目的巩固练习',
      difficulty: 1,
      questionId: selectedQuestion.value,
      template: generateDefaultPractice(language.value)
    })
  }
  
  // 添加题目库中预定义的练习作为补充
  const predefinedPractices = getCurrentPractices()
  practiceList.value = [...newPractices, ...predefinedPractices]
  
  const weakPoints = deductions.map(d => d.type)
  if (weakPoints.length > 0) {
    fetch('/api/learning-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weak_points: weakPoints, language: language.value })
    }).then(r => r.json()).then(data => {
      learningPath.value = data.path || []
    }).catch(() => {})
  }
}

const openTutor = () => { showTutor.value = true }

// 开始练习
const startPractice = (practice) => {
  if (!practice || practiceLoading.value) return
  
  practiceLoading.value = true
  
  setTimeout(() => {
    try {
      originalCode.value = code.value
      
      isProgrammaticChange.value = true
      isPracticeMode.value = true
      currentPractice.value = practice
      currentPracticeDescription.value = practice.description || getCurrentDescription()
      
      if (practice.template) {
        code.value = practice.template
      }
      
      if (practice.questionId) {
        selectedQuestion.value = practice.questionId
      }
      
      isProgrammaticChange.value = false
      
      showTutor.value = false
      report.value = null
      reportJson.value = '{}'
      streamContent.value = ''
      
      window.scrollTo({ top: 0, behavior: 'smooth' })
      
      nextTick(() => {
        alert('已进入推荐练习模式！\n\n练习内容已填充到编辑器，可以开始练习。\n批改结果将保存到个人档案，但不会提交给教师。')
      })
    } finally {
      practiceLoading.value = false
    }
  }, 300)
}

const handleStartStep = (step) => {
  code.value = `# 学习任务：${step.name}
# ${step.desc}
# 推荐资源：${step.resource}

def practice():
    pass`
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped>
.student-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 20px;
  box-shadow: 0 2px 15px rgba(102,126,234,0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left h1 {
  color: #fff;
  font-size: 20px;
  margin: 0;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-name {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.profile-btn {
  color: #fff !important;
  background: rgba(255,255,255,0.2) !important;
  border: 1px solid rgba(255,255,255,0.5) !important;
  font-weight: 600;
}
.profile-btn:hover {
  background: rgba(255,255,255,0.35) !important;
}

.el-main {
  padding: 20px;
  overflow: hidden;
}

.el-row {
  margin: 0 !important;
  display: flex;
  flex-wrap: wrap;
}

.left-col, .right-col {
  margin-bottom: 16px;
  height: calc(100vh - 96px);
  overflow-y: auto;
  overflow-x: hidden;
}

.left-col::-webkit-scrollbar,
.right-col::-webkit-scrollbar {
  width: 8px;
}

.left-col::-webkit-scrollbar-track,
.right-col::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.left-col::-webkit-scrollbar-thumb,
.right-col::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.left-col::-webkit-scrollbar-thumb:hover,
.right-col::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.left-col .el-card,
.right-col .el-card {
  width: 100%;
  min-width: 0;
}

.full-width {
  width: 100%;
}

.submit-btn {
  width: 100%;
}

.run-btn {
  width: 120px;
}

.editor-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border: 1px dashed #ccc;
  color: #999;
}

.practice-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.practice-indicator.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.indicator-icon {
  font-size: 18px;
}

.practice-content-area {
  background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.practice-title-section {
  margin-bottom: 12px;
}

.practice-section-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #856404;
}

.practice-divider {
  margin: 0 !important;
}

.practice-description-box {
  margin-bottom: 12px;
}

.practice-description {
  background: #fff !important;
  border: 1px solid #ffeeba !important;
}

.practice-objective {
  margin-bottom: 12px;
  padding: 10px;
  background: rgba(255, 235, 59, 0.2);
  border-radius: 6px;
}

.objective-label {
  font-weight: 600;
  color: #856404;
  margin-bottom: 4px;
}

.objective-content {
  font-size: 13px;
  color: #856404;
}

.practice-action {
  display: flex;
  justify-content: flex-end;
}

.fill-btn {
  background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
  border: none;
}

.fill-btn:hover {
  background: linear-gradient(135deg, #ffb300 0%, #f57c00 100%);
}

.output-container {
  min-height: 100px;
}

.running-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: #667eea;
}

.output-success {
  background: #e8f5e9;
  padding: 15px;
  border-radius: 6px;
}

.output-error {
  background: #ffebee;
  padding: 15px;
  border-radius: 6px;
}

.output-text, .error-text {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  margin: 0;
}

.error-text {
  color: #c62828;
}

.editor-wrapper {
  position: relative;
}

.floating-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
  border: 1px solid #ff9800;
  border-radius: 12px;
  padding: 16px 24px;
  color: #e65100;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 20px rgba(255, 152, 0, 0.3);
  z-index: 10;
  animation: fadeInUp 0.3s ease-in-out;
}

.floating-hint .hint-icon {
  font-size: 20px;
}

.floating-hint .hint-text {
  font-weight: 500;
}

.floating-hint .hint-close {
  margin-left: 12px;
  font-size: 20px;
  cursor: pointer;
  color: #ff9800;
  transition: color 0.2s;
}

.floating-hint .hint-close:hover {
  color: #e65100;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translate(-50%, -40%); }
  to { opacity: 1; transform: translate(-50%, -50%); }
}

.auto-save-status {
  font-size: 12px;
  color: #66bb6a;
  margin-top: 8px;
  text-align: right;
}

.submit-to-teacher {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 10px;
}

.teacher-btn {
  width: 100%;
}

.submit-hint {
  font-size: 12px;
  color: #999;
}

.practice-mode-hint {
  margin-top: 16px;
}

.placeholder-text {
  text-align: center;
  padding: 40px;
  color: #999;
}

.practice-area {
  margin-top: 16px;
}

.practice-area h3 {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
}

.practice-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.practice-item:hover {
  background: #e9ecef;
}

.practice-item.active {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-color: #2196f3;
}

.practice-info {
  flex: 1;
  margin-right: 12px;
}

.practice-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.practice-badge {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: #667eea;
  padding: 2px 8px;
  border-radius: 10px;
}

.difficulty-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
}

.difficulty-badge.level-1 {
  background: #c8e6c9;
  color: #2e7d32;
}

.difficulty-badge.level-2 {
  background: #ffecb3;
  color: #f57c00;
}

.difficulty-badge.level-3 {
  background: #ffcdd2;
  color: #c62828;
}

.practice-title {
  font-size: 14px;
  color: #333;
}

.practice-detail {
  font-size: 12px;
  color: #666;
  margin: 4px 0 0 0;
}
</style>

