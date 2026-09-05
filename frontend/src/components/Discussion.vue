<template>
  <div class="discussion-container">
    <div class="page-header">
      <h1 class="page-title">讨论区</h1>
      <p class="subtitle">交流学习心得 · 反馈使用问题 · 一起进步</p>
    </div>

    <button class="btn-post" @click="showPostForm = !showPostForm">
      <span class="btn-icon">+</span> 发布新帖
    </button>

    <transition name="slide-down">
      <div v-if="showPostForm" class="glass-card post-form">
        <input v-model="newPost.title" class="glass-input" placeholder="帖子标题" />
        <textarea v-model="newPost.content" class="glass-input" placeholder="写下你想分享的内容..."></textarea>
        <label class="privacy-toggle">
          <input type="checkbox" v-model="newPost.is_private" />
          🔒 设为私密（仅自己可见，发布后可在个人主页管理）
        </label>
        <div class="form-actions">
          <button class="btn-primary" @click="submitPost">发布</button>
          <button class="btn-ghost" @click="showPostForm = false">取消</button>
        </div>
      </div>
    </transition>

    <div v-if="loading" class="empty-tip">加载中...</div>
    <div v-else-if="posts.length === 0" class="empty-tip">还没有帖子，来发第一帖吧！</div>

    <transition-group name="post-list" tag="div" class="post-list">
      <div v-for="post in posts" :key="post._id" class="glass-card post-card" @click="viewPost(post._id)">
        <div class="post-card-header">
          <h3 class="post-title">{{ post.title }}</h3>
        </div>
        <p class="post-content">{{ post.content.substring(0, 120) }}{{ post.content.length > 120 ? '...' : '' }}</p>
        <div class="post-meta">
          <span class="meta-author link-author" @click.stop="goProfile(post.username)" title="查看TA的主页">
            <span class="avatar-dot">{{ (post.username || '匿名').charAt(0) }}</span>
            {{ post.username }}
          </span>
          <span v-if="post.is_private" class="meta-private">🔒 私密</span>
          <span class="meta-time">{{ formatTime(post.created_at) }}</span>
          <span
            class="meta-btn like-btn"
            :class="{ active: post.is_liked }"
            @click.stop="toggleLike(post)"
            :title="post.is_liked ? '取消点赞' : '点赞'"
          >
            <span class="icon-heart">{{ post.is_liked ? '♥' : '♡' }}</span> {{ post.likes || 0 }}
          </span>
          <span class="meta-static">💬 {{ post.reply_count || 0 }}</span>
          <span class="meta-static">👁️ {{ post.views || 0 }}</span>
          <span
            v-if="isOwnPost(post)"
            class="meta-btn delete-btn"
            @click.stop="deletePost(post)"
          >🗑 删除</span>
        </div>
      </div>
    </transition-group>

    <div v-if="pages > 1" class="pagination">
      <button :disabled="page <= 1" @click="changePage(page - 1)">‹ 上一页</button>
      <span class="page-info">{{ page }} / {{ pages }}</span>
      <button :disabled="page >= pages" @click="changePage(page + 1)">下一页 ›</button>
    </div>

    <transition name="modal-fade">
      <div v-if="selectedPost" class="modal-overlay" @click.self="closeDetail">
        <div class="glass-card modal-content">
          <h2 class="modal-title">{{ selectedPost.title }}</h2>
          <div class="post-info">
            <span class="meta-author link-author" @click="goProfile(selectedPost.username)" title="查看TA的主页">
              <span class="avatar-dot">{{ (selectedPost.username || '匿名').charAt(0) }}</span>
              {{ selectedPost.username }}
            </span>
            <span v-if="selectedPost.is_private" class="meta-private">🔒 私密</span>
            <span class="meta-time">{{ formatTime(selectedPost.created_at) }}</span>
            <span class="meta-static">👁️ {{ selectedPost.views || 0 }} 次浏览</span>
            <span
              v-if="!isOwnPost(selectedPost)"
              class="meta-btn dm-btn"
              @click="goChat(selectedPost.username)"
              title="私信TA"
            >✉️ 私信</span>
          </div>
          <p class="post-body">{{ selectedPost.content }}</p>

          <div class="action-bar">
            <span
              class="meta-btn like-btn"
              :class="{ active: selectedPost.is_liked }"
              @click="toggleLike(selectedPost)"
            >
              <span class="icon-heart">{{ selectedPost.is_liked ? '♥' : '♡' }}</span> 点赞 {{ selectedPost.likes || 0 }}
            </span>
            <span
              class="meta-btn fav-btn"
              :class="{ active: selectedPost.is_favorited }"
              @click="toggleFavorite(selectedPost)"
            >
              <span class="icon-star">{{ selectedPost.is_favorited ? '★' : '☆' }}</span>
              {{ selectedPost.is_favorited ? '已收藏' : '收藏' }}
            </span>
            <span class="meta-btn share-btn" @click="sharePost(selectedPost)">
              🔗 分享 ({{ selectedPost.shares || 0 }})
            </span>
          </div>

          <div class="replies-section">
            <h4 class="replies-title">回复 ({{ countReplies(selectedPost.replies) }})</h4>
            <div v-if="selectedPost.replies?.length" class="replies-list">
              <reply-node
                v-for="reply in selectedPost.replies"
                :key="reply._id"
                :reply="reply"
                :depth="0"
                :current-user-id="currentUserId"
                :current-username="currentUsername"
                @reply="onReplyClick"
                @like="toggleLike"
                @favorite="toggleFavorite"
                @share="sharePost"
                @delete-reply="deleteReply"
              />
            </div>
            <div v-else class="no-replies">暂无回复，来抢沙发吧</div>
          </div>

          <div class="reply-input">
            <textarea
              v-model="replyContent"
              class="glass-input"
              placeholder="写下你的回复..."
            ></textarea>
            <button class="btn-primary reply-btn" @click="submitReply(selectedPost._id, selectedPost._id)">回复</button>
          </div>

          <button class="btn-ghost close-btn" @click="closeDetail">关闭</button>
        </div>
      </div>
    </transition>

    <!-- 嵌套回复输入弹窗 -->
    <transition name="modal-fade">
      <div v-if="replyTarget" class="modal-overlay" @click.self="replyTarget = null">
        <div class="glass-card modal-content" style="max-width: 480px;">
          <h3 class="modal-title" style="font-size: 18px;">回复 @{{ replyTarget.username }}</h3>
          <textarea
            v-model="replyTargetContent"
            class="glass-input"
            placeholder="写下你的回复..."
            style="height: 100px;"
          ></textarea>
          <div class="form-actions" style="margin-top: 14px;">
            <button class="btn-ghost" @click="replyTarget = null">取消</button>
            <button class="btn-primary" @click="submitNestedReply">发送</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { useUserStore } from '../store/user'
