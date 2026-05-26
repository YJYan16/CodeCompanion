<template>
  <div class="admin-page">
    <el-card>
      <template #header>
        <span>📊 成绩查看</span>
        <div style="float:right;display:flex;gap:8px">
          <el-button type="success" size="small" @click="handleExportExcel">
            📥 导出Excel
          </el-button>
          <el-button type="warning" size="small" @click="handleExportCSV">
            📄 导出CSV
          </el-button>
          <el-button type="info" size="small" @click="handleExportJSON">
            📋 导出JSON
          </el-button>
          <el-button type="primary" size="small" @click="handleExportCode">
            💾 导出代码包
          </el-button>
        </div>
      </template>

      <!-- 原有表格不变 -->
      <el-table :data="reportsList" stripe v-if="reportsList.length > 0">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="student_name" label="学生" width="120" />
        <el-table-column prop="overall_score" label="总分" width="80" sortable />
        <el-table-column prop="summary" label="评语" show-overflow-tooltip />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="reportsList.length === 0" description="暂无批改记录" />

      <div v-if="reportsList.length > 0" style="margin-top:20px">
        <div ref="chartRef" style="width:100%;height:300px"></div>
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDialog" title="批改详情" width="700px">
      <template v-if="currentReport">
        <div style="display:flex;gap:20px">
          <div style="flex:1">
            <h4>学生代码</h4>
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
import { exportToExcel, exportToCSV, exportToJSON, exportCodeZip } from '@/utils/export.js'

const reportsList = computed(() => adminStore.reports)
const showDialog = ref(false)
const currentReport = ref(null)
const chartRef = ref(null)

const handleExportExcel = () => {
  if (reportsList.value.length === 0) return alert('暂无数据')
  exportToExcel(reportsList.value, '编程作业成绩表')
}

const handleExportCSV = () => {
  if (reportsList.value.length === 0) return alert('暂无数据')
  exportToCSV(reportsList.value, '编程作业成绩表')
}

const handleExportJSON = () => {
  if (reportsList.value.length === 0) return alert('暂无数据')
  exportToJSON(reportsList.value, '批改报告')
}

const handleExportCode = async () => {
  if (reportsList.value.length === 0) return alert('暂无数据')
  await exportCodeZip(reportsList.value, '学生代码包')
}

const renderChart = () => {
  if (!chartRef.value || reportsList.value.length === 0) return
  const existing = echarts.getInstanceByDom(chartRef.value)
  if (existing) existing.dispose()
  const chart = echarts.init(chartRef.value)
  const scores = reportsList.value.map(r => r.overall_score).filter(s => s !== undefined)
  const bins = ['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89','90-100']
  const counts = bins.map((_, i) => scores.filter(s => s >= i*10 && s <= (i===9?100:i*10+9)).length)
  chart.setOption({
    title: { text: '成绩分布' },
    xAxis: { data: bins },
    yAxis: { name: '人数' },
    series: [{
      type: 'bar', data: counts,
      itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0,color:'#667eea'},{offset:1,color:'#764ba2'}]) }
    }]
  })
}

const showDetail = (row) => {
  currentReport.value = row
  showDialog.value = true
}

onMounted(() => nextTick(() => renderChart()))
watch(reportsList, () => nextTick(() => renderChart()))
</script>

<style scoped>
.admin-page { max-width: 1100px; }
.code-block {
  background: #1a1a2e; color: #e0e0e0; padding: 12px;
  border-radius: 8px; max-height: 300px; overflow: auto; font-size: 13px;
}
.deduction {
  background: #f9f9f9; padding: 8px; margin: 8px 0; border-radius: 6px;
}
</style>