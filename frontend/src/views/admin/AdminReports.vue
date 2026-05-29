<template>
  <div class="admin-page">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">批改总数</div>
        </div>
      </el-card>
      <el-card class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.passed }}</div>
          <div class="stat-label">及格人数</div>
        </div>
      </el-card>
      <el-card class="stat-card warning">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.failed }}</div>
          <div class="stat-label">不及格人数</div>
        </div>
      </el-card>
      <el-card class="stat-card primary">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.averageScore }}<span class="stat-unit">分</span></div>
          <div class="stat-label">平均分</div>
        </div>
      </el-card>
    </div>

    <el-card>
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
          <span>📊 成绩查看</span>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <el-select v-model="currentClass" @change="switchClass" size="small" style="width:140px">
              <el-option v-for="c in adminStore.classes" :key="c" :label="c" :value="c" />
            </el-select>
            <el-select v-model="sourceFilter" size="small" style="width:110px">
              <el-option label="全部来源" value="all" />
              <el-option label="批量批改" value="batch" />
              <el-option label="学生提交" value="student" />
            </el-select>
            <el-select v-model="langFilter" size="small" style="width:100px">
              <el-option label="全部语言" value="all" />
              <el-option label="Python" value="python" />
              <el-option label="Java" value="java" />
            </el-select>
            <el-select v-model="questionFilter" size="small" style="width:150px" filterable clearable placeholder="搜索题目">
              <el-option label="全部题目" value="all" />
              <el-option v-for="q in adminStore.questions" :key="q.id" :label="q.title" :value="q.title" />
            </el-select>
            <el-button size="small" @click="refreshData" type="primary" plain>🔄 刷新</el-button>
            <el-button type="success" size="small" @click="handleExportCSV">📥 CSV</el-button>
            <el-button type="info" size="small" @click="handleExportJSON">📋 JSON</el-button>
            <el-button type="primary" size="small" @click="handleExportCode">💾 代码</el-button>
          </div>
        </div>
      </template>

      <!-- 题目统计 -->
      <div v-if="Object.keys(stats.questionStats).length > 0" class="question-stats">
        <h4>📋 题目统计</h4>
        <el-row :gutter="16">
          <el-col v-for="(stat, q) in stats.questionStats" :key="q" :span="8">
            <el-card class="mini-card">
              <div class="q-title">{{ q }}</div>
              <div class="q-stats">
                <span>人数: {{ stat.count }}</span>
                <span>平均分: {{ stat.avg }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 学生统计 -->
      <div v-if="Object.keys(stats.studentStats).length > 0" class="student-stats">
        <h4>🎓 学生统计</h4>
        <el-table :data="studentStatsList" stripe>
          <el-table-column prop="name" label="学生" />
          <el-table-column prop="count" label="提交次数" />
          <el-table-column prop="avg" label="平均分" />
          <el-table-column prop="best" label="最高分" />
        </el-table>
      </div>

      <el-table :data="filteredReports" stripe v-if="filteredReports.length > 0">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="question" label="题目" width="120" show-overflow-tooltip />
        <el-table-column label="语言" width="70">
          <template #default="{ row }">
            <el-tag :type="row.language === 'java' ? 'warning' : 'primary'" size="small">
              {{ row.language || 'python' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="80">
          <template #default="{ row }">
            <el-tag :type="row.source === 'batch' ? 'warning' : 'success'" size="small">
              {{ row.source === 'batch' ? '批量' : '提交' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overall_score" label="总分" width="70" sortable />
        <el-table-column prop="summary" label="评语" show-overflow-tooltip />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredReports.length === 0" description="暂无批改记录，请点击刷新按钮" />

      <div v-if="filteredReports.length > 0" style="margin-top:20px">
        <div ref="chartRef" style="width:100%;height:300px"></div>
      </div>
    </el-card>

    <el-dialog v-model="showDialog" title="批改详情" width="700px">
      <template v-if="currentReport">
        <div style="display:flex;gap:20px">
          <div style="flex:1">
            <h4>学生代码 ({{ currentReport.language || 'python' }})</h4>
            <pre class="code-block"><code>{{ currentReport.code }}</code></pre>
          </div>
          <div style="flex:1">
            <h4>批改报告（由AI生成）</h4>
            <p><strong>总分: {{ currentReport.overall_score }}/100</strong></p>
            <p>{{ currentReport.summary }}</p>
            <div v-for="(d, i) in currentReport.deductions" :key="i" class="deduction">
              <p>第{{ d.line }}行 - {{ d.type }} (扣{{ d.points_deducted }}分)</p>
              <p>{{ d.suggestion }}</p>
            </div>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { adminStore } from '@/store/index.js'
import { exportToCSV, exportToJSON, exportCodeZip } from '@/utils/export.js'

const currentClass = ref(adminStore.currentClass)
const sourceFilter = ref('all')
const langFilter = ref('all')
const questionFilter = ref('all')
const showDialog = ref(false)
const currentReport = ref(null)
const chartRef = ref(null)

const reportsList = computed(() => adminStore.allReports[currentClass.value] || [])

// 统计数据
const stats = computed(() => {
  const reports = reportsList.value
  const filtered = reports.filter(r => {
    if (sourceFilter.value !== 'all' && r.source !== sourceFilter.value) return false
    if (langFilter.value !== 'all' && (r.language || 'python') !== langFilter.value) return false
    if (questionFilter.value !== 'all' && (r.question || '') !== questionFilter.value) return false
    return true
  })

  const result = {
    total: filtered.length,
    averageScore: 0,
    passed: 0,
    failed: 0,
    questionStats: {},
    studentStats: {}
  }

  if (filtered.length === 0) return result

  let totalScore = 0
  filtered.forEach(r => {
    const score = r.overall_score || 0
    totalScore += score

    if (score >= 60) result.passed++
    else result.failed++

    const q = r.question || '未知'
    if (!result.questionStats[q]) {
      result.questionStats[q] = { total: 0, count: 0, avg: 0 }
    }
    result.questionStats[q].total += score
    result.questionStats[q].count++

    const student = r.student_name || r.userId || '未知'
    if (!result.studentStats[student]) {
      result.studentStats[student] = { total: 0, count: 0, avg: 0, best: 0 }
    }
    result.studentStats[student].total += score
    result.studentStats[student].count++
    if (score > result.studentStats[student].best) {
      result.studentStats[student].best = score
    }
  })

  result.averageScore = Math.round(totalScore / filtered.length * 10) / 10

  Object.keys(result.questionStats).forEach(q => {
    result.questionStats[q].avg = Math.round(result.questionStats[q].total / result.questionStats[q].count * 10) / 10
  })

  Object.keys(result.studentStats).forEach(s => {
    result.studentStats[s].avg = Math.round(result.studentStats[s].total / result.studentStats[s].count * 10) / 10
  })

  return result
})

// 学生统计列表（用于表格展示）
const studentStatsList = computed(() => {
  return Object.entries(stats.value.studentStats).map(([name, data]) => ({
    name,
    count: data.count,
    avg: data.avg,
    best: data.best
  })).sort((a, b) => b.avg - a.avg)
})

const sortedReports = computed(() => {
  return [...reportsList.value].sort((a, b) => {
    return (b.submitted_at || '').localeCompare(a.submitted_at || '')
  })
})

const filteredReports = computed(() => {
  let result = sortedReports.value
  // ★ 强制修正来源：有 submitted_at 且无 batch 标记的视为学生提交
  result = result.map(r => {
    if (r.submitted_at && r.source !== 'batch') {
      r.source = 'student'
    }
    return r
  })
  if (sourceFilter.value !== 'all') result = result.filter(r => r.source === sourceFilter.value)
  if (langFilter.value !== 'all') result = result.filter(r => (r.language || 'python') === langFilter.value)
  if (questionFilter.value !== 'all') result = result.filter(r => (r.question || '') === questionFilter.value)
  return result
})

const switchClass = (name) => {
  currentClass.value = name
  adminStore.switchClass(name)
  nextTick(() => renderChart())
}

const refreshData = () => {
  // 强制从 localStorage 重新读取
  const reports = localStorage.getItem('admin_reports')
  if (reports) {
    const allReports = JSON.parse(reports)
    allReports.forEach(r => {
      const cls = r.class || '默认班级'
      if (!adminStore.allReports[cls]) adminStore.allReports[cls] = []
      const exists = adminStore.allReports[cls].findIndex(x =>
        x.userId === r.userId && x.submitted_at === r.submitted_at
      )
      if (exists >= 0) {
        adminStore.allReports[cls][exists] = r
      } else {
        adminStore.allReports[cls].push(r)
      }
    })
    adminStore.saveToStorage()
  }
  nextTick(() => renderChart())
}

const handleExportCSV = () => {
  if (filteredReports.value.length === 0) return alert('暂无数据')
  exportToCSV(filteredReports.value, '成绩表-' + currentClass.value)
}

const handleExportJSON = () => {
  if (filteredReports.value.length === 0) return alert('暂无数据')
  exportToJSON(filteredReports.value, '批改报告-' + currentClass.value)
}

const handleExportCode = async () => {
  if (filteredReports.value.length === 0) return alert('暂无数据')
  await exportCodeZip(filteredReports.value, '学生代码-' + currentClass.value)
}

const renderChart = () => {
  if (!chartRef.value || filteredReports.value.length === 0) return
  const existing = echarts.getInstanceByDom(chartRef.value)
  if (existing) existing.dispose()
  const chart = echarts.init(chartRef.value)
  const scores = filteredReports.value.map(r => r.overall_score).filter(s => s !== undefined)
  const bins = ['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89','90-100']
  const counts = bins.map((_, i) => scores.filter(s => s >= i*10 && s <= (i===9?100:i*10+9)).length)
  chart.setOption({
    title: { text: currentClass.value + ' - 成绩分布' },
    xAxis: { data: bins },
    yAxis: { name: '人数' },
    series: [{ type: 'bar', data: counts, itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#667eea'},{offset:1,color:'#764ba2'}]) } }]
  })
}

const showDetail = (row) => {
  currentReport.value = row
  showDialog.value = true
}

onMounted(() => {
  adminStore.loadStudentReports()
  nextTick(() => renderChart())
})

watch([reportsList, sourceFilter, langFilter, questionFilter], () => nextTick(() => renderChart()))
</script>

<style scoped>
.admin-page { max-width: 1200px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card.warning {
  background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
}

.stat-card.primary {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
}

.stat-unit {
  font-size: 14px;
  font-weight: normal;
  margin-left: 4px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.question-stats, .student-stats {
  margin-bottom: 20px;
}

.question-stats h4, .student-stats h4 {
  margin-bottom: 12px;
  color: #333;
}

.mini-card {
  text-align: center;
}

.q-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #666;
}

.q-stats {
  display: flex;
  justify-content: space-around;
  color: #888;
  font-size: 14px;
}

.code-block {
  background: #1a1a2e; color: #e0e0e0; padding: 12px;
  border-radius: 8px; max-height: 300px; overflow: auto; font-size: 13px;
}

.deduction {
  background: #f9f9f9; padding: 8px; margin: 8px 0; border-radius: 6px;
}
</style>