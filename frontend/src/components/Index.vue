<template>
  <div class="zyyo-filter"></div>
  <div class="zyyo-main">
    <div class="zyyo-left">
      <div class="logo" style="background-image: url('../../static/img/touxiang.jpg');">
        <img style="position: absolute;top:-15%;left:-10%;width: 120%; aspect-ratio: 1/1;" src="../../static/img/logokuang.png">
      </div>
      <div class="left-div left-des">
        <div class="left-des-item">
          <svg t="1705773709627" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1478">
            <path d="M512 249.976471c-99.388235 0-180.705882 81.317647-180.705882 180.705882s81.317647 180.705882 180.705882 180.705882 180.705882-81.317647 180.705882-180.705882-81.317647-180.705882-180.705882-180.705882z m0 301.17647c-66.258824 0-120.470588-54.211765-120.470588-120.470588s54.211765-120.470588 120.470588-120.470588 120.470588 54.211765 120.470588 120.470588-54.211765 120.470588-120.470588 120.470588z" p-id="1479"></path>
            <path d="M512 39.152941c-216.847059 0-391.529412 174.682353-391.529412 391.529412 0 349.364706 391.529412 572.235294 391.529412 572.235294s391.529412-222.870588 391.529412-572.235294c0-216.847059-174.682353-391.529412-391.529412-391.529412z m0 891.482353C424.658824 873.411765 180.705882 686.682353 180.705882 430.682353c0-183.717647 147.576471-331.294118 331.294118-331.294118s331.294118 147.576471 331.294118 331.294118c0 256-243.952941 442.729412-331.294118 499.952941z" p-id="1480"></path>
          </svg>
          China-Yantai
        </div>
        <div class="left-des-item">
          <svg t="1705773906032" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2474">
            <path d="M729.6 234.666667H294.4V157.866667a51.2 51.2 0 0 1 51.2-51.2h332.8a51.2 51.2 0 0 1 51.2 51.2v76.8z m179.2 51.2a51.2 51.2 0 0 1 51.2 51.2v512a51.2 51.2 0 0 1-51.2 51.2H115.2a51.2 51.2 0 0 1-51.2-51.2v-512a51.2 51.2 0 0 1 51.2-51.2h793.557333z m-768 172.032c0 16.384 13.312 29.696 29.696 29.696h683.008a29.696 29.696 0 1 0 0-59.392H170.410667a29.696 29.696 0 0 0-29.696 29.696z m252.416 118.784c0 16.384 13.312 29.696 29.696 29.696h178.176a29.696 29.696 0 1 0 0-59.392H422.912a29.738667 29.738667 0 0 0-29.696 29.696z" p-id="2475"></path>
          </svg>
          AI通识教育平台
        </div>
      </div>
      <div class="left-div left-tag">
          <div class="left-tag-item">OpenMAIC</div>
          <div class="left-tag-item">学知识</div>
          <div class="left-tag-item">看效果</div> 
          <div class="left-tag-item">动手做</div>
          <div class="left-tag-item">得反馈</div>
        </div>
      <div class="left-div left-time">
        <ul id="line">
          <li>
            <div class="focus"></div>
            <div>敬请期待</div>
            <div>2026.6</div>
          </li>
          <li>
            <div class="focus"></div>
            <div>OmniAI Edu</div>
            <div>2026.5</div>
          </li>
          <li>
            <div class="focus"></div>
            <div>进军人工智能通识教育</div>
            <div>2026.2</div>
          </li>
          <li>
            <div class="focus"></div>
            <div>师小助V2.0</div>
            <div>2025.12</div>
          </li>
          <li>
            <div class="focus"></div>
            <div>进行全面升级(Langchain)</div>
            <div>2025.11</div>
          </li>
          <li>
            <div class="focus"></div>
            <div>师小助V1.0</div>
            <div>2025.9</div>
          </li>
          <li>
            <div class="focus"></div>
            <div>完成初版(Coze、Dify)</div>
            <div>2025.8</div>
          </li>
          <li>
            <div class="focus"></div>
            <div>师小助启动</div>
            <div>2025.7</div>
          </li>
        </ul>
      </div>
    </div>
    <div class="zyyo-right">
      <header>
        <div class="header-actions">
          <router-link to="/api-management" class="api-mgmt-btn" title="API管理">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
            API管理
          </router-link>
          <button class="logout-btn" @click="handleLogout" title="退出登录">
            <svg viewBox="0 0 1024 1024" width="16" height="16">
              <circle cx="512" cy="512" r="450" fill="currentColor"/>
            </svg>
            退出
          </button>
        </div>
        <div class="index-logo" style="background-image: url('../../static/img/logo.png');">
          <img style="position: absolute;top:-15%;left:-10%;width: 120%; aspect-ratio: 1/1;" src="../../static/img/logokuang.png">
        </div>
        <div class="welcome">
          <span class="gradientText">AI通识一站式实践平台</span>
        </div>
        <div class="description">
          📝 <span class="purpleText">OmniAI Edu</span> 是一款人工智能通识教育一站式实践平台，提供 
          <span class="purpleText textBackground">学知识</span> 
          <span class="purpleText textBackground">看效果</span>  
          <span class="purpleText textBackground">动手做</span> 
          <span class="purpleText textBackground">得反馈</span>
          四大模块，助力AI通识教育。
        </div>
        <div class="description">
          🚀 <span class="purpleText">OmniAI Edu</span> 目前处于初始阶段，未来将持续更新和完善，敬请期待！
        </div>
        <div class="iconContainer">
          <a class="iconItem" href="https://github.com/abaiar/OmniAI-Edu" target="_blank">
            <svg t="1704870335945" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2487">
              <path d="M511.6 76.3C264.3 76.2 64 276.4 64 523.5 64 718.9 189.3 885 363.8 946c23.5 5.9 19.9-10.8 19.9-22.2v-77.5c-135.7 15.9-141.2-73.9-150.3-88.9C215 726 171.5 718 184.5 703c30.9-15.9 62.4 4 98.9 57.9 26.4 39.1 77.9 32.5 104 26 5.7-23.5 17.9-44.5 34.7-60.8-140.6-25.2-199.2-111-199.2-213 0-49.5 16.3-95 48.3-131.7-20.4-60.5 1.9-112.3 4.9-120 58.1-5.2 118.5 41.6 123.2 45.3 33-8.9 70.7-13.6 112.9-13.6 42.4 0 80.2 4.9 113.5 13.9 11.3-8.6 67.3-48.8 121.3-43.9 2.9 7.7 24.7 58.3 5.5 118 32.4 36.8 48.9 82.7 48.9 132.3 0 102.2-59 188.1-200 212.9 23.5 23.2 38.1 55.4 38.1 91v112.5c0.8 9 0 17.9 15 17.9 177.1-59.7 304.6-227 304.6-424.1 0-247.2-200.4-447.3-447.5-447.3z"  p-id="2488"></path>
            </svg>
            <div class="iconTip">Github</div>
          </a>
          <a class="iconItem" href="https://qm.qq.com/q/iJCJ0Frfe8" target="_blank">
            <svg t="1704870588438" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="3174" >
              <path d="M926.47619 355.644952V780.190476a73.142857 73.142857 0 0 1-73.142857 73.142857H170.666667a73.142857 73.142857 0 0 1-73.142857-73.142857V355.644952l304.103619 257.828572a170.666667 170.666667 0 0 0 220.745142 0L926.47619 355.644952zM853.333333 170.666667a74.044952 74.044952 0 0 1 26.087619 4.778666 72.704 72.704 0 0 1 30.622477 22.186667 73.508571 73.508571 0 0 1 10.678857 17.67619c3.169524 7.509333 5.12 15.652571 5.607619 24.210286L926.47619 243.809524v24.380952L559.469714 581.241905a73.142857 73.142857 0 0 1-91.306666 2.901333l-3.632762-2.925714L97.52381 268.190476v-24.380952a72.899048 72.899048 0 0 1 40.155428-65.292191A72.97219 72.97219 0 0 1 170.666667 170.666667h682.666666z"  p-id="3175"></path>
            </svg>
            <div class="iconTip">Mail</div>
          </a>
          <a class="iconItem" @click="pop('../../static/img/qq.jpg')" href="javascript:void(0)">
            <svg t="1712319361023" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1861">
              <path d="M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 689.3 112 511.5 112 331.7 112 256.2 265.2 261 447.9c-28.4 70.8-46.7 113.7-62.7 165.3-34 109.5-23 154.8-14.6 155.8 18 2.2 70.1-82.4 70.1-82.4 0 49 25.2 112.9 79.8 159-26.4 8.1-85.7 29.9-71.6 53.8 11.4 19.3 196.2 12.3 249.5 6.3 53.3 6 238.1 13 249.5-6.3 14.1-23.8-45.3-45.7-71.6-53.8 54.6-46.2 79.8-110.1 79.8-159 0 0 52.1 84.6 70.1 82.4 8.5-1.1 19.5-46.4-14.5-155.8z" p-id="1862"></path>
            </svg>
            <div class="iconTip">QQ</div>
          </a>
          <a class="switch" href="javascript:void(0)">
            <div class="onoffswitch">
              <input type="checkbox" name="onoffswitch" class="onoffswitch-checkbox" id="myonoffswitch" @click="toggleMode">
              <label class="onoffswitch-label" for="myonoffswitch">
                <span class="onoffswitch-inner"></span>
                <span class="onoffswitch-switch"></span>
              </label>
            </div>
          </a>
        </div>
        <div class="tanChiShe">
          <img id="tanChiShe" src="../../static/svg/snake-Light.svg" alt="">
        </div>
      </header>
      <div class="content">
        <div class="title">
          <svg t="1705257422086" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1891">
            <path d="M629.333333 202.666667v213.333333h277.333334v448h-512v-213.333333h-277.333334v-448h512z m213.333334 277.333333h-213.333334v170.666667h-170.666666v149.333333h384v-320z m-277.333334-213.333333h-384v320h213.333334v-170.666667h170.666666v-149.333333z m0 213.333333h-106.666666v106.666667h106.666666v-106.666667z"  p-id="1892"></path>
          </svg>
          智慧课堂
        </div>
        <div class="projectList">
          <a 
            class="projectItem ai-course-item" 
            @click.prevent="navigateToOpenMAIC"
            href="http://10.10.12.47:5006"
          >
            <img src="../../static/img/logo-openmaic.png" alt="OpenMAIC" class="ai-course-logo">
          </a>
        </div>
        
        <div class="title">
          <svg t="1705257422086" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1891">
            <path d="M629.333333 202.666667v213.333333h277.333334v448h-512v-213.333333h-277.333334v-448h512z m213.333334 277.333333h-213.333334v170.666667h-170.666666v149.333333h384v-320z m-277.333334-213.333333h-384v320h213.333334v-170.666667h170.666666v-149.333333z m0 213.333333h-106.666666v106.666667h106.666666v-106.666667z"  p-id="1892"></path>
          </svg>
          核心功能模块
        </div>
        <div class="projectList module-grid">
          <div class="projectItem module-card" @click="navigateToModule('learn')">
            <div class="module-icon learn-icon">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M512 128c-212.1 0-384 171.9-384 384s171.9 384 384 384 384-171.9 384-384-171.9-384-384-384z m0 704c-176.7 0-320-143.3-320-320s143.3-320 320-320 320 143.3 320 320-143.3 320-320 320z" fill="currentColor"/>
                <path d="M512 256c-141.4 0-256 114.6-256 256s114.6 256 256 256 256-114.6 256-256-114.6-256-256-256z m0 448c-106 0-192-86-192-192s86-192 192-192 192 86 192 192-86 192-192 192z" fill="currentColor"/>
                <path d="M480 352h64v192h-64z" fill="currentColor"/>
                <path d="M480 480h192v64H480z" fill="currentColor"/>
              </svg>
            </div>
            <div class="module-content">
              <h1>学知识</h1>
              <p>系统学习AI基础知识，从理论到实践</p>
            </div>
          </div>
          
          <div class="projectItem module-card" @click="navigateToModule('demo')">
            <div class="module-icon demo-icon">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M928 160H96c-17.7 0-32 14.3-32 32v640c0 17.7 14.3 32 32 32h832c17.7 0 32-14.3 32-32V192c0-17.7-14.3-32-32-32z m-40 632H136V232h752v560z" fill="currentColor"/>
                <path d="M610.3 476h123.4c1.3 0 2.3-3.6 2.3-8v-48c0-4.4-1-8-2.3-8H610.3c-1.3 0-2.3 3.6-2.3 8v48c0 4.4 1 8 2.3 8z m-220.8-8v-48c0-4.4 1-8 2.3-8h123.4c1.3 0 2.3 3.6 2.3 8v48c0 4.4-1 8-2.3 8H391.8c-1.3 0-2.3-3.6-2.3-8z m-196.2 0v-48c0-4.4 1-8 2.3-8h123.4c1.3 0 2.3 3.6 2.3 8v48c0 4.4-1 8-2.3 8H195.6c-1.3 0-2.3-3.6-2.3-8z" fill="currentColor"/>
                <path d="M473 577.5L426.5 624 473 670.5l45-45L654.5 762l45-45L518 577.5z" fill="currentColor"/>
              </svg>
            </div>
            <div class="module-content">
              <h1>看效果</h1>
              <p>直观体验AI技术效果与应用场景</p>
            </div>
          </div>
          
          <div class="projectItem module-card" @click="navigateToModule('practice')">
            <div class="module-icon practice-icon">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M880 112H144c-17.7 0-32 14.3-32 32v736c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V144c0-17.7-14.3-32-32-32z m-40 728H184V184h656v656z" fill="currentColor"/>
                <path d="M492 400h184c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8H492c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8z" fill="currentColor"/>
                <path d="M492 544h184c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8H492c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8z" fill="currentColor"/>
                <path d="M492 688h184c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8H492c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8z" fill="currentColor"/>
                <path d="M340 400h48c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8z" fill="currentColor"/>
                <path d="M340 544h48c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8z" fill="currentColor"/>
                <path d="M340 688h48c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8z" fill="currentColor"/>
              </svg>
            </div>
            <div class="module-content">
              <h1>动手做</h1>
              <p>亲自实践AI项目，提升动手能力</p>
            </div>
          </div>
          
          <div class="projectItem module-card" @click="navigateToModule('feedback')">
            <div class="module-icon feedback-icon">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M512 128c-212.1 0-384 171.9-384 384s171.9 384 384 384 384-171.9 384-384-171.9-384-384-384z m0 704c-176.7 0-320-143.3-320-320s143.3-320 320-320 320 143.3 320 320-143.3 320-320 320z" fill="currentColor"/>
                <path d="M512 256c-141.4 0-256 114.6-256 256s114.6 256 256 256 256-114.6 256-256-114.6-256-256-256z m0 448c-106 0-192-86-192-192s86-192 192-192 192 86 192 192-86 192-192 192z" fill="currentColor"/>
                <path d="M464 384a48 48 0 1 1 96 0 48 48 0 1 1-96 0z" fill="currentColor"/>
                <path d="M512 480c-52.9 0-96 43.1-96 96h64c0-17.7 14.3-32 32-32s32 14.3 32 32-14.3 32-32 32h-32v64h32c52.9 0 96-43.1 96-96s-43.1-96-96-96z" fill="currentColor"/>
              </svg>
            </div>
            <div class="module-content">
              <h1>得反馈</h1>
              <p>获取智能反馈，持续改进学习效果</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="tc">
    <div onclick="" class="tc-main">
      <img class="tc-img" src="" alt="" srcset="">
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import axios from 'axios'

