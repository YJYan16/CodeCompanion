<template>
  <div class="admin-page">
    <el-card>
      <template #header>🕵️ 学术诚信 - 代码相似度检测</template>

      <div v-if="reports.length < 2">
        <el-empty description="至少需要2份作业才能检测" />
      </div>

      <div v-else>
        <el-button type="primary" @click="detectPlagiarism" :loading="detecting">
          🔍 开始检测
        </el-button>

        <div v-if="result" style="margin-top:20px">
          <h4>相似度矩阵</h4>
          <div ref="matrixRef" style="height:400px"></div>

          <h4 style="margin-top:20px">可疑组合（相似度 > 70%）</h4>
          <div v-if="suspicious.length > 0">
            <el-card v-for="(pair, i) in suspicious" :key="i" class="suspicious-card">
              <el-tag type="danger" size="large">
                {{ pair[0] }} ↔ {{ pair[1] }}：{{ (pair[2] * 100).toFixed(1) }}%
              </el-tag>
              <div style="display:flex;gap:20px;margin-top:10px">
                <div style="flex:1">
                  <strong>{{ pair[0] }}</strong>
                  <pre class="code-block"><code>{{ codes[pair[0]] }}</code></pre>
                </div>
                <div style="flex:1">
                  <strong>{{ pair[1] }}</strong>
                  <pre class="code-block"><code>{{ codes[pair[1]] }}</code></pre>
                </div>
              </div>
            </el-card>
          </div>
          <el-empty v-else description="未发现明显抄袭行为" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { adminStore } from '@/store/index.js'

const reports = computed(() => adminStore.reports)
const codes = computed(() => {
  const map = {}
  reports.value.forEach(r => {
    map[r.student_name] = r.code || ''
  })
  return map
})

const result = ref(false)
const suspicious = ref([])
const detecting = ref(false)
const matrixRef = ref(null)

const calculateSimilarity = (code1, code2) => {
  if (!code1 || !code2) return 0
  const tokens1 = new Set(code1.split(/\s+/).filter(t => t.length > 1))
  const tokens2 = new Set(code2.split(/\s+/).filter(t => t.length > 1))
  const intersection = new Set([...tokens1].filter(t => tokens2.has(t)))
  const union = new Set([...tokens1, ...tokens2])
  return intersection.size / union.size
}

const detectPlagiarism = async () => {
  detecting.value = true
  const names = reports.value.map(r => r.student_name)
  const n = names.length
  const matrix = Array.from({ length: n }, () => Array(n).fill(0))
  const pairs = []

  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const sim = calculateSimilarity(reports.value[i].code || '', reports.value[j].code || '')
      matrix[i][j] = sim
      matrix[j][i] = sim
      if (sim > 0.7) {
        pairs.push([names[i], names[j], sim])
      }
    }
  }

  result.value = true
  suspicious.value = pairs.sort((a, b) => b[2] - a[2])

  await nextTick()
  if (matrixRef.value) {
    const chart = echarts.init(matrixRef.value)
    const heatmapData = []
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        heatmapData.push([j, i, matrix[i][j]])
      }
    }
    chart.setOption({
      tooltip: {},
      xAxis: { data: names, axisLabel: { rotate: 45 } },
      yAxis: { data: names },
      visualMap: { min: 0, max: 1, inRange: { color: ['#fff', '#ff0000'] } },
      series: [{ type: 'heatmap', data: heatmapData }]
    })
  }
  detecting.value = false
}
</script>

<style scoped>
.admin-page { max-width: 1000px; }
.suspicious-card { margin-top: 10px; }
.code-block {
  background: #1e1e1e; color: #d4d4d4; padding: 10px;
  border-radius: 4px; max-height: 200px; overflow: auto; font-size: 13px;
}
</style>