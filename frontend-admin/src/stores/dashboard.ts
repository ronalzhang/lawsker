import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'
import type { DashboardStats, ChartData } from '@/types'
import request from '@/utils/request'
import { wsManager } from '@/utils/websocket'

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态
  const stats = ref<DashboardStats>({
    users: {
      total: 0,
      active: 0,
      new_today: 0,
      growth_rate: 0
    },
    lawyers: {
      total: 0,
      verified: 0,
      pending: 0,
      growth_rate: 0
    },
    cases: {
      total: 0,
      pending: 0,
      in_progress: 0,
      completed: 0,
      growth_rate: 0
    },
    revenue: {
      total: 0,
      today: 0,
      this_month: 0,
      growth_rate: 0
    }
  })

  const userTrendData = ref<ChartData>({
    labels: [],
    datasets: []
  })

  const caseTrendData = ref<ChartData>({
    labels: [],
    datasets: []
  })

  const revenueTrendData = ref<ChartData>({
    labels: [],
    datasets: []
  })

  const realtimeData = ref({
    online_users: 0,
    active_sessions: 0,
    server_load: 0,
    memory_usage: 0
  })

  const loading = ref(false)

  // 动作
  const fetchStats = async () => {
    loading.value = true
    try {
      const response = await request({
        url: '/admin/dashboard/stats',
        method: 'get'
      })
      
      stats.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchUserTrend = async (period: string = '7d') => {
    try {
      const response = await request({
        url: '/admin/dashboard/user-trend',
        method: 'get',
        params: { period }
      })
      
      userTrendData.value = response.data
      return response
    } catch (error) {
      throw error
    }
  }

  const fetchCaseTrend = async (period: string = '7d') => {
    try {
      const response = await request({
        url: '/admin/dashboard/case-trend',
        method: 'get',
        params: { period }
      })
      
      caseTrendData.value = response.data
      return response
    } catch (error) {
      throw error
    }
  }

  const fetchRevenueTrend = async (period: string = '7d') => {
    try {
      const response = await request({
        url: '/admin/dashboard/revenue-trend',
        method: 'get',
        params: { period }
      })
      
      revenueTrendData.value = response.data
      return response
    } catch (error) {
      throw error
    }
  }

  const fetchRealtimeData = async () => {
    try {
      const response = await request({
        url: '/admin/dashboard/realtime',
        method: 'get'
      })
      
      realtimeData.value = response.data
      return response
    } catch (error) {
      throw error
    }
  }

  // WebSocket事件处理
  const setupWebSocketListeners = () => {
    wsManager.on('stats_update', (data: any) => {
      if (data.type === 'dashboard_stats') {
        stats.value = { ...stats.value, ...data.stats }
      }
    })

    wsManager.on('user_activity', (data: any) => {
      realtimeData.value = { ...realtimeData.value, ...data }
    })
  }

  const removeWebSocketListeners = () => {
    wsManager.off('stats_update')
    wsManager.off('user_activity')
  }

  // 初始化数据
  const initDashboard = async () => {
    await Promise.all([
      fetchStats(),
      fetchUserTrend(),
      fetchCaseTrend(),
      fetchRevenueTrend(),
      fetchRealtimeData()
    ])
    
    setupWebSocketListeners()
  }

  const refreshData = async () => {
    await Promise.all([
      fetchStats(),
      fetchRealtimeData()
    ])
  }

  return {
    // 状态
    stats: readonly(stats),
    userTrendData: readonly(userTrendData),
    caseTrendData: readonly(caseTrendData),
    revenueTrendData: readonly(revenueTrendData),
    realtimeData: readonly(realtimeData),
    loading: readonly(loading),
    
    // 动作
    fetchStats,
    fetchUserTrend,
    fetchCaseTrend,
    fetchRevenueTrend,
    fetchRealtimeData,
    initDashboard,
    refreshData,
    setupWebSocketListeners,
    removeWebSocketListeners
  }
})