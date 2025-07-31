<template>
  <workspace-layout :breadcrumb-items="breadcrumbItems">
    <div class="dashboard-container">
      <!-- 欢迎区域 -->
      <div class="dashboard-welcome">
        <div class="welcome-content">
          <div class="welcome-text">
            <h1>欢迎回来，{{ userStore.userName }}！</h1>
            <p>{{ welcomeMessage }}</p>
          </div>
          <div class="welcome-actions">
            <lk-button
              v-if="userStore.userRole === 'user'"
              type="primary"
              size="large"
              @click="$router.push('/cases/create')"
            >
              <el-icon><Plus /></el-icon>
              发布新案件
            </lk-button>
            <lk-button
              v-else-if="userStore.userRole === 'lawyer'"
              type="primary"
              size="large"
              @click="$router.push('/cases')"
            >
              <el-icon><Search /></el-icon>
              查找案件
            </lk-button>
          </div>
        </div>
        <div class="welcome-avatar">
          <el-avatar :size="80" :src="userStore.userAvatar">
            {{ userStore.userName.charAt(0) }}
          </el-avatar>
        </div>
      </div>

      <!-- 数据统计卡片 -->
      <div class="dashboard-stats">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="总案件数"
              :value="stats.totalCases"
              :trend="stats.caseTrend"
              :icon="Document"
              color="primary"
              :loading="statsLoading"
            >
              <template #footer>
                <el-link type="primary" @click="$router.push('/cases')">
                  查看详情
                </el-link>
              </template>
            </data-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="待处理"
              :value="stats.pendingCases"
              :trend="stats.pendingTrend"
              :icon="Clock"
              color="warning"
              :loading="statsLoading"
            />
          </el-col>
          
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="进行中"
              :value="stats.activeCases"
              :trend="stats.activeTrend"
              :icon="Loading"
              color="info"
              :loading="statsLoading"
            />
          </el-col>
          
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="已完成"
              :value="stats.completedCases"
              :trend="stats.completedTrend"
              :icon="Check"
              color="success"
              :loading="statsLoading"
            />
          </el-col>
        </el-row>
      </div>

      <!-- 主要内容区域 -->
      <el-row :gutter="24" class="dashboard-main">
        <el-col :xs="24" :lg="16">
          <!-- 案件趋势图表 -->
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>案件趋势</span>
                <el-radio-group v-model="chartPeriod" size="small">
                  <el-radio-button label="week">本周</el-radio-button>
                  <el-radio-button label="month">本月</el-radio-button>
                  <el-radio-button label="quarter">本季度</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            
            <lk-chart
              :option="chartOption"
              height="300px"
              :loading="chartLoading"
              @chart-ready="handleChartReady"
            />
          </el-card>

          <!-- 最近案件列表 -->
          <el-card class="recent-cases" style="margin-top: 24px;">
            <template #header>
              <div class="card-header">
                <span>最近案件</span>
                <el-button type="primary" text @click="$router.push('/cases')">
                  查看全部
                </el-button>
              </div>
            </template>
            
            <case-list
              :cases="recentCases"
              :loading="casesLoading"
              :show-filters="false"
              :show-pagination="false"
              @case-click="handleCaseClick"
              @view-case="handleViewCase"
            />
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="8">
          <!-- 快捷操作 -->
          <el-card class="quick-actions">
            <template #header>
              <span>快捷操作</span>
            </template>
            
            <div class="action-grid">
              <div
                v-for="action in quickActions"
                :key="action.key"
                class="action-item"
                @click="handleQuickAction(action)"
              >
                <div class="action-icon">
                  <el-icon>
                    <component :is="action.icon" />
                  </el-icon>
                </div>
                <div class="action-text">
                  <div class="action-title">{{ action.title }}</div>
                  <div class="action-desc">{{ action.description }}</div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 待办事项 -->
          <el-card class="todo-list" style="margin-top: 24px;">
            <template #header>
              <div class="card-header">
                <span>待办事项</span>
                <el-badge :value="todoCount" :hidden="todoCount === 0" />
              </div>
            </template>
            
            <div v-if="todos.length === 0" class="empty-state">
              <el-empty description="暂无待办事项" />
            </div>
            
            <div v-else class="todo-items">
              <div
                v-for="todo in todos"
                :key="todo.id"
                class="todo-item"
                :class="{ completed: todo.completed }"
                @click="handleTodoClick(todo)"
              >
                <el-checkbox
                  v-model="todo.completed"
                  @change="handleTodoToggle(todo)"
                  @click.stop
                />
                <div class="todo-content">
                  <div class="todo-title">{{ todo.title }}</div>
                  <div class="todo-time">{{ formatRelativeTime(todo.due_date) }}</div>
                </div>
                <div class="todo-priority" :class="`priority-${todo.priority}`" />
              </div>
            </div>
          </el-card>

          <!-- 系统通知 -->
          <el-card class="notifications" style="margin-top: 24px;">
            <template #header>
              <div class="card-header">
                <span>系统通知</span>
                <el-badge :value="unreadNotificationCount" :hidden="unreadNotificationCount === 0" />
              </div>
            </template>
            
            <div v-if="notifications.length === 0" class="empty-state">
              <el-empty description="暂无通知" />
            </div>
            
            <div v-else class="notification-list">
              <div
                v-for="notification in notifications.slice(0, 5)"
                :key="notification.id"
                class="notification-item"
                :class="{ unread: !notification.read }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-avatar">
                  <el-avatar :size="32" :src="notification.avatar">
                    <el-icon><Bell /></el-icon>
                  </el-avatar>
                </div>
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-time">{{ formatRelativeTime(notification.created_at) }}</div>
                </div>
                <el-badge v-if="!notification.read" is-dot />
              </div>
              
              <div class="notification-footer" v-if="notifications.length > 5">
                <el-button type="primary" text @click="$router.push('/notifications')">
                  查看全部通知
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </workspace-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  ElRow,
  ElCol,
  ElCard,
  ElButton,
  ElIcon,
  ElAvatar,
  ElLink,
  ElRadioGroup,
  ElRadioButton,
  ElBadge,
  ElCheckbox,
  ElEmpty
} from 'element-plus'
import {
  Document,
  Clock,
  Loading,
  Check,
  Plus,
  Search,
  Bell,
  User,
  Briefcase,
  OfficeBuilding,
  Setting,
  ChatDotRound,
  Files
} from '@element-plus/icons-vue'
import WorkspaceLayout from '@/components/layout/WorkspaceLayout/index.vue'
import DataCard from '@/components/common/DataCard/index.vue'
import LkChart from '@/components/common/Chart/index.vue'
import { CaseList, LkButton } from '@/components'
import { formatRelativeTime } from '@/utils/format'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()