const API_BASE = ''

export default {
  name: 'Index',
  methods: {
    pop(imagePath) {
      const tc = document.querySelector('.tc')
      const tcImg = document.querySelector('.tc-img')
      tcImg.src = imagePath
      tc.style.display = 'block'
    },
    async syncThemeToBackend(theme) {
      try {
        await axios.post(`${API_BASE}/api/theme`, { theme }, { timeout: 3000 })
      } catch (e) {
        console.warn('同步主题到后端失败:', e.message)
      }
    },
    toggleMode() {
      const html = document.documentElement;
      const tanChiSheImg = document.getElementById('tanChiShe');
      let newTheme;
      if (html.getAttribute('data-theme') === 'Dark') {
        html.removeAttribute('data-theme');
        html.classList.remove('Dark');
        if (tanChiSheImg) {
          tanChiSheImg.src = '../../static/svg/snake-Light.svg';
        }
        newTheme = 'light';
      } else {
        html.setAttribute('data-theme', 'Dark');
        html.classList.add('Dark');
        if (tanChiSheImg) {
          tanChiSheImg.src = '../../static/svg/snake-Dark.svg';
        }
        newTheme = 'dark';
      }
      try { localStorage.setItem('theme', newTheme) } catch (e) {}
      this.syncThemeToBackend(newTheme);
    },
    handleLogout() {
      if (confirm('确定要退出登录吗？')) {
        const userStore = useUserStore()
        userStore.logout()
        this.$router.push('/login')
      }
    },
    navigateToOpenMAIC() {
      const targetUrl = 'http://10.10.12.47:5006'
      try {
        window.location.href = targetUrl
      } catch (error) {
        console.error('导航到OpenMAIC服务失败:', error)
        window.location.href = targetUrl
      }
    },
    navigateToModule(moduleType) {
      if (moduleType === 'learn') {
        this.$router.push('/learn')
      } else if (moduleType === 'demo') {
        this.$router.push('/demo')
      } else if (moduleType === 'practice') {
        this.$router.push('/practice')
      } else if (moduleType === 'feedback') {
        this.$router.push('/feedback')
      }
    }
  },
  mounted() {
    const savedTheme = (() => { try { return localStorage.getItem('theme') } catch (e) { return null } })()
    const html = document.documentElement
    const tanChiSheImg = document.getElementById('tanChiShe')
    if (savedTheme === 'dark' || (!savedTheme && html.getAttribute('data-theme') === 'Dark')) {
      html.setAttribute('data-theme', 'Dark')
      html.classList.add('Dark')
      if (tanChiSheImg) tanChiSheImg.src = '../../static/svg/snake-Dark.svg'
    } else if (savedTheme === 'light') {
      html.removeAttribute('data-theme')
      html.classList.remove('Dark')
      if (tanChiSheImg) tanChiSheImg.src = '../../static/svg/snake-Light.svg'
    }
  }
}
</script>

