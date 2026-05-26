<template>
  <div class="profile-container">
    <!-- 头部 -->
    <div class="profile-header">
      <el-button @click="goBack" class="back-btn" link>
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1>📊 学习档案</h1>
      <p>你的编程学习成长轨迹</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">{{ card.icon }}</div>
          <h3>{{ card.value }}</h3>
          <p>{{ card.label }}</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 雷达图 + 知识点树 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card header="🎯 能力雷达图">
          <div ref="radarRef" style="height:350px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="🌳 知识点掌握情况">
          <div ref="treeRef" style="height:350px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 成绩趋势 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="24">
        <el-card header="📈 成绩趋势">
          <div ref="lineRef" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 提交历史 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="24">
        <el-card header="📝 提交历史">
          <el-table :data="history" stripe v-if="history.length > 0">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="question" label="题目" />
            <el-table-column prop="language" label="语言" width="80" />
            <el-table-column prop="score" label="分数" width="80" sortable>
              <template #default="{ row }">
                <el-tag :type="scoreType(row.score)">{{ row.score }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" link @click="viewDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无提交记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

// 模拟学习数据（实际从后端获取）
const history = ref([
  { date: '2026-05-20', question: '找最大值', language: 'Python', score: 65, deductions: [{ type: '初始化错误' }] },
  { date: '2026-05-21', question: '找最大值', language: 'Python', score: 80, deductions: [{ type: '边界处理' }] },
  { date: '2026-05-22', question: '列表去重', language: 'Python', score: 90, deductions: [] },
  { date: '2026-05-23', question: '斐波那契数列', language: 'Python', score: 75, deductions: [{ type: '逻辑错误' }] },
  { date: '2026-05-24', question: '找最大值', language: 'Java', score: 85, deductions: [] },
])

const radarRef = ref(null)
const treeRef = ref(null)
const lineRef = ref(null)

const statCards = computed(() => {
  const scores = history.value.map(h => h.score)
  if (scores.length === 0) return []
  return [
    { icon: '📝', label: '提交次数', value: history.value.length },
    { icon: '📊', label: '平均分', value: (scores.reduce((a,b) => a+b, 0) / scores.length).toFixed(1) },
    { icon: '🏆', label: '最高分', value: Math.max(...scores) },
    { icon: '📉', label: '最低分', value: Math.min(...scores) },
  ]
})

const scoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

const goBack = () => router.push('/')

const viewDetail = (row) => {
  console.log('查看详情:', row)
}

onMounted(() => {
  nextTick(() => {
    // 雷达图
    if (radarRef.value) {
      const chart = echarts.init(radarRef.value)
      chart.setOption({
        radar: {
          indicator: [
            { name: '逻辑正确', max: 100 },
            { name: '边界处理', max: 100 },
            { name: '代码规范', max: 100 },
            { name: '算法效率', max: 100 },
          ]
        },
        series: [{
          type: 'radar',
          data: [{ value: [78, 70, 85, 65], name: '你', areaStyle: { color: 'rgba(102,126,234,0.2)' } }]
        }]
      })
    }

    // 知识点树
    if (treeRef.value) {
      const chart = echarts.init(treeRef.value)
      chart.setOption({
        series: [{
          type: 'tree',
          data: [{
            name: '编程基础',
            children: [
              { name: '变量初始化 ✅', itemStyle: { color: '#67c23a' } },
              { name: '循环遍历 ✅', itemStyle: { color: '#67c23a' } },
              { name: '边界处理 ⚠️', itemStyle: { color: '#e6a23c' } },
              { name: '函数定义 ✅', itemStyle: { color: '#67c23a' } },
            ]
          }],
          layout: 'radial',
          symbol: 'roundRect',
          symbolSize: 10,
        }]
      })
    }

    // 趋势图
    if (lineRef.value) {
      const chart = echarts.init(lineRef.value)
      chart.setOption({
        xAxis: { data: history.value.map(h => h.date) },
        yAxis: { min: 0, max: 100 },
        series: [{
          type: 'line',
          data: history.value.map(h => h.score),
          smooth: true,
          lineStyle: { color: '#667eea', width: 3 },
          itemStyle: { color: '#667eea' },
          areaStyle: { color: 'rgba(102,126,234,0.1)' }
        }]
      })
    }
  })
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  padding: 24px;
}

.profile-header {
  text-align: center;
  padding: 30px 0 20px;
}
.profile-header h1 {
  font-size: 28px;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.profile-header p {
  color: #888;
  margin: 6px 0 0;
}

.back-btn {
  position: absolute;
  left: 30px;
  top: 30px;
  font-size: 14px;
}

.stats-row {
  margin-top: 10px;
}

.stat-card {
  text-align: center;
  border-radius: 16px !important;
  border: none !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important;
  transition: all 0.3s ease;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.12) !important;
}
.stat-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
.stat-card h3 {
  font-size: 28px;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.stat-card p {
  color: #888;
  margin: 4px 0 0;
  font-size: 13px;
}

:deep(.el-card) {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
:deep(.el-card__header) {
  font-weight: 600;
}
</style>