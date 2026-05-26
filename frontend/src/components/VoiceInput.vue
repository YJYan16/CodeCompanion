<template>
  <div class="voice-input">
    <el-button
      :type="isListening ? 'danger' : 'primary'"
      :icon="isListening ? 'Microphone' : 'Microphone'"
      circle
      @click="toggleListening"
      :loading="processing"
      size="large"
      class="voice-btn"
    />
    <span class="voice-hint">{{ isListening ? '正在聆听...' : '点击语音提问' }}</span>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['result'])
const isListening = ref(false)
const processing = ref(false)

// 检查浏览器是否支持语音识别
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
let recognition = null

if (SpeechRecognition) {
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.continuous = false
  recognition.interimResults = false

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript
    emit('result', text)
    isListening.value = false
  }

  recognition.onerror = () => {
    isListening.value = false
    processing.value = false
  }

  recognition.onend = () => {
    isListening.value = false
    processing.value = false
  }
}

const toggleListening = () => {
  if (!SpeechRecognition) {
    alert('您的浏览器不支持语音识别，请使用Chrome浏览器')
    return
  }
  if (isListening.value) {
    recognition.stop()
  } else {
    recognition.start()
    isListening.value = true
  }
}
</script>

<style scoped>
.voice-input {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0;
}
.voice-btn {
  width: 48px;
  height: 48px;
  font-size: 20px;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4); }
  50% { box-shadow: 0 0 0 15px rgba(102, 126, 234, 0); }
}
.voice-hint {
  color: #999;
  font-size: 13px;
}
</style>