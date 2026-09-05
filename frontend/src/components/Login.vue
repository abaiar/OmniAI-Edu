<template>
  <div class="login-page">
    <div class="login-box">
      <!-- ===== 登录模式 ===== -->
      <template v-if="mode === 'login'">
        <h1 class="login-title">微信号/QQ号/邮箱登录</h1>

        <form @submit.prevent="handleSubmit" class="login-form" novalidate>
          <div class="form-row">
            <label for="account">帐号</label>
            <input
              id="account"
              v-model="form.username"
              type="text"
              placeholder="微信号/QQ号/邮箱"
              autocomplete="username"
              spellcheck="false"
            >
          </div>

          <div class="form-row">
            <label for="password">密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="请填写密码"
              autocomplete="current-password"
            >
          </div>

          <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

          <button type="submit" class="btn-primary" :disabled="isLoading">
            {{ isLoading ? '登录中...' : '登录' }}
          </button>
        </form>

        <div class="bottom-links">
          <a class="link-left" @click="mode = 'reset'" href="javascript:void(0)">忘记密码？</a>
        </div>

        <p class="register-row">
          还没有账号？<router-link to="/auth">去注册</router-link>
        </p>
      </template>

      <!-- ===== 忘记密码模式 ===== -->
      <template v-else>
        <h1 class="login-title">重置密码</h1>
        <p class="reset-sub">输入注册时使用的账号，通过验证码验证身份后重置密码</p>

        <form @submit.prevent="handleReset" class="login-form" novalidate>
          <div class="form-row">
            <label for="reset-account">帐号</label>
            <input
              id="reset-account"
              v-model="resetForm.account"
              type="text"
              placeholder="手机号 / 邮箱"
              spellcheck="false"
            >
          </div>
          <p class="reset-hint">仅支持通过注册时绑定的手机号或邮箱重置密码</p>

          <div class="form-row">
            <label for="reset-code">验证码</label>
            <div class="code-row">
              <input
                id="reset-code"
                v-model="resetForm.code"
                type="text"
                placeholder="6位验证码"
                maxlength="6"
              >
              <button type="button" class="btn-send" @click="sendResetCode" :disabled="codeSending">
                {{ codeSending ? `${countdown}s` : '获取验证码' }}
              </button>
            </div>
          </div>

          <div v-if="codeHint" class="code-hint-box">
            <span class="hint-label">验证码</span>
            <strong class="hint-code">{{ codeHint }}</strong>
            <span class="hint-note">（调试模式）</span>
          </div>

          <div class="form-row">
            <label for="new-password">新密码</label>
            <input
              id="new-password"
              v-model="resetForm.newPassword"
              type="password"
              placeholder="至少6位新密码"
              autocomplete="new-password"
            >
          </div>

          <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
          <p v-if="successMessage" class="success-msg">{{ successMessage }}</p>

          <button type="submit" class="btn-primary" :disabled="isLoading">
            {{ isLoading ? '提交中...' : '重置密码' }}
          </button>
        </form>

        <p class="register-row">
          <a @click="backToLogin" href="javascript:void(0)">← 返回登录</a>
        </p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const mode = ref('login') // login | reset

const form = reactive({
  username: '',
  password: ''
})

const resetForm = reactive({
  account: '',
  code: '',
  newPassword: ''
})
const codeSending = ref(false)
const countdown = ref(60)
let timer = null
const codeHint = ref('')

const handleSubmit = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (!form.username.trim() || !form.password.trim()) {
    errorMessage.value = '请输入帐号和密码'
    return
  }

  isLoading.value = true
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        method: 'password',
        account: form.username.trim(),
        password: form.password
      })
    })
    const data = await res.json()
    if (data.code === 200) {
      userStore.login(data.data)
      localStorage.setItem('user_id', data.data._id)
      localStorage.setItem('username', data.data.username)
      const redirect = router.currentRoute.value.query.redirect || '/'
      router.push(redirect)
    } else {
      errorMessage.value = data.message || '登录失败'
    }
  } catch (error) {
    errorMessage.value = '网络连接错误，请检查后端服务是否启动'
  } finally {
    isLoading.value = false
  }
}

