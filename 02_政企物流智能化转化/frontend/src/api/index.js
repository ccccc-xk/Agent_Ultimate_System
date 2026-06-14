import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || ''

const http = axios.create({
    baseURL: apiBase + '/api',
    timeout: 90000,
    headers: { 'Content-Type': 'application/json' }
})

// 响应拦截器
http.interceptors.response.use(
    (res) => res.data,
    (err) => {
        const msg = err.response?.data?.message || err.message || '网络请求失败'
        return Promise.reject(new Error(msg))
    }
)

// 工单管理
export const getWorkOrders = (params) =>
    http.get('/work-order/list', { params })

export const getWorkOrderDetail = (id) =>
    http.get(`/work-order/${id}`)

export const updateWorkOrderStatus = (id, status) =>
    http.put('/work-order/status', { id, status })


export const updateWorkOrder = (data) =>
    http.put('/work-order', data)
export const deleteWorkOrder = (id) =>
    http.delete(`/work-order/${id}`)

// NLP 派单
export const dispatchWorkOrder = (text) =>
    http.post('/nlp/dispatch', { text })

// NLP 查询
export const nlpQuery = (question) =>
    http.post('/nlp/query', { question })

export const getQueryHistory = (limit = 20) =>
    http.get('/nlp/query/history', { params: { limit } })

export const deleteQueryHistory = (id) =>
    http.delete(`/nlp/query/history/${id}`)

export const updateQueryHistory = (id, question) =>
    http.put(`/nlp/query/history/${id}`, { question })

export default http
