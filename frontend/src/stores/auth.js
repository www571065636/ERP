import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/utils/http'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const permissions = computed(() => user.value?.permissions || [])

  function hasPermission(perm) {
    return permissions.value.includes(perm)
  }

  async function login(username, password) {
    const res = await http.post('/auth/login/', { username, password })
    token.value = res.data.access
    refreshToken.value = res.data.refresh
    user.value = res.data.user
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    return res.data
  }

  async function logout() {
    try {
      await http.post('/auth/logout/', { refresh: refreshToken.value })
    } catch {}
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async function fetchMe() {
    const res = await http.get('/auth/me/')
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  }

  return { token, user, isLoggedIn, permissions, hasPermission, login, logout, fetchMe }
})
