import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginForm, RegisterForm } from '@/types/user'
import { authApi } from '@/api/auth'
import { getToken, setToken, removeToken } from '@/utils/auth'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string>('')
  const loading = ref(false)
  const refreshTokenTimer = ref<NodeJS.Timeout | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role || '')
  const userName = computed(() => user.value?.username || user.value?.real_name || '')
  const userAvatar = computed(() => user.value?.avatar || '')
  const isEmailVerified = computed(() => user.value?.email_verified || false)
  const isPhoneVerified = computed(() => user.value?.phone_verified || false)

  // Token自动刷新
  const startTokenRefresh = () => {
    // 每50分钟刷新一次token（假设token有效期为1小时）
    refreshTokenTimer.value = setInterval(async () => {
      try {
        const response = await authApi.refreshToken()
        const { access_token } = response.data
        token.value = access_token
        setToken(access_token)
      } catch (error) {
        console.error('Token refresh failed:', error)
        // Token刷新失败，清除登录状态
        await logout()
      }
    }, 50 * 60 * 1000) // 50分钟
  }

  const stopTokenRefresh = () => {
    if (refreshTokenTimer.value) {
      clearInterval(refreshTokenTimer.value)
      refreshTokenTimer.value = null
    }
  }

  // 动作
  const login = async (loginForm: LoginForm) => {
    loading.value = true
    try {
      const response = await authApi.login(loginForm)
      const { access_token, user: userInfo } = response.data
      
      // 保存token和用户信息
      token.value = access_token
      user.value = userInfo
      setToken(access_token)
      
      // 启动token自动刷新
      startTokenRefresh()
      
      ElMessage.success('登录成功')
      return Promise.resolve(response)
    } catch (error: any) {
      ElMessage.error(error.message || '登录失败')
      return Promise.reject(error)
    } finally {
      loading.value = false
    }
  }

  const register = async (registerForm: RegisterForm) => {
    loading.value = true
    try {
      const response = await authApi.register(registerForm)
      ElMessage.success('注册成功，请登录')
      return Promise.resolve(response)
    } catch (error: any) {
      ElMessage.error(error.message || '注册失败')
      return Promise.reject(error)
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 停止token刷新
      stopTokenRefresh()
      
      // 清除本地状态
      user.value = null
      token.value = ''
      removeToken()
      ElMessage.success('已退出登录')
    }
  }

  const checkLoginStatus = async () => {
    const savedToken = getToken()
    if (!savedToken) {
      return false
    }

    try {
      token.value = savedToken
      const response = await authApi.getCurrentUser()
      user.value = response.data
      
      // 启动token自动刷新
      startTokenRefresh()
      
      return true
    } catch (error) {
      // Token无效，清除本地存储
      removeToken()
      token.value = ''
      user.value = null
      return false
    }
  }

  const updateProfile = async (profileData: Partial<User>) => {
    loading.value = true
    try {
      const response = await authApi.updateProfile(profileData)
      user.value = { ...user.value, ...response.data }
      ElMessage.success('个人信息更新成功')
      return Promise.resolve(response)
    } catch (error: any) {
      ElMessage.error(error.message || '更新失败')
      return Promise.reject(error)
    } finally {
      loading.value = false
    }
  }

  const changePassword = async (oldPassword: string, newPassword: string) => {
    loading.value = true
    try {
      await authApi.changePassword({ 
        old_password: oldPassword, 
        new_password: newPassword,
        confirm_password: newPassword
      })
      ElMessage.success('密码修改成功')
    } catch (error: any) {
      ElMessage.error(error.message || '密码修改失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const sendEmailVerification = async () => {
    if (!user.value?.email) {
      ElMessage.error('邮箱地址不存在')
      return
    }
    
    loading.value = true
    try {
      await authApi.sendEmailVerification(user.value.email)
      ElMessage.success('验证邮件已发送')
    } catch (error: any) {
      ElMessage.error(error.message || '发送失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const verifyEmail = async (verificationToken: string) => {
    loading.value = true
    try {
      await authApi.verifyEmail(verificationToken)
      if (user.value) {
        user.value.email_verified = true
      }
      ElMessage.success('邮箱验证成功')
    } catch (error: any) {
      ElMessage.error(error.message || '验证失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const refreshUserInfo = async () => {
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data
    } catch (error) {
      console.error('Failed to refresh user info:', error)
    }
  }

  return {
    // 状态
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    
    // 计算属性
    isLoggedIn,
    userRole,
    userName,
    userAvatar,
    isEmailVerified,
    isPhoneVerified,
    
    // 动作
    login,
    register,
    logout,
    checkLoginStatus,
    updateProfile,
    changePassword,
    sendEmailVerification,
    verifyEmail,
    refreshUserInfo
  }
})