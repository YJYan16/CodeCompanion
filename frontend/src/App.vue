<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { authStore } from '@/store/auth.js'
import { adminStore } from '@/store/admin.js'
import { useWebSocket } from '@/composables/useWebSocket.js'

onMounted(async () => {
  await authStore.checkLogin()
  if (authStore.role === 'admin') {
    await adminStore.init()
  }
})

useWebSocket((event, data) => {
  adminStore.handleRealtimeEvent(event, data)
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

body {
  margin: 0;
  padding: 0;
  background: #f0f2f5;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
}
::-webkit-scrollbar-track {
  background: transparent;
}

.code-block {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
  padding: 16px !important;
  border-radius: 8px !important;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  margin: 12px 0;
  white-space: pre-wrap;
  border: 1px solid #2a2a4a;
}

.gradient-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: #fff !important;
  transition: all 0.3s ease !important;
}
.gradient-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
}
@media screen and (max-width: 768px) {
  .el-card {
    border-radius: 12px !important;
  }
  .el-button {
    min-height: 40px;
    font-size: 14px;
  }
  .el-table {
    font-size: 12px;
  }
}
</style>
