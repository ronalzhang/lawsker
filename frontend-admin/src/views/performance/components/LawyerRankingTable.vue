<template>
  <div class="lawyer-ranking-table">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索律师姓名"
        :prefix-icon="Search"
        @input="handleSearch"
        style="width: 300px;"
        clearable
      />
      
      <el-button :icon="Refresh" @click="$emit('refresh')">
        刷新
      </el-button>
    </div>

    <!-- 排行榜表格 -->
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
              <Trophy />
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
        prop="name"
        label="律师信息"
        width="200"
        fixed="left"
      >
        <template #default="{ row }">
          <div class="lawyer-info">
            <el-avatar :size="40" :src="row.avatar">
              {{ row.name.charAt(0) }}
            </el-avatar>
            <div class="info-text">
              <span class="name">{{ row.name }}</span>
              <div class="rating">
                <el-rate
                  :model-value="row.client_rating"
                  disabled
                  show-score
                  text-color="#ff9900"
                  score-template="{value}"
                  size="small"
                />
              </div>
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="total_revenue"
        label="总收入"
        width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <div class="revenue-cell">
            <span class="amount">¥{{ row.total_revenue.toLocaleString() }}</span>
            <div v-if="row.growth_rate !== 0" class="growth-rate">
              <el-tag
                :type="row.growth_rate > 0 ? 'success' : 'danger'"
                size="small"
              >
                {{ row.growth_rate > 0 ? '+' : '' }}{{ row.growth_rate.toFixed(1) }}%
              </el-tag>
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="cases_completed"
        label="完成案件"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.cases_completed }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="response_time"
        label="平均响应时间"
        width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="time-cell">{{ formatResponseTime(row.response_time) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        label="业绩趋势"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <div class="trend-cell">
            <el-progress
              :percentage="getPerformanceScore(row)"
              :color="getPerformanceColor(row)"
              :show-text="false"
              :stroke-width="8"
            />
            <span class="score-text">{{ getPerformanceScore(row) }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        label="操作"
        width="150"
        align="center"
        fixed="right"
      >
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              size="small"
              type="primary"
              @click="$emit('view-trend', row.lawyer_id)"
            >
              查看趋势
            </el-button>
            <el-button
              size="small"
              type="info"
              @click="handleViewDetails(row)"
            >
              详情
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
import { Search, Refresh, Trophy, ArrowUp, ArrowDown } from '@element-plus/icons-vue'

interface LawyerRankingData {
  lawyer_id: string
  name: string
  avatar?: string
  total_revenue: number
  cases_completed: number
  client_rating: number
  response_time: number
  rank: number
  rank_change: number
  growth_rate: number
}

interface Props {
  data: LawyerRankingData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  'view-trend': [lawyerId: string]
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
      item.name.toLowerCase().includes(keyword)
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

// 格式化响应时间
const formatResponseTime = (minutes: number) => {
  if (minutes < 60) {
    return `${Math.round(minutes)}分钟`
  } else if (minutes < 1440) {
    return `${Math.round(minutes / 60)}小时`
  } else {
    return `${Math.round(minutes / 1440)}天`
  }
}

// 计算业绩评分
const getPerformanceScore = (row: LawyerRankingData) => {
  // 综合评分算法：收入权重40%，案件数量30%，评分20%，响应时间10%
  const revenueScore = Math.min(row.total_revenue / 100000 * 40, 40)
  const casesScore = Math.min(row.cases_completed / 50 * 30, 30)
  const ratingScore = row.client_rating * 4 // 5分制转20分制
  const responseScore = Math.max(10 - (row.response_time / 60), 0) // 响应时间越短分数越高
  
  return Math.round(revenueScore + casesScore + ratingScore + responseScore)
}

// 获取业绩颜色
const getPerformanceColor = (row: LawyerRankingData) => {
  const score = getPerformanceScore(row)
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 40) return '#e6a23c'
  return '#f56c6c'
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

// 查看详情
const handleViewDetails = (row: LawyerRankingData) => {
  // 这里可以打开详情对话框或跳转到详情页面
  console.log('View lawyer details:', row)
}
</script>

<style lang="scss" scoped>
.lawyer-ranking-table {
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
  
  .lawyer-info {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .info-text {
      .name {
        display: block;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .rating {
        :deep(.el-rate) {
          .el-rate__text {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
  
  .revenue-cell {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
    
    .amount {
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
  
  .number-cell {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .time-cell {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .trend-cell {
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