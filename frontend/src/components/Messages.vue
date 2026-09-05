<template>
  <div class="messages-page">
    <!-- Toast -->
    <transition name="toast-slide">
      <div v-if="toast.show" class="toast" :class="toast.type" @click="toast.show = false">{{ toast.msg }}</div>
    </transition>

    <div class="glass-card chat-card">
      <!-- ===== 左侧：会话列表 ===== -->
      <div class="conv-panel">
        <div class="conv-head">
          <h3>私信</h3>
          <button class="new-btn" @click="showSearch = !showSearch">＋</button>
        </div>

        <div v-if="showSearch" class="search-box">
          <input
            v-model="searchKw"
            class="glass-input"
            placeholder="搜索用户名..."
            @input="searchUsers"
          />
          <div v-if="searchResults.length" class="search-results">
            <div v-for="u in searchResults" :key="u.username" class="conv-item" @click="openChat(u.username)">
              <span class="avatar-dot sm">{{ (u.username || '?').charAt(0) }}</span>
              <div class="conv-info">
                <strong>{{ u.username }}</strong>
              </div>
            </div>
          </div>
        </div>

        <div class="conv-list">
          <div v-if="conversations.length === 0" class="empty-tip">暂无私信<br>点右上角 ＋ 开始聊天</div>
          <div
            v-for="c in conversations"
            :key="c.peer"
            class="conv-item"
            :class="{ active: c.peer === peer }"
            @click="openChat(c.peer)"
          >
            <span class="avatar-dot sm">{{ (c.peer || '?').charAt(0) }}</span>
            <div class="conv-info">
              <div class="conv-row">
                <strong>{{ c.peer }}</strong>
                <span class="unread-badge" v-if="c.unread > 0">{{ c.unread > 99 ? '99+' : c.unread }}</span>
              </div>
              <small class="conv-last">{{ c.last_from_me ? '我: ' : '' }}{{ c.last_content }}</small>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 右侧：聊天窗口 ===== -->
      <div class="chat-panel">
        <template v-if="peer">
          <div class="chat-head">
            <span class="avatar-dot sm">{{ peer.charAt(0) }}</span>
            <strong class="peer-name" @click="goProfile(peer)">{{ peer }}</strong>
            <span class="peer-link" @click="goProfile(peer)">查看主页 →</span>
          </div>

          <div class="chat-body" ref="chatBody">
            <div v-if="messages.length === 0" class="empty-tip">还没有消息，打个招呼吧~</div>
            <div
              v-for="m in messages"
              :key="m._id"
              class="msg-row"
              :class="{ mine: m.from_user === myUsername }"
            >
              <div class="bubble">
                <p class="msg-content">{{ m.content }}</p>
                <div class="msg-meta">
                  <span>{{ formatTime(m.created_at) }}</span>
                  <!-- 已读 / 未读 只显示在自己发的消息上 -->
                  <span v-if="m.from_user === myUsername" class="read-state" :class="{ read: m.read }">
                    {{ m.read ? '已读' : '未读' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-input">
            <textarea
              v-model="draft"
              class="glass-input"
              placeholder="输入消息，Enter 发送，Shift+Enter 换行"
              @keydown.enter.exact.prevent="sendMessage"
            ></textarea>
            <button class="btn-send" @click="sendMessage" :disabled="!draft.trim()">发送</button>
          </div>
        </template>
        <div v-else class="chat-empty">
          <div class="chat-empty-icon">💬</div>
          <p>选择左侧会话，或点 ＞ 搜索用户开始私信</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const API_BASE = '/api/social'

export default {
  name: 'MessagesPage',
  data() {
    return {
      conversations: [],
      messages: [],
      peer: '',
      draft: '',
      showSearch: false,
      searchKw: '',
      searchResults: [],
      pollTimer: null,
      toast: { show: false, msg: '', type: 'info', timer: null }
    }
  },
  computed: {
    myUsername() {
      return localStorage.getItem('username') || ''
    }
  },
  created() {
    const routePeer = this.$route.params.username
    if (routePeer) this.openChat(routePeer)
    this.loadConversations()
    this.pollTimer = setInterval(() => {
      this.loadConversations(true)
      if (this.peer) this.loadMessages(true)
    }, 4000)
  },
  beforeUnmount() {
    clearInterval(this.pollTimer)
    clearTimeout(this.toast.timer)
  },
  watch: {
    '$route.params.username'(val) {
      if (val) this.openChat(val)
    }
  },
  methods: {
    showToast(msg, type = 'info') {
      clearTimeout(this.toast.timer)
      this.toast = { show: true, msg, type, timer: setTimeout(() => { this.toast.show = false }, 3000) }
    },
    async loadConversations(silent = false) {
      if (!this.myUsername) return
      try {
        const res = await fetch(`${API_BASE}/messages/conversations/${encodeURIComponent(this.myUsername)}`)
        const data = await res.json()
        if (data.code === 200) this.conversations = data.data.conversations
      } catch (e) {
        if (!silent) this.showToast('加载会话失败', 'error')
      }
    },
    async openChat(username) {
      if (username === this.myUsername) return this.showToast('不能给自己发私信', 'error')
      this.peer = username
      this.showSearch = false
      if (this.$route.params.username !== username) {
        this.$router.replace(`/messages/${encodeURIComponent(username)}`).catch(() => {})
      }
      await this.loadMessages()
      this.loadConversations(true)
    },
    async loadMessages(silent = false) {
      if (!this.peer || !this.myUsername) return
      try {
        const res = await fetch(`${API_BASE}/messages/chat/${encodeURIComponent(this.myUsername)}/${encodeURIComponent(this.peer)}`)
        const data = await res.json()
        if (data.code === 200) {
          const prevLen = this.messages.length
          this.messages = data.data.messages
          if (!silent || prevLen !== this.messages.length) {
            this.$nextTick(() => this.scrollToBottom())
          }
        }
      } catch (e) {
        if (!silent) this.showToast('加载消息失败', 'error')
      }
    },
    async sendMessage() {
      const content = this.draft.trim()
      if (!content || !this.peer) return
      this.draft = ''
      try {
        const res = await fetch(`${API_BASE}/messages`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ from_user: this.myUsername, to_user: this.peer, content })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.messages.push(data.data)
          this.scrollToBottom()
          this.loadConversations(true)
        } else {
          this.showToast(data.message, 'error')
        }
      } catch (e) {
        this.showToast('发送失败，请检查后端服务', 'error')
      }
    },
    async searchUsers() {
      if (!this.searchKw.trim()) { this.searchResults = []; return }
      try {
        const res = await fetch(`${API_BASE}/users/search?q=${encodeURIComponent(this.searchKw.trim())}`)
        const data = await res.json()
        if (data.code === 200) {
          this.searchResults = data.data.users.filter(u => u.username !== this.myUsername)
        }
      } catch (e) { /* ignore */ }
    },
    goProfile(username) {
      this.$router.push(`/profile/${encodeURIComponent(username)}`)
    },
    scrollToBottom() {
      const el = this.$refs.chatBody
      if (el) el.scrollTop = el.scrollHeight
    },
    formatTime(dt) {
      if (!dt) return ''
      const d = new Date(dt)
      const diff = (Date.now() - d.getTime()) / 1000
      if (diff < 60) return '刚刚'
      if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
      if (d.toDateString() === new Date().toDateString()) {
        return d.toTimeString().substring(0, 5)
      }
      return `${d.getMonth() + 1}-${d.getDate()} ${d.toTimeString().substring(0, 5)}`
    }
  }
}
</script>

