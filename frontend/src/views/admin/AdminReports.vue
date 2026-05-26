<template>
  <div class="admin-page">
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
.code-block {
  background: #1a1a2e; color: #e0e0e0; padding: 12px;
  border-radius: 8px; max-height: 300px; overflow: auto; font-size: 13px;
}
.deduction {
  background: #f9f9f9; padding: 8px; margin: 8px 0; border-radius: 6px;
}
</style>