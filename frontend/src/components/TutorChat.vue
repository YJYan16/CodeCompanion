<!-- frontend/src/components/TutorChat.vue -->
<template>
  <el-drawer
    v-model="visible"
    title="💬 追问辅导"
    direction="rtl"
    size="40%"
    :before-close="handleClose"
  >
    <div class="chat-container">
      <!-- 对话历史 -->
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-for="(msg, index) in messages" :key="index" class="message-item">
          <div v-if="msg.role === 'user'" class="user-msg">
            <strong>你：</strong>{{ msg.content }}
          </div>
          <div v-else class="ai-msg">
            <strong>🤖 码途智伴：</strong>
            <span v-html="formatContent(msg.content)"></span>
            <el-tag size="small" type="info" effect="plain">由AI生成</el-tag>
          </div>
        </div>
      </div>
      <VoiceInput @result="onVoiceResult" />
      <!-- 输入区域 -->
      <div class="chat-input">
        <el-input
          v-model="inputText"
          placeholder="输入你的疑问..."
          @keyup.enter="sendMessage"
          :disabled="sending"
        >
          <template #append>
            <el-button @click="sendMessage" :loading="sending">发送</el-button>
          </template>
        </el-input>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { askTutor } from '@/api/index.js'
import VoiceInput from '@/components/VoiceInput.vue'
import { ElMessage } from 'element-plus'

const onVoiceResult = (text) => {
  inputText.value = text
  nextTick(() => sendMessage())
}

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  reportJson: { type: String, default: '{}' },
  studentCode: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const chatMessagesRef = ref(null)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    inputText.value = ''
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleClose = () => {
  visible.value = false
}

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
  
  // 处理代码块，添加特殊背景框和复制按钮
  result = result.replace(/```(\w*)\s*\n([\s\S]*?)```/g, (match, lang, code) => {
    const escapedCode = escapeHtml(code.trim())
    const copyBtn = `<button class="code-copy-btn" onclick="copyCode(this)" data-code="${escapeHtml(code.trim())}">📋 复制</button>`
    return `<div class="code-block-wrapper">${copyBtn}<div class="code-block" style="background:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:6px;overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;font-size:14px;line-height:1.6;margin:10px 0;white-space:pre-wrap;position:relative;">${escapedCode}</div></div>`
  })
  
  return result
}

// 全局复制函数，供 onclick 调用
if (typeof window !== 'undefined') {
  window.copyCode = (btn) => {
    const code = btn.getAttribute('data-code')
    navigator.clipboard.writeText(code).then(() => {
      ElMessage.success('代码已复制到剪贴板')
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  }
}

import { fetchEventSource } from '@microsoft/fetch-event-source'

const sendMessage = async () => {
  const question = inputText.value.trim()
  if (!question || sending.value) return

  messages.value.push({ role: 'user', content: question })
  inputText.value = ''
  sending.value = true

  // 先添加一个空的 AI 消息占位
  messages.value.push({ role: 'assistant', content: '' })
  const aiMsgIndex = messages.value.length - 1

  try {
    await fetchEventSource('/api/tutor/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        chat_history: messages.value.slice(0, -1),
        report_json: props.reportJson,
        student_code: props.studentCode   // 新增：传递学生代码
      }),
      onmessage(event) {
        if (event.data === '[DONE]') return
        const data = JSON.parse(event.data)
        if (data.content) {
          messages.value[aiMsgIndex].content += data.content
        }
      },
      onerror(err) {
        console.error('流式请求错误:', err)
        messages.value[aiMsgIndex].content = '抱歉，暂时无法回答。'
        throw err
      }
    })
  } catch (err) {
    messages.value[aiMsgIndex].content = '抱歉，暂时无法回答。'
  } finally {
    sending.value = false
    await nextTick()
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 10px;
}
.message-item {
  margin-bottom: 15px;
}
.user-msg {
  background: #e1f3d8;
  padding: 8px;
  border-radius: 8px;
  text-align: right;
}
.ai-msg {
  background: #fff;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}
.chat-input {
  margin-top: 10px;
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