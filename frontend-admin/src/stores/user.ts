import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type { AdminUser } from '@/types'
import request from '@/utils/request'
import { wsManager } from '@/utils/websocket'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<AdminUser | null>(null)
  const token = ref<string>('')
  const permissions = ref<string[]>([])

  // 计算属性
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.role === 'super_admin')
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')

  // 动作
  const login = async (username: string, password: string) => {
    const credentials = { username, password }
    try {
      const response = await request({
        url: '/api/v1/auth/login',
        method: 'post',
        data: credentials
      })

      const { user: userInfo } = response.data
      
      // 不再存储token，使用HttpOnly Cookie
      user.value = userInfo
      permissions.value = userInfo.permissions || []
      
      // 只保存用户信息到localStorage（不包含敏感token）
      localStorage.setItem('admin_user', JSON.stringify(userInfo))
      
      // 连接WebSocket（token会从Cookie自动获取）
      wsManager.connect()
      
      return response
    } catch (error) {
      throw error
    }
  }

  const logout = async () => {
    try {
      await request({
        url: '/api/v1/auth/logout',
        method: 'post'
      })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 清除状态
      user.value = null
      token.value = ''
      permissions.value = []
      
      // 清除localStorage
      localStorage.removeItem('admin_user')
      
      // 断开WebSocket
      wsManager.disconnect()
    }
  }

  const checkLoginStatus = async () => {
    try {
      // 验证HttpOnly Cookie中的token有效性
      const response = await request({
        url: '/api/v1/auth/me',
        method: 'get'
      })
      
      user.value = response.data
      permissions.value = response.data.permissions || []
      
      // 保存用户信息到localStorage
      localStorage.setItem('admin_user', JSON.stringify(response.data))
      
      // 连接WebSocket
      wsManager.connect()
      
      return true
    } catch (error) {
      // Cookie中的token无效，清除本地存储
      localStorage.removeItem('admin_user')
      token.value = ''
      user.value = null
      permissions.value = []
      return false
    }
  }

  const hasPermission = (permission: string) => {
    if (isSuperAdmin.value) return true
    return permissions.value.includes(permission)
  }

  const hasAnyPermission = (permissionList: string[]) => {
    if (isSuperAdmin.value) return true
    return permissionList.some(permission => permissions.value.includes(permission))
  }

  const updateProfile = async (profileData: Partial<AdminUser>) => {
    try {
      const response = await request({
        url: '/api/v1/auth/profile',
        method: 'put',
        data: profileData
      })
      
      user.value = { ...user.value, ...response.data }
      localStorage.setItem('admin_user', JSON.stringify(user.value))
      
      return response
    } catch (error) {
      throw error
    }
  }

  const changePassword = async (data: {
    old_password: string
    new_password: string
    confirm_password: string
  }) => {
    try {
      await request({
        url: '/api/v1/auth/change-password',
        method: 'post',
        data
      })
    } catch (error) {
      throw error
    }
  }

  // 刷新令牌
  const refreshToken = async () => {
    try {
      await request({
        url: '/api/v1/auth/refresh',
        method: 'post'
      })
      return true
    } catch (error) {
      console.error('Token refresh error:', error)
      // 刷新失败，清除用户状态
      user.value = null
      token.value = ''
      permissions.value = []
      localStorage.removeItem('admin_user')
      return false
    }
  }

  // 验证令牌
  const verifyToken = async () => {
    try {
      const response = await request({
        url: '/api/v1/auth/verify-token',
        method: 'post'
      })
      return response.data
    } catch (error) {
      return { valid: false }
    }
  }

  return {
    // 状态
    user: readonly(user),
    token: readonly(token),
    permissions: readonly(permissions),
    
    // 计算属性
    isLoggedIn,
    isAdmin,
    isSuperAdmin,
    
    // 动作
    login,
    logout,
    checkLoginStatus,
    hasPermission,
    hasAnyPermission,
    updateProfile,
    changePassword,
    refreshToken,
    verifyToken
  }
})