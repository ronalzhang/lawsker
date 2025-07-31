import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'
import type { AccessAnalytics, IpAnalysis, UserPathAnalysis } from '@/types'
import request from '@/utils/request'

export const useAnalyticsStore = defineStore('analytics', () => {
  // 状态
  const accessAnalytics = ref<AccessAnalytics>({
    pageViews: {
      total: 0,
      unique: 0,
      bounce_rate: 0,
      avg_session_duration: 0
    },
    topPages: [],
    geoDistribution: [],
    deviceStats: {
      desktop: 0,
      mobile: 0,
      tablet: 0
    },
    browserStats: [],
    trafficSources: []
  })

  const ipAnalysis = ref<IpAnalysis>({
    topIps: [],
    geoData: []
  })

  const userPathAnalysis = ref<UserPathAnalysis>({
    commonPaths: [],
    entryPages: [],
    exitPages: []
  })

  const loading = ref({
    accessAnalytics: false,
    ipAnalysis: false,
    userPathAnalysis: false
  })

  // 动作
  const fetchAccessAnalytics = async (period: string = '7d') => {
    loading.value.accessAnalytics = true
    try {
      const response = await request({
        url: '/admin/analytics/access',
        method: 'get',
        params: { period }
      })
      
      accessAnalytics.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.accessAnalytics = false
    }
  }

  const fetchIpAnalysis = async (period: string = '7d') => {
    loading.value.ipAnalysis = true
    try {
      const response = await request({
        url: '/admin/analytics/ip-analysis',
        method: 'get',
        params: { period }
      })
      
      ipAnalysis.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.ipAnalysis = false
    }
  }

  const fetchUserPathAnalysis = async (period: string = '7d') => {
    loading.value.userPathAnalysis = true
    try {
      const response = await request({
        url: '/admin/analytics/user-paths',
        method: 'get',
        params: { period }
      })
      
      userPathAnalysis.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.userPathAnalysis = false
    }
  }

  const fetchPageViewTrend = async (period: string = '7d') => {
    try {
      const response = await request({
        url: '/admin/analytics/pageview-trend',
        method: 'get',
        params: { period }
      })
      
      return response.data
    } catch (error) {
      throw error
    }
  }

  const initAnalytics = async () => {
    await Promise.all([
      fetchAccessAnalytics(),
      fetchIpAnalysis(),
      fetchUserPathAnalysis()
    ])
  }

  return {
    // 状态
    accessAnalytics: readonly(accessAnalytics),
    ipAnalysis: readonly(ipAnalysis),
    userPathAnalysis: readonly(userPathAnalysis),
    loading: readonly(loading),
    
    // 动作
    fetchAccessAnalytics,
    fetchIpAnalysis,
    fetchUserPathAnalysis,
    fetchPageViewTrend,
    initAnalytics
  }
})