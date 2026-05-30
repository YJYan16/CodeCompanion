<template>
  <div class="admin-page">
    <el-card>
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between">
          <span>📤 批量批改作业</span>
          <div style="display:flex;align-items:center;gap:10px">
            <span style="color:#666;font-size:14px">当前班级：</span>
            <el-select v-model="currentClass" @change="switchClass" size="small" style="width:150px">
              <el-option v-for="c in adminStore.classes" :key="c" :label="c" :value="c" />
            </el-select>
          </div>
        </div>
      </template>

      <el-form label-width="100px">
        <el-form-item label="选择题目">
          <el-select v-model="selectedQuestion" placeholder="请选择题目" filterable style="width:250px">
            <el-option v-for="q in filteredQuestions" :key="q.id" :label="q.title" :value="q.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="语言">
          <el-select v-model="batchLanguage" placeholder="选择语言" style="width:200px" @change="onLanguageChange">
            <el-option label="Python" value="python" />
            <el-option label="Java" value="java" />
          </el-select>
        </el-form-item>

        <el-form-item label="提交方式">
          <el-radio-group v-model="submitMode">
            <el-radio value="single">粘贴单个代码</el-radio>
            <el-radio value="batch">上传作业包 (.zip)</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="submitMode === 'single'">
          <el-form-item label="学生姓名">
            <el-input v-model="studentName" style="width:200px" />
          </el-form-item>
          <el-form-item label="代码">
            <el-input v-model="singleCode" type="textarea" :rows="10" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitSingle" :loading="grading">🚀 批改此作业</el-button>
          </el-form-item>
          <el-card v-if="singleReport" class="result-card">
            <p><strong>总分: {{ singleReport.overall_score }}/100（由AI生成）</strong></p>
            <p>{{ singleReport.summary }}</p>
            <div v-for="(d, i) in singleReport.deductions" :key="i" class="deduction">
              <p>第{{ d.line }}行 - {{ d.type }} (扣{{ d.points_deducted }}分)</p>
              <p>建议: {{ d.suggestion }}</p>
            </div>
          </el-card>
        </template>

        <template v-if="submitMode === 'batch'">
          <el-form-item>
            <el-upload drag :auto-upload="false" :on-change="handleZipUpload" accept=".zip">
              <el-icon><Upload /></el-icon>
              <div>拖拽或点击上传 ZIP 文件</div>
            </el-upload>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitBatch" :loading="grading">🚀 批量批改</el-button>
          </el-form-item>
          <el-progress v-if="grading" :percentage="progress" />
          <el-table v-if="batchResults.length > 0" :data="batchResults" stripe>
            <el-table-column prop="student_name" label="学生" width="120" />
            <el-table-column prop="overall_score" label="总分" width="80" />
            <el-table-column prop="summary" label="评语" />
          </el-table>
          <div v-if="batchStats" class="stats">
            <el-tag type="success">平均分: {{ batchStats.avg }}</el-tag>
            <el-tag type="warning">最高分: {{ batchStats.max }}</el-tag>
            <el-tag type="danger">最低分: {{ batchStats.min }}</el-tag>
          </div>
        </template>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { submitGrade } from '@/api/index.js'
import { adminStore } from '@/store/index.js'

const selectedQuestion = ref('q1')
const batchLanguage = ref('python')
const submitMode = ref('single')
const studentName = ref('测试学生')
const singleCode = ref('')
const grading = ref(false)
const progress = ref(0)
const singleReport = ref(null)
const batchResults = ref([])
const zipFile = ref(null)
const currentClass = ref(adminStore.currentClass)

const filteredQuestions = computed(() => {
  return adminStore.questions.filter(q => q.languages.includes(batchLanguage.value))
})

const batchStats = computed(() => {
  const scores = batchResults.value.map(r => r.overall_score).filter(s => s !== undefined)
  if (scores.length === 0) return null
  return {
    avg: (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1),
    max: Math.max(...scores),
    min: Math.min(...scores)
  }
})

const getQuestion = () => {
  const q = adminStore.questions.find(q => q.id === selectedQuestion.value)
  if (!q) return null
  const langConfig = q[batchLanguage.value] || q.python || {}
  return { ...q, ...langConfig }
}

const onLanguageChange = () => {
  const first = filteredQuestions.value[0]
  if (first && !filteredQuestions.value.find(q => q.id === selectedQuestion.value)) {
    selectedQuestion.value = first.id
  }
}

const switchClass = (name) => {
  currentClass.value = name
  adminStore.switchClass(name)
}

const submitSingle = async () => {
  grading.value = true
  singleReport.value = null
  try {
    const q = getQuestion()
    if (!q) return alert('请先选择题库中的题目')
    const response = await submitGrade(singleCode.value, q.description, q.rubrics, batchLanguage.value)
    singleReport.value = response.data

    // 保存到后端数据库
    await adminStore.addReport({
      student_name: studentName.value,
      code: singleCode.value,
      language: batchLanguage.value,
      class: adminStore.currentClass,
      source: 'batch',
      question: q.title,
      question_id: selectedQuestion.value,
      overall_score: response.data.overall_score || 0,
      summary: response.data.summary || '',
      deductions: response.data.deductions || [],
      ...response.data
    })
  } catch (e) {
    alert('批改失败: ' + e.message)
  } finally {
    grading.value = false
  }
}

const handleZipUpload = (file) => {
  zipFile.value = file.raw
}

const submitBatch = async () => {
  if (!zipFile.value) return alert('请先上传 ZIP 文件')
  grading.value = true
  batchResults.value = []
  progress.value = 0

  try {
    const JSZip = await import('jszip')
    const zip = await JSZip.loadAsync(zipFile.value)
    const files = Object.keys(zip.files).filter(f => f.endsWith('.py') || f.endsWith('.java'))
    const total = files.length
    const q = getQuestion()
    if (!q) return alert('请先选择题库中的题目')

    for (let i = 0; i < files.length; i++) {
      const filename = files[i]
      const content = await zip.files[filename].async('string')
      const name = filename.replace(/\.(py|java)$/, '')
      const lang = filename.endsWith('.java') ? 'java' : batchLanguage.value

      try {
    const response = await fetch('/api/grade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: content,
        question: q.description,
        rubrics: q.rubrics,
        language: lang
      })
    })
    const result = await response.json()

    // ★ 调试：打印第一个结果
    if (i === 0) {
      console.log('🔍 后端返回的完整结果:', JSON.stringify(result))
    }
    
    const record = {
      student_name: name,
      code: content,
      language: lang,
      class: adminStore.currentClass,
      source: 'batch',
      question: q.title,
      question_id: selectedQuestion.value,
      overall_score: result.overall_score || 0,
      summary: result.summary || '',
      deductions: result.deductions || [],
    }
    batchResults.value.push(record)
    await adminStore.addReport(record)
  } catch (e) {
        batchResults.value.push({
          student_name: name,
          overall_score: 0,
          summary: '批改失败: ' + e.message,
          deductions: []
        })
      }
      progress.value = Math.round(((i + 1) / total) * 100)
    }
  } catch (e) {
    alert('解析 ZIP 失败: ' + e.message)
  } finally {
    grading.value = false
  }
}
</script>

<style scoped>
.admin-page { max-width: 1000px; }
.result-card { margin-top: 16px; }
.deduction { background: #f9f9f9; padding: 8px; margin: 8px 0; border-radius: 4px; }
.stats { margin-top: 16px; display: flex; gap: 10px; }
</style>