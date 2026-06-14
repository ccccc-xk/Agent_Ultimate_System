import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'WorkOrder',
        component: () => import('../views/WorkOrderView.vue')
    },
    {
        path: '/query',
        name: 'NlpQuery',
        component: () => import('../views/QueryView.vue')
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
