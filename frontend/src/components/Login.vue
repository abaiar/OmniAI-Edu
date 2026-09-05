<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-container">
          <div class="logo-bg" style="background-image: url('../../static/img/touxiang.jpg');"></div>
          <img src="../../static/img/logokuang.png" alt="Logo" class="logo-frame">
        </div>
        <h2>教师助手系统</h2>
        <p class="subtitle">{{ isLoginMode ? '账号登录' : '新用户注册' }}</p>
      </div>
      
      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input 
            type="text" 
            id="username" 
            v-model="form.username" 
            placeholder="请输入用户名"
            required
          >
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input 
            type="password" 
            id="password" 
            v-model="form.password" 
            placeholder="请输入密码"
            required
          >
        </div>

        <div class="form-group" v-if="!isLoginMode">
          <label for="confirmPassword">确认密码</label>
          <input 
            type="password" 
            id="confirmPassword" 
            v-model="form.confirmPassword" 
            placeholder="请再次输入密码"
            required
          >
        </div>

        <div class="form-group" v-if="!isLoginMode">
          <label for="class_name">班级</label>
          <input 
            type="text" 
            id="class_name" 
            v-model="form.class_name" 
            placeholder="请输入班级"
          >
        </div> 

        <div class="form-group" v-if="!isLoginMode">
          <label for="cstudent_id">学号</label>
          <input 
            type="text" 
            id="student_id" 
            v-model="form.student_id" 
            placeholder="请输入学号"
          >
        </div>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>
        
        <button type="submit" class="login-button" :disabled="isLoading">
          {{ isLoading ? '处理中...' : (isLoginMode ? '登录' : '立即注册') }}
        </button>
      </form>
      
      <div class="toggle-mode">
        <span v-if="isLoginMode">
          还没有账号？ <a href="#" @click.prevent="toggleMode">去注册</a>
        </span>
        <span v-else>
          已有账号？ <a href="#" @click.prevent="toggleMode">去登录</a>
        </span>
      </div>

      <div class="login-footer">
        <p>教师助手系统 © 2026</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import axios from 'axios'
import { getServiceUrl } from '../config/api'

const router = useRouter()
const userStore = useUserStore()

const LOGIN_BASE_URL = ''

const isLoginMode = ref(true)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  class_name: '',
  student_id: ''
})

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
  errorMessage.value = ''
  successMessage.value = ''
  form.password = ''
  form.confirmPassword = ''
}

const handleSubmit = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  
  if (!isLoginMode.value && form.password !== form.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  isLoading.value = true

  const formData = new FormData()
  formData.append('username', form.username)
  formData.append('password', form.password)
  if (!isLoginMode.value){
    formData.append('class_name', form.class_name)
    formData.append('student_id', form.student_id)
  }

  const url = isLoginMode.value ? `${LOGIN_BASE_URL}/login` : `${LOGIN_BASE_URL}/register`

  try {
    const response = await axios.post(url, formData)
    
    if (response.data.success) {
      if (isLoginMode.value) {
        console.log('登录成功:', response.data.user)
        userStore.login(response.data.user)
        router.push('/') 
      } else {
        successMessage.value = '注册成功！请登录。'
        setTimeout(() => {
          toggleMode()
          form.password = ''
        }, 1000)
      }
    }
  } catch (error) {
    console.error('请求失败:', error)
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || '操作失败'
    } else {
      errorMessage.value = '网络连接错误，请检查后端服务是否启动'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* 保持原有样式，新增部分辅助样式 */
.login-container {
  height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  /* 使用你的背景图 */
  background-image: url('../../assets/background.jpg'); 
  background-size: cover;
  background-position: center;
}

.login-box {
  background-color: rgba(255, 255, 255, 0.95);
  padding: 2.5rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 420px;
  backdrop-filter: blur(5px);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.subtitle {
  color: #666;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.logo-container {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 1rem auto;
}

.logo-bg {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-size: cover;
  background-position: center;
  position: relative;
}

.logo-frame {
  position: absolute;
  top: -15%;
  left: -10%;
  width: 120%;
  aspect-ratio: 1/1;
  pointer-events: none;
}

.login-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #4a5568;
  font-weight: 500;
  font-size: 0.95rem;
}

.form-group input {
  padding: 0.8rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.1);
}

.error-message {
  color: #e53e3e;
  font-size: 0.9rem;
  text-align: center;
  background-color: #fff5f5;
  padding: 0.5rem;
  border-radius: 6px;
}

.success-message {
  color: #38a169;
  font-size: 0.9rem;
  text-align: center;
  background-color: #f0fff4;
  padding: 0.5rem;
  border-radius: 6px;
}

.login-button {
  background-color: #42b983;
  color: white;
  padding: 0.9rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 0.5rem;
}

.login-button:hover {
  background-color: #3aa876;
}

.login-button:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.toggle-mode {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.95rem;
  color: #718096;
}

.toggle-mode a {
  color: #42b983;
  text-decoration: none;
  font-weight: 600;
}

.toggle-mode a:hover {
  text-decoration: underline;
}

.login-footer {
  text-align: center;
  margin-top: 2rem;
  color: #a0aec0;
  font-size: 0.85rem;
}
</style>
