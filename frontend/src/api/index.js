// frontend/src/api/index.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 提交代码批改（增加 language 参数）
export function submitGrade(code, question, rubrics, language = 'python') {
  return api.post('/grade', { code, question, rubrics, language })
}

// 流式提交批改
export function submitGradeStream(code, question, rubrics, language, onMessage, onDone, onError) {
  return fetch('/api/grade/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, question, rubrics, language })
  }).then(response => {
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

// 追问辅导
export function askTutor(question, chatHistory, reportJson) {
  return api.post('/tutor', { question, chat_history: chatHistory, report_json: reportJson })
}

// 获取批改报告（暂未使用）
export function getReport(reportId) {
  return api.get(`/report/${reportId}`)
}
// 健康检查
export const healthCheck = () => api.get('/health')

// 非流式批改（教师端用）
export const gradeCode = (code, question, rubrics, language) => {
  return api.post('/grade', { code, question, rubrics, language })
}

// 沙箱执行
export const executeCode = (code, language, timeout = 5) => {
  return api.post('/sandbox/execute', { code, language, timeout })
}

export default api