<template>
  <div class="security-dashboard">
    <el-card class="overview-card">
      <template #header>
        <div class="card-header">
          <span>安全概览</span>
          <div class="header-controls">
            <el-select v-model="timeRange" @change="handleTimeRangeChange">
              <el-option label="最近1小时" value="1h" />
              <el-option label="最近24小时" value="24h" />
              <el-option label="最近7天" value="7d" />
              <el-option label="最近30天" value="30d" />
            </el-select>
            <el-button :icon="Refresh" @click="refreshData" :loading="loading">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 安全指标卡片 -->
      <div class="metrics-grid">
        <StatCard
          title="安全事件总数"
          :value="securityStats.totalEvents"
          :trend="securityStats.eventsTrend"
          icon="Shield"
          color="#409EFF"
        />
        <StatCard
          title="高危事件"
          :value="securityStats.criticalEvents"
          :trend="securityStats.criticalTrend"
          icon="Warning"
          color="#F56C6C"
        />
        <StatCard
          title="登录失败次数"
          :value="securityStats.loginFailures"
          :trend="securityStats.loginFailuresTrend"
          icon="Lock"
          color="#E6A23C"
        />
        <StatCard
          title="被阻止的IP"
          :value="securityStats.blockedIPs"
          :trend="securityStats.blockedIPsTrend"
          icon="CircleClose"
          color="#909399"
        />
      </div>
    </el-card>

    <div class="dashboard-content">
      <div class="left-panel">
        <!-- 安全事件趋势图 -->
        <el-card class="chart-card">
          <template #header>
            <span>安全事件趋势</span>
          </template>
          <LineChart
            :data="eventTrendData"
            :x-axis-data="eventTrendXAxis"
            title=""
            :height="'300px'"
            :smooth="true"
            y-axis-name="事件数量"
            x-axis-name="时间"
          />
        </el-card>

        <!-- 事件类型分布 -->
        <el-card class="chart-card">
          <template #header>
            <span>事件类型分布</span>
          </template>
          <PieChart
            :data="eventTypeData"
            title=""
            :height="'300px'"
            :show-legend="true"
          />
        </el-card>
      </div>

      <div class="right-panel">
        <!-- 实时告警 -->
        <el-card class="alerts-card">
          <template #header>
            <div class="card-header">
              <span>实时告警</span>
              <el-badge :value="unreadAlerts" class="alert-badge">
                <el-icon><Bell /></el-icon>
              </el-badge>
            </div>
          </template>
          
          <div class="alerts-list">
            <div
              v-for="alert in recentAlerts"
              :key="alert.id"
              :class="['alert-item', `alert-${alert.level}`]"
            >
              <div class="alert-icon">
                <el-icon>
                  <Warning v-if="alert.level === 'critical'" />
                  <InfoFilled v-else-if="alert.level === 'high'" />
                  <QuestionFilled v-else />
                </el-icon>
              </div>
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-description">{{ alert.description }}</div>
                <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
              </div>
              <div class="alert-actions">
                <el-button size="small" @click="handleAlert(alert)">
                  处理
                </el-button>
              </div>
            </div>
          </div>
        </el-card>

        <!-- Top威胁IP -->
        <el-card class="threats-card">
          <template #header>
            <span>威胁IP排行</span>
          </template>
          
          <div class="threats-list">
            <div
              v-for="(threat, index) in topThreats"
              :key="threat.ip"
              class="threat-item"
            >
              <div class="threat-rank">{{ index + 1 }}</div>
              <div class="threat-info">
                <div class="threat-ip">{{ threat.ip }}</div>
                <div class="threat-location">{{ threat.location }}</div>
              </div>
              <div class="threat-stats">
                <div class="threat-count">{{ threat.eventCount }} 次</div>
                <div class="threat-level">{{ threat.riskLevel }}</div>
              </div>
              <div class="threat-actions">
                <el-button
                  size="small"
                  type="danger"
                  @click="blockIP(threat.ip)"
                >
                  封禁
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 安全事件详情表格 -->
    <el-card class="events-table-card">
      <template #header>
        <div class="card-header">
          <span>安全事件记录</span>
          <div class="header-controls">
            <el-input
              v-model="searchQuery"
              placeholder="搜索事件..."
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
              class="search-input"
            />
            <el-select v-model="eventTypeFilter" placeholder="事件类型" clearable>
              <el-option
                v-for="type in eventTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
            <el-select v-model="levelFilter" placeholder="事件级别" clearable>
              <el-option label="严重" value="critical" />
              <el-option label="高危" value="high" />
              <el-option label="中等" value="medium" />
              <el-option label="低危" value="low" />
            </el-select>
          </div>
        </div>
      </template>

      <EnhancedVirtualTable
        :data="securityEvents"
        :columns="eventColumns"
        :loading="eventsLoading"
        :container-height="400"
        :show-pagination="true"
        :page-size="50"
        @row-click="handleEventClick"
        @refresh="loadSecurityEvents"
      >
        <template #level="{ row }">
          <el-tag :type="getLevelType(row.level)">
            {{ getLevelText(row.level) }}
          </el-tag>
        </template>
        
        <template #event_type="{ row }">
          <el-tag type="info">
            {{ getEventTypeText(row.event_type) }}
          </el-tag>
        </template>
        
        <template #timestamp="{ row }">
          {{ formatDateTime(row.timestamp) }}
        </template>
        
        <template #actions="{ row }">
          <el-button size="small" @click="viewEventDetails(row)">
            详情
          </el-button>
          <el-button
            v-if="row.level === 'critical' || row.level === 'high'"
            size="small"
            type="primary"
            @click="handleSecurityEvent(row)"
          >
            处理
          </el-button>
        </template>
      </EnhancedVirtualTable>
    </el-card>

    <!-- 事件详情弹窗 -->
    <el-dialog
      v-model="eventDetailVisible"
      title="安全事件详情"
      width="60%"
      :close-on-click-modal="false"
    >
      <div v-if="selectedEvent" class="event-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="事件ID">
            {{ selectedEvent.id }}
          </el-descriptions-item>
          <el-descriptions-item label="事件类型">
            <el-tag type="info">{{ getEventTypeText(selectedEvent.event_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="事件级别">
            <el-tag :type="getLevelType(selectedEvent.level)">
              {{ getLevelText(selectedEvent.level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发生时间">
            {{ formatDateTime(selectedEvent.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户ID">
            {{ selectedEvent.user_id || '匿名' }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ selectedEvent.ip_address }}
          </el-descriptions-item>
          <el-descriptions-item label="请求路径">
            {{ selectedEvent.endpoint }}
          </el-descriptions-item>
          <el-descriptions-item label="请求方法">
            {{ selectedEvent.method }}
          </el-descriptions-item>
          <el-descriptions-item label="用户代理" span="2">
            {{ selectedEvent.user_agent }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedEvent.details" class="event-details-section">
          <h4>详细信息</h4>
          <el-input
            v-model="eventDetailsJson"
            type="textarea"
            :rows="6"
            readonly
          />
        </div>
      </div>
      
      <template #footer>
        <el-button @click="eventDetailVisible = false">关闭</el-button>
        <el-button
          v-if="selectedEvent && (selectedEvent.level === 'critical' || selectedEvent.level === 'high')"
          type="primary"
          @click="handleSecurityEvent(selectedEvent)"
        >
          处理事件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Search, Shield, Warning, Lock, CircleClose,
  Bell, InfoFilled, QuestionFilled
} from '@element-plus/icons-vue'
import StatCard from '@/components/common/StatCard.vue'
import LineChart from '@/components/charts/LineChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import EnhancedVirtualTable from '@/components/common/EnhancedVirtualTable.vue'
import { request } from '@/utils/request'

// 响应式数据
const loading = ref(false)
const eventsLoading = ref(false)
const timeRange = ref('24h')
const searchQuery = ref('')
const eventTypeFilter = ref('')
const levelFilter = ref('')
const eventDetailVisible = ref(false)
const selectedEvent = ref(null)
const unreadAlerts = ref(0)

// WebSocket连接
let wsConnection: WebSocket | null = null

// 安全统计数据
const securityStats = reactive({
  totalEvents: 0,
  eventsTrend: 0,
  criticalEvents: 0,
  criticalTrend: 0,
  loginFailures: 0,
  loginFailuresTrend: 0,
  blockedIPs: 0,
  blockedIPsTrend: 0
})

// 图表数据
const eventTrendData = ref([
  {
    name: '安全事件',
    data: [],
    color: '#409EFF'
  }
])
const eventTrendXAxis = ref([])

const eventTypeData = ref([])

// 实时告警数据
const recentAlerts = ref([])

// 威胁IP数据
const topThreats = ref([])

// 安全事件数据
const securityEvents = ref([])

// 事件类型选项
const eventTypes = [
  { label: '登录失败', value: 'login_failed' },
  { label: '权限拒绝', value: 'permission_denied' },
  { label: '可疑活动', value: 'suspicious_activity' },
  { label: '限流触发', value: 'rate_limit_exceeded' },
  { label: 'CSRF攻击', value: 'csrf_attack' },
  { label: '未授权访问', value: 'unauthorized_access' }
]

// 表格列配置
const eventColumns = [
  { key: 'timestamp', title: '时间', width: '180px', sortable: true },
  { key: 'event_type', title: '事件类型', width: '120px', sortable: true },
  { key: 'level', title: '级别', width: '80px', sortable: true },
  { key: 'user_id', title: '用户ID', width: '120px' },
  { key: 'ip_address', title: 'IP地址', width: '140px' },
  { key: 'endpoint', title: '请求路径', width: '200px' },
  { key: 'actions', title: '操作', width: '150px' }
]

// 计算属性
const eventDetailsJson = computed(() => {
  if (selectedEvent.value?.details) {
    return JSON.stringify(selectedEvent.value.details, null, 2)
  }
  return ''
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadSecurityStats(),
      loadEventTrend(),
      loadEventTypeDistribution(),
      loadRecentAlerts(),
      loadTopThreats(),
      loadSecurityEvents()
    ])
  } finally {
    loading.value = false
  }
}

const loadSecurityStats = async () => {
  try {
    const response = await request.get('/api/v1/security/stats', {
      params: { time_range: timeRange.value }
    })
    Object.assign(securityStats, response.data)
  } catch (error) {
    console.error('Failed to load security stats:', error)
  }
}

const loadEventTrend = async () => {
  try {
    const response = await request.get('/api/v1/security/events/trend', {
      params: { time_range: timeRange.value }
    })
    
    eventTrendData.value[0].data = response.data.data
    eventTrendXAxis.value = response.data.labels
  } catch (error) {
    console.error('Failed to load event trend:', error)
  }
}

const loadEventTypeDistribution = async () => {
  try {
    const response = await request.get('/api/v1/security/events/distribution', {
      params: { time_range: timeRange.value }
    })
    eventTypeData.value = response.data
  } catch (error) {
    console.error('Failed to load event type distribution:', error)
  }
}

const loadRecentAlerts = async () => {
  try {
    const response = await request.get('/api/v1/security/alerts/recent')
    recentAlerts.value = response.data
    unreadAlerts.value = response.data.filter(alert => !alert.read).length
  } catch (error) {
    console.error('Failed to load recent alerts:', error)
  }
}

const loadTopThreats = async () => {
  try {
    const response = await request.get('/api/v1/security/threats/top', {
      params: { time_range: timeRange.value }
    })
    topThreats.value = response.data
  } catch (error) {
    console.error('Failed to load top threats:', error)
  }
}

const loadSecurityEvents = async () => {
  eventsLoading.value = true
  try {
    const response = await request.get('/api/v1/security/events', {
      params: {
        time_range: timeRange.value,
        search: searchQuery.value,
        event_type: eventTypeFilter.value,
        level: levelFilter.value,
        limit: 1000
      }
    })
    securityEvents.value = response.data
  } catch (error) {
    console.error('Failed to load security events:', error)
  } finally {
    eventsLoading.value = false
  }
}

const handleTimeRangeChange = () => {
  refreshData()
}

const handleSearch = () => {
  loadSecurityEvents()
}

const handleEventClick = (event) => {
  viewEventDetails(event)
}

const viewEventDetails = (event) => {
  selectedEvent.value = event
  eventDetailVisible.value = true
}

const handleAlert = async (alert) => {
  try {
    await ElMessageBox.confirm(
      `确定要处理这个告警吗？`,
      '处理告警',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await request.post(`/api/v1/security/alerts/${alert.id}/handle`)
    ElMessage.success('告警处理成功')
    loadRecentAlerts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('告警处理失败')
    }
  }
}

const handleSecurityEvent = async (event) => {
  try {
    await ElMessageBox.confirm(
      `确定要处理这个安全事件吗？`,
      '处理安全事件',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await request.post(`/api/v1/security/events/${event.id}/handle`)
    ElMessage.success('安全事件处理成功')
    eventDetailVisible.value = false
    loadSecurityEvents()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('安全事件处理失败')
    }
  }
}

const blockIP = async (ip) => {
  try {
    await ElMessageBox.confirm(
      `确定要封禁IP地址 ${ip} 吗？`,
      '封禁IP',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await request.post('/api/v1/security/ip/block', { ip })
    ElMessage.success('IP封禁成功')
    loadTopThreats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('IP封禁失败')
    }
  }
}

// 工具函数
const getLevelType = (level) => {
  const typeMap = {
    critical: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'success'
  }
  return typeMap[level] || 'info'
}

const getLevelText = (level) => {
  const textMap = {
    critical: '严重',
    high: '高危',
    medium: '中等',
    low: '低危'
  }
  return textMap[level] || level
}

const getEventTypeText = (type) => {
  const typeMap = {
    login_failed: '登录失败',
    permission_denied: '权限拒绝',
    suspicious_activity: '可疑活动',
    rate_limit_exceeded: '限流触发',
    csrf_attack: 'CSRF攻击',
    unauthorized_access: '未授权访问'
  }
  return typeMap[type] || type
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const formatDateTime = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}

// WebSocket连接
const connectWebSocket = () => {
  const wsUrl = `ws://localhost:8000/api/v1/security/ws`
  wsConnection = new WebSocket(wsUrl)
  
  wsConnection.onopen = () => {
    console.log('Security WebSocket connected')
  }
  
  wsConnection.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'security_alert') {
      recentAlerts.value.unshift(data.alert)
      unreadAlerts.value++
      ElMessage.warning(`新的安全告警: ${data.alert.title}`)
    } else if (data.type === 'security_event') {
      securityEvents.value.unshift(data.event)
      // 更新统计数据
      securityStats.totalEvents++
    }
  }
  
  wsConnection.onclose = () => {
    console.log('Security WebSocket disconnected')
    // 重连
    setTimeout(connectWebSocket, 5000)
  }
  
  wsConnection.onerror = (error) => {
    console.error('Security WebSocket error:', error)
  }
}

// 生命周期
onMounted(() => {
  refreshData()
  connectWebSocket()
})

onUnmounted(() => {
  if (wsConnection) {
    wsConnection.close()
  }
})
</script>

<style scoped>
.security-dashboard {
  padding: 20px;
}

.overview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 200px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-card {
  height: fit-content;
}

.alerts-card,
.threats-card {
  height: fit-content;
}

.alert-badge {
  cursor: pointer;
}

.alerts-list,
.threats-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 8px;
  border-left: 4px solid;
}

.alert-critical {
  background-color: #fef0f0;
  border-left-color: #f56c6c;
}

.alert-high {
  background-color: #fdf6ec;
  border-left-color: #e6a23c;
}

.alert-medium {
  background-color: #f4f4f5;
  border-left-color: #909399;
}

.alert-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.alert-description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.alert-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.alert-actions {
  flex-shrink: 0;
}

.threat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.threat-rank {
  font-weight: bold;
  color: var(--el-color-primary);
  width: 20px;
}

.threat-info {
  flex: 1;
}

.threat-ip {
  font-weight: 600;
  margin-bottom: 2px;
}

.threat-location {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.threat-stats {
  text-align: right;
}

.threat-count {
  font-weight: 600;
  margin-bottom: 2px;
}

.threat-level {
  font-size: 12px;
  color: var(--el-color-danger);
}

.threat-actions {
  flex-shrink: 0;
}

.events-table-card {
  margin-top: 20px;
}

.event-detail {
  padding: 20px 0;
}

.event-details-section {
  margin-top: 20px;
}

.event-details-section h4 {
  margin-bottom: 10px;
  color: var(--el-text-color-primary);
}

@media (max-width: 1200px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-controls {
    width: 100%;
    justify-content: center;
  }
}
</style>