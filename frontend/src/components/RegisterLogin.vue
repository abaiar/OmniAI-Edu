<template>
  <div class="auth-page">
    <!-- Toast 通知 -->
    <transition name="toast-slide">
      <div v-if="toast.show" class="toast" :class="toast.type" @click="toast.show = false">
        {{ toast.msg }}
      </div>
    </transition>

    <div class="glass-card auth-box">
      <h1 class="auth-title">注册账号</h1>
      <p class="auth-sub">完成注册后即可使用教师助手全部功能</p>

      <div class="tab-bar">
        <button :class="{ active: tab === 'code' }" @click="tab='code'">验证码注册</button>
        <button :class="{ active: tab === 'password' }" @click="tab='password'">密码注册</button>
      </div>

      <!-- ===== 验证码注册 ===== -->
      <form v-if="tab === 'code'" @submit.prevent="handleCodeRegister">
        <input v-model="form.account" class="glass-input" placeholder="QQ号 / 微信号 / 邮箱 / 手机号" required />

        <div class="code-row">
          <input v-model="form.code" class="glass-input" placeholder="验证码" required />
          <button type="button" class="btn-send-code" @click="sendCode" :disabled="codeSending">
            {{ codeSending ? `${countdown}s` : '发送验证码' }}
          </button>
        </div>

        <div v-if="codeHint" class="code-hint-box">
          <span class="hint-label">验证码</span>
          <strong class="hint-code">{{ codeHint }}</strong>
          <span class="hint-note">（调试模式：未配置邮箱/短信凭证时显示在此处）</span>
        </div>

        <input v-model="form.password" type="password" class="glass-input" placeholder="设置登录密码（至少 6 位）" required minlength="6" />
        <input v-model="form.confirm" type="password" class="glass-input" placeholder="再次输入密码" required minlength="6" />

        <button type="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? '注册中...' : '注册并登录' }}
        </button>
      </form>

      <!-- ===== 密码注册 ===== -->
      <form v-else @submit.prevent="handlePasswordRegister">
        <input v-model="form.username" class="glass-input" placeholder="用户名" required minlength="3" />
        <input v-model="form.password" type="password" class="glass-input" placeholder="密码（至少 6 位）" required minlength="6" />
        <input v-model="form.confirm" type="password" class="glass-input" placeholder="再次输入密码" required minlength="6" />

        <button type="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? '注册中...' : '注册并登录' }}
        </button>
      </form>

      <p class="switch-link">
        已有账号？<router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import { useUserStore } from '../store/user'

const AUTH_BASE = '/api/auth'

export default {
  data() {
    return {
      tab: 'code',
      form: {
        username: '',
        password: '',
        confirm: '',
        phone: '',
        email: '',
        account: '',
        code: ''
      },
      codeSending: false,
      countdown: 60,
      timer: null,
      codeHint: '',
      codeHintNote: '',
      submitting: false,
      toast: { show: false, msg: '', type: 'info', timer: null }
    }
  },
  methods: {
    showToast(msg, type = 'info') {
      clearTimeout(this.toast.timer)
      this.toast = { show: true, msg, type, timer: setTimeout(() => { this.toast.show = false }, 3500) }
    },
    resetForm() {
      this.form = { username: '', password: '', confirm: '', phone: '', email: '', account: '', code: '' }
      this.codeHint = ''
    },
    handleAuthSuccess(userData, tip) {
      const userStore = useUserStore()
      userStore.login(userData)
      localStorage.setItem('user_id', userData._id)
      localStorage.setItem('username', userData.username)
      this.showToast(tip, 'success')
      setTimeout(() => {
        const redirect = this.$route.query.redirect || '/'
        this.$router.push(redirect)
      }, 600)
    },
    startCountdown(field, sendingField) {
      const t = setInterval(() => {
        this[field]--
        if (this[field] <= 0) {
          clearInterval(t)
          this[sendingField] = false
        }
      }, 1000)
      return t
    },
    /* ====== 发送验证码 ====== */
    async sendCode() {
      if (!this.form.account) return this.showToast('请输入QQ号/微信号/邮箱/手机号', 'error')
      this.codeSending = true
      this.countdown = 60
      this.codeHint = ''
      try {
        const res = await fetch(`${AUTH_BASE}/send-code`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ account: this.form.account, purpose: 'register' })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.codeHint = data.debug_code || ''
          this.showToast(data.dev_mode ? '验证码已生成（调试模式见下方）' : '验证码已发送，请注意查收', 'success')
          this.timer = this.startCountdown('countdown', 'codeSending')
        } else {
          this.showToast(data.message, 'error')
          this.codeSending = false
        }
      } catch (e) {
        this.showToast('发送失败，请检查后端服务', 'error')
        this.codeSending = false
      }
    },
    /* ====== 验证码注册 ====== */
    async handleCodeRegister() {
      const { account, code, password, confirm } = this.form
      if (!account || !code || !password) return this.showToast('请完整填写信息', 'error')
      if (password !== confirm) return this.showToast('两次输入的密码不一致', 'error')

      this.submitting = true
      try {
        const res = await fetch(`${AUTH_BASE}/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ method: 'code', account, code, password })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.handleAuthSuccess(data.data, '注册成功')
        } else {
          this.showToast(data.message, 'error')
        }
      } catch (e) {
        this.showToast('网络错误，请检查后端服务', 'error')
      } finally {
        this.submitting = false
      }
    },
    /* ====== 密码注册 ====== */
    async handlePasswordRegister() {
      const { username, password, confirm } = this.form
      if (!username || !password) return this.showToast('请填写用户名和密码', 'error')
      if (password.length < 6) return this.showToast('密码至少 6 位', 'error')
      if (password !== confirm) return this.showToast('两次输入的密码不一致', 'error')

      this.submitting = true
      try {
        const res = await fetch(`${AUTH_BASE}/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            method: 'password',
            username,
            password
          })
        })
        const data = await res.json()
        if (data.code === 200) {
          this.handleAuthSuccess(data.data, '注册成功')
        } else {
          this.showToast(data.message, 'error')
        }
      } catch (e) {
        this.showToast('网络错误，请检查后端服务', 'error')
      } finally {
        this.submitting = false
      }
    },
    handleOAuthCallback() {
      const params = new URLSearchParams(window.location.search)
      const error = params.get('error')
      if (error) {
        this.showToast(`授权失败：${error}`, 'error')
      }
    }
  },
  mounted() {
    this.handleOAuthCallback()
  },
  beforeUnmount() {
    clearInterval(this.timer)
    clearTimeout(this.toast.timer)
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url('../../assets/background.jpg');
  background-size: cover;
  background-position: center;
  padding: 24px;
  box-sizing: border-box;
}

