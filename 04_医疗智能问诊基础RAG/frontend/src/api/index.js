import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: apiBase + '/api',
  timeout: 60000,
})

// Chat API (non-streaming)
export function chat(question, topK = 3) {
  return api.post('/chat', { question, top_k: topK })
}

// Chat Stream API (SSE)
export async function chatStream(question, topK = 3, onChunk, onSources, onDone, onError) {
  try {
    const response = await fetch(apiBase + '/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: topK }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let eventType = ''
      let eventData = ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          eventData = line.slice(6)
          try {
            const data = JSON.parse(eventData)
            if (eventType === 'chunk' && onChunk) onChunk(data)
            if (eventType === 'sources' && onSources) onSources(data)
            if (eventType === 'done' && onDone) onDone(data)
          } catch (e) {
            // Skip malformed JSON
          }
        }
      }
    }
  } catch (error) {
    if (onError) onError(error)
  }
}

// Knowledge API
export function uploadKnowledge(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  })
}

export function listKnowledge() {
  return api.get('/knowledge/list')
}

export function deleteKnowledge(docName) {
  return api.delete(`/knowledge/${encodeURIComponent(docName)}`)
}

export default api
