<template>
  <div class="analytics-view">
    <!-- 页面标题和时间选择器 -->
    <div class="analytics-header">
      <h2>访问数据分析</h2>
      <el-select v-model="selectedPeriod" @change="handlePeriodChange" size="default">
        <el-option label="最近7天" value="7d" />
        <el-option label="最近30天" value="30d" />
        <el-option label="最近90天" value="90d" />
      </el-select>
    </div>

    <!-- 访问概览统计卡片 -->
    <div class="overview-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="总访问量"
            :value="analyticsStore.accessAnalytics.pageViews.total"
            :icon="View"
            color="primary"
            :loading="analyticsStore.loading.accessAnalytics"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="独立访客"
            :value="analyticsStore.accessAnalytics.pageViews.unique"
            :icon="User"
            color="success"
            :loading="analyticsStore.loading.accessAnalytics"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="跳出率"
            :value="`${analyticsStore.accessAnalytics.pageViews.bounce_rate}%`"
            :icon="TrendCharts"
            color="warning"
            :loading="analyticsStore.loading.accessAnalytics"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="平均会话时长"
            :value="formatDuration(analyticsStore.accessAnalytics.pageViews.avg_session_duration)"
            :icon="Timer"
            color="info"
            :loading="analyticsStore.loading.accessAnalytics"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 访问量趋势图 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>访问量趋势</span>
            </template>
            <div class="chart-container">
              <PageViewTrendChart :period="selectedPeriod" />
            </div>
          </el-card>
        </el-col>

        <!-- 设备类型分布 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>设备类型分布</span>
            </template>
            <div class="chart-container">
              <DeviceStatsChart :data="analyticsStore.accessAnalytics.deviceStats" :loading="analyticsStore.loading.accessAnalytics" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 浏览器统计 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>浏览器统计</span>
            </template>
            <div class="chart-container">
              <BrowserStatsChart :data="analyticsStore.accessAnalytics.browserStats" :loading="analyticsStore.loading.accessAnalytics" />
            </div>
          </el-card>
        </el-col>

        <!-- 地域分布热力图 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>地域分布</span>
            </template>
            <div class="chart-container">
              <GeoDistributionChart :data="analyticsStore.accessAnalytics.geoDistribution" :loading="analyticsStore.loading.accessAnalytics" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 数据表格区域 -->
    <div class="tables-section">
      <el-row :gutter="20">
        <!-- 热门页面排行 -->
        <el-col :xs="24" :lg="12">
          <el-card class="table-card" shadow="hover">
            <template #header>
              <span>热门页面排行</span>
            </template>
            <TopPagesTable :data="analyticsStore.accessAnalytics.topPages" :loading="analyticsStore.loading.accessAnalytics" />
          </el-card>
        </el-col>

        <!-- IP地址分析 -->
        <el-col :xs="24" :lg="12">
          <el-card class="table-card" shadow="hover">
            <template #header>
              <span>IP地址分析</span>
            </template>
            <IpAnalysisTable :data="analyticsStore.ipAnalysis.topIps" :loading="analyticsStore.loading.ipAnalysis" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 用户路径分析 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card class="table-card" shadow="hover">
            <template #header>
              <span>用户路径分析</span>
            </template>
            <UserPathAnalysisTable :data="analyticsStore.userPathAnalysis" :loading="analyticsStore.loading.userPathAnalysis" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { View, User, TrendCharts, Timer } from '@element-plus/icons-vue'
import { useAnalyticsStore } from '@/stores/analytics'
import StatCard from '@/components/common/StatCard.vue'
import PageViewTrendChart from './components/PageViewTrendChart.vue'
import DeviceStatsChart from './components/DeviceStatsChart.vue'
import BrowserStatsChart from './components/BrowserStatsChart.vue'
import GeoDistributionChart from './components/GeoDistributionChart.vue'
import TopPagesTable from './components/TopPagesTable.vue'
import IpAnalysisTable from './components/IpAnalysisTable.vue'
import UserPathAnalysisTable from './components/UserPathAnalysisTable.vue'

const analyticsStore = useAnalyticsStore()
const selectedPeriod = ref('7d')

// 格式化时长显示
const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}分钟`
  } else {
    return `${Math.round(seconds / 3600)}小时`
  }
}

// 处理时间周期变化
const handlePeriodChange = async (period: string) => {
  await Promise.all([
    analyticsStore.fetchAccessAnalytics(period),
    analyticsStore.fetchIpAnalysis(period),
    analyticsStore.fetchUserPathAnalysis(period)
  ])
}

onMounted(async () => {
  await analyticsStore.initAnalytics()
})
</script>

<style lang="scss" scoped>
.analytics-view {
  padding: 20px;
  
  .analytics-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
      color: var(--el-text-color-primary);
    }
  }
  
  .overview-cards {
    margin-bottom: 20px;
  }
  
  .charts-section {
    margin-bottom: 20px;
    
    .chart-card {
      .chart-container {
        height: 300px;
        padding: 10px 0;
      }
    }
  }
  
  .tables-section {
    .table-card {
      :deep(.el-card__body) {
        padding: 0;
      }
    }
  }
}

@media (max-width: 768px) {
  .analytics-view {
    padding: 10px;
    
    .analytics-header {
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