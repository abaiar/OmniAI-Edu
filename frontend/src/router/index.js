import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'

import Login from '../components/Login.vue'
import Index from '../components/Index.vue'
import ApiManagement from '../components/api-management.vue'
import LearnRoadmap from '../components/LearnRoadmap.vue'
import KnowledgeDetail from '../components/KnowledgeDetail.vue'
import DemoShowcase from '../components/DemoShowcase.vue'
import DigitRecognizer from '../components/DigitRecognizer.vue'
import PracticePage from '../components/PracticePage.vue'
import QuizPage from '../components/QuizPage.vue'
import QuizReport from '../components/QuizReport.vue'
import FeedbackPage from '../components/FeedbackPage.vue'
import Discussion from '../components/Discussion.vue'
import RegisterLogin from '../components/RegisterLogin.vue'
import ProfilePage from '../components/ProfilePage.vue'
import Messages from '../components/Messages.vue'


const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    name: 'Index',
    component: Index,
    meta: { requiresAuth: true }
  },
  {
    path: '/learn',
    name: 'LearnRoadmap',
    component: LearnRoadmap,
    meta: { requiresAuth: true }
  },
  {
    path: '/learn/knowledge/:id',
    name: 'KnowledgeDetail',
    component: KnowledgeDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/demo',
    name: 'DemoShowcase',
    component: DemoShowcase,
    meta: { requiresAuth: true }
  },
  {
    path: '/demo/digit-recognizer',
    name: 'DigitRecognizer',
    component: DigitRecognizer,
    meta: { requiresAuth: true }
  },
  {
    path: '/api-management',
    name: 'ApiManagement',
    component: ApiManagement,
    meta: { requiresAuth: true }
  },
  {
    path: '/practice',
    name: 'PracticePage',
    component: PracticePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/practice/quiz',
    name: 'QuizPage',
    component: QuizPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/practice/report',
    name: 'QuizReport',
    component: QuizReport,
    meta: { requiresAuth: true }
  },
  {
    path: '/feedback',
    name: 'FeedbackPage',
    component: FeedbackPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/discussion',
    name: 'Discussion',
    component: Discussion,
    meta: { requiresAuth: true }
  },
  {
    path: '/auth',
    name: 'Auth',
    component: RegisterLogin
  },
  {
    path: '/profile/:username',
    name: 'Profile',
    component: ProfilePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/messages',
    name: 'Messages',
    component: Messages,
    meta: { requiresAuth: true }
  },
  {
    path: '/messages/:username',
    name: 'Chat',
    component: Messages,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!userStore.isAuthenticated) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router