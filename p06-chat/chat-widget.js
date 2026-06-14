/**
 * Agent Chat Widget — JavaScript SDK
 * 嵌入式智能客服聊天组件，对接 Dify Chatflow SSE 流式 API
 *
 * 用法:
 *   <script src="chat-widget.js"></script>
 *   <script>
 *     AgentChatWidget.init({
 *       apiBase: 'http://your-dify-host:80',
 *       apiKey: 'app-your-api-key',
 *       primaryColor: '#1890ff',
 *       title: '智能客服助手',
 *       subtitle: '在线为您服务',
 *       welcomeText: '您好！请问有什么可以帮您的？',
 *       logo: '🤖',
 *       position: 'bottom-right'
 *     });
 *   </script>
 */
;(function () {
  'use strict';

  const STYLE_ID = 'agent-chat-widget-style';
  const WIDGET_ID = 'agent-chat-widget-root';
  const STORAGE_KEY = 'agent_chat_history';
  const USER_ID_KEY = 'agent_chat_user_id';

  // ---------- helpers ----------

  function generateUserId() {
    let uid = sessionStorage.getItem(USER_ID_KEY);
    if (!uid) {
      uid = 'user_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
      sessionStorage.setItem(USER_ID_KEY, uid);
    }
    return uid;
  }

  function timeStr() {
    const d = new Date();
    return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function loadHistory() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || [];
    } catch (_) {
      return [];
    }
  }

  function saveHistory(history) {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-50)));
    } catch (_) {}
  }

  // ---------- inject CSS ----------

  function injectStyles(css) {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ---------- SSE stream parser ----------

  function parseSSEStream(reader, onEvent) {
    const decoder = new TextDecoder();
    let buffer = '';

    function pump() {
      return reader.read().then(function (result) {
        if (result.done) return;
        buffer += decoder.decode(result.value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') continue;
            try {
              onEvent(JSON.parse(data));
            } catch (_) {}
          }
        }
        return pump();
      });
    }
    return pump();
  }

  // ---------- Widget class ----------

  function AgentChatWidget(config) {
    this.config = Object.assign({
      apiBase: '',
      apiKey: '',
      primaryColor: '#1890ff',
      title: '智能客服助手',
      subtitle: '在线为您服务',
      welcomeText: '您好！我是AI智能客服总管，可以帮您查询数据、报修派单、咨询政策。请问有什么需要帮助的吗？',
      logo: '🤖',
      position: 'bottom-right',
      containerSelector: null,
    }, config);

    this.userId = generateUserId();
    this.conversationId = '';
    this.history = loadHistory();
    this.isOpen = false;
    this.isStreaming = false;

    this._init();
  }

  AgentChatWidget.prototype._init = function () {
    // Inject CSS
    const linkEl = document.createElement('link');
    linkEl.rel = 'stylesheet';
    linkEl.href = this._resolveCssPath();
    document.head.appendChild(linkEl);

    // Set CSS custom properties
    const root = document.documentElement;
    root.style.setProperty('--agent-primary', this.config.primaryColor);

    // Create DOM
    this._createDOM();

    // Render history
    this._renderHistory();

    // Bind events
    this._bindEvents();
  };

  AgentChatWidget.prototype._resolveCssPath = function () {
    // Resolve CSS path relative to this script
    const scripts = document.getElementsByTagName('script');
    for (let i = 0; i < scripts.length; i++) {
      const src = scripts[i].src || '';
      if (src.indexOf('chat-widget.js') !== -1) {
        return src.replace('chat-widget.js', 'chat-widget.css');
      }
    }
    return 'chat-widget.css';
  };

  AgentChatWidget.prototype._createDOM = function () {
    // Remove existing
    const existing = document.getElementById(WIDGET_ID);
    if (existing) existing.remove();

    const root = document.createElement('div');
    root.id = WIDGET_ID;

    // Trigger button
    const triggerBtn = document.createElement('button');
    triggerBtn.className = 'agent-chat-trigger';
    triggerBtn.setAttribute('aria-label', '打开聊天');
    triggerBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';

    // Container
    const container = document.createElement('div');
    container.className = 'agent-chat-container';

    // Header
    container.innerHTML =
      '<div class="agent-chat-header">' +
        '<div class="agent-chat-header-left">' +
          '<div class="agent-chat-avatar">' + escapeHtml(this.config.logo) + '</div>' +
          '<div>' +
            '<div class="agent-chat-title">' + escapeHtml(this.config.title) + '</div>' +
            '<div class="agent-chat-subtitle">' + escapeHtml(this.config.subtitle) + '</div>' +
          '</div>' +
        '</div>' +
        '<button class="agent-chat-close" aria-label="关闭">&times;</button>' +
      '</div>' +
      '<div class="agent-chat-messages" id="agent-messages"></div>' +
      '<div class="agent-chat-input-area">' +
        '<textarea class="agent-chat-input" id="agent-input" placeholder="输入您的问题..." rows="1"></textarea>' +
        '<button class="agent-chat-send" id="agent-send" aria-label="发送">' +
          '<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>' +
        '</button>' +
      '</div>';

    root.appendChild(triggerBtn);
    root.appendChild(container);

    const target = this.config.containerSelector
      ? document.querySelector(this.config.containerSelector) || document.body
      : document.body;
    target.appendChild(root);

    this.triggerBtn = triggerBtn;
    this.container = container;
    this.messagesEl = container.querySelector('#agent-messages');
    this.inputEl = container.querySelector('#agent-input');
    this.sendBtn = container.querySelector('#agent-send');
  };

  AgentChatWidget.prototype._bindEvents = function () {
    var self = this;

    this.triggerBtn.addEventListener('click', function () {
      self.toggle();
    });

    this.container.querySelector('.agent-chat-close').addEventListener('click', function () {
      self.toggle(false);
    });

    this.sendBtn.addEventListener('click', function () {
      self.sendMessage();
    });

    this.inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        self.sendMessage();
      }
    });

    // Auto-resize textarea
    this.inputEl.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });
  };

  AgentChatWidget.prototype.toggle = function (forceState) {
    this.isOpen = forceState !== undefined ? forceState : !this.isOpen;
    this.container.classList.toggle('open', this.isOpen);
    if (this.isOpen) {
      this.triggerBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';
      this.inputEl.focus();
      this._scrollToBottom();
    } else {
      this.triggerBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';
    }
  };

  AgentChatWidget.prototype._renderHistory = function () {
    if (this.history.length === 0) {
      this._showWelcome();
      return;
    }
    for (var i = 0; i < this.history.length; i++) {
      var m = this.history[i];
      this._appendMessage(m.role, m.content, false);
    }
  };

  AgentChatWidget.prototype._showWelcome = function () {
    var hints = [
      '查询财务报表', '用户信息查询', '设备报修派单',
      '咨询公司政策', '转人工客服'
    ];
    var hintsHtml = '';
    for (var i = 0; i < hints.length; i++) {
      hintsHtml += '<span class="agent-welcome-hint" data-hint="' + escapeHtml(hints[i]) + '">' + escapeHtml(hints[i]) + '</span>';
    }

    var welcomeEl = document.createElement('div');
    welcomeEl.className = 'agent-welcome';
    welcomeEl.innerHTML =
      '<div class="agent-welcome-title">👋 ' + escapeHtml(this.config.title) + '</div>' +
      '<div>' + escapeHtml(this.config.welcomeText) + '</div>' +
      '<div class="agent-welcome-hints">' + hintsHtml + '</div>';

    this.messagesEl.appendChild(welcomeEl);

    // Bind hint clicks
    var self = this;
    this.messagesEl.querySelectorAll('.agent-welcome-hint').forEach(function (el) {
      el.addEventListener('click', function () {
        self.inputEl.value = this.getAttribute('data-hint');
        self.sendMessage();
      });
    });
  };

  AgentChatWidget.prototype._appendMessage = function (role, content, animate) {
    // Remove welcome if present
    var welcome = this.messagesEl.querySelector('.agent-welcome');
    if (welcome) welcome.remove();

    var msg = document.createElement('div');
    msg.className = 'agent-msg ' + role;

    var avatarLabel = role === 'user' ? '我' : this.config.logo;
    msg.innerHTML =
      '<div class="agent-msg-avatar">' + escapeHtml(avatarLabel) + '</div>' +
      '<div class="agent-msg-bubble">' + this._formatContent(content) + '</div>';

    this.messagesEl.appendChild(msg);
    this._scrollToBottom();
    return msg;
  };

  AgentChatWidget.prototype._formatContent = function (content) {
    // Basic markdown-like formatting
    var html = escapeHtml(content);
    // Bold: **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
  };

  AgentChatWidget.prototype._appendTyping = function () {
    var el = document.createElement('div');
    el.className = 'agent-msg assistant';
    el.innerHTML =
      '<div class="agent-msg-avatar">' + escapeHtml(this.config.logo) + '</div>' +
      '<div class="agent-typing"><span></span><span></span><span></span></div>';
    this.messagesEl.appendChild(el);
    this._scrollToBottom();
    return el;
  };

  AgentChatWidget.prototype._scrollToBottom = function () {
    var el = this.messagesEl;
    requestAnimationFrame(function () {
      el.scrollTop = el.scrollHeight;
    });
  };

  AgentChatWidget.prototype.sendMessage = function () {
    var text = this.inputEl.value.trim();
    if (!text || this.isStreaming) return;

    this.inputEl.value = '';
    this.inputEl.style.height = 'auto';

    // Append user message
    this._appendMessage('user', text);
    this.history.push({ role: 'user', content: text });
    saveHistory(this.history);

    // Show typing indicator
    var typingEl = this._appendTyping();

    // Call Dify API
    this._streamChat(text, typingEl);
  };

  AgentChatWidget.prototype._streamChat = function (query, typingEl) {
    var self = this;
    this.isStreaming = true;
    this.sendBtn.disabled = true;

    var apiBase = this.config.apiBase.replace(/\/+$/, '');
    var url = apiBase + '/v1/chat-messages';

    var body = {
      inputs: {},
      query: query,
      response_mode: 'streaming',
      conversation_id: this.conversationId || '',
      user: this.userId,
    };

    var fullResponse = '';

    fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + this.config.apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }).then(function (response) {
      if (!response.ok) {
        throw new Error('API error: ' + response.status + ' ' + response.statusText);
      }

      var reader = response.body.getReader();

      // Replace typing with message bubble
      typingEl.querySelector('.agent-typing').outerHTML =
        '<div class="agent-msg-bubble"></div>';
      var bubble = typingEl.querySelector('.agent-msg-bubble');

      return parseSSEStream(reader, function (event) {
        if (event.event === 'message' || event.event === 'agent_message') {
          fullResponse += event.answer || '';
          bubble.innerHTML = self._formatContent(fullResponse);
          self._scrollToBottom();
        }
        if (event.event === 'message_end') {
          self.conversationId = event.conversation_id || self.conversationId;
        }
      });
    }).then(function () {
      // Done
      if (fullResponse) {
        self.history.push({ role: 'assistant', content: fullResponse });
        saveHistory(self.history);
      }
    }).catch(function (err) {
      console.error('Agent Chat Error:', err);
      var errBubble = typingEl.querySelector('.agent-msg-bubble');
      if (!errBubble) {
        typingEl.querySelector('.agent-typing').outerHTML =
          '<div class="agent-msg-bubble"></div>';
        errBubble = typingEl.querySelector('.agent-msg-bubble');
      }
      errBubble.innerHTML = '<span style="color:#ff4d4f">抱歉，服务暂时不可用，请稍后重试。</span>';
    }).finally(function () {
      self.isStreaming = false;
      self.sendBtn.disabled = false;
      self.inputEl.focus();
    });
  };

  // ---------- Public API ----------

  window.AgentChatWidget = {
    _instance: null,

    /**
     * Initialize the chat widget
     * @param {Object} config
     * @param {string} config.apiBase - Dify API base URL (e.g. http://localhost:80)
     * @param {string} config.apiKey - Dify app API key
     * @param {string} [config.primaryColor='#1890ff'] - Theme primary color
     * @param {string} [config.title='智能客服助手'] - Header title
     * @param {string} [config.subtitle='在线为您服务'] - Header subtitle
     * @param {string} [config.welcomeText] - Welcome message
     * @param {string} [config.logo='🤖'] - Logo emoji or text
     * @param {string} [config.containerSelector] - Custom mount target
     */
    init: function (config) {
      if (this._instance) {
        console.warn('AgentChatWidget already initialized.');
        return;
      }
      if (!config || !config.apiBase || !config.apiKey) {
        console.error('AgentChatWidget: apiBase and apiKey are required.');
        return;
      }
      this._instance = new AgentChatWidget(config);
    },

    /** Toggle the chat panel open/close */
    toggle: function () {
      if (this._instance) this._instance.toggle();
    },

    /** Open the chat panel */
    open: function () {
      if (this._instance) this._instance.toggle(true);
    },

    /** Close the chat panel */
    close: function () {
      if (this._instance) this._instance.toggle(false);
    },

    /** Clear conversation history */
    clearHistory: function () {
      if (this._instance) {
        sessionStorage.removeItem(STORAGE_KEY);
        this._instance.history = [];
        this._instance.conversationId = '';
        this._instance.messagesEl.innerHTML = '';
        this._instance._showWelcome();
      }
    },

    /** Destroy the widget */
    destroy: function () {
      var root = document.getElementById(WIDGET_ID);
      if (root) root.remove();
      var style = document.getElementById(STYLE_ID);
      if (style) style.remove();
      this._instance = null;
    }
  };
})();