/* ===== 玻璃拟态卡片 ===== */
.glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px) saturate(1.2);
  -webkit-backdrop-filter: blur(12px) saturate(1.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  border-radius: 14px;
}

.auth-box {
  padding: 32px 30px 28px;
  width: 420px;
  max-width: 100%;
}

/* ===== 标题 ===== */
.auth-title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: #1f1f1f;
  margin: 0 0 4px;
}

.auth-sub {
  text-align: center;
  font-size: 13px;
  color: #888;
  margin: 0 0 22px;
}

/* ===== Tab 切换 ===== */
.tab-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 18px;
  background: #f1f3f7;
  border-radius: 10px;
  padding: 4px;
}

.tab-bar button {
  flex: 1;
  padding: 8px;
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

/* ===== 输入框 ===== */
.glass-input {
  width: 100%;
  padding: 11px 14px;
  background: #f7f9fc;
  border: 1px solid #e5e9f0;
  border-radius: 8px;
  color: #1f1f1f;
  font-size: 14px;
  box-sizing: border-box;
  margin-bottom: 10px;
  transition: border-color 0.25s, box-shadow 0.25s;
}

.glass-input::placeholder {
  color: #aab2bd;
}

.glass-input:focus {
  outline: none;
  border-color: #5b8def;
  box-shadow: 0 0 0 3px rgba(91, 141, 239, 0.12);
  background: #fff;
}

/* ===== 验证码行 ===== */
.code-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.code-row .glass-input {
  flex: 1;
  margin-bottom: 0;
}

.btn-send-code {
  white-space: nowrap;
  padding: 11px 16px;
  background: #f1f3f7;
  border: 1px solid #e5e9f0;
  border-radius: 8px;
  color: #1f1f1f;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s, border-color 0.2s;
}

.btn-send-code:hover:not(:disabled) {
  background: #e7ecf5;
  border-color: #5b8def;
}

.btn-send-code:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== 验证码提示框 ===== */
.code-hint-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #fff8e1;
  border: 1px solid #ffe0a0;
  border-radius: 8px;
  margin-bottom: 14px;
  font-size: 13px;
}

.hint-label {
  color: #856404;
  font-size: 12px;
}

.hint-code {
  color: #d97706;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
}

.hint-note {
  color: #856404;
  font-size: 12px;
}

/* ===== 按钮 ===== */
.btn-primary {
  width: 100%;
  padding: 12px;
  background: linear-gradient(90deg, #5b8def, #6f7cff);
  color: #fff;
  border: none;
  border-radius: 22px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 6px;
  transition: opacity 0.2s, transform 0.1s;
  height: 44px;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.92;
}

.btn-primary:active:not(:disabled) {
  transform: translateY(1px);
}

.btn-primary:disabled {
  background: #b9c4e3;
  cursor: not-allowed;
}

/* ===== 切换链接 ===== */
.switch-link {
  text-align: center;
  margin-top: 18px;
  font-size: 13px;
  color: #888;
}

.switch-link a {
  color: #5b8def;
  text-decoration: none;
  font-weight: 500;
}

.switch-link a:hover {
  text-decoration: underline;
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

.toast.success {
  background: #07c160;
  color: #fff;
}

.toast.error {
  background: #e53935;
  color: #fff;
}

.toast.info {
  background: #5b8def;
  color: #fff;
}

/* ===== 过渡动画 ===== */
.toast-slide-enter-active, .toast-slide-leave-active {
  transition: all 0.3s ease;
}

.toast-slide-enter-from, .toast-slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-12px);
}

/* ===== 移动端 ===== */
@media (max-width: 480px) {
  .auth-box {
    padding: 24px 20px;
  }
  .auth-title {
    font-size: 20px;
  }
}
</style>
