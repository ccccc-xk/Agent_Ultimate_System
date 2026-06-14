<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ collapsed: isCollapse }">
      <div class="sidebar-logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
        </div>
        <transition name="fade">
          <div v-if="!isCollapse" class="logo-text-wrap">
            <span class="logo-text">企业管理基座</span>
            <span class="logo-sub">Enterprise</span>
          </div>
        </transition>
      </div>

      <el-scrollbar class="sidebar-menu-wrap">
        <el-menu
          :default-active="currentRoute"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          class="sidebar-menu"
        >
          <template v-for="menu in menus" :key="menu.id">
            <el-sub-menu v-if="menu.children && menu.children.length" :index="menu.path">
              <template #title>
                <el-icon class="menu-icon"><component :is="menu.icon" /></el-icon>
                <span class="menu-label">{{ menu.menuName }}</span>
              </template>
              <el-menu-item
                v-for="child in menu.children"
                :key="child.id"
                :index="child.path"
              >
                <el-icon v-if="child.icon" class="menu-icon"><component :is="child.icon" /></el-icon>
                <span class="menu-label">{{ child.menuName }}</span>
              </el-menu-item>
            </el-sub-menu>
            <el-menu-item v-else :index="menu.path">
              <el-icon class="menu-icon"><component :is="menu.icon" /></el-icon>
              <span class="menu-label">{{ menu.menuName }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>

      <div class="sidebar-footer">
        <div class="sidebar-footer-inner">
          <div class="footer-dot"></div>
          <transition name="fade">
            <span v-if="!isCollapse" class="sidebar-footer-text">v1.0.0</span>
          </transition>
        </div>
      </div>
    </aside>

    <!-- Main Area -->
    <div class="main-area">
      <!-- Header -->
      <header class="top-header">
        <div class="header-left">
          <div class="collapse-btn" @click="isCollapse = !isCollapse">
            <el-icon :size="18">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
          </div>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle !== '业务数据看板'">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <div class="header-greeting">
            <span>{{ greetingText }}，</span>
            <strong>{{ userStore.userInfo?.realName || userStore.userInfo?.username || '用户' }}</strong>
          </div>
          <div class="header-divider"></div>
          <div class="header-clock">
            <el-icon :size="13"><Clock /></el-icon>
            <span>{{ currentTime }}</span>
          </div>
          <div class="header-divider"></div>
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <div class="user-avatar">
                {{ (userStore.userInfo?.realName || userStore.userInfo?.username || 'U').charAt(0) }}
              </div>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <div class="dropdown-user-card">
                    <div class="dropdown-avatar">
                      {{ (userStore.userInfo?.realName || userStore.userInfo?.username || 'U').charAt(0) }}
                    </div>
                    <div>
                      <div class="dropdown-name">{{ userStore.userInfo?.realName || userStore.userInfo?.username }}</div>
                      <div class="dropdown-role">{{ userStore.userInfo?.roles?.[0] || '普通用户' }}</div>
                    </div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Content -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)
const currentTime = ref('')
let clockTimer = null

const currentRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '管理系统')
const menus = computed(() => userStore.menus)

const greetingText = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '凌晨好'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

function updateClock() {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${h}:${m}:${s}`
}

onMounted(async () => {
  try {
    await userStore.fetchInfo()
    await userStore.fetchMenus()
  } catch (e) {
    console.error('Failed to load user info', e)
  }
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})

onBeforeUnmount(() => {
  if (clockTimer) clearInterval(clockTimer)
})

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-main);
}

/* ======== Sidebar ======== */
.sidebar {
  width: 232px;
  background: linear-gradient(180deg, #161b2e 0%, #0d1117 100%);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-slow);
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
  z-index: 10;
}
.sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02), rgba(255,255,255,0.06));
  pointer-events: none;
}
.sidebar.collapsed {
  width: 64px;
}

/* Logo */
.sidebar-logo {
  height: 68px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
  overflow: hidden;
  white-space: nowrap;
}
.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35);
  position: relative;
}
.logo-icon::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.2));
  z-index: -1;
  animation: logoPulse 3s ease-in-out infinite;
}
@keyframes logoPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}
.logo-text-wrap {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.logo-text {
  color: #e2e8f0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.logo-sub {
  font-size: 10px;
  color: #475569;
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* Menu */
.sidebar-menu-wrap {
  flex: 1;
  overflow: hidden;
}
.sidebar-menu {
  border-right: none !important;
  background: transparent !important;
  padding: 12px 0;
}
.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  color: #7e8aa0 !important;
  height: 44px;
  line-height: 44px;
  margin: 2px 10px;
  border-radius: 10px;
  transition: all 0.2s ease;
  font-size: 13.5px;
}
.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #c8d0de !important;
}
.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.18), rgba(99, 102, 241, 0.12)) !important;
  color: #60a5fa !important;
  position: relative;
  font-weight: 500;
}
.sidebar-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, var(--primary), var(--accent));
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
}
.sidebar-menu :deep(.el-menu-item.is-active .menu-icon) {
  color: #60a5fa;
}
.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 52px !important;
  min-width: auto;
}
.sidebar-menu :deep(.el-menu--collapse .el-menu-item),
.sidebar-menu :deep(.el-menu--collapse .el-sub-menu__title) {
  padding: 0;
  margin: 2px 10px;
  justify-content: center;
}

.menu-icon {
  font-size: 18px;
  width: 18px;
  margin-right: 10px;
}
.menu-label {
  font-size: 13.5px;
}

/* Sidebar Footer */
.sidebar-footer {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  flex-shrink: 0;
}
.sidebar-footer-inner {
  display: flex;
  align-items: center;
  gap: 8px;
}
.footer-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
  animation: dotPulse 2s ease-in-out infinite;
}
@keyframes dotPulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
.sidebar-footer-text {
  font-size: 11px;
  color: #475569;
  letter-spacing: 0.5px;
}

/* ======== Main Area ======== */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* Header */
.top-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  position: relative;
  z-index: 5;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.collapse-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  transition: all var(--transition-normal);
  border-radius: 8px;
}
.collapse-btn:hover {
  color: var(--primary);
  background: rgba(59, 130, 246, 0.08);
}

.breadcrumb {
  font-size: 14px;
}
.breadcrumb :deep(.el-breadcrumb__inner) {
  color: var(--text-light);
  font-weight: 400;
}
.breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--text-primary);
  font-weight: 600;
}

.header-greeting {
  font-size: 13px;
  color: var(--text-muted);
}
.header-greeting strong {
  color: var(--text-primary);
  font-weight: 600;
}

.header-clock {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  color: var(--text-light);
  font-family: 'SF Mono', 'Consolas', 'Menlo', monospace;
  font-variant-numeric: tabular-nums;
}
.header-divider {
  width: 1px;
  height: 18px;
  background: var(--border-color);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 10px;
  transition: all var(--transition-fast);
}
.user-info:hover {
  background: rgba(59, 130, 246, 0.06);
}
.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  transition: all var(--transition-normal);
}
.user-info:hover .user-avatar {
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
  transform: scale(1.05);
}
.dropdown-arrow {
  font-size: 11px;
  color: var(--text-light);
  transition: transform var(--transition-fast);
}

/* Dropdown user card */
.dropdown-user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}
.dropdown-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}
.dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.dropdown-role {
  font-size: 11px;
  color: var(--text-light);
  margin-top: 2px;
}

/* Content */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-main);
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
