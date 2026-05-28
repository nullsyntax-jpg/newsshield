import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
})

export const getRisk     = (industry) => api.get('/api/risk',    { params: { industry } })
export const getAlerts   = ()          => api.get('/api/alerts')
export const getHistory  = (event)     => api.get('/api/history', { params: { event } })
export const searchNews  = (query)     => api.get('/api/search',  { params: { query } })
export const askAI       = (question)  => api.get('/api/ask',     { params: { question } })
export const getStats    = ()          => api.get('/api/stats')
export const subscribe   = (email)     => api.post('/api/subscribe', { email })

export default api