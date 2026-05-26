<template>
  <div class="admin-page">
    <el-card>
      <template #header>📤 批量批改作业</template>

      <el-form label-width="100px">
        <el-form-item label="选择题目">
          <el-select v-model="selectedQuestion" placeholder="请选择题目">
            <el-option v-for="q in questions" :key="q.id" :label="q.title" :value="q.id" />
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
import { gradeCode } from '@/api/index.js'
import { adminStore } from '@/store/index.js'

const questions = ref([
  { id: 'q1', title: '找最大值 (Python)', language: 'python',
    description: '编写函数 find_max(numbers)...',
    rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)' },
  { id: 'j1', title: '找最大值 (Java)', language: 'java',
    description: '编写 findMax 方法...',
    rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)' }
])

const selectedQuestion = ref('q1')
const submitMode = ref('single')
const studentName = ref('测试学生')
const singleCode = ref('')
const grading = ref(false)
const progress = ref(0)
const singleReport = ref(null)
const batchResults = ref([])
const zipFile = ref(null)

const batchStats = computed(() => {
  const scores = batchResults.value.map(r => r.overall_score).filter(s => s !== undefined)
  if (scores.length === 0) return null
  return {
    avg: (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1),
    max: Math.max(...scores),
    min: Math.min(...scores)
  }
})

const getQuestion = () => questions.value.find(q => q.id === selectedQuestion.value)

const submitSingle = async () => {
  grading.value = true
  singleReport.value = null
  try {
    const q = getQuestion()
    const response = await gradeCode(singleCode.value, q.description, q.rubrics, q.language)
    singleReport.value = response.data
    
    adminStore.addReport({
      student_name: studentName.value,
      code: singleCode.value,
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

    for (let i = 0; i < files.length; i++) {
      const filename = files[i]
      const content = await zip.files[filename].async('string')
      const name = filename.replace(/\.(py|java)$/, '')
      const lang = filename.endsWith('.java') ? 'java' : 'python'

      try {
        const response = await gradeCode(content, q.description, q.rubrics, lang)
        const record = {
          student_name: name,
          code: content,
          ...response.data
        }
        batchResults.value.push(record)
        adminStore.addReport(record)
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