<style scoped>
.messages-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 16px 40px;
  height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

.glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-radius: 14px;
}

.chat-card {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 480px;
}

/* ===== 左侧 ===== */
.conv-panel {
  width: 280px;
  border-right: 1px solid #eef1f6;
  display: flex;
  flex-direction: column;
}

.conv-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f2f6;
}

.conv-head h3 { margin: 0; font-size: 17px; color: #1f1f1f; }

.new-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b8def, #6f7cff);
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  line-height: 1;
}

.search-box { padding: 10px 12px; border-bottom: 1px solid #f0f2f6; }

.glass-input {
  width: 100%;
  padding: 9px 12px;
  background: #f7f9fc;
  border: 1px solid #e5e9f0;
  border-radius: 8px;
  color: #1f1f1f;
  font-size: 13px;
  box-sizing: border-box;
  outline: none;
}

.glass-input:focus { border-color: #5b8def; }

.search-results {
  max-height: 180px;
  overflow-y: auto;
  margin-top: 8px;
}

.conv-list { flex: 1; overflow-y: auto; }

.conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.conv-item:hover, .conv-item.active { background: #f0f4ff; }

.conv-info { flex: 1; min-width: 0; }
.conv-info strong {
  color: #1f1f1f;
  font-weight: 600;
  font-size: 14px;
}

.conv-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conv-row strong { font-size: 14px; color: #1f1f1f; }

.unread-badge {
  background: #e53935;
  color: #fff;
  font-size: 11px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
}

.conv-last {
  display: block;
  color: #999;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* ===== 右侧 ===== */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid #f0f2f6;
}

.peer-name { font-size: 15px; color: #1f1f1f; cursor: pointer; }
.peer-name:hover { color: #5b8def; }

.peer-link {
  margin-left: auto;
  font-size: 12px;
  color: #5b8def;
  cursor: pointer;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  background: #fafbfd;
}

.msg-row {
  display: flex;
  margin-bottom: 14px;
}

.msg-row.mine { justify-content: flex-end; }

.bubble {
  max-width: 65%;
  background: #fff;
  border: 1px solid #e8ecf3;
  border-radius: 12px;
  padding: 10px 14px;
}

.msg-row.mine .bubble {
  background: linear-gradient(135deg, #5b8def, #6f7cff);
  border: none;
}

.msg-content { margin: 0; font-size: 14px; color: #1f1f1f; word-break: break-word; white-space: pre-wrap; }

.msg-row.mine .msg-content { color: #fff; }

.msg-meta {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 4px;
  font-size: 11px;
  color: #b0b7c3;
}

.read-state { font-weight: 500; }
.read-state.read { color: #9fe3b3; }

.chat-input {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #f0f2f6;
  align-items: flex-end;
}

.chat-input .glass-input {
  flex: 1;
  resize: none;
  height: 42px;
  max-height: 100px;
  font-family: inherit;
}

.btn-send {
  padding: 11px 22px;
  border: none;
  border-radius: 21px;
  background: linear-gradient(90deg, #5b8def, #6f7cff);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.btn-send:disabled { background: #b9c4e3; cursor: not-allowed; }

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #aaa;
}

.chat-empty-icon { font-size: 48px; margin-bottom: 10px; }

.avatar-dot.sm {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b8def, #6f7cff);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 30px 0;
  font-size: 13px;
  line-height: 1.8;
}

/* ===== Toast ===== */
.toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  cursor: pointer;
  white-space: nowrap;
}
.toast.success { background: #07c160; color: #fff; }
.toast.error { background: #e53935; color: #fff; }
.toast.info { background: #5b8def; color: #fff; }

.toast-slide-enter-active, .toast-slide-leave-active { transition: all 0.3s ease; }
.toast-slide-enter-from, .toast-slide-leave-to { opacity: 0; transform: translateX(-50%) translateY(-12px); }

@media (max-width: 640px) {
  .conv-panel { width: 88px; }
  .conv-info { display: none; }
  .conv-head h3 { display: none; }
}
</style>