// 面包屑导航
const breadcrumbItems = [
  { title: '工作台', path: '/dashboard' }
]

// 响应式数据
const statsLoading = ref(false)
const chartLoading = ref(false)
const casesLoading = ref(false)
const chartPeriod = ref('month')

const stats = ref({
  totalCases: 0,
  pendingCases: 0,
  activeCases: 0,
  completedCases: 0,
  caseTrend: 0,
  pendingTrend: 0,
  activeTrend: 0,
  completedTrend: 0
})

const recentCases = ref([])
const notifications = ref([])
const todos = ref([])

// 计算属性
const welcomeMessage = computed(() => {
  const hour = dayjs().hour()
  let greeting = '早上好'
  
  if (hour >= 12 && hour < 18) {
    greeting = '下午好'
  } else if (hour >= 18) {
    greeting = '晚上好'
  }
  
  const today = dayjs().format('YYYY年MM月DD日')
  return `${greeting}！今天是${today}，祝您工作愉快`
})

const quickActions = computed(() => {
  const baseActions = [
    {
      key: 'profile',
      title: '个人中心',
      description: '查看和编辑个人信息',
      icon: User,
      path: '/profile'
    },
    {
      key: 'messages',
      title: '消息中心',
      description: '查看最新消息',
      icon: ChatDotRound,
      path: '/messages'
    },
    {
      key: 'documents',
      title: '文档中心',
      description: '管理相关文档',
      icon: Files,
      path: '/documents'
    },
    {
      key: 'settings',
      title: '系统设置',
      description: '个性化设置',
      icon: Setting,
      path: '/settings'
    }
  ]
  
  // 根据用户角色添加特定操作
  if (userStore.userRole === 'user') {
    baseActions.unshift({
      key: 'create-case',
      title: '发布案件',
      description: '发布新的法律服务需求',
      icon: Plus,
      path: '/cases/create'
    })
  } else if (userStore.userRole === 'lawyer') {
    baseActions.unshift({
      key: 'find-cases',
      title: '查找案件',
      description: '寻找合适的案件',
      icon: Search,
      path: '/cases'
    })
    baseActions.splice(1, 0, {
      key: 'lawyer-workspace',
      title: '律师工作台',
      description: '专业律师功能',
      icon: Briefcase,
      path: '/lawyer'
    })
  } else if (userStore.userRole === 'institution') {
    baseActions.unshift({
      key: 'institution-workspace',
      title: '机构工作台',
      description: '机构管理功能',
      icon: OfficeBuilding,
      path: '/institution'
    })
  }
  
  return baseActions
})

