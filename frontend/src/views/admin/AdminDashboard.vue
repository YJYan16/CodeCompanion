<template>
  <div class="dashboard-container">
    <h2 class="page-title">📈 教学数据驾驶舱</h2>

    <div style="display:flex;gap:10px;margin-bottom:16px;align-items:center">
      <span style="color:#666;font-size:14px">班级:</span>
      <el-select v-model="filterClass" size="small" style="width:160px" filterable @change="onFilterChange">
        <el-option v-for="c in adminStore.classes" :key="c" :label="c" :value="c" />
      </el-select>
      <span style="color:#666;font-size:14px;margin-left:10px">语言:</span>
      <el-select v-model="filterLang" size="small" style="width:120px" @change="onFilterChange">
        <el-option label="全部语言" value="all" />
        <el-option label="Python" value="python" />
        <el-option label="Java" value="java" />
      </el-select>
    </div>

    <el-row :gutter="16" v-if="filteredReports.length > 0">
      <el-col :span="4" v-for="card in statCards" :key="card.label">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-icon">{{ card.icon }}</div>
          <h3 :style="{ color: card.color }">{{ card.value }}</h3>
          <p>{{ card.label }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px" v-if="filteredReports.length > 0">
      <el-col :span="12">
        <el-card header="📊 成绩分布">
          <div ref="histRef" style="height:320px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="🔴 高频错误 Top10">
          <div ref="errorRef" style="height:320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px" v-if="filteredReports.length > 0">
      <el-col :span="12">
        <el-card header="⚠️ 薄弱知识点分布（由AI生成）">
          <div ref="kpRef" style="height:320px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="🔥 知识点热力图">
          <div ref="heatRef" style="height:320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px" v-if="filteredReports.length > 0">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🎯 个人能力雷达图</span>
            <el-select v-model="selectedStudent" @change="renderRadar" style="width:220px;margin-left:12px" filterable clearable placeholder="搜索学生">
              <el-option v-for="r in filteredReports" :key="r.student_name" :label="r.student_name" :value="r.student_name" />
            </el-select>
          </template>
          <div ref="radarRef" style="height:350px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="🚨 学困生预警（60分以下）">
          <div v-if="warningList.length > 0">
            <div v-for="(s, i) in warningList" :key="i" class="warning-item">
              <span class="warning-rank">#{{ i + 1 }}</span>
              <span class="warning-name">{{ s.student_name }}</span>
              <el-progress :percentage="s.overall_score" :color="warningColor(s.overall_score)" style="flex:1;margin:0 12px" />
              <el-tag :type="s.overall_score < 40 ? 'danger' : 'warning'" size="small">{{ s.overall_score }}分</el-tag>
            </div>
          </div>
          <el-empty v-else description="🎉 全部及格，没有学困生！" />
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="filteredReports.length === 0" description="暂无批改数据" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { adminStore } from '@/store/index.js'

const filterClass = ref(adminStore.currentClass)
const filterLang = ref('all')
const selectedStudent = ref('')
const histRef = ref(null)
const errorRef = ref(null)
const kpRef = ref(null)
const heatRef = ref(null)
const radarRef = ref(null)

const filteredReports = computed(() => {
  let result = adminStore.allReports[filterClass.value] || []
  if (filterLang.value !== 'all') {
    result = result.filter(r => (r.language || 'python') === filterLang.value)
  }
  return result
})

const statCards = computed(() => {
  const scores = filteredReports.value.map(r => r.overall_score).filter(s => s !== undefined)
  if (scores.length === 0) return []
  return [
    { icon: '👥', label: '总人数', value: filteredReports.value.length, color: '#409eff' },
    { icon: '📊', label: '平均分', value: (scores.reduce((a,b) => a+b, 0) / scores.length).toFixed(1), color: '#67c23a' },
    { icon: '🏆', label: '最高分', value: Math.max(...scores), color: '#e6a23c' },
    { icon: '📉', label: '最低分', value: Math.min(...scores), color: '#f56c6c' },
    { icon: '✅', label: '及格率', value: (scores.filter(s => s >= 60).length / scores.length * 100).toFixed(1) + '%', color: '#67c23a' },
    { icon: '🚨', label: '学困生', value: scores.filter(s => s < 60).length + '人', color: '#f56c6c' },
  ]
})

const warningList = computed(() => {
  return filteredReports.value.filter(r => r.overall_score < 60).sort((a, b) => a.overall_score - b.overall_score)
})

const warningColor = (score) => score < 30 ? '#f56c6c' : '#e6a23c'

const onFilterChange = () => { nextTick(() => renderAllCharts()) }

const renderAllCharts = () => {
  if (filteredReports.value.length === 0) return

  if (histRef.value) {
    const existing = echarts.getInstanceByDom(histRef.value); if (existing) existing.dispose()
    const chart = echarts.init(histRef.value)
    const scores = filteredReports.value.map(r => r.overall_score).filter(s => s !== undefined)
    const bins = ['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89','90-100']
    const counts = bins.map((_, i) => scores.filter(s => s >= i*10 && s <= (i===9?100:i*10+9)).length)
    chart.setOption({
      xAxis: { data: bins }, yAxis: { name: '人数' },
      series: [{ type: 'bar', data: counts, itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#667eea'},{offset:1,color:'#764ba2'}]) } }]
    })
  }

  if (errorRef.value) {
    const existing = echarts.getInstanceByDom(errorRef.value); if (existing) existing.dispose()
    const chart = echarts.init(errorRef.value)
    const counts = {}
    filteredReports.value.forEach(r => { r.deductions?.forEach(d => { counts[d.type] = (counts[d.type] || 0) + 1 }) })
    const sorted = Object.entries(counts).sort((a,b) => b[1]-a[1])
    chart.setOption({
      yAxis: { type: 'category', data: sorted.map(s => s[0]).reverse(), axisLabel: { fontSize: 11 } },
      xAxis: { name: '次数' },
      series: [{ type: 'bar', data: sorted.map(s => s[1]).reverse(), itemStyle: { color: '#f56c6c', borderRadius: [0,4,4,0] } }],
      grid: { left: 120 }
    })
  }

  if (kpRef.value) {
    const existing = echarts.getInstanceByDom(kpRef.value); if (existing) existing.dispose()
    const chart = echarts.init(kpRef.value)
    const counts = {}
    filteredReports.value.forEach(r => { r.deductions?.forEach(d => { if (d.type) counts[d.type] = (counts[d.type] || 0) + 1 }) })
    chart.setOption({
      series: [{ type: 'pie', data: Object.entries(counts).map(([n,v]) => ({ name: n, value: v })), radius: ['45%','75%'], label: { formatter: '{b}\n{d}%' } }]
    })
  }

  if (heatRef.value) {
    const existing = echarts.getInstanceByDom(heatRef.value); if (existing) existing.dispose()
    const chart = echarts.init(heatRef.value)
    const students = filteredReports.value.map(r => r.student_name)
    const allTypes = [...new Set(filteredReports.value.flatMap(r => (r.deductions||[]).map(d => d.type)))]
    const data = []
    filteredReports.value.forEach((r,i) => { r.deductions?.forEach(d => { const j = allTypes.indexOf(d.type); if (j>=0) data.push([j,i,d.points_deducted]) }) })
    chart.setOption({
      xAxis: { data: allTypes, axisLabel: { rotate:30, fontSize:10 } },
      yAxis: { data: students },
      visualMap: { min:0, max:30, inRange: { color: ['#f0f0f0','#f56c6c'] } },
      series: [{ type: 'heatmap', data }]
    })
  }
}

const renderRadar = () => {
  if (!radarRef.value || !selectedStudent.value) return
  const existing = echarts.getInstanceByDom(radarRef.value); if (existing) existing.dispose()
  const chart = echarts.init(radarRef.value)
  const r = filteredReports.value.find(r => r.student_name === selectedStudent.value)
  if (!r) return
  const dims = { '逻辑正确':100, '边界处理':100, '代码规范':100, '算法效率':100 }
  r.deductions?.forEach(d => {
    if (d.type.includes('逻辑')||d.type.includes('初始化')) dims['逻辑正确'] -= d.points_deducted
    else if (d.type.includes('越界')||d.type.includes('空')) dims['边界处理'] -= d.points_deducted
    else if (d.type.includes('规范')||d.type.includes('缩进')) dims['代码规范'] -= d.points_deducted
    else dims['算法效率'] -= d.points_deducted
  })
  Object.keys(dims).forEach(k => { dims[k] = Math.max(0, dims[k]) })
  chart.setOption({
    radar: { indicator: Object.keys(dims).map(k => ({ name: k, max: 100 })) },
    series: [{ type: 'radar', data: [{ value: Object.values(dims), name: r.student_name, areaStyle: { color: 'rgba(102,126,234,0.2)' } }] }]
  })
}

onMounted(() => {
  if (filteredReports.value.length > 0) selectedStudent.value = filteredReports.value[0].student_name
  nextTick(() => { renderAllCharts(); renderRadar() })
})

watch(filteredReports, () => {
  nextTick(() => { if (filteredReports.value.length > 0 && !selectedStudent.value) selectedStudent.value = filteredReports.value[0].student_name; renderAllCharts(); renderRadar() })
}, { deep: true })
</script>

<style scoped>
.dashboard-container { max-width: 1300px; }
.page-title { font-size: 24px; margin: 0 0 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.metric-card { text-align: center; border-radius: 16px !important; border: none !important; box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important; transition: all 0.3s ease; }
.metric-card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(0,0,0,0.12) !important; }
.metric-icon { font-size: 28px; margin-bottom: 4px; }
.metric-card h3 { font-size: 26px; margin: 0; font-weight: 700; }
.metric-card p { color: #888; margin: 2px 0 0; font-size: 12px; }
.warning-item { display: flex; align-items: center; padding: 10px; margin: 6px 0; background: #fff; border-radius: 8px; border: 1px solid #fde2e2; }
.warning-rank { font-weight: 700; font-size: 18px; color: #f56c6c; width: 40px; }
.warning-name { width: 100px; font-weight: 500; }
:deep(.el-card) { border-radius: 16px; border: none; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
:deep(.el-card__header) { font-weight: 600; display: flex; align-items: center; }
</style>