<style scoped>
header {
  position: relative;
}

.header-actions {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 10;
}

.api-mgmt-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: white;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 12px rgba(108, 92, 231, 0.35);
  text-decoration: none;
  position: relative;
  overflow: hidden;
}

.api-mgmt-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.4s ease, height 0.4s ease;
}

.api-mgmt-btn:hover::before {
  width: 200%;
  height: 200%;
}

.api-mgmt-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 18px rgba(108, 92, 231, 0.5);
}

.api-mgmt-btn svg {
  stroke: white;
}

@keyframes api-pulse {
  0%, 100% { box-shadow: 0 2px 12px rgba(108, 92, 231, 0.35); }
  50% { box-shadow: 0 2px 20px rgba(108, 92, 231, 0.6); }
}

.api-mgmt-btn {
  animation: api-pulse 3s ease-in-out infinite;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background-color: rgba(255, 255, 255, 0.9);
  color: #dc3545;
  border: 1px solid #dc3545;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.logout-btn svg {
  fill: currentColor;
  margin-top: -2px;
}

.logout-btn:hover {
  background-color: #dc3545;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.logout-btn:active {
  transform: translateY(0);
}

.ai-course-item {
  width: calc(100% - 15px) !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-decoration: none !important;
  height: 120px !important;
  border-radius: 12px !important;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
  transition: all 0.4s ease !important;
  position: relative;
  overflow: hidden;
}

