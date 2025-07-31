import request from '@/utils/request'
import type { LoginForm, RegisterForm, User, ChangePasswordForm, UserProfile } from '@/types/user'
import type { ApiResponse } from '@/types/api'

export const authApi = {
  // 用户登录
  login(data: LoginForm): Promise<ApiResponse<{ access_token: string; user: User }>> {
    return request({
      url: '/auth/login',
      method: 'post',
      data
    })
  },

  // 用户注册
  register(data: RegisterForm): Promise<ApiResponse<User>> {
    return request({
      url: '/auth/register',
      method: 'post',
      data
    })
  },

  // 用户登出
  logout(): Promise<ApiResponse> {
    return request({
      url: '/auth/logout',
      method: 'post'
    })
  },

  // 获取当前用户信息
  getCurrentUser(): Promise<ApiResponse<User>> {
    return request({
      url: '/auth/me',
      method: 'get'
    })
  },

  // 更新用户资料
  updateProfile(data: UserProfile): Promise<ApiResponse<User>> {
    return request({
      url: '/auth/profile',
      method: 'put',
      data
    })
  },

  // 修改密码
  changePassword(data: ChangePasswordForm): Promise<ApiResponse> {
    return request({
      url: '/auth/change-password',
      method: 'post',
      data
    })
  },

  // 发送邮箱验证码
  sendEmailVerification(email: string): Promise<ApiResponse> {
    return request({
      url: '/auth/send-email-verification',
      method: 'post',
      data: { email }
    })
  },

  // 验证邮箱
  verifyEmail(token: string): Promise<ApiResponse> {
    return request({
      url: '/auth/verify-email',
      method: 'post',
      data: { token }
    })
  },

  // 发送密码重置邮件
  sendPasswordReset(email: string): Promise<ApiResponse> {
    return request({
      url: '/auth/send-password-reset',
      method: 'post',
      data: { email }
    })
  },

  // 重置密码
  resetPassword(token: string, password: string): Promise<ApiResponse> {
    return request({
      url: '/auth/reset-password',
      method: 'post',
      data: { token, password }
    })
  },

  // 刷新token
  refreshToken(): Promise<ApiResponse<{ access_token: string }>> {
    return request({
      url: '/auth/refresh',
      method: 'post'
    })
  }
}