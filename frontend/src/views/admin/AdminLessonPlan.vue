<template>
  <div class="admin-page">
    <el-card>
      <template #header>
        <span>📝 教案生成</span>
        <el-button type="primary" size="small" @click="generatePlan" :loading="generating" style="float:right">
          🤖 生成教案
        </el-button>
      </template>

      <div v-if="!plan && !generating">
        <el-empty description="点击「生成教案」根据批改结果自动生成" />
      </div>

      <div v-if="generating" style="text-align:center;padding:40px">
        <p style="color:#999">正在分析批改数据，生成教案中...</p>
      </div>

      <div v-if="plan" class="plan-content">
        <div class="plan-toolbar">
          <el-button type="success" size="small" @click="copyPlan">📋 一键复制</el-button>
          <el-button size="small" @click="downloadPlan">📥 下载TXT</el-button>
          <el-tag size="small" type="info" effect="plain" style="margin-left:8px">由AI生成</el-tag>
        </div>
        <div class="plan-text" v-html="formatPlan(plan)"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { adminStore } from '@/store/index.js'
import { saveAs } from 'file-saver'
import api from '@/api/index.js'

const plan = ref('')
const generating = ref(false)

const generatePlan = async () => {
  if (adminStore.reports.length === 0) {
    alert('暂无批改数据，请先完成批改')
    return
  }
  generating.value = true
  plan.value = ''
  try {
    const res = await api.post('/lesson-plan', { reports: adminStore.reports })
    plan.value = res.data.plan
  } catch (e) {
    plan.value = generateLocalPlan()
  } finally {
    generating.value = false
  }
}

const generateLocalPlan = () => {
  const reports = adminStore.reports
  const scores = reports.map(r => r.overall_score).filter(s => s !== undefined)
  const avg = (scores.reduce((a,b) => a+b, 0) / scores.length).toFixed(1)
  
  const errors = {}
  reports.forEach(r => {
    r.deductions?.forEach(d => {
      errors[d.type] = (errors[d.type] || 0) + 1
    })
  })
  
  let text = `【编程作业讲评教案】（由AI生成）\n\n`
  text += `一、班级整体情况\n- 人数：${reports.length} 人\n- 平均分：${avg} 分\n\n`
  text += `二、高频错误\n`
  Object.entries(errors).sort((a,b) => b[1]-a[1]).slice(0,5).forEach(([t, c], i) => {
    text += `${i+1}. ${t}：${c} 人次\n`
  })
  text += `\n三、复习重点\n- 针对高频错误进行课堂讲解\n`
  text += `\n四、课后作业\n- 完成平台推荐的专项练习\n`
  return text
}

const formatPlan = (text) => {
  return text.replace(/\n/g, '<br>')
}

const copyPlan = () => {
  navigator.clipboard.writeText(plan.value.replace(/<br>/g, '\n').replace(/<[^>]+>/g, ''))
  alert('已复制到剪贴板，可直接粘贴到教案中')
}

const downloadPlan = () => {
  const text = plan.value.replace(/<br>/g, '\n').replace(/<[^>]+>/g, '')
  const blob = new Blob(['\uFEFF' + text], { type: 'text/plain;charset=utf-8' })
  saveAs(blob, '编程作业讲评教案.txt')
}
</script>

<style scoped>
.admin-page { max-width: 900px; }
.plan-content { margin-top: 16px; }
.plan-toolbar { margin-bottom: 16px; display: flex; align-items: center; }
.plan-text {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 24px;
  line-height: 2;
  color: #333;
  white-space: pre-wrap;
}
</style>