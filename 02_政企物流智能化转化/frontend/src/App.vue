<template>
    <div class="app-container">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="logo-icon">
                    <el-icon><Van /></el-icon>
                </div>
                <div class="sidebar-brand">
                    <h2>物流智能化平台</h2>
                    <p>政企智能派单 & 查询系统</p>
                </div>
            </div>
            <el-menu
                :default-active="$route.path"
                router
                background-color="transparent"
                text-color="rgba(255,255,255,0.5)"
                active-text-color="#fff"
            >
                <el-menu-item index="/">
                    <el-icon><Tickets /></el-icon>
                    <span>工单管理</span>
                </el-menu-item>
                <el-menu-item index="/query">
                    <el-icon><DataAnalysis /></el-icon>
                    <span>智能查询</span>
                </el-menu-item>
            </el-menu>
            <div class="sidebar-footer">
                <div class="version-badge">v2.0</div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <router-view v-slot="{ Component }">
                <transition name="page-fade" mode="out-in">
                    <component :is="Component" />
                </transition>
            </router-view>
        </main>

        <!-- Notification Bubble -->
        <transition name="el-fade-in">
            <div v-if="notification" class="notification-bubble">
                <el-alert
                    :title="notification.title"
                    :description="notification.description"
                    :type="notification.type"
                    show-icon
                    closable
                    @close="notification = null"
                />
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from './composables/useWebSocket'

const notification = ref(null)
let clearTimer = null

const { connect, disconnect, onMessage } = useWebSocket()

onMounted(() => {
    connect()

    onMessage((data) => {
        if (data.type === 'NEW_WORK_ORDER') {
            notification.value = {
                title: '新工单创建',
                description: `${data.data?.location || ''} - ${data.data?.issue || '新工单'}`,
                type: 'success'
            }
        } else if (data.type === 'STATUS_CHANGE') {
            notification.value = {
                title: '工单状态变更',
                description: `工单 #${data.data?.id} 状态已更新为 ${data.data?.status}`,
                type: 'info'
            }
        }

        if (clearTimer) clearTimeout(clearTimer)
        clearTimer = setTimeout(() => { notification.value = null }, 5000)
    })
})

onUnmounted(() => {
    disconnect()
    if (clearTimer) clearTimeout(clearTimer)
})
</script>

<style scoped>
.sidebar-brand {
    flex: 1;
}

.sidebar-footer {
    padding: 16px 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    align-items: center;
}

.version-badge {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.06);
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
    letter-spacing: 0.3px;
}

.page-fade-enter-active,
.page-fade-leave-active {
    transition: opacity 0.2s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
    opacity: 0;
}
</style>
