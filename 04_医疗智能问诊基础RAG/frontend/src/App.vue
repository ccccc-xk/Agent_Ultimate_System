<template>
  <div class="app-layout">
    <!-- Sidebar (desktop + tablet) -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo" @click="sidebarCollapsed = !sidebarCollapsed">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none">
              <rect x="2" y="2" width="20" height="20" rx="4" fill="#EBF3FF"/>
              <path d="M12 7v10M7 12h10" stroke="#2B7DE9" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <transition name="fade">
            <span v-if="!sidebarCollapsed" class="logo-text">医疗智能问诊</span>
          </transition>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <transition name="fade">
            <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          </transition>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <transition name="fade">
          <span v-if="!sidebarCollapsed" class="version">Medical RAG v1.0</span>
        </transition>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Mobile bottom tab bar -->
    <nav class="mobile-tabs">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="tab-item"
        :class="{ active: route.path === item.path }"
      >
        <el-icon :size="22"><component :is="item.icon" /></el-icon>
        <span class="tab-label">{{ item.shortLabel }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, Collection } from '@element-plus/icons-vue'

const route = useRoute()
const sidebarCollapsed = ref(false)

const navItems = [
  { path: '/', label: '智能问诊', shortLabel: '问诊', icon: ChatDotRound },
  { path: '/knowledge', label: '知识库管理', shortLabel: '知识库', icon: Collection },
]
</script>

<style lang="scss">
@import './assets/styles/variables.scss';

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;
  color: $text-body;
  -webkit-font-smoothing: antialiased;
}

.app-layout {
  display: flex;
  height: 100vh;
  background: $bg-gray;
}

/* ===== Sidebar ===== */
.sidebar {
  width: $sidebar-width;
  background: $bg-white;
  border-right: 1px solid $border-light;
  display: flex;
  flex-direction: column;
  transition: width 200ms ease;
  flex-shrink: 0;
  z-index: 10;

  &.collapsed {
    width: $sidebar-collapsed;
  }

  @include tablet-and-below {
    width: $sidebar-collapsed;
  }

  @include mobile {
    display: none;
  }
}

.sidebar-header {
  padding: 20px 16px;
  border-bottom: 1px solid $border-light;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
}

.logo-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $primary-light;
  border-radius: $radius-md;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: $text-title;
  letter-spacing: 0.5px;
}

/* ===== Navigation ===== */
.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: $radius-md;
  color: $text-body;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 150ms ease;
  white-space: nowrap;
  overflow: hidden;
  position: relative;

  &:hover {
    background: $bg-hover;
    color: $primary-blue;
  }

  &.active {
    background: $primary-light;
    color: $primary-blue;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 8px;
      bottom: 8px;
      width: 3px;
      background: $primary-blue;
      border-radius: 0 2px 2px 0;
    }
  }
}

.nav-label {
  flex-shrink: 0;
}

/* ===== Footer ===== */
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid $border-light;
}

.version {
  font-size: 11px;
  color: $text-assist;
  letter-spacing: 0.3px;
}

/* ===== Main Content ===== */
.main-content {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

/* ===== Mobile Bottom Tabs ===== */
.mobile-tabs {
  display: none;

  @include mobile {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: $mobile-tab-height;
    background: $bg-white;
    border-top: 1px solid $border-light;
    z-index: 100;
    padding: 0 8px;
    padding-bottom: env(safe-area-inset-bottom);
  }
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-decoration: none;
  color: $text-assist;
  font-size: 10px;
  font-weight: 500;
  transition: color 150ms ease;
  -webkit-tap-highlight-color: transparent;

  &.active {
    color: $primary-blue;
  }
}

.tab-label {
  line-height: 1;
}

/* ===== Transitions ===== */
.fade-enter-active, .fade-leave-active {
  transition: opacity 150ms ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.page-slide-enter-active {
  transition: all 250ms ease-out;
}
.page-slide-leave-active {
  transition: all 200ms ease-in;
}
.page-slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.page-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