import ReplyNode from './ReplyNode.vue'

const API_BASE = '/api/discussions'

export default {
  components: { ReplyNode },
  data() {
    return {
      posts: [],
      page: 1,
      pages: 1,
      loading: false,
      showPostForm: false,
      newPost: { title: '', content: '', is_private: false },
      selectedPost: null,
      replyContent: '',
      replyTarget: null,
      replyTargetContent: ''
    }
  },
  computed: {
    userStore() {
      return useUserStore()
    },
    currentUserId() {
      return this.userStore.user?._id || localStorage.getItem('user_id') || ''
    },
    currentUsername() {
      return this.userStore.user?.username || localStorage.getItem('username') || '匿名用户'
    }
  },
  mounted() {
    this.fetchPosts()
    // 如果从个人主页跳转过来（带 ?post=ID），自动打开该帖详情
    const postId = this.$route.query.post
    if (postId) {
      this.viewPost(String(postId))
      // 清掉 query，避免分享/刷新重复弹窗
      this.$router.replace({ path: '/discussion' })
    }
  },
  watch: {
    // 支持路由参数化跳转（如 PostsList 里点哪条直接定位）
    '$route.query.post'(val) {
      if (val) this.viewPost(String(val))
    }
  },
  methods: {
    isOwnPost(post) {
      return this.currentUserId && String(post.user_id || '') === String(this.currentUserId)
    },
    goProfile(username) {
      if (!username) return
      this.selectedPost = null
      this.$router.push(`/profile/${encodeURIComponent(username)}`)
    },
    goChat(username) {
      if (!username) return
      if (username === this.currentUsername) return alert('不能给自己发私信')
      this.selectedPost = null
      this.$router.push(`/messages/${encodeURIComponent(username)}`)
    },
    countReplies(replies) {
      if (!replies) return 0
      let count = replies.length
      replies.forEach(r => {
        if (r.replies?.length) count += this.countReplies(r.replies)
      })
      return count
    },
    async fetchPosts() {
      this.loading = true
      try {
        const res = await fetch(`${API_BASE}?page=${this.page}&limit=10&user_id=${encodeURIComponent(this.currentUserId)}`)
        const data = await res.json()
        if (data.code === 200) {
          this.posts = data.data.posts
          this.pages = data.data.pages
        }
      } catch (e) {
        console.error('获取帖子失败:', e)
      } finally {
        this.loading = false
      }
    },
    changePage(p) {
      this.page = p
      this.fetchPosts()
    },
    async submitPost() {
      if (!this.newPost.title || !this.newPost.content) return alert('请填写标题和内容')
      try {
        const res = await fetch(API_BASE, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...this.newPost,
            user_id: this.currentUserId,
            username: this.currentUsername
          })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.showPostForm = false
          this.newPost = { title: '', content: '', is_private: false }
          this.fetchPosts()
        } else {
          alert(data.message)
        }
      } catch (e) {
        alert('发布失败')
      }
    },
    async viewPost(id) {
      try {
        const res = await fetch(`${API_BASE}/${id}?user_id=${encodeURIComponent(this.currentUserId)}`)
        const data = await res.json()
        if (data.code === 200) {
          this.selectedPost = data.data
        }
      } catch (e) {
        console.error('获取帖子详情失败:', e)
      }
    },
    closeDetail() {
      this.selectedPost = null
      this.replyContent = ''
      this.fetchPosts()
    },
    async toggleLike(post) {
      if (!this.currentUserId) return alert('请先登录')
      try {
        const res = await fetch(`${API_BASE}/${post._id}/like`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: this.currentUserId })
        })
        const data = await res.json()
        if (data.code === 200) {
          post.likes = data.likes
          post.is_liked = data.is_liked
        }
      } catch (e) {
        console.error('点赞失败:', e)
      }
    },
    async toggleFavorite(post) {
      if (!this.currentUserId) return alert('请先登录')
      try {
        const res = await fetch(`${API_BASE}/${post._id}/favorite`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: this.currentUserId })
        })
        const data = await res.json()
        if (data.code === 200) {
          post.is_favorited = data.is_favorited
          post.favorites = data.favorites
        }
      } catch (e) {
        console.error('收藏失败:', e)
      }
    },
    async sharePost(post) {
      try {
        const res = await fetch(`${API_BASE}/${post._id}/share`, { method: 'POST' })
        const data = await res.json()
        if (data.code === 200) {
          post.shares = data.shares
        }
        // 复制链接到剪贴板
        const url = `${window.location.origin}/discussion#post-${post._id}`
        try {
          await navigator.clipboard.writeText(url)
          alert('链接已复制到剪贴板')
        } catch (e) {
          prompt('请手动复制分享链接:', url)
        }
      } catch (e) {
        console.error('分享失败:', e)
      }
    },
    async deletePost(post) {
      if (!confirm('确定要删除这篇帖子吗？（回复也会一并删除）')) return
      try {
        const res = await fetch(`${API_BASE}/${post._id}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: this.currentUserId })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.fetchPosts()
        } else {
          alert(data.message)
        }
      } catch (e) {
        alert('删除失败')
      }
    },
    async submitReply(postId, replyToId) {
      if (!this.replyContent.trim()) return alert('请输入回复内容')
      try {
        const res = await fetch(`${API_BASE}/${postId}/reply`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: this.replyContent,
            user_id: this.currentUserId,
            username: this.currentUsername,
            reply_to_id: replyToId
          })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.replyContent = ''
          this.viewPost(postId)
        } else {
          alert(data.message)
        }
      } catch (e) {
        alert('回复失败')
      }
    },
    onReplyClick({ postId, target }) {
      this.replyTarget = { postId, ...target }
      this.replyTargetContent = ''
    },
    async submitNestedReply() {
      if (!this.replyTargetContent.trim()) return alert('请输入回复内容')
      const { postId, _id, username } = this.replyTarget
      try {
        const res = await fetch(`${API_BASE}/${postId}/reply`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: this.replyTargetContent,
            user_id: this.currentUserId,
            username: this.currentUsername,
            reply_to_id: _id
          })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.replyTarget = null
          this.replyTargetContent = ''
          this.viewPost(postId)
        } else {
          alert(data.message)
        }
      } catch (e) {
        alert('回复失败')
      }
    },
    async deleteReply(reply) {
      if (!confirm('确定要删除这条回复吗？')) return
      try {
        const res = await fetch(`${API_BASE}/${reply._id}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: this.currentUserId })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.viewPost(this.selectedPost._id)
          this.fetchPosts()
        } else {
          alert(data.message)
        }
      } catch (e) {
        alert('删除失败')
      }
    },
    formatTime(t) {
      if (!t) return ''
      return new Date(t).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
/* ===== 基础容器 ===== */
.discussion-container {
  max-width: 820px;
  margin: 0 auto;
  padding: 28px 20px 48px;
  color: var(--item_left_text_color, rgba(255, 255, 255, 0.85));
}

/* ===== 玻璃拟态通用卡片 ===== */
.glass-card {
  background: var(--item_bg_color, rgba(20, 20, 35, 0.5));
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

/* ===== 页面标题 ===== */
.page-header {
  text-align: center;
  margin-bottom: 28px;
}
.page-title {
  font-size: 30px;
  font-weight: 800;
  background: var(--gradient, linear-gradient(120deg, #bd34fe, #41d1ff));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 6px;
  letter-spacing: 1px;
}
.subtitle {
  color: var(--item_left_text_color, rgba(255, 255, 255, 0.6));
  font-size: 14px;
  opacity: 0.75;
}

/* ===== 玻璃输入框 ===== */
.glass-input {
  width: 100%;
  padding: 11px 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  color: var(--item_left_title_color, #ffffff);
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.glass-input::placeholder {
  color: rgba(255, 255, 255, 0.35);
}
.glass-input:focus {
  outline: none;
  border-color: rgba(108, 92, 231, 0.6);
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.15);
}

/* ===== 按钮 ===== */
.btn-post {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: #fff;
  border: none;
  border-radius: 22px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 18px rgba(108, 92, 231, 0.4);
  transition: transform 0.25s, box-shadow 0.25s;
  margin-bottom: 18px;
}
.btn-post:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(108, 92, 231, 0.55);
}
.btn-icon {
  font-size: 18px;
  line-height: 1;
}

.btn-primary {
  padding: 10px 24px;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(108, 92, 231, 0.4);
}

.btn-ghost {
  padding: 10px 22px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--item_left_title_color, rgba(255, 255, 255, 0.8));
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.14);
}

/* ===== 发帖表单 ===== */
.post-form {
  padding: 20px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.post-form textarea {
  height: 100px;
  resize: vertical;
}
.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

/* ===== 帖子列表 ===== */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.post-card {
  padding: 18px 20px;
  cursor: pointer;
  transition: transform 0.28s, border-color 0.28s, box-shadow 0.28s;
}
.post-card:hover {
  transform: translateY(-2px);
  border-color: rgba(108, 92, 231, 0.4);
  box-shadow: 0 12px 40px rgba(108, 92, 231, 0.15), 0 8px 32px rgba(0, 0, 0, 0.2);
}
.post-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--item_left_title_color, #ffffff);
  margin: 0 0 8px;
  line-height: 1.4;
}
.post-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--item_left_text_color, rgba(255, 255, 255, 0.75));
  margin: 0 0 12px;
}

/* ===== 帖子元信息 ===== */
.post-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  flex-wrap: wrap;
}
.meta-author {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--item_left_title_color, rgba(255, 255, 255, 0.85));
  font-weight: 500;
}
.link-author {
  cursor: pointer;
  transition: opacity 0.2s;
}
.link-author:hover {
  opacity: 0.75;
  text-decoration: underline;
}
.meta-private {
  font-size: 12px;
  color: #f0a020;
  background: rgba(240, 160, 32, 0.12);
  border: 1px solid rgba(240, 160, 32, 0.35);
  border-radius: 10px;
  padding: 1px 8px;
}
.dm-btn {
  color: #5b8def !important;
  font-weight: 600;
}
.privacy-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  cursor: pointer;
  user-select: none;
  margin-bottom: 12px;
}
.privacy-toggle input {
  accent-color: #5b8def;
  width: 16px;
  height: 16px;
  cursor: pointer;
}
.avatar-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.avatar-dot.sm {
  width: 20px;
  height: 20px;
  font-size: 10px;
}
.meta-time {
  opacity: 0.6;
}
.meta-btn {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s, transform 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.meta-btn:hover {
  color: #a29bfe;
  transform: scale(1.05);
}
.like-btn.active {
  color: #ff6b9d;
}
.fav-btn.active {
  color: #ffd93d;
}
.icon-heart {
  font-size: 16px;
}
.icon-star {
  font-size: 16px;
}
.meta-static {
  opacity: 0.7;
}
.delete-btn:hover {
  color: #ff6b6b !important;
}

/* ===== 空状态 / 分页 ===== */
.empty-tip {
  text-align: center;
  color: rgba(255, 255, 255, 0.45);
  padding: 48px 0;
  font-size: 15px;
}
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 28px;
}
.pagination button {
  padding: 8px 20px;
  background: var(--item_bg_color, rgba(20, 20, 35, 0.4));
  color: var(--item_left_title_color, rgba(255, 255, 255, 0.8));
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s, border-color 0.2s;
}
.pagination button:hover:not(:disabled) {
  background: rgba(108, 92, 231, 0.2);
  border-color: rgba(108, 92, 231, 0.4);
}
.pagination button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.page-info {
  color: var(--item_left_title_color, rgba(255, 255, 255, 0.7));
  font-size: 14px;
}

