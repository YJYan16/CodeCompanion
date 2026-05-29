import { onMounted, onUnmounted, ref } from 'vue'
import { authStore } from '@/store/auth.js'

export function useWebSocket(onEvent) {
  const connected = ref(false)
  let socket = null
  let reconnectTimer = null

  const connect = () => {
    if (!authStore.token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws?token=${encodeURIComponent(authStore.token)}`

    socket = new WebSocket(url)

    socket.onopen = () => {
      connected.value = true
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        onEvent?.(payload.event, payload.data)
      } catch {
        // ignore malformed messages
      }
    }

    socket.onclose = () => {
      connected.value = false
      reconnectTimer = setTimeout(connect, 5000)
    }
  }

  const disconnect = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    socket?.close()
    socket = null
    connected.value = false
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { connected, disconnect, reconnect: connect }
}