.ai-course-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  transition: left 0.5s ease;
}

.ai-course-item:hover::before {
  left: 100%;
}

.ai-course-item:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15) !important;
  border-color: rgba(255,255,255,0.2) !important;
}

.ai-course-logo {
  max-width: 80%;
  max-height: 70px;
  object-fit: contain;
  transition: transform 0.4s ease;
}

.ai-course-item:hover .ai-course-logo {
  transform: scale(1.05);
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.module-card {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 180px !important;
  padding: 20px !important;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(147, 112, 219, 0.2) !important;
}

.module-card:hover {
  border-color: rgba(147, 112, 219, 0.5) !important;
}

.module-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.module-icon svg {
  width: 32px;
  height: 32px;
}

.module-card:hover .module-icon {
  transform: scale(1.1);
}

.learn-icon {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  color: #667eea;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.demo-icon {
  background: linear-gradient(135deg, rgba(240, 147, 251, 0.2), rgba(245, 87, 108, 0.2));
  color: #f093fb;
  box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
}

.practice-icon {
  background: linear-gradient(135deg, rgba(67, 233, 123, 0.2), rgba(56, 249, 215, 0.2));
  color: #43e97b;
  box-shadow: 0 4px 15px rgba(67, 233, 123, 0.3);
}

.feedback-icon {
  background: linear-gradient(135deg, rgba(250, 112, 154, 0.2), rgba(254, 225, 64, 0.2));
  color: #fa709a;
  box-shadow: 0 4px 15px rgba(250, 112, 154, 0.3);
}

.module-content {
  text-align: center;
}

.module-content h1 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--item_left_title_color);
  transition: font-size 0.3s ease;
}

