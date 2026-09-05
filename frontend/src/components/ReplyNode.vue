<template>
  <div class="reply-node" :style="{ marginLeft: indentPx }">
    <div class="reply-item">
      <div class="reply-header">
        <span class="avatar-dot sm link-author" @click="goProfile(reply.username)" title="查看TA的主页">{{ (reply.username || '匿名').charAt(0) }}</span>
        <strong class="link-author" @click="goProfile(reply.username)" title="查看TA的主页">{{ reply.username }}</strong>
        <span v-if="reply.reply_to_username" class="reply-to">回复 @{{ reply.reply_to_username }}</span>
        <small>{{ formatTime(reply.created_at) }}</small>
        <span
          v-if="currentUsername && reply.username !== currentUsername"
          class="meta-btn dm-btn"
          @click="goChat(reply.username)"
          title="私信TA"
        >✉️</span>
      </div>
      <p class="reply-text">{{ reply.content }}</p>
      <div class="reply-actions">
        <span
          class="meta-btn like-btn"
          :class="{ active: reply.is_liked }"
          @click="$emit('like', reply)"
          :title="reply.is_liked ? '取消点赞' : '点赞'"
        >
          <span class="icon-heart">{{ reply.is_liked ? '♥' : '♡' }}</span> {{ reply.likes || 0 }}
        </span>
        <span
          class="meta-btn fav-btn"
          :class="{ active: reply.is_favorited }"
          @click="$emit('favorite', reply)"
        >
          <span class="icon-star">{{ reply.is_favorited ? '★' : '☆' }}</span>
          {{ reply.is_favorited ? '已收藏' : '收藏' }}
        </span>
        <span class="meta-btn reply-btn" @click="$emit('reply', { postId: postId, target: reply })">
          💬 回复
        </span>
        <span class="meta-btn share-btn" @click="$emit('share', reply)">
          🔗 分享 ({{ reply.shares || 0 }})
        </span>
        <span
          v-if="isOwn"
          class="meta-btn delete-btn"
          @click="$emit('delete-reply', reply)"
        >
          🗑 删除
        </span>
      </div>
    </div>

    <!-- 递归渲染子回复 -->
    <div v-if="reply.replies?.length" class="nested-replies">
      <reply-node
        v-for="child in reply.replies"
        :key="child._id"
        :reply="child"
        :depth="depth + 1"
        :post-id="postId"
        :current-user-id="currentUserId"
        :current-username="currentUsername"
        @reply="$emit('reply', $event)"
        @like="$emit('like', $event)"
        @favorite="$emit('favorite', $event)"
        @share="$emit('share', $event)"
        @delete-reply="$emit('delete-reply', $event)"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReplyNode',
  props: {
    reply: { type: Object, required: true },
    depth: { type: Number, default: 0 },
    postId: { type: String, required: true },
    currentUserId: { type: String, default: '' },
    currentUsername: { type: String, default: '' }
  },
  emits: ['reply', 'like', 'favorite', 'share', 'delete-reply'],
  computed: {
    indentPx() {
      return Math.min(this.depth * 20, 80) + 'px'
    },
    isOwn() {
      return this.currentUserId && String(this.reply.user_id || '') === String(this.currentUserId)
    }
  },
  methods: {
    formatTime(t) {
      if (!t) return ''
      return new Date(t).toLocaleString('zh-CN')
    },
    goProfile(username) {
      if (!username) return
      this.$router.push(`/profile/${encodeURIComponent(username)}`)
    },
    goChat(username) {
      if (!username) return
      this.$router.push(`/messages/${encodeURIComponent(username)}`)
    }
  }
}
</script>

<style scoped>
.reply-node {
  position: relative;
}
.link-author {
  cursor: pointer;
  transition: opacity 0.2s;
}
.link-author:hover {
  opacity: 0.75;
  text-decoration: underline;
}
.dm-btn {
  color: #5b8def;
  font-size: 12px;
}
.reply-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 8px;
}
.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.reply-header strong {
  color: var(--item_left_title_color, rgba(255, 255, 255, 0.9));
  font-size: 13px;
}
.reply-header small {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  margin-left: auto;
}
.reply-to {
  color: rgba(108, 92, 231, 0.85);
  font-size: 12px;
  font-weight: 500;
}
.reply-text {
  margin: 0 0 8px;
  color: var(--item_left_text_color, rgba(255, 255, 255, 0.75));
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.reply-actions {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  flex-wrap: wrap;
}
.reply-actions .meta-btn {
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s, transform 0.2s;
}
.reply-actions .meta-btn:hover {
  color: #a29bfe;
  transform: scale(1.05);
}
.reply-actions .like-btn.active {
  color: #ff6b9d;
}
.reply-actions .fav-btn.active {
  color: #ffd93d;
}
.reply-actions .delete-btn:hover {
  color: #ff6b6b !important;
}
.icon-heart, .icon-star {
  font-size: 14px;
}
.nested-replies {
  margin-left: 0;
}
</style>