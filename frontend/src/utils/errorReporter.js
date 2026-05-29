import api from '@/api/client.js'

export function setupErrorReporter(app) {
  app.config.errorHandler = (err, instance, info) => {
    console.error('[Vue Error]', err, info)
    reportError({
      message: err?.message || String(err),
      stack: err?.stack || '',
      component: instance?.$options?.name || info,
      url: window.location.href,
    })
  }

  window.addEventListener('unhandledrejection', (event) => {
    reportError({
      message: event.reason?.message || String(event.reason),
      stack: event.reason?.stack || '',
      component: 'unhandledrejection',
      url: window.location.href,
    })
  })
}

export async function reportError({ message, stack, component, url }) {
  try {
    await api.post('/errors/report', { message, stack, component, url })
  } catch {
    // 静默失败，避免错误上报循环
  }
}
