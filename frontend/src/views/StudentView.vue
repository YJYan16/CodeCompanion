<template>
  <div class="student-container">
    <el-header>
      <div class="header-content">
        <h1>🤖 码途智伴</h1>
        <el-button @click="$router.push('/profile')" class="profile-btn" size="small">
          📊 档案
        </el-button>
      </div>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <!-- 左侧 -->
        <el-col :xs="24" :lg="12" class="left-col">
          <el-card header="📝 提交作业">
            <el-form label-width="80px" class="submit-form">
              <el-form-item label="题目">
                <el-select v-model="selectedQuestion" placeholder="请选择题目" class="full-width">
                  <el-option label="找最大值" value="q1" />
                  <el-option label="列表去重" value="q2" />
                  <el-option label="斐波那契数列" value="q3" />
                </el-select>
              </el-form-item>
              <el-form-item label="语言">
                <el-select v-model="language" placeholder="选择语言" class="full-width">
                  <el-option label="Python" value="python" />
                  <el-option label="Java" value="java" />
                </el-select>
              </el-form-item>
              <el-form-item label="代码">
                <CodeEditor v-if="editorReady" v-model="code" :language="language" />
                <div v-else class="editor-placeholder">加载中...</div>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="submitGrade" :loading="loading" class="submit-btn">
                  🚀 提交批改
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧 -->
        <el-col :xs="24" :lg="12" class="right-col">
          <el-card header="📊 批改报告">
            <div v-if="loading">
              <el-skeleton :rows="8" animated />
            </div>
            <GradeReport v-if="report" :report="report" :stream-content="streamContent" @ask="openTutor" />
            <div v-if="!report && !loading" class="placeholder-text">等待提交代码...</div>

            <WeakKnowledgeCard :knowledge-points="weakKnowledge" />

            <LearningPath :steps="learningPath" :active-step="0" @start-step="handleStartStep" />

            <div v-if="practiceList.length > 0" class="practice-area">
              <el-divider />
              <h3>🎯 推荐练习</h3>
              <div v-for="(p, i) in practiceList" :key="i" class="practice-item" @click="startPractice(p)">
                <strong>练习{{ i+1 }}:</strong> {{ p.description }}
                <el-button size="small" type="primary">开始</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <TutorChat v-model="showTutor" :report-json="reportJson" :student-code="code" />
    </el-main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import CodeEditor from '@/components/CodeEditor.vue'
import GradeReport from '@/components/GradeReport.vue'
import TutorChat from '@/components/TutorChat.vue'
import WeakKnowledgeCard from '@/components/WeakKnowledgeCard.vue'
import LearningPath from '@/components/LearningPath.vue'

const code = ref('')
const language = ref('python')
const selectedQuestion = ref('q1')
const report = ref(null)
const reportJson = ref('{}')
const loading = ref(false)
const showTutor = ref(false)
const streamContent = ref('')
const weakKnowledge = ref([])
const practiceList = ref([])
const editorReady = ref(false)

const questionBank = {
  q1: {
    title: "找最大值",
    description: "编写函数，接收整数列表/数组，返回最大值。不能使用内置排序/max函数。",
    rubrics: "1. 逻辑正确(60分)；2. 代码规范(20分)；3. 边界处理(20分)",
    python: {
      template: `# 题目：找最大值
def find_max(numbers):
    pass`,
      practices: [
        { description: "基础练习：遍历列表找最大值", difficulty: 1, questionId: "q1", template: `def find_max(numbers):\n    max_val = numbers[0]\n    pass` }
      ]
    },
    java: {
      template: `// 找最大值 (Java)
public class Main {
    public static int findMax(int[] numbers) {
        return 0;
    }
}`,
      practices: [
        { description: "基础练习：遍历数组找最大值", difficulty: 1, questionId: "q1", template: `public class Main {\n    public static int findMax(int[] numbers) {\n        int maxVal = numbers[0];\n        return 0;\n    }\n}` }
      ]
    }
  },
  q2: {
    title: "列表去重",
    description: "编写函数，接收一个列表/数组，返回去重后的新列表/数组。",
    rubrics: "1. 逻辑正确(60分)；2. 代码规范(20分)；3. 效率(20分)",
    python: {
      template: `# 列表去重
def remove_duplicates(lst):
    pass`,
      practices: [
        { description: "基础练习：保持顺序的去重", difficulty: 1, questionId: "q2", template: `def remove_duplicates(lst):\n    result = []\n    pass` }
      ]
    },
    java: {
      template: `// 数组去重 (Java)
public class Main {
    public static int[] removeDuplicates(int[] arr) {
        return new int[0];
    }
}`,
      practices: [
        { description: "基础练习：保持顺序的去重", difficulty: 1, questionId: "q2", template: `public class Main {\n    public static int[] removeDuplicates(int[] arr) {\n        return new int[0];\n    }\n}` }
      ]
    }
  },
  q3: {
    title: "斐波那契数列",
    description: "编写函数，返回前n个斐波那契数组成的列表/数组。",
    rubrics: "1. 逻辑正确(60分)；2. 代码规范(20分)；3. 边界处理(20分)",
    python: {
      template: `# 斐波那契数列
def fibonacci(n):
    pass`,
      practices: [
        { description: "基础练习：用循环生成", difficulty: 1, questionId: "q3", template: `def fibonacci(n):\n    pass` }
      ]
    },
    java: {
      template: `// 斐波那契数列 (Java)
public class Main {
    public static int[] fibonacci(int n) {
        return new int[0];
    }
}`,
      practices: [
        { description: "基础练习：用循环生成", difficulty: 1, questionId: "q3", template: `public class Main {\n    public static int[] fibonacci(int n) {\n        return new int[0];\n    }\n}` }
      ]
    }
  }
}