.module-content p {
  font-size: 13px;
  color: var(--item_left_text_color);
  line-height: 1.4;
}

.module-card:hover .module-content h1 {
  font-size: 20px;
}

@media (max-width: 1150px) {
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .module-card {
    height: 160px !important;
  }
}

@media (max-width: 768px) {
  .ai-course-item {
    height: 100px !important;
  }
  
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .module-card {
    height: 140px !important;
    padding: 15px !important;
  }
  
  .module-icon {
    width: 50px;
    height: 50px;
    margin-bottom: 10px;
  }
  
  .module-icon svg {
    width: 26px;
    height: 26px;
  }
  
  .module-content h1 {
    font-size: 16px;
  }
  
  .module-content p {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .ai-course-item {
    height: 80px !important;
  }
  
  .module-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .module-card {
    height: 100px !important;
    flex-direction: row !important;
    justify-content: flex-start !important;
    padding: 15px 20px !important;
  }
  
  .module-icon {
    width: 45px;
    height: 45px;
    margin-bottom: 0;
    margin-right: 15px;
    flex-shrink: 0;
  }
  
  .module-content {
    text-align: left;
  }
  
  .module-content h1 {
    font-size: 16px;
    margin-bottom: 4px;
  }
  
  .module-content p {
    font-size: 12px;
  }
}
</style>
