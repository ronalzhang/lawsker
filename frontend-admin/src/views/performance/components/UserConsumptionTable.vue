<template>
  <div class="user-consumption-table">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名"
        :prefix-icon="Search"
        @input="handleSearch"
        style="width: 300px;"
        clearable
      />
      
      <el-button :icon="Refresh" @click="$emit('refresh')">
        刷新
      </el-button>
    </div>

    <!-- 消费排行表格 -->
    <el-table
      :data="filteredData"
      v-loading="loading"
      stripe
      style="width: 100%"
      :height="500"
    >
      <el-table-column
        prop="rank"
        label="排名"
        width="80"
        align="center"
        fixed="left"
      >
        <template #default="{ row }">
          <div class="rank-cell">
            <el-icon v-if="row.rank <= 3" class="rank-icon" :class="getRankClass(row.rank)">
              <Medal />
            </el-icon>
            <span v-else class="rank-number">{{ row.rank }}</span>
            
            <div v-if="row.rank_change !== 0" class="rank-change">
              <el-icon :class="row.rank_change > 0 ? 'rank-up' : 'rank-down'">
                <component :is="row.rank_change > 0 ? ArrowUp : ArrowDown" />
              </el-icon>
              <span class="change-number">{{ Math.abs(row.rank_change) }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="username"
        label="用户信息"
        width="200"
        fixed="left"
      >
        <template #default="{ row }">
          <div class="user-info">
            <el-avatar :size="40" :src="row.avatar">
              {{ row.username.charAt(0) }}
            </el-avatar>
            <div class="info-text">
              <span class="username">{{ row.username }}</span>
              <div class="loyalty">
                <el-tag :type="getLoyaltyType(row.loyalty_score)" size="small">
                  {{ getLoyaltyText(row.loyalty_score) }}
                </el-tag>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="total_spent"
        label="总消费"
        width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="amount-cell">¥{{ row.total_spent.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="cases_count"
        label="案件数量"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.cases_count }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="avg_case_value"
        label="平均案件价值"
        width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="amount-cell">¥{{ row.avg_case_value.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="last_payment"
        label="最后支付"
        width="120"
        sortable
      >
        <template #default="{ row }">
          <span class="time-cell">{{ formatTime(row.last_payment) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="loyalty_score"
        label="忠诚度评分"
        width="120"
        align="center"
        sortable
      >
        <template #default="{ row }">
          <div class="loyalty-cell">
            <el-progress
              :percentage="row.loyalty_score"
              :color="getLoyaltyColor(row.loyalty_score)"
              :show-text="false"
              :stroke-width="8"
            />
            <span class="score-text">{{ row.loyalty_score }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        label="消费趋势"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <div class="trend-indicator">
            <el-icon :class="getTrendClass(row)" class="trend-icon">
              <component :is="getTrendIcon(row)" />
            </el-icon>
            <span class="trend-text">{{ getTrendText(row) }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        label="操作"
        width="120"
        align="center"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            size="small"
            type="primary"
            @click="handleViewDetails(row)"
          >
            查看详情
          </el-button>
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
import { Search, Refresh, Medal, ArrowUp, ArrowDown, TrendCharts, Bottom } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

interface UserConsumptionData {
  user_id: string
  username: string
  avatar?: string
  total_spent: number
  cases_count: number
  avg_case_value: number
  last_payment: string
  rank: number
  rank_change: number
  loyalty_score: number
}

interface Props {
  data: UserConsumptionData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  refresh: []
}>()

const searchKeyword = ref('')

// 过滤数据
const filteredData = computed(() => {
  let result = props.data

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.username.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 获取排名样式类
const getRankClass = (rank: number) => {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return ''
}

// 格式化时间
const formatTime = (timeStr: string) => {
  return dayjs(timeStr).format('YYYY-MM-DD')
}

// 获取忠诚度类型
const getLoyaltyType = (score: number) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'primary'
  if (score >= 40) return 'warning'
  return 'danger'
}

// 获取忠诚度文本
const getLoyaltyText = (score: number) => {
  if (score >= 80) return 'VIP客户'
  if (score >= 60) return '忠实客户'
  if (score >= 40) return '普通客户'
  return '新客户'
}

// 获取忠诚度颜色
const getLoyaltyColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 40) return '#e6a23c'
  return '#f56c6c'
}

// 获取趋势样式类
const getTrendClass = (row: UserConsumptionData) => {
  if (row.rank_change > 0) return 'trend-up'
  if (row.rank_change < 0) return 'trend-down'
  return 'trend-stable'
}

// 获取趋势图标
const getTrendIcon = (row: UserConsumptionData) => {
  if (row.rank_change > 0) return TrendCharts
  if (row.rank_change < 0) return Bottom
  return TrendCharts
}

// 获取趋势文本
const getTrendText = (row: UserConsumptionData) => {
  if (row.rank_change > 0) return '上升'
  if (row.rank_change < 0) return '下降'
  return '稳定'
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

// 查看详情
const handleViewDetails = (row: UserConsumptionData) => {
  // 这里可以打开详情对话框或跳转到详情页面
  console.log('View user details:', row)
}
</script>

<style lang="scss" scoped>
.user-consumption-table {
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: center;
  }
  
  .rank-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    
    .rank-icon {
      font-size: 24px;
      
      &.rank-gold {
        color: #ffd700;
      }
      
      &.rank-silver {
        color: #c0c0c0;
      }
      
      &.rank-bronze {
        color: #cd7f32;
      }
    }
    
    .rank-number {
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    .rank-change {
      display: flex;
      align-items: center;
      gap: 2px;
      font-size: 10px;
      
      .rank-up {
        color: #67c23a;
      }
      
      .rank-down {
        color: #f56c6c;
      }
      
      .change-number {
        font-weight: 600;
      }
    }
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .info-text {
      .username {
        display: block;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
    }
  }
  
  .amount-cell {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .number-cell {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .time-cell {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .loyalty-cell {
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
  
  .trend-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    
    .trend-icon {
      font-size: 16px;
      
      &.trend-up {
        color: #67c23a;
      }
      
      &.trend-down {
        color: #f56c6c;
      }
      
      &.trend-stable {
        color: #909399;
      }
    }
    
    .trend-text {
      font-size: 10px;
      color: var(--el-text-color-secondary);
    }
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