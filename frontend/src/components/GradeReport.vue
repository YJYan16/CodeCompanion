<template>
  <div class="grade-report" v-if="report">
    <!-- 流式生成中 -->
    <div v-if="report.streaming" class="streaming-box">
      <div class="streaming-header">
        <span class="score-title">⏳ 正在批改...</span>
        <el-tag size="small" type="info" effect="plain">由AI生成</el-tag>
      </div>
      <div class="streaming-content" v-html="formatContent(streamContent)"></div>
      <el-tag type="warning" size="small" style="margin-top:8px">正在生成...</el-tag>
    </div>

    <!-- 批改完成 -->
    <template v-else>
      <div class="score-header">
        <span class="score-title">总分: {{ report.overall_score }}/100</span>
        <el-tag size="small" type="info" effect="plain">由AI生成</el-tag>
      </div>
      <div class="summary-text" v-html="formatContent(report.summary)"></div>

      <!-- 扣分明细 -->
      <div v-if="report.deductions && report.deductions.length > 0" class="deduction-section">
        <el-divider />
        <h4>📌 扣分明细</h4>
        <div v-for="(item, index) in report.deductions" :key="index" class="deduction-card">
          <div class="deduction-header">
            <span class="deduction-tag">{{ item.type }}</span>
            <span class="deduction-score">-{{ item.points_deducted }}分</span>
          </div>
          <p class="deduction-reason">{{ item.reason }}</p>
          <div class="deduction-suggestion">
            <span class="suggestion-label">💡 改进建议:</span>
            {{ item.suggestion }}
          </div>
          <el-button type="primary" link size="small" @click="$emit('ask', item)">💬 追问</el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'

defineProps({
  report: { type: Object, default: null },
  streamContent: { type: String, default: '' }
})
defineEmits(['ask'])

const escapeHtml = (str) => {
  if (!str) return ''
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

const copyCode = (code, event) => {
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success('代码已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const formatContent = (text) => {
  if (!text) return ''
  let result = text
  result = result.replace(/```(\w*)\s*\n([\s\S]*?)```/g, (match, lang, code) => {
    const escapedCode = escapeHtml(code.trim())
    const copyBtn = `<button class="code-copy-btn" onclick="window.copyCodeGradeReport(this)" data-code="${escapeHtml(code.trim())}">📋 复制</button>`
    return `<div class="code-block-wrapper">${copyBtn}<div class="code-block" style="background:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:6px;overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;font-size:14px;line-height:1.6;margin:10px 0;white-space:pre-wrap;position:relative;">${escapedCode}</div></div>`
  })
  result = result.replace(/\n/g, '<br>')
  return result
}

// 全局复制函数
if (typeof window !== 'undefined') {
  window.copyCodeGradeReport = (btn) => {
    const code = btn.getAttribute('data-code')
    navigator.clipboard.writeText(code).then(() => {
      ElMessage.success('代码已复制到剪贴板')
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  }
}
</script>

<style scoped>
.grade-report {
  padding: 10px;
}

.streaming-box {
  background: #fafafa;
  padding: 15px;
  border-radius: 8px;
}
.streaming-header {
  margin-bottom: 10px;
}
.streaming-content {
  line-height: 1.8;
  color: #333;
}

.score-header {
  margin-bottom: 10px;
}
.score-title {
  font-size: 26px;
  font-weight: bold;
  color: #409eff;
  margin-right: 10px;
}
.summary-text {
  color: #555;
  line-height: 1.8;
  background: #f0f7ff;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.deduction-section {
  margin-top: 10px;
}
.deduction-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  margin: 10px 0;
}
.deduction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.deduction-tag {
  background: #f56c6c;
  color: #fff;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: bold;
}
.deduction-score {
  color: #f56c6c;
  font-weight: bold;
  font-size: 16px;
}
.deduction-reason {
  color: #666;
  margin: 6px 0;
}
.deduction-suggestion {
  background: #f0f9eb;
  padding: 8px;
  border-radius: 4px;
  color: #67c23a;
  margin: 8px 0;
}
.suggestion-label {
  font-weight: bold;
}
.score-title {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: scorePop 0.6s ease-out;
}

@keyframes scorePop {
  0% { transform: scale(0.5); opacity: 0; }
  70% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

.code-block-wrapper {
  position: relative;
  margin: 10px 0;
}

.code-copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  z-index: 10;
  transition: all 0.3s ease;
}

.code-copy-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.code-block {
  position: relative;
}

.code-block-wrapper:hover .code-copy-btn {
  opacity: 1;
}
</style>