<template>
  <div class="user-management-view">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <h2>用户管理分析</h2>
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

    <!-- 用户统计概览卡片 -->
    <div class="overview-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="总用户数"
            :value="userManagementStore.analytics.userRegistration.total"
            :trend="userManagementStore.analytics.userRegistration.growth_rate"
            :icon="User"
            color="primary"
            :loading="userManagementStore.loading.analytics"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="今日新增"
            :value="userManagementStore.analytics.userRegistration.today"
            :icon="UserFilled"
            color="success"
            :loading="userManagementStore.loading.analytics"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="活跃用户"
            :value="userManagementStore.analytics.userActivity.active_users"
            :icon="Connection"
            color="warning"
            :loading="userManagementStore.loading.analytics"
          />
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <StatCard
            title="认证律师"
            :value="userManagementStore.analytics.lawyerCertification.verified"
            :trend="userManagementStore.analytics.lawyerCertification.verification_rate"
            :icon="Medal"
            color="danger"
            :loading="userManagementStore.loading.analytics"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 图表分析区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 用户注册趋势 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>用户注册趋势</span>
            </template>
            <div class="chart-container">
              <UserRegistrationChart 
                :data="userManagementStore.registrationTrend" 
                :loading="userManagementStore.loading.registrationTrend" 
              />
            </div>
          </el-card>
        </el-col>

        <!-- 用户活跃度分析 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>用户活跃度分析</span>
            </template>
            <div class="chart-container">
              <UserActivityChart 
                :data="userManagementStore.analytics.userActivity" 
                :loading="userManagementStore.loading.analytics" 
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 律师认证状态 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>律师认证状态</span>
            </template>
            <div class="chart-container">
              <LawyerCertificationChart 
                :data="userManagementStore.analytics.lawyerCertification" 
                :loading="userManagementStore.loading.analytics" 
              />
            </div>
          </el-card>
        </el-col>

        <!-- 用户行为分析 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span>用户行为分析</span>
            </template>
            <div class="chart-container">
              <UserBehaviorChart 
                :data="userManagementStore.analytics.userBehavior" 
                :loading="userManagementStore.loading.analytics" 
              />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 管理表格区域 -->
    <div class="tables-section">
      <el-tabs v-model="activeTab" type="card">
        <!-- 律师认证管理 -->
        <el-tab-pane label="律师认证管理" name="lawyerCertification">
          <LawyerCertificationTable 
            :data="userManagementStore.lawyerCertifications"
            :loading="userManagementStore.loading.lawyerCertifications"
            @approve="handleApproveLawyer"
            @reject="handleRejectLawyer"
            @refresh="fetchLawyerCertifications"
          />
        </el-tab-pane>

        <!-- 用户活跃度管理 -->
        <el-tab-pane label="用户活跃度管理" name="userActivity">
          <UserActivityTable 
            :data="userManagementStore.userActivities"
            :loading="userManagementStore.loading.userActivities"
            @update-status="handleUpdateUserStatus"
            @view-behavior="handleViewUserBehavior"
            @refresh="fetchUserActivities"
          />
        </el-tab-pane>

        <!-- 用户行为轨迹 -->
        <el-tab-pane label="用户行为轨迹" name="behaviorTrace">
          <UserBehaviorTraceTable 
            :data="userManagementStore.userBehaviorTraces"
            :loading="userManagementStore.loading.userBehaviorTraces"
            @refresh="fetchUserBehaviorTraces"
          />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  User, 
  UserFilled, 
  Connection, 
  Medal, 
  Refresh 
} from '@element-plus/icons-vue'
import { useUserManagementStore } from '@/stores/userManagement'
import StatCard from '@/components/common/StatCard.vue'
import UserRegistrationChart from './components/UserRegistrationChart.vue'
import UserActivityChart from './components/UserActivityChart.vue'
import LawyerCertificationChart from './components/LawyerCertificationChart.vue'
import UserBehaviorChart from './components/UserBehaviorChart.vue'
import LawyerCertificationTable from './components/LawyerCertificationTable.vue'
import UserActivityTable from './components/UserActivityTable.vue'
import UserBehaviorTraceTable from './components/UserBehaviorTraceTable.vue'

const userManagementStore = useUserManagementStore()
const selectedPeriod = ref('30d')
const activeTab = ref('lawyerCertification')

// 处理时间周期变化
const handlePeriodChange = async (period: string) => {
  await Promise.all([
    userManagementStore.fetchAnalytics(period),
    userManagementStore.fetchRegistrationTrend(period)
  ])
}

// 刷新数据
const refreshData = async () => {
  try {
    await userManagementStore.initUserManagement()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  }
}

// 律师认证操作
const handleApproveLawyer = async (lawyerId: string, note?: string) => {
  try {
    await userManagementStore.approveLawyerCertification(lawyerId, note)
    ElMessage.success('律师认证已通过')
    await fetchLawyerCertifications()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleRejectLawyer = async (lawyerId: string, reason: string) => {
  try {
    await userManagementStore.rejectLawyerCertification(lawyerId, reason)
    ElMessage.success('律师认证已拒绝')
    await fetchLawyerCertifications()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 用户状态管理
const handleUpdateUserStatus = async (userId: string, status: 'active' | 'inactive') => {
  try {
    await userManagementStore.updateUserStatus(userId, status)
    ElMessage.success('用户状态更新成功')
    await fetchUserActivities()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 查看用户行为
const handleViewUserBehavior = async (userId: string) => {
  activeTab.value = 'behaviorTrace'
  await userManagementStore.fetchUserBehaviorTraces(userId)
}

// 获取数据的便捷方法
const fetchLawyerCertifications = () => userManagementStore.fetchLawyerCertifications()
const fetchUserActivities = () => userManagementStore.fetchUserActivities()
const fetchUserBehaviorTraces = () => userManagementStore.fetchUserBehaviorTraces()

onMounted(async () => {
  await userManagementStore.initUserManagement()
})
</script>

<style lang="scss" scoped>
.user-management-view {
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
      .chart-container {
        height: 300px;
        padding: 10px 0;
      }
    }
  }
  
  .tables-section {
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
  .user-management-view {
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