const getCurrentTemplate = () => {
  const q = questionBank[selectedQuestion.value]
  if (!q) return ''
  const lang = language.value === 'java' ? 'java' : 'python'
  return q[lang]?.template || ''
}

const getCurrentPractices = () => {
  const q = questionBank[selectedQuestion.value]
  if (!q) return []
  const lang = language.value === 'java' ? 'java' : 'python'
  return q[lang]?.practices || []
}

const getCurrentDescription = () => questionBank[selectedQuestion.value]?.description || ''
const getCurrentRubrics = () => questionBank[selectedQuestion.value]?.rubrics || ''

const updateEditor = () => {
  const template = getCurrentTemplate()
  if (template) code.value = template
  practiceList.value = getCurrentPractices()
  report.value = null
  reportJson.value = '{}'
  weakKnowledge.value = []
  editorReady.value = false
  nextTick(() => { editorReady.value = true })
}

onMounted(() => updateEditor())
watch(selectedQuestion, () => updateEditor())
watch(language, () => updateEditor())

const submitGrade = async () => {
  const codeStr = String(code.value || '')
  if (!codeStr.trim()) { alert('请先输入代码'); return }
  loading.value = true
  report.value = null
  streamContent.value = ''
  reportJson.value = '{}'
  report.value = { overall_score: '...', summary: '', deductions: [], streaming: true }

  try {
    const desc = getCurrentDescription()
    const rubrics = getCurrentRubrics()
    const response = await fetch('/api/grade/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: codeStr, question: desc, rubrics, language: language.value })
    })
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    function processStream() {
      reader.read().then(({ done, value }) => {
        if (done) { loading.value = false; return }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6)
            if (jsonStr === '[DONE]') { loading.value = false; return }
            try {
              const msg = JSON.parse(jsonStr)
              if (msg.type === 'review' || msg.type === 'content') streamContent.value += msg.content
              else if (msg.type === 'result') {
                report.value = { ...msg.data, streaming: false }
                reportJson.value = JSON.stringify(msg.data)
                generateKnowledgeAndPractices(msg.data)
              } else if (msg.type === 'error') {
                report.value = { overall_score: '?', summary: '批改出错', deductions: [], streaming: false }
              }
            } catch (e) {}
          }
        }
        processStream()
      })
    }
    processStream()
  } catch (err) {
    report.value = { overall_score: '?', summary: '请求失败', deductions: [], streaming: false }
    loading.value = false
  }
}

const learningPath = ref([])

const generateKnowledgeAndPractices = (evaluationData) => {
  const deductions = evaluationData.deductions || []
  
  weakKnowledge.value = deductions.map(d => ({
    name: d.type,
    explanation: `${d.reason}\n\n改进建议: ${d.suggestion}`,
    common_mistake: d.reason
  }))
  
  practiceList.value = [{
    description: deductions.length > 0 ? `针对「${deductions[0].type}」的专项练习` : '巩固练习',
    difficulty: 1,
    questionId: selectedQuestion.value,
    template: code.value
  }]
  
  // 生成学习路径
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

const startPractice = (practice) => {
  if (!practice) return
  if (practice.template) code.value = practice.template
  if (practice.questionId) selectedQuestion.value = practice.questionId
  showTutor.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleStartStep = (step) => {
  // 将学习步骤的练习模板填入代码编辑器
  code.value = `# 学习任务：${step.name}
# ${step.desc}
# 推荐资源：${step.resource}

def practice():
    # 在这里练习
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

.header-content h1 {
  color: #fff;
  font-size: 20px;
  margin: 0;
  font-weight: 600;
}

.profile-btn {
  color: #fff !important;
  border-color: rgba(255,255,255,0.5) !important;
}

.el-main {
  padding: 20px;
}

.el-row {
  margin: 0 !important;
}

.left-col, .right-col {
  margin-bottom: 16px;
}

.full-width {
  width: 100%;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.placeholder-text {
  color: #b0b0b0;
  text-align: center;
  margin-top: 80px;
  font-size: 15px;
}

.editor-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b0b0b0;
  border: 2px dashed #d0d0d0;
  border-radius: 12px;
}

.practice-area {
  margin-top: 12px;
}
.practice-item {
  margin: 8px 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.left-col, .right-col {
  height: calc(100vh - 96px);
  overflow-y: auto;
  padding-right: 8px;
}

.left-col::-webkit-scrollbar,
.right-col::-webkit-scrollbar {
  width: 6px;
}

.left-col::-webkit-scrollbar-thumb,
.right-col::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
}

.left-col::-webkit-scrollbar-track,
.right-col::-webkit-scrollbar-track {
  background: transparent;
}

/* ========== 移动端适配 ========== */
@media screen and (max-width: 768px) {
  .el-header {
    height: 48px;
    padding: 0 12px;
  }
  .header-content h1 {
    font-size: 16px;
  }
  
  .el-main {
    padding: 10px;
    overflow-y: visible;
  }
  
  .left-col, .right-col {
    width: 100% !important;
    max-width: 100% !important;
    flex: none !important;
    padding: 0 !important;
  }
  
  .submit-form :deep(.el-form-item__label) {
    width: 50px !important;
    font-size: 13px;
  }
  
  .codemirror-container {
    height: 250px !important;
  }
  
  .placeholder-text {
    margin-top: 40px;
  }
  
  .practice-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>