import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const menus = ref([])

  async function login(username, password) {
    const res = await request.post('/api/auth/login', { username, password })
    // login 接口将 token 放在 roles[0] 中
    const tk = res.data.roles[0]
    token.value = tk
    localStorage.setItem('token', tk)
    userInfo.value = res.data
    return res
  }

  async function fetchInfo() {
    const res = await request.get('/api/auth/info')
    userInfo.value = res.data
    return res.data
  }

  async function fetchMenus() {
    const res = await request.get('/api/menu/list')
    menus.value = res.data
    return res.data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    menus.value = []
    localStorage.removeItem('token')
  }

  return { token, userInfo, menus, login, fetchInfo, fetchMenus, logout }
})
