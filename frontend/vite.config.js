import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    open: true,
    proxy: {
      // 登录服务 (5000)
      '/login': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/register': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      // API管理服务 (5010)
      '/api/theme': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true
      },
      '/api/providers': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true
      },
      '/api/config': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true
      },
      '/api/health': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true
      },
      '/api/test-connection': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true
      },
      '/api/check-model': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true
      },
      '/api/openmaic': {
        target: 'http://127.0.0.1:5010',
        changeOrigin: true
      },
      // 手写数字识别服务 (5005)
      '/api/digit': {
        target: 'http://127.0.0.1:5005',
        changeOrigin: true
      },
      // 练习反馈服务 (5011)
      '/api/practice': {
        target: 'http://127.0.0.1:5011',
        changeOrigin: true
      },
      '/api/agent': {
        target: 'http://127.0.0.1:5011',
        changeOrigin: true
      },
      // 多方式认证服务 (5021)
      '/api/auth': {
        target: 'http://127.0.0.1:5021',
        changeOrigin: true
      },
      // 讨论区服务 (5020)
      '/api/discussions': {
        target: 'http://127.0.0.1:5020',
        changeOrigin: true
      },
      // 社交服务：个人主页/关注/私信 (5022)
      '/api/social': {
        target: 'http://127.0.0.1:5022',
        changeOrigin: true
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts']
        }
      }
    },
    commonjsOptions: {
      transformMixedEsModules: true
    }
  },
  optimizeDeps: {
    include: ['echarts']
  }
})