import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

export const healthCheck = () => api.get('/health')

export const gradeCode = (code, question, rubrics, language) => {
  return api.post('/grade', { code, question, rubrics, language })
}

export const executeCode = (code, language, timeout = 5) => {
  return api.post('/sandbox/execute', { code, language, timeout })
}

export default api