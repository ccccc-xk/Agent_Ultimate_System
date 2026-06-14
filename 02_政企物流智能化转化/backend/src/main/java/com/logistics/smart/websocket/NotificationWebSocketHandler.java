package com.logistics.smart.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArraySet;

/**
 * WebSocket 工单通知处理器
 * 新工单创建或状态变更时，广播通知所有在线用户
 */
@Slf4j
@Component
public class NotificationWebSocketHandler extends TextWebSocketHandler {

    private final CopyOnWriteArraySet<WebSocketSession> sessions = new CopyOnWriteArraySet<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);
        log.info("WebSocket 连接建立: {}, 当前在线: {}", session.getId(), sessions.size());
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);
        log.info("WebSocket 连接关闭: {}, 当前在线: {}", session.getId(), sessions.size());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        // 心跳回复
        if ("ping".equals(message.getPayload())) {
            try {
                session.sendMessage(new TextMessage("{\"type\":\"pong\",\"time\":\"" + LocalDateTime.now() + "\"}"));
            } catch (IOException e) {
                log.error("心跳回复失败", e);
            }
        }
    }

    /**
     * 广播通知给所有在线客户端
     */
    public void broadcast(String type, Object data) {
        Map<String, Object> notification = new ConcurrentHashMap<>();
        notification.put("type", type);
        notification.put("data", data);
        notification.put("time", LocalDateTime.now().toString());

        try {
            String json = objectMapper.writeValueAsString(notification);
            TextMessage message = new TextMessage(json);
            for (WebSocketSession session : sessions) {
                if (session.isOpen()) {
                    try {
                        session.sendMessage(message);
                    } catch (IOException e) {
                        log.error("WebSocket 消息发送失败: {}", session.getId(), e);
                    }
                }
            }
            log.info("广播通知 [{}] 已发送给 {} 个客户端", type, sessions.size());
        } catch (Exception e) {
            log.error("广播序列化失败", e);
        }
    }

    /**
     * 发送新工单通知
     */
    public void notifyNewWorkOrder(Object workOrder) {
        broadcast("NEW_WORK_ORDER", workOrder);
    }

    /**
     * 发送工单状态变更通知
     */
    public void notifyStatusChange(Object workOrder) {
        broadcast("STATUS_CHANGE", workOrder);
    }
}