const sendResetCode = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  codeHint.value = ''

  if (!resetForm.account.trim()) {
    errorMessage.value = '请先输入注册时使用的账号'
    return
  }

  codeSending.value = true
  countdown.value = 60
  try {
    const res = await fetch('/api/auth/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account: resetForm.account.trim() })
    })
    const data = await res.json()
    if (data.code === 200) {
      // 调试模式可能不返回 debug_code（生产防护）
      codeHint.value = data.debug_code || ''
      timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          clearInterval(timer)
          codeSending.value = false
        }
      }, 1000)
    } else {
      errorMessage.value = data.message || '验证码发送失败'
      // QQ/微信账号不支持密码重置
      if (data.unsupported_reset) {
        errorMessage.value = data.message + '，请直接用 QQ/微信 扫码登录'
      } else if (data.code === 404) {
        errorMessage.value = data.message + '（如已注册请用注册时的手机/邮箱）'
      }
      codeSending.value = false
    }
  } catch (e) {
    errorMessage.value = '发送失败，请检查后端服务'
    codeSending.value = false
  }
}

const handleReset = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  const { account, code, newPassword } = resetForm
  if (!account.trim() || !code.trim() || !newPassword) {
    errorMessage.value = '请完整填写账号、验证码和新密码'
    return
  }
  if (newPassword.length < 6) {
    errorMessage.value = '新密码至少6位'
    return
  }

  isLoading.value = true
  try {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account: account.trim(), code: code.trim(), new_password: newPassword })
    })
    const data = await res.json()
    if (data.code === 200) {
      successMessage.value = data.message + '，2秒后返回登录...'
      setTimeout(() => {
        backToLogin()
        form.username = account.trim()
        form.password = ''
      }, 2000)
    } else {
      errorMessage.value = data.message || '重置失败'
    }
  } catch (e) {
    errorMessage.value = '网络错误，请检查后端服务'
  } finally {
    isLoading.value = false
  }
}

const backToLogin = () => {
  mode.value = 'login'
  errorMessage.value = ''
  successMessage.value = ''
  codeHint.value = ''
  clearInterval(timer)
  codeSending.value = false
  resetForm.account = ''
  resetForm.code = ''
  resetForm.newPassword = ''
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url('../../assets/background.jpg');
  background-size: cover;
  background-position: center;
  padding: 24px;
  box-sizing: border-box;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: #ffffff;
  border-radius: 8px;
  padding: 32px 32px 28px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f1f1f;
  margin: 4px 0 28px;
  text-align: left;
  letter-spacing: 0;
}

.reset-sub {
  font-size: 13px;
  color: #888;
  margin: -20px 0 24px;
}

.reset-hint {
  font-size: 12px;
  color: #c0c4cc;
  margin: -10px 0 0;
  padding-left: 2px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-row label {
  font-size: 14px;
  color: #4a4a4a;
  font-weight: 500;
}

.form-row input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: none;
  border-bottom: 1px solid #e5e7eb;
  background: transparent;
  font-size: 15px;
  color: #111;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-row input::placeholder {
  color: #c0c4cc;
}

.form-row input:focus {
  border-bottom-color: #5b8def;
}

.code-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.code-row input {
  flex: 1;
}

.btn-send {
  white-space: nowrap;
  height: 40px;
  padding: 0 16px;
  background: #f1f3f7;
  border: 1px solid #e5e9f0;
  border-radius: 20px;
  color: #1f1f1f;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-send:hover:not(:disabled) {
  border-color: #5b8def;
  color: #5b8def;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.code-hint-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #fff8e1;
  border: 1px solid #ffe0a0;
  border-radius: 8px;
  font-size: 13px;
}

.hint-label { color: #856404; font-size: 12px; }
.hint-code { color: #d97706; font-size: 18px; font-weight: 700; letter-spacing: 2px; }
.hint-note { color: #856404; font-size: 12px; }

.error-msg {
  margin: -4px 0 0;
  color: #e53935;
  font-size: 13px;
  background: #fff5f5;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #ffd6d6;
}

.success-msg {
  margin: -4px 0 0;
  color: #07c160;
  font-size: 13px;
  background: #f0fff4;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #c8f7d4;
}

.btn-primary {
  margin-top: 8px;
  height: 44px;
  border: none;
  border-radius: 22px;
  background: linear-gradient(90deg, #5b8def, #6f7cff);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.btn-primary:hover:not(:disabled) { opacity: 0.92; }
.btn-primary:active:not(:disabled) { transform: translateY(1px); }
.btn-primary:disabled { background: #b9c4e3; cursor: not-allowed; }

.bottom-links {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.link-left {
  font-size: 13px;
  color: #5b8def;
  cursor: pointer;
  font-weight: 500;
}

.link-left:hover { text-decoration: underline; }

.register-row {
  margin: 18px 0 0;
  text-align: center;
  font-size: 13px;
  color: #888;
}

.register-row a {
  color: #5b8def;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.register-row a:hover { text-decoration: underline; }

@media (max-width: 480px) {
  .login-box { padding: 28px 22px 22px; }
  .login-title { font-size: 20px; }
}
</style>
