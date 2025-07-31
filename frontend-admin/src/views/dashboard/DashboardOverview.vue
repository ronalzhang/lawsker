<template>
  <div class="dashboard-overview">
    <!-- 实时数据卡片区域 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="总用户数"
            :value="dashboardStore.stats.users.total"
            :trend="dashboardStore.stats.users.growth_rate"
            :icon="User"
            color="primary"
            :loading="dashboardStore.loading"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="认证律师"
            :value="dashboardStore.stats.lawyers.verified"
            :trend="dashboardStore.stats.lawyers.growth_rate"
            :icon="UserFilled"
            color="success"
            :loading="dashboardStore.loading"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="进行中案件"
            :value="dashboardStore.stats.cases.in_progress"
            :trend="dashboardStore.stats.cases.growth_rate"
            :icon="Document"
            color="warning"
            :loading="dashboardStore.loading"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="今日收入"
            :value="dashboardStore.stats.revenue.today"
            unit="元"
            :trend="dashboardStore.stats.revenue.growth_rate"
            :icon="Money"
            color="danger"
            :loading="dashboardStore.loading"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 实时系统状态监控 -->
    <div class="realtime-status">
      <el-card class="status-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>实时系统状态</span>
            <el-tag :type="systemStatusType" size="small">
              {{ systemStatusText }}
            </el-tag>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="status-item">
              <div class="status-label">在线用户</div>
              <div class="status-value">{{ dashboardStore.realtimeData.online_users }}</div>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <div class="status-item">
              <div class="status-label">活跃会话</div>
              <div class="status-value">{{ dashboardStore.realtimeData.active_sessions }}</div>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <div class="status-item">
              <div class="status-label">服务器负载</div>
              <div class="status-value">{{ dashboardStore.realtimeData.server_load }}%</div>
              <el-progress 
                :percentage="dashboardStore.realtimeData.server_load" 
                :color="getProgressColor(dashboardStore.realtimeData.server_load)"
                :show-text="false"
                :stroke-width="6"
              />
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <div class="status-item">
              <div class="status-label">内存使用</div>
              <div class="status-value">{{ dashboardStore.realtimeData.memory_usage }}%</div>
              <el-progress 
                :percentage="dashboardStore.realtimeData.memory_usage" 
                :color="getProgressColor(dashboardStore.realtimeData.memory_usage)"
                :show-text="false"
                :stroke-width="6"
              />
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 趋势图表区域 -->
    <div class="trend-charts">
      <el-row :gutter="20">
        <!-- 用户增长趋势 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>用户增长趋势</span>
                <el-select v-model="userTrendPeriod" @change="handleUserTrendPeriodChange" size="small">
                  <el-option label="7天" value="7d" />
                  <el-option label="30天" value="30d" />
                  <el-option label="90天" value="90d" />
                </el-select>
              </div>
            </template>
            
            <div class="chart-container">
              <UserTrendChart :data="dashboardStore.userTrendData" :loading="chartLoading.userTrend" />
            </div>
          </el-card>
        </el-col>

        <!-- 案件处理趋势 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>案件处理趋势</span>
                <el-select v-model="caseTrendPeriod" @change="handleCaseTrendPeriodChange" size="small">
                  <el-option label="7天" value="7d" />
                  <el-option label="30天" value="30d" />
                  <el-option label="90天" value="90d" />
                </el-select>
              </div>
            </template>
            
            <div class="chart-container">
              <CaseTrendChart :data="dashboardStore.caseTrendData" :loading="chartLoading.caseTrend" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 收入趋势图表 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>收入趋势分析</span>
                <el-select v-model="revenueTrendPeriod" @change="handleRevenueTrendPeriodChange" size="small">
                  <el-option label="7天" value="7d" />
                  <el-option label="30天" value="30d" />
                  <el-option label="90天" value="90d" />
                </el-select>
              </div>
            </template>
            
            <div class="chart-container">
              <RevenueTrendChart :data="dashboardStore.revenueTrendData" :loading="chartLoading.revenueTrend" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { User, UserFilled, Document, Money } from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'
import StatCard from '@/components/common/StatCard.vue'
import UserTrendChart from './components/UserTrendChart.vue'
import CaseTrendChart from './components/CaseTrendChart.vue'
import RevenueTrendChart from './components/RevenueTrendChart.vue'

const dashboardStore = useDashboardStore()

// 图表时间周期
const userTrendPeriod = ref('7d')
const caseTrendPeriod = ref('7d')
const revenueTrendPeriod = ref('7d')

// 图表加载状态
const chartLoading = ref({
  userTrend: false,
  caseTrend: false,
  revenueTrend: false
})

// 系统状态计算
const systemStatusType = computed(() => {
  const serverLoad = dashboardStore.realtimeData.server_load
  const memoryUsage = dashboardStore.realtimeData.memory_usage
  
  if (serverLoad > 80 || memoryUsage > 80) return 'danger'
  if (serverLoad > 60 || memoryUsage > 60) return 'warning'
  return 'success'
})

const systemStatusText = computed(() => {
  const type = systemStatusType.value
  if (type === 'danger') return '高负载'
  if (type === 'warning') return '中等负载'
  return '正常'
})

// 进度条颜色
const getProgressColor = (percentage: number) => {
  if (percentage > 80) return '#f56c6c'
  if (percentage > 60) return '#e6a23c'
  return '#67c23a'
}

// 处理时间周期变化
const handleUserTrendPeriodChange = async (period: string) => {
  chartLoading.value.userTrend = true
  try {
    await dashboardStore.fetchUserTrend(period)
  } finally {
    chartLoading.value.userTrend = false
  }
}

const handleCaseTrendPeriodChange = async (period: string) => {
  chartLoading.value.caseTrend = true
  try {
    await dashboardStore.fetchCaseTrend(period)
  } finally {
    chartLoading.value.caseTrend = false
  }
}

const handleRevenueTrendPeriodChange = async (period: string) => {
  chartLoading.value.revenueTrend = true
  try {
    await dashboardStore.fetchRevenueTrend(period)
  } finally {
    chartLoading.value.revenueTrend = false
  }
}

// 定时刷新实时数据
let refreshTimer: NodeJS.Timeout | null = null

const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    dashboardStore.refreshData()
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(async () => {
  await dashboardStore.initDashboard()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  dashboardStore.removeWebSocketListeners()
})
</script>

<style lang="scss" scoped>
.dashboard-overview {
  padding: 20px;
  
  .stats-cards {
    margin-bottom: 20px;
  }
  
  .realtime-status {
    margin-bottom: 20px;
    
    .status-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .status-item {
        text-align: center;
        padding: 10px;
        
        .status-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          margin-bottom: 8px;
        }
        
        .status-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 8px;
        }
      }
    }
  }
  
  .trend-charts {
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
}

@media (max-width: 768px) {
  .dashboard-overview {
    padding: 10px;
    
    .trend-charts {
      .chart-container {
        height: 250px;
      }
    }
  }
}
</style>