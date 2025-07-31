<template>
  <div class="performance-view">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <h2>业绩排行系统</h2>
      <div class="header-actions">
        <el-select v-model="selectedPeriod" @change="handlePeriodChange" size="default">
          <el-option label="最近7天" value="7d" />
          <el-option label="最近30天" value="30d" />
          <el-option label="最近90天" value="90d" />
        </el-select>
        <el-button type="primary" :icon="Refresh" @click="refreshData">
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 平台收入概览卡片 -->
    <div class="overview-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="平台总收入"
            :value="performanceStore.ranking.platformRevenue.total_revenue"
            unit="元"
            :trend="performanceStore.ranking.platformRevenue.growth_rate"
            :icon="Money"
            color="primary"
            :loading="performanceStore.loading.ranking"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="律师费用"
            :value="performanceStore.ranking.platformRevenue.lawyer_fees"
            unit="元"
            :icon="Wallet"
            color="success"
            :loading="performanceStore.loading.ranking"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="平台佣金"
            :value="performanceStore.ranking.platformRevenue.platform_commission"
            unit="元"
            :icon="CreditCard"
            color="warning"
            :loading="performanceStore.loading.ranking"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="活跃律师"
            :value="performanceStore.ranking.lawyerRanking.length"
            :icon="UserFilled"
            color="info"
            :loading="performanceStore.loading.ranking"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 图表分析区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 平台收入趋势 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>平台收入趋势</span>
            </template>
            <div class="chart-container">
              <RevenueeTrendChart 
                :data="performanceStore.ranking.platformRevenue.monthly_trend" 
                :loading="performanceStore.loading.ranking" 
              />
            </div>
          </el-card>
        </el-col>

        <!-- 业绩对比分析 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>业绩对比分析</span>
                <el-select v-model="comparisonPeriod" @change="handleComparisonChange" size="small">
                  <el-option label="与上月对比" value="30d" />
                  <el-option label="与上季度对比" value="90d" />
                  <el-option label="与去年同期对比" value="365d" />
                </el-select>
              </div>
            </template>
            <div class="chart-container">
              <PerformanceComparisonChart 
                :data="performanceStore.comparison" 
                :loading="performanceStore.loading.comparison" 
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 趋势预测图表 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>收入趋势预测</span>
                <el-select v-model="forecastDays" @change="handleForecastChange" size="small">
                  <el-option label="未来30天" :value="30" />
                  <el-option label="未来60天" :value="60" />
                  <el-option label="未来90天" :value="90" />
                </el-select>
              </div>
            </template>
            <div class="chart-container">
              <TrendPredictionChart 
                :data="performanceStore.prediction.revenue_forecast" 
                :loading="performanceStore.loading.prediction" 
              />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 排行榜区域 -->
    <div class="ranking-section">
      <el-tabs v-model="activeTab" type="card">
        <!-- 律师业绩排行榜 -->
        <el-tab-pane label="律师业绩排行" name="lawyerRanking">
          <LawyerRankingTable 
            :data="performanceStore.ranking.lawyerRanking"
            :loading="performanceStore.loading.ranking"
            @view-trend="handleViewLawyerTrend"
          />
        </el-tab-pane>

        <!-- 用户消费排行 -->
        <el-tab-pane label="用户消费排行" name="userConsumption">
          <UserConsumptionTable 
            :data="performanceStore.ranking.userConsumption"
            :loading="performanceStore.loading.ranking"
          />
        </el-tab-pane>

        <!-- 律师业绩预测 -->
        <el-tab-pane label="律师业绩预测" name="lawyerForecast">
          <LawyerForecastTable 
            :data="performanceStore.prediction.lawyer_performance_forecast"
            :loading="performanceStore.loading.prediction"
          />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template><
script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Money, 
  Wallet, 
  CreditCard, 
  UserFilled, 
  Refresh 
} from '@element-plus/icons-vue'
import { usePerformanceStore } from '@/stores/performance'
import StatCard from '@/components/common/StatCard.vue'
import RevenueeTrendChart from './components/RevenueTrendChart.vue'
import PerformanceComparisonChart from './components/PerformanceComparisonChart.vue'
import TrendPredictionChart from './components/TrendPredictionChart.vue'
import LawyerRankingTable from './components/LawyerRankingTable.vue'
import UserConsumptionTable from './components/UserConsumptionTable.vue'
import LawyerForecastTable from './components/LawyerForecastTable.vue'

const performanceStore = usePerformanceStore()
const selectedPeriod = ref('30d')
const comparisonPeriod = ref('30d')
const forecastDays = ref(30)
const activeTab = ref('lawyerRanking')

// 处理时间周期变化
const handlePeriodChange = async (period: string) => {
  await performanceStore.fetchRanking(period)
}

// 处理对比周期变化
const handleComparisonChange = async (period: string) => {
  await performanceStore.fetchComparison(selectedPeriod.value, period)
}

// 处理预测周期变化
const handleForecastChange = async (days: number) => {
  await performanceStore.fetchPrediction(days)
}

// 刷新数据
const refreshData = async () => {
  try {
    await performanceStore.initPerformance()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  }
}

// 查看律师趋势
const handleViewLawyerTrend = async (lawyerId: string) => {
  try {
    const trendData = await performanceStore.fetchLawyerRankingTrend(lawyerId)
    // 这里可以打开一个对话框显示律师的详细趋势
    console.log('Lawyer trend data:', trendData)
  } catch (error) {
    ElMessage.error('获取律师趋势数据失败')
  }
}

onMounted(async () => {
  await performanceStore.initPerformance()
})
</script>

<style lang="scss" scoped>
.performance-view {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
      color: var(--el-text-color-primary);
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }
  
  .overview-cards {
    margin-bottom: 20px;
  }
  
  .charts-section {
    margin-bottom: 20px;
    
    .chart-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .chart-container {
        height: 300px;
        padding: 10px 0;
      }
    }
  }
  
  .ranking-section {
    :deep(.el-tabs) {
      .el-tabs__header {
        margin-bottom: 20px;
      }
      
      .el-tabs__content {
        padding: 0;
      }
    }
  }
}

@media (max-width: 768px) {
  .performance-view {
    padding: 10px;
    
    .page-header {
      flex-direction: column;
      gap: 10px;
      align-items: flex-start;
    }
    
    .charts-section {
      .chart-container {
        height: 250px;
      }
    }
  }
}
</style>