/* ===== 模态框 ===== */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
  padding: 20px;
}
.modal-content {
  padding: 32px;
  max-width: 720px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
}
.modal-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--item_left_title_color, #ffffff);
  margin: 0 0 14px;
  line-height: 1.4;
}
.post-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.post-body {
  line-height: 1.8;
  white-space: pre-wrap;
  color: var(--item_left_text_color, rgba(255, 255, 255, 0.85));
  font-size: 15px;
  margin-bottom: 16px;
}

/* ===== 操作栏 ===== */
.action-bar {
  display: flex;
  gap: 14px;
  padding: 14px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.action-bar .meta-btn {
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.action-bar .meta-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* ===== 回复区 ===== */
.replies-section {
  padding-top: 12px;
}
.replies-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--item_left_title_color, rgba(255, 255, 255, 0.9));
  margin: 0 0 14px;
}
.replies-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
}
.no-replies {
  color: rgba(255, 255, 255, 0.35);
  font-size: 14px;
  padding: 12px 0;
}

/* ===== 回复输入 ===== */
.reply-input {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  margin-bottom: 16px;
}
.reply-input textarea {
  flex: 1;
  height: 56px;
  resize: none;
}
.reply-btn {
  white-space: nowrap;
  align-self: flex-end;
}

.close-btn {
  display: block;
  margin: 0 auto;
}

/* ===== 过渡动画 ===== */
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  max-height: 0;
  margin-bottom: 0 !important;
}
.slide-down-enter-to, .slide-down-leave-from {
  opacity: 1;
  max-height: 400px;
}

.post-list-enter-active {
  transition: all 0.35s ease;
}
.post-list-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.25s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}

/* ===== 暗色主题适配 ===== */
html[data-theme="Dark"] .glass-card {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

/* ===== 移动端适配 ===== */
@media (max-width: 640px) {
  .discussion-container { padding: 20px 14px 36px; }
  .page-title { font-size: 26px; }
  .post-card { padding: 14px 16px; }
  .post-meta { gap: 10px; font-size: 12px; }
  .modal-content { padding: 22px; }
}
</style>