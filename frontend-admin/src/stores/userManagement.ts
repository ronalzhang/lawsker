import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'
import type { 
  UserManagementAnalytics, 
  UserRegistrationTrend, 
  LawyerCertificationData,
  UserActivityData,
  UserBehaviorTrace
} from '@/types'
import request from '@/utils/request'

export const useUserManagementStore = defineStore('userManagement', () => {
  // 状态
  const analytics = ref<UserManagementAnalytics>({
    userRegistration: {
      total: 0,
      today: 0,
      this_week: 0,
      this_month: 0,
      growth_rate: 0
    },
    userActivity: {
      active_users: 0,
      inactive_users: 0,
      new_users_retention: 0,
      avg_session_duration: 0
    },
    lawyerCertification: {
      total_lawyers: 0,
      verified: 0,
      pending: 0,
      rejected: 0,
      verification_rate: 0
    },
    userBehavior: []
  })

  const registrationTrend = ref<UserRegistrationTrend>({
    labels: [],
    datasets: []
  })

  const lawyerCertifications = ref<LawyerCertificationData[]>([])
  const userActivities = ref<UserActivityData[]>([])
  const userBehaviorTraces = ref<UserBehaviorTrace[]>([])

  const loading = ref({
    analytics: false,
    registrationTrend: false,
    lawyerCertifications: false,
    userActivities: false,
    userBehaviorTraces: false
  })

  // 动作
  const fetchAnalytics = async (period: string = '7d') => {
    loading.value.analytics = true
    try {
      const response = await request({
        url: '/admin/user-management/analytics',
        method: 'get',
        params: { period }
      })
      
      analytics.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.analytics = false
    }
  }

  const fetchRegistrationTrend = async (period: string = '30d') => {
    loading.value.registrationTrend = true
    try {
      const response = await request({
        url: '/admin/user-management/registration-trend',
        method: 'get',
        params: { period }
      })
      
      registrationTrend.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.registrationTrend = false
    }
  }

  const fetchLawyerCertifications = async (status?: string, page: number = 1, size: number = 20) => {
    loading.value.lawyerCertifications = true
    try {
      const response = await request({
        url: '/admin/user-management/lawyer-certifications',
        method: 'get',
        params: { status, page, size }
      })
      
      lawyerCertifications.value = response.data.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.lawyerCertifications = false
    }
  }

  const fetchUserActivities = async (status?: string, page: number = 1, size: number = 20) => {
    loading.value.userActivities = true
    try {
      const response = await request({
        url: '/admin/user-management/user-activities',
        method: 'get',
        params: { status, page, size }
      })
      
      userActivities.value = response.data.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.userActivities = false
    }
  }

  const fetchUserBehaviorTraces = async (userId?: string, page: number = 1, size: number = 10) => {
    loading.value.userBehaviorTraces = true
    try {
      const response = await request({
        url: '/admin/user-management/behavior-traces',
        method: 'get',
        params: { user_id: userId, page, size }
      })
      
      userBehaviorTraces.value = response.data.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.userBehaviorTraces = false
    }
  }

  // 律师认证操作
  const approveLawyerCertification = async (lawyerId: string, note?: string) => {
    try {
      const response = await request({
        url: `/admin/user-management/lawyer-certifications/${lawyerId}/approve`,
        method: 'post',
        data: { note }
      })
      
      // 更新本地数据
      const index = lawyerCertifications.value.findIndex(item => item.id === lawyerId)
      if (index !== -1) {
        lawyerCertifications.value[index].status = 'verified'
        lawyerCertifications.value[index].reviewed_at = new Date().toISOString()
      }
      
      return response
    } catch (error) {
      throw error
    }
  }

  const rejectLawyerCertification = async (lawyerId: string, reason: string) => {
    try {
      const response = await request({
        url: `/admin/user-management/lawyer-certifications/${lawyerId}/reject`,
        method: 'post',
        data: { reason }
      })
      
      // 更新本地数据
      const index = lawyerCertifications.value.findIndex(item => item.id === lawyerId)
      if (index !== -1) {
        lawyerCertifications.value[index].status = 'rejected'
        lawyerCertifications.value[index].reviewed_at = new Date().toISOString()
        lawyerCertifications.value[index].rejection_reason = reason
      }
      
      return response
    } catch (error) {
      throw error
    }
  }

  // 用户状态管理
  const updateUserStatus = async (userId: string, status: 'active' | 'inactive') => {
    try {
      const response = await request({
        url: `/admin/user-management/users/${userId}/status`,
        method: 'put',
        data: { status }
      })
      
      // 更新本地数据
      const index = userActivities.value.findIndex(item => item.user_id === userId)
      if (index !== -1) {
        userActivities.value[index].status = status
      }
      
      return response
    } catch (error) {
      throw error
    }
  }

  const initUserManagement = async () => {
    await Promise.all([
      fetchAnalytics(),
      fetchRegistrationTrend(),
      fetchLawyerCertifications(),
      fetchUserActivities()
    ])
  }

  return {
    // 状态
    analytics: readonly(analytics),
    registrationTrend: readonly(registrationTrend),
    lawyerCertifications: readonly(lawyerCertifications),
    userActivities: readonly(userActivities),
    userBehaviorTraces: readonly(userBehaviorTraces),
    loading: readonly(loading),
    
    // 动作
    fetchAnalytics,
    fetchRegistrationTrend,
    fetchLawyerCertifications,
    fetchUserActivities,
    fetchUserBehaviorTraces,
    approveLawyerCertification,
    rejectLawyerCertification,
    updateUserStatus,
    initUserManagement
  }
})