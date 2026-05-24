import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

let refreshing = null

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  async (err) => {
    const status = err.response?.status
    const originalRequest = err.config || {}
    const auth = useAuthStore()
    const isLoginRequest = originalRequest.url?.includes('/auth/login')

    // Token 刷新逻辑
    if (status === 401 && auth.refreshToken && !originalRequest._retry && !isLoginRequest) {
      originalRequest._retry = true
      try {
        refreshing ||= http.post('/auth/token/refresh/', { refresh: auth.refreshToken })
        const res = await refreshing
        refreshing = null
        auth.setAccessToken(res.access)
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${auth.token}`
        return http(originalRequest)
      } catch {
        refreshing = null
      }
    }
    // 非登录请求的 401 才触发登出跳转
    if (status === 401 && !isLoginRequest) {
      await auth.logout()
      router.push('/login')
    }
    const msg = err.response?.data?.msg || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default http
