<template>
  <div class="profile-page">
    <!-- Toast -->
    <transition name="toast-slide">
      <div v-if="toast.show" class="toast" :class="toast.type" @click="toast.show = false">{{ toast.msg }}</div>
    </transition>

    <div v-if="loading" class="empty-tip">加载中...</div>
    <div v-else-if="!profile" class="empty-tip">用户不存在 <router-link to="/discussion">返回讨论区</router-link></div>

    <template v-else>
      <!-- ===== 头部：头像 + 名称 + 简介 + 操作 ===== -->
      <div class="glass-card profile-header">
        <div class="avatar-big">{{ (profile.user.username || '?').charAt(0).toUpperCase() }}</div>

        <div class="profile-info">
          <div class="name-row">
            <h2 class="username">{{ profile.user.username }}</h2>
            <span v-if="profile.is_self" class="self-badge">我</span>
          </div>
          <p class="bio" v-if="!editingBio">{{ profile.user.bio || (profile.is_self ? '点击右侧"编辑"添加个人简介' : '这个人很懒，什么都没有写~') }}</p>
          <div v-else class="bio-edit-row">
            <input v-model="bioDraft" class="glass-input" maxlength="200" placeholder="写一段个人简介（200字以内）" />
            <button class="btn-mini" @click="saveBio">保存</button>
            <button class="btn-mini ghost" @click="editingBio = false">取消</button>
          </div>
          <p class="join-time">加入于 {{ formatDate(profile.user.created_at) }}</p>
        </div>

        <div class="profile-actions">
          <template v-if="!profile.is_self">
            <button class="btn-primary sm" :class="{ following: profile.is_following }" @click="toggleFollow">
              {{ profile.is_following ? '已关注' : '+ 关注' }}
            </button>
            <button class="btn-primary sm ghost" @click="goChat">私信</button>
          </template>
          <button v-else class="btn-primary sm ghost" @click="startEditBio">编辑资料</button>
        </div>
      </div>

      <!-- ===== 数据统计栏 ===== -->
      <div class="glass-card stats-bar">
        <div class="stat-item" @click="showFollowList('following')">
          <strong>{{ profile.stats.following }}</strong>
          <span>关注</span>
        </div>
        <div class="stat-item" @click="showFollowList('followers')">
          <strong>{{ profile.stats.followers }}</strong>
          <span>粉丝</span>
        </div>
        <div class="stat-item">
          <strong>{{ profile.stats.likes_received }}</strong>
          <span>获赞</span>
        </div>
        <div class="stat-item">
          <strong>{{ profile.stats.favorites_received }}</strong>
          <span>获收藏</span>
        </div>
        <div class="stat-item">
          <strong>{{ profile.stats.views }}</strong>
          <span>浏览</span>
        </div>
        <div class="stat-item">
          <strong>{{ profile.stats.posts }}</strong>
          <span>发帖</span>
        </div>
      </div>

      <!-- ===== 内容分栏 ===== -->
      <div class="glass-card content-card">
        <div class="tab-bar">
          <button :class="{ active: contentTab === 'public' }" @click="contentTab = 'public'">
            🌐 公开内容 ({{ posts.public.length }})
          </button>
          <button v-if="profile.is_self" :class="{ active: contentTab === 'private' }" @click="contentTab = 'private'">
            🔒 私密内容 ({{ posts.private.length }})
          </button>
        </div>

        <div class="post-list">
          <div v-if="currentPosts.length === 0" class="empty-tip">
            {{ contentTab === 'public' ? '暂无公开内容' : '暂无私密内容' }}
          </div>
          <div v-for="post in currentPosts" :key="post._id" class="post-item clickable" @click="viewPost(post._id)">
            <div class="post-item-head">
              <h4 class="post-item-title">
                {{ post.is_private ? '🔒 ' : '' }}{{ post.title }} <span class="open-hint">打开 ›</span>
              </h4>
              <span
                v-if="profile.is_self"
                class="visibility-toggle"
                @click.stop="toggleVisibility(post)"
                :title="post.is_private ? '设为公开' : '设为私密'"
              >
                {{ post.is_private ? '🔒 转公开' : '🌐 转私密' }}
              </span>
            </div>
            <p class="post-item-content">{{ post.content.substring(0, 100) }}{{ post.content.length > 100 ? '...' : '' }}</p>
            <div class="post-item-meta">
              <span>❤️ {{ post.likes || 0 }}</span>
              <span>👁️ {{ post.views || 0 }}</span>
              <span>{{ formatTime(post.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ===== 关注/粉丝列表弹窗 ===== -->
    <transition name="modal-fade">
      <div v-if="followListVisible" class="modal-overlay" @click.self="followListVisible = false">
        <div class="glass-card modal-content">
          <h3 class="modal-title">{{ followListType === 'following' ? '关注列表' : '粉丝列表' }}</h3>
          <div v-if="followList.length === 0" class="empty-tip">暂无{{ followListType === 'following' ? '关注' : '粉丝' }}</div>
          <div v-for="u in followList" :key="u.username" class="follow-item" @click="goProfile(u.username)">
            <span class="avatar-dot">{{ (u.username || '?').charAt(0) }}</span>
            <div class="follow-info">
              <strong>{{ u.username }}</strong>
              <small>{{ u.bio || '' }}</small>
            </div>
          </div>
          <button class="btn-ghost close-btn" @click="followListVisible = false">关闭</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
const API_BASE = '/api/social'

export default {
  name: 'ProfilePage',
  data() {
    return {
      loading: true,
      profile: null,
      posts: { public: [], private: [] },
      contentTab: 'public',
      editingBio: false,
      bioDraft: '',
      followListVisible: false,
      followListType: 'following',
      followList: [],
      toast: { show: false, msg: '', type: 'info', timer: null }
    }
  },
  computed: {
    currentPosts() {
      return this.contentTab === 'public' ? this.posts.public : this.posts.private
    },
    currentUserId() {
      return localStorage.getItem('user_id') || ''
    },
    currentUsername() {
      return localStorage.getItem('username') || ''
    }
  },
  watch: {
    '$route.params.username': {
      immediate: true,
      handler() { this.load() }
    }
  },
  methods: {
    showToast(msg, type = 'info') {
      clearTimeout(this.toast.timer)
      this.toast = { show: true, msg, type, timer: setTimeout(() => { this.toast.show = false }, 3000) }
    },
    async load() {
      this.loading = true
      const username = this.$route.params.username
      try {
        const [pRes, postsRes] = await Promise.all([
          fetch(`${API_BASE}/profile/${encodeURIComponent(username)}?viewer_id=${this.currentUserId}`),
          fetch(`${API_BASE}/posts/${encodeURIComponent(username)}?viewer_id=${this.currentUserId}`)
        ])
        const p = await pRes.json()
        const postsData = await postsRes.json()
        if (p.code === 200) this.profile = p.data
        if (postsData.code === 200) this.posts = postsData.data
        if (this.contentTab === 'private' && !(this.profile?.is_self)) this.contentTab = 'public'
      } catch (e) {
        this.showToast('加载失败，请检查后端服务', 'error')
      } finally {
        this.loading = false
      }
    },
    async toggleFollow() {
      if (!this.currentUserId) return this.showToast('请先登录', 'error')
      try {
        const res = await fetch(`${API_BASE}/follow`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: this.currentUserId, target_username: this.$route.params.username })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.profile.is_following = data.data.following
          this.profile.stats.following += data.data.following ? 1 : -1
          this.showToast(data.message, 'success')
        } else {
          this.showToast(data.message, 'error')
        }
      } catch (e) {
        this.showToast('操作失败', 'error')
      }
    },
    async toggleVisibility(post) {
      try {
        const res = await fetch(`${API_BASE}/posts/${post._id}/visibility`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: this.currentUserId })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.showToast(data.message, 'success')
          this.load()
        } else {
          this.showToast(data.message, 'error')
        }
      } catch (e) {
        this.showToast('操作失败', 'error')
      }
    },
    startEditBio() {
      this.bioDraft = this.profile.user.bio || ''
      this.editingBio = true
    },
    async saveBio() {
      try {
        const res = await fetch(`${API_BASE}/profile/${encodeURIComponent(this.$route.params.username)}/bio`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: this.currentUserId, bio: this.bioDraft })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.profile.user.bio = this.bioDraft
          this.editingBio = false
          this.showToast('简介已更新', 'success')
        } else {
          this.showToast(data.message, 'error')
        }
      } catch (e) {
        this.showToast('保存失败', 'error')
      }
    },
    async showFollowList(type) {
      this.followListType = type
      this.followListVisible = true
      try {
        const res = await fetch(`${API_BASE}/follow/list/${encodeURIComponent(this.$route.params.username)}?type=${type}`)
        const data = await res.json()
        if (data.code === 200) this.followList = data.data.users
      } catch (e) {
        this.showToast('加载失败', 'error')
      }
    },
    goChat() {
      this.$router.push(`/messages/${encodeURIComponent(this.$route.params.username)}`)
    },
    goProfile(username) {
      this.followListVisible = false
      this.$router.push(`/profile/${encodeURIComponent(username)}`)
    },
    viewPost(postId) {
      this.$router.push(`/discussion?post=${postId}`)
    },
    formatDate(dt) {
      if (!dt) return ''
      return new Date(dt).toLocaleDateString('zh-CN')
    },
    formatTime(dt) {
      if (!dt) return ''
      const d = new Date(dt)
      const diff = (Date.now() - d.getTime()) / 1000
      if (diff < 60) return '刚刚'
      if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
      if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
      if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`
      return d.toLocaleDateString('zh-CN')
    }
  }
}
</script>

<style scoped>
.profile-page {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px 16px 60px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-radius: 14px;
}

/* ===== 头部 ===== */
.profile-header {
  display: flex;
  gap: 20px;
  padding: 24px 28px;
  align-items: center;
  flex-wrap: wrap;
}

.avatar-big {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b8def, #6f7cff);
  color: #fff;
  font-size: 36px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-info { flex: 1; min-width: 220px; }

.name-row { display: flex; align-items: center; gap: 8px; }

.username { margin: 0; font-size: 22px; color: #1f1f1f; }

.self-badge {
  background: #5b8def;
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
}

.bio { margin: 8px 0 4px; font-size: 14px; color: #555; }

.bio-edit-row { display: flex; gap: 8px; margin: 8px 0 4px; }
.bio-edit-row .glass-input { flex: 1; margin-bottom: 0; }

.join-time { margin: 4px 0 0; font-size: 12px; color: #999; }

.profile-actions { display: flex; gap: 10px; }

/* ===== 统计栏 ===== */
.stats-bar {
  display: flex;
  margin-top: 16px;
  padding: 16px 10px;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  border-radius: 8px;
  padding: 6px 0;
  transition: background 0.2s;
}

.stat-item:hover { background: #f1f4fb; }

.stat-item strong { font-size: 20px; color: #1f1f1f; }
.stat-item span { font-size: 12px; color: #888; }

/* ===== 内容 ===== */
.content-card { margin-top: 16px; padding: 20px 24px; }

.tab-bar {
  display: flex;
  gap: 6px;
  background: #f1f3f7;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 16px;
}

.tab-bar button {
  flex: 1;
  padding: 9px;
  border: none;
  background: transparent;
  color: #5a5a5a;
  border-radius: 7px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.25s;
}

.tab-bar button.active {
  background: linear-gradient(135deg, #5b8def, #6f7cff);
  color: #fff;
  box-shadow: 0 2px 8px rgba(91, 141, 239, 0.3);
}

.post-item {
  padding: 14px 4px;
  border-bottom: 1px solid #f0f2f6;
}

.post-item:last-child { border-bottom: none; }

.post-item.clickable {
  cursor: pointer;
  border-radius: 10px;
  padding: 14px 12px;
  margin: 4px 0;
  transition: background 0.15s, transform 0.15s;
}

.post-item.clickable:hover {
  background: #f5f8ff;
  transform: translateX(2px);
}

.post-item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.post-item-title {
  margin: 0;
  font-size: 15px;
  color: #1f1f1f;
  cursor: pointer;
}

.post-item-title:hover { color: #5b8def; }

.open-hint {
  font-size: 12px;
  font-weight: normal;
  color: #5b8def;
  margin-left: 6px;
}

.visibility-toggle {
  font-size: 12px;
  color: #5b8def;
  cursor: pointer;
  white-space: nowrap;
  padding: 4px 10px;
  border: 1px solid #e0e8f7;
  border-radius: 12px;
  transition: all 0.2s;
}

.visibility-toggle:hover { background: #f0f4ff; }

.post-item-content {
  margin: 8px 0;
  font-size: 13px;
  color: #666;
}

.post-item-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

/* ===== 按钮 ===== */
.btn-primary.sm {
  width: auto;
  padding: 8px 20px;
  height: auto;
  margin-top: 0;
  font-size: 13px;
}

.btn-primary.sm.following {
  background: #f1f3f7;
  color: #666;
}

.btn-primary.sm.ghost {
  background: transparent;
  color: #5b8def;
  border: 1px solid #5b8def;
}

.btn-mini {
  padding: 8px 16px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(90deg, #5b8def, #6f7cff);
  color: #fff;
  font-size: 12px;
  cursor: pointer;
}

.btn-mini.ghost {
  background: #f1f3f7;
  color: #666;
}

.glass-input {
  padding: 10px 14px;
  background: #f7f9fc;
  border: 1px solid #e5e9f0;
  border-radius: 8px;
  color: #1f1f1f;
  font-size: 14px;
  box-sizing: border-box;
  outline: none;
}

.glass-input:focus { border-color: #5b8def; }

/* ===== 关注列表 ===== */
.follow-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
}

.follow-item:hover { background: #f5f7fc; }

.avatar-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b8def, #6f7cff);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.follow-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.follow-info strong {
  color: #1f1f1f;
  font-weight: 600;
  font-size: 14px;
}
.follow-info small { color: #6b7280; font-size: 12px; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  width: 100%;
  max-width: 400px;
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.modal-title { margin: 0 0 14px; font-size: 17px; color: #1f1f1f; text-align: center; }

.close-btn {
  width: 100%;
  margin-top: 14px;
  padding: 9px;
  border: 1px solid #e0e5ef;
  border-radius: 8px;
  background: transparent;
  color: #666;
  cursor: pointer;
}

.btn-ghost:hover { border-color: #5b8def; color: #5b8def; }

.empty-tip { text-align: center; color: #999; padding: 30px 0; font-size: 14px; }
.empty-tip a { color: #5b8def; text-decoration: none; }

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

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.25s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

@media (max-width: 600px) {
  .profile-header { flex-direction: column; text-align: center; }
  .profile-info { width: 100%; }
  .profile-actions { justify-content: center; width: 100%; }
  .stats-bar { flex-wrap: wrap; }
  .stat-item { min-width: 33%; }
}
</style>
