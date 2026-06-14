import { ref } from 'vue'

/**
 * WebSocket 连接 composable
 * 自动重连 + 心跳保活
 */
export function useWebSocket() {
    const ws = ref(null)
    const listeners = []
    let reconnectTimer = null
    let heartbeatTimer = null

    function connect() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
        const url = `${protocol}//${location.host}/ws/notification`

        ws.value = new WebSocket(url)

        ws.value.onopen = () => {
            console.log('[WS] 连接成功')
            // 心跳
            heartbeatTimer = setInterval(() => {
                if (ws.value?.readyState === WebSocket.OPEN) {
                    ws.value.send('ping')
                }
            }, 30000)
        }

        ws.value.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.type === 'pong') return
                listeners.forEach(fn => fn(data))
            } catch {
                // ignore non-JSON
            }
        }

        ws.value.onclose = () => {
            console.log('[WS] 连接关闭，3 秒后重连')
            clearInterval(heartbeatTimer)
            reconnectTimer = setTimeout(connect, 3000)
        }

        ws.value.onerror = (err) => {
            console.error('[WS] 错误', err)
            ws.value?.close()
        }
    }

    function disconnect() {
        clearInterval(heartbeatTimer)
        clearTimeout(reconnectTimer)
        ws.value?.close()
    }

    function onMessage(callback) {
        listeners.push(callback)
    }

    return { connect, disconnect, onMessage }
}
