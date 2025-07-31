<template>
  <div class="user-activity-table">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="statusFilter" @change="handleStatusFilter" placeholder="筛选状态" clearable>
        <el-option label="全部" value="" />
        <el-option label="活跃" value="active" />
        <el-option label="不活跃" value="inactive" />
        <el-option label="休眠" value="dormant" />
      </el-select>
      
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名或邮箱"
        :prefix-icon="Search"
        @input="handleSearch"
        style="width: 300px;"
        clearable
      />
      
      <el-button :icon="Refresh" @click="$emit('refresh')">
        刷新
      </el-button>
    </div>

    <!-- 表格 -->
    <el-table
      :data="filteredData"
      v-loading="loading"
      stripe
      style="width: 100%"
      :height="500"
    >
      <el-table-column
        prop="username"
        label="用户名"
        width="120"
        fixed="left"
      >
        <template #default="{ row }">
          <div class="user-info">
            <span class="username">{{ row.username }}</span>
            <span class="email">{{ row.email }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="status"
        label="状态"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="last_login"
        label="最后登录"
        width="160"
        sortable
      >
        <template #default="{ row }">
          <span class="time-cell">{{ formatTime(row.last_login) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="login_count"
        label="登录次数"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.login_count.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="session_duration"
        label="会话时长"
        width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="duration-cell">{{ formatDuration(row.session_duration) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="page_views"
        label="页面浏览"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.page_views.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="actions_count"
        label="操作次数"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.actions_count.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="activity_score"
        label="活跃度评分"
        width="120"
        align="center"
        sortable
      >
        <template #default="{ row }">
          <div class="score-cell">
            <el-progress
              :percentage="row.activity_score"
              :color="getScoreColor(row.activity_score)"
              :show-text="false"
              :stroke-width="8"
            />
            <span class="score-text">{{ row.activity_score }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        label="操作"
        width="200"
        align="center"
        fixed="right"
      >
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              size="small"
              type="primary"
              @click="$emit('view-behavior', row.user_id)"
            >
              查看行为
            </el-button>
            <el-button
              v-if="row.status === 'active'"
              size="small"
              type="warning"
              @click="handleUpdateStatus(row, 'inactive')"
            >
              设为不活跃
            </el-button>
            <el-button
              v-else
              size="small"
              type="success"
              @click="handleUpdateStatus(row, 'active')"
            >
              激活用户
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="!loading && (!data || data.length === 0)" class="empty-state">
      <el-empty description="暂无数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { UserActivityData } from '@/types'

interface Props {
  data: UserActivityData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'update-status': [userId: string, status: 'active' | 'inactive']
  'view-behavior': [userId: string]
  refresh: []
}>()

const statusFilter = ref('')
const searchKeyword = ref('')

// 过滤数据
const filteredData = computed(() => {
  let result = props.data

  // 状态筛选
  if (statusFilter.value) {
    result = result.filter(item => item.status === statusFilter.value)
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.username.toLowerCase().includes(keyword) ||
      item.email.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 格式化时间
const formatTime = (timeStr: string) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
}

// 格式化时长
const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}分钟`
  } else {
    return `${Math.round(seconds / 3600)}小时`
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const typeMap = {
    active: 'success',
    inactive: 'warning',
    dormant: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap = {
    active: '活跃',
    inactive: '不活跃',
    dormant: '休眠'
  }
  return textMap[status as keyof typeof textMap] || status
}

// 获取评分颜色
const getScoreColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 40) return '#e6a23c'
  return '#f56c6c'
}

// 处理状态筛选
const handleStatusFilter = () => {
  // 筛选逻辑已在computed中处理
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

// 更新用户状态
const handleUpdateStatus = async (row: UserActivityData, newStatus: 'active' | 'inactive') => {
  try {
    const action = newStatus === 'active' ? '激活' : '设为不活跃'
    await ElMessageBox.confirm(
      `确定要${action}用户 ${row.username} 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    emit('update-status', row.user_id, newStatus)
  } catch {
    // 用户取消操作
  }
}
</script>

<style lang="scss" scoped>
.user-activity-table {
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: center;
  }
  
  .user-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .username {
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    .email {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
  
  .time-cell {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .number-cell {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .duration-cell {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .score-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    
    .score-text {
      font-size: 12px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .empty-state {
    padding: 40px 0;
  }
  
  :deep(.el-table) {
    .el-table__row {
      &:hover {
        background-color: var(--el-table-row-hover-bg-color);
      }
    }
    
    .el-table__header {
      th {
        background-color: var(--el-bg-color-page);
        color: var(--el-text-color-primary);
        font-weight: 600;
      }
    }
  }
}
</style>