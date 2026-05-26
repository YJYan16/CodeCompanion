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

const onVoiceResult = (text) => {
  inputText.value = text
  // 自动发送
  nextTick(() => sendMessage())
}

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  reportJson: { type: String, default: '{}' },
  studentCode: { type: String, default: '' }  // 新增
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
    // 不再清空 messages，保留历史对话
    inputText.value = ''
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleClose = () => {
  visible.value = false
}

const formatContent = (text) => {
  return text.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>').replace(/\n/g, '<br>')
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
</style>