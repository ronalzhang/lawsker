import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true, // 支持HttpOnly Cookie
  headers: {
    'Content-Type': 'application/json'
  }
})

let loadingInstance: any = null
let requestCount = 0

// 显示loading
const showLoading = () => {
  if (requestCount === 0) {
    loadingInstance = ElLoading.service({
      text: '加载中...',
      background: 'rgba(0, 0, 0, 0.7)'
    })
  }
  requestCount++
}

// 隐藏loading
const hideLoading = () => {
  requestCount--
  if (requestCount <= 0) {
    requestCount = 0
    if (loadingInstance) {
      loadingInstance.close()
      loadingInstance = null
    }
  }
}

// CSRF Token管理
let csrfToken: string | null = null

// 获取CSRF Token
const getCSRFToken = async (): Promise<string | null> => {
  if (csrfToken) {
    return csrfToken
  }
  
  try {
    const response = await axios.get('/api/v1/csrf/csrf-token', {
      withCredentials: true
    })
    csrfToken = response.data.csrf_token
    return csrfToken
  } catch (error) {
    console.error('Failed to get CSRF token:', error)
    return null
  }
}

// 从Cookie获取CSRF Token
const getCSRFTokenFromCookie = (): string | null => {
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrf_token') {
      // 解析cookie中的token值（格式：token.timestamp.signature）
      const parts = value.split('.')
      return parts[0] || null
    }
  }
  return null
}

// 请求拦截器
service.interceptors.request.use(
  async (config: AxiosRequestConfig) => {
    // 显示loading
    if (config.loading !== false) {
      showLoading()
    }

    // HttpOnly Cookie会自动携带，不需要手动添加token
    config.headers = config.headers || {}
    
    // 为需要CSRF保护的请求添加CSRF token
    const needsCSRF = ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')
    const isCSRFExempt = [
      '/api/v1/auth/login',
      '/api/v1/auth/register',
      '/api/v1/auth/forgot-password',
      '/api/v1/auth/reset-password',
      '/api/v1/auth/send-sms-code',
      '/api/v1/auth/verify-sms-code',
      '/api/v1/csrf/csrf-token'
    ].some(path => config.url?.includes(path))
    
    if (needsCSRF && !isCSRFExempt) {
      // 首先尝试从Cookie获取token
      let token = getCSRFTokenFromCookie()
      
      // 如果Cookie中没有，则请求新的token
      if (!token) {
        token = await getCSRFToken()
      }
      
      if (token) {
        config.headers['X-CSRF-Token'] = token
      }
    }
    
    return config
  },
  (error) => {
    hideLoading()
    return Promise.reject(error)
  }
)

// 令牌刷新标志
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

// 处理队列中的请求
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token)
    }
  })
  
  failedQueue = []
}

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    hideLoading()
    
    // 直接返回响应数据，不再检查code字段
    return response.data
  },
  async (error) => {
    hideLoading()
    
    const { response, config } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 如果是刷新令牌的请求失败，直接跳转登录
          if (config.url?.includes('/auth/refresh')) {
            ElMessage.error('登录已过期，请重新登录')
            const userStore = useUserStore()
            await userStore.logout()
            router.push('/login')
            return Promise.reject(error)
          }
          
          // 尝试刷新令牌
          if (!isRefreshing) {
            isRefreshing = true
            
            try {
              const userStore = useUserStore()
              const success = await userStore.refreshToken()
              
              if (success) {
                processQueue(null, 'refreshed')
                // 重试原始请求
                return service(config)
              } else {
                processQueue(error, null)
                ElMessage.error('登录已过期，请重新登录')
                await userStore.logout()
                router.push('/login')
              }
            } catch (refreshError) {
              processQueue(refreshError, null)
              ElMessage.error('登录已过期，请重新登录')
              const userStore = useUserStore()
              await userStore.logout()
              router.push('/login')
            } finally {
              isRefreshing = false
            }
          } else {
            // 如果正在刷新，将请求加入队列
            return new Promise((resolve, reject) => {
              failedQueue.push({ resolve, reject })
            }).then(() => {
              return service(config)
            }).catch((err) => {
              return Promise.reject(err)
            })
          }
          break
          
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 500:
          ElMessage.error('服务器内部错误')
          break
          
        default:
          ElMessage.error(data?.detail || data?.message || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default service