const todoCount = computed(() => {
  return todos.value.filter(todo => !todo.completed).length
})

const unreadNotificationCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

const chartOption = computed(() => {
  return {
    title: {
      text: '案件处理趋势',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['新增案件', '完成案件'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '新增案件',
        type: 'line',
        data: [12, 19, 15, 25, 22, 30, 28],
        smooth: true,
        itemStyle: {
          color: '#409eff'
        }
      },
      {
        name: '完成案件',
        type: 'line',
        data: [8, 15, 12, 20, 18, 25, 24],
        smooth: true,
        itemStyle: {
          color: '#67c23a'
        }
      }
    ]
  }
})

// 方法
const loadDashboardData = async () => {
  statsLoading.value = true
  casesLoading.value = true
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    stats.value = {
      totalCases: 156,
      pendingCases: 23,
      activeCases: 45,
      completedCases: 88,
      caseTrend: 12.5,
      pendingTrend: -5.2,
      activeTrend: 8.3,
      completedTrend: 15.7
    }
    
    recentCases.value = [
      {
        id: '1',
        title: '合同纠纷咨询',
        description: '关于房屋租赁合同的法律问题咨询',
        status: 'in_progress',
        type: 'civil',
        amount: 500,
        createdAt: '2024-01-15T10:30:00Z',
        client: {
          id: '1',
          name: '张先生',
          avatar: ''
        },
        lawyer: {
          id: '2',
          name: '李律师',
          avatar: ''
        }
      },
      {
        id: '2',
        title: '劳动争议处理',
        description: '员工与公司之间的劳动合同纠纷',
        status: 'pending',
        type: 'labor',
        amount: 800,
        createdAt: '2024-01-14T15:20:00Z',
        client: {
          id: '3',
          name: '王女士',
          avatar: ''
        }
      }
    ]
    
    notifications.value = [
      {
        id: '1',
        title: '新案件分配',
        message: '您有一个新的合同审查案件',
        read: false,
        avatar: '',
        created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString()
      },
      {
        id: '2',
        title: '系统更新通知',
        message: '系统将于今晚进行维护更新',
        read: true,
        avatar: '',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
      }
    ]
    
    todos.value = [
      {
        id: '1',
        title: '完成案件报告',
        completed: false,
        priority: 'high',
        due_date: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString()
      },
      {
        id: '2',
        title: '回复客户咨询',
        completed: false,
        priority: 'medium',
        due_date: new Date(Date.now() + 1000 * 60 * 60 * 4).toISOString()
      }
    ]
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    statsLoading.value = false
    casesLoading.value = false
  }
}

const loadChartData = async () => {
  chartLoading.value = true
  try {
    // 模拟图表数据加载
    await new Promise(resolve => setTimeout(resolve, 800))
  } catch (error) {
    console.error('Failed to load chart data:', error)
  } finally {
    chartLoading.value = false
  }
}

const handleChartReady = (chart: any) => {
  console.log('Chart ready:', chart)
}

const handleCaseClick = (caseItem: any) => {
  router.push(`/cases/${caseItem.id}`)
}

const handleViewCase = (caseItem: any) => {
  router.push(`/cases/${caseItem.id}`)
}

const handleQuickAction = (action: any) => {
  if (action.path) {
    router.push(action.path)
  }
}

const handleTodoClick = (todo: any) => {
  // 处理待办事项点击
}

const handleTodoToggle = (todo: any) => {
  // 处理待办事项状态切换
}

const handleNotificationClick = (notification: any) => {
  if (!notification.read) {
    notification.read = true
  }
  // 处理通知点击
}

// 监听图表周期变化
watch(chartPeriod, () => {
  loadChartData()
})

onMounted(() => {
  loadDashboardData()
  loadChartData()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}

.dashboard-welcome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 32px;
  
  .welcome-content {
    flex: 1;
    
    .welcome-text {
      h1 {
        font-size: 32px;
        font-weight: 600;
        margin: 0 0 8px 0;
      }
      
      p {
        font-size: 16px;
        opacity: 0.9;
        margin: 0 0 24px 0;
      }
    }
    
    .welcome-actions {
      .lk-button {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.3);
        color: white;
        
        &:hover {
          background: rgba(255, 255, 255, 0.3);
          border-color: rgba(255, 255, 255, 0.5);
        }
      }
    }
  }
  
  .welcome-avatar {
    flex-shrink: 0;
    margin-left: 24px;
    
    .el-avatar {
      border: 3px solid rgba(255, 255, 255, 0.3);
    }
  }
}

.dashboard-stats {
  margin-bottom: 32px;
}

.dashboard-main {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    span {
      font-size: 16px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }
  
  .chart-card {
    .el-card__body {
      padding: 20px;
    }
  }
  
  .recent-cases {
    .el-card__body {
      padding: 0;
    }
  }
  
  .quick-actions {
    .action-grid {
      display: grid;
      gap: 16px;
      
      .action-item {
        display: flex;
        align-items: center;
        padding: 16px;
        border: 1px solid var(--el-border-color-light);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          border-color: var(--el-color-primary);
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
          transform: translateY(-2px);
        }
        
        .action-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: var(--el-color-primary-light-9);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          flex-shrink: 0;
          
          .el-icon {
            font-size: 20px;
            color: var(--el-color-primary);
          }
        }
        
        .action-text {
          flex: 1;
          min-width: 0;
          
          .action-title {
            font-size: 14px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }
          
          .action-desc {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            line-height: 1.4;
          }
        }
      }
    }
  }
  
  .todo-list {
    .todo-items {
      .todo-item {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid var(--el-border-color-lighter);
        cursor: pointer;
        transition: background-color 0.3s;
        
        &:hover {
          background-color: var(--el-bg-color-page);
        }
        
        &:last-child {
          border-bottom: none;
        }
        
        &.completed {
          opacity: 0.6;
          
          .todo-title {
            text-decoration: line-through;
          }
        }
        
        .el-checkbox {
          margin-right: 12px;
        }
        
        .todo-content {
          flex: 1;
          min-width: 0;
          
          .todo-title {
            font-size: 14px;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }
          
          .todo-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
        
        .todo-priority {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-left: 8px;
          
          &.priority-high {
            background-color: var(--el-color-danger);
          }
          
          &.priority-medium {
            background-color: var(--el-color-warning);
          }
          
          &.priority-low {
            background-color: var(--el-color-success);
          }
        }
      }
    }
  }
  
  .notifications {
    .notification-list {
      .notification-item {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid var(--el-border-color-lighter);
        cursor: pointer;
        transition: background-color 0.3s;
        
        &:hover {
          background-color: var(--el-bg-color-page);
        }
        
        &:last-child {
          border-bottom: none;
        }
        
        &.unread {
          background-color: var(--el-color-primary-light-9);
          border-left: 3px solid var(--el-color-primary);
          margin-left: -16px;
          padding-left: 13px;
        }
        
        .notification-avatar {
          margin-right: 12px;
          flex-shrink: 0;
        }
        
        .notification-content {
          flex: 1;
          min-width: 0;
          
          .notification-title {
            font-size: 14px;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          
          .notification-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
      
      .notification-footer {
        padding: 16px 0 0 0;
        text-align: center;
        border-top: 1px solid var(--el-border-color-lighter);
        margin-top: 16px;
      }
    }
  }
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

// 响应式设计
@media (max-width: 1200px) {
  .dashboard-main {
    .action-grid {
      grid-template-columns: 1fr;
    }
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .dashboard-welcome {
    flex-direction: column;
    text-align: center;
    padding: 24px;
    
    .welcome-avatar {
      margin-left: 0;
      margin-top: 16px;
    }
  }
  
  .dashboard-stats {
    margin-bottom: 24px;
  }
  
  .dashboard-main {
    .el-col {
      margin-bottom: 24px;
    }
  }
}
</style>