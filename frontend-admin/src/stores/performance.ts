import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'
import type { 
  PerformanceRanking, 
  PerformanceComparison, 
  TrendPrediction 
} from '@/types'
import request from '@/utils/request'

export const usePerformanceStore = defineStore('performance', () => {
  // 状态
  const ranking = ref<PerformanceRanking>({
    lawyerRanking: [],
    userConsumption: [],
    platformRevenue: {
      total_revenue: 0,
      lawyer_fees: 0,
      platform_commission: 0,
      growth_rate: 0,
      monthly_trend: []
    }
  })

  const comparison = ref<PerformanceComparison>({
    period: '',
    lawyers: [],
    categories: []
  })

  const prediction = ref<TrendPrediction>({
    revenue_forecast: [],
    lawyer_performance_forecast: [],
    market_trends: []
  })

  const loading = ref({
    ranking: false,
    comparison: false,
    prediction: false
  })

  // 动作
  const fetchRanking = async (period: string = '30d') => {
    loading.value.ranking = true
    try {
      const response = await request({
        url: '/admin/performance/ranking',
        method: 'get',
        params: { period }
      })
      
      ranking.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.ranking = false
    }
  }  co
nst fetchComparison = async (period: string = '30d', comparePeriod: string = '30d') => {
    loading.value.comparison = true
    try {
      const response = await request({
        url: '/admin/performance/comparison',
        method: 'get',
        params: { period, compare_period: comparePeriod }
      })
      
      comparison.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.comparison = false
    }
  }

  const fetchPrediction = async (forecastDays: number = 30) => {
    loading.value.prediction = true
    try {
      const response = await request({
        url: '/admin/performance/prediction',
        method: 'get',
        params: { forecast_days: forecastDays }
      })
      
      prediction.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value.prediction = false
    }
  }

  const fetchLawyerRankingTrend = async (lawyerId: string, period: string = '90d') => {
    try {
      const response = await request({
        url: `/admin/performance/lawyer-trend/${lawyerId}`,
        method: 'get',
        params: { period }
      })
      
      return response.data
    } catch (error) {
      throw error
    }
  }

  const fetchRevenueBreakdown = async (period: string = '30d') => {
    try {
      const response = await request({
        url: '/admin/performance/revenue-breakdown',
        method: 'get',
        params: { period }
      })
      
      return response.data
    } catch (error) {
      throw error
    }
  }

  const initPerformance = async () => {
    await Promise.all([
      fetchRanking(),
      fetchComparison(),
      fetchPrediction()
    ])
  }

  return {
    // 状态
    ranking: readonly(ranking),
    comparison: readonly(comparison),
    prediction: readonly(prediction),
    loading: readonly(loading),
    
    // 动作
    fetchRanking,
    fetchComparison,
    fetchPrediction,
    fetchLawyerRankingTrend,
    fetchRevenueBreakdown,
    initPerformance
  }
})