// frontend/src/api/index.js
import api from './client.js'

export function submitGrade(code, question, rubrics, language = 'python') {
  return api.post('/grade', { code, question, rubrics, language })
}

export function submitGradeStream(code, question, rubrics, language, onMessage, onDone, onError) {
  return fetch('/api/grade/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${sessionStorage.getItem('auth_token') || ''}`,
    },
    body: JSON.stringify({ code, question, rubrics, language }),
  }).then((response) => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) {
          onDone && onDone()
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              onDone && onDone()
              return
            }
            try {
              const parsed = JSON.parse(data)
              onMessage && onMessage(parsed)
            } catch (e) {}
          }
        }
        read()
      })
    }
    read()
  }).catch(onError)
}

export function askTutor(question, chatHistory, reportJson) {
  return api.post('/tutor', { question, chat_history: chatHistory, report_json: reportJson })
}

export function login(username, password) {
  return api.post('/login', { username, password })
}

export const executeCode = (code, language, timeout = 5) => {
  return api.post('/sandbox/execute', { code, language, timeout })
}

export default api
