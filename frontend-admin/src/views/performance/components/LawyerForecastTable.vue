<template>
  <div class="lawyer-forecast-table">
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
      
      <el-select v-model="confidenceFilter" @change="handleConfidenceFilter" placeholder="筛选置信度" clearable>
        <el-option label="全部" value="" />
        <el-option label="高置信度 (≥80%)" value="high" />
        <el-option label="中等置信度 (60-80%)" value="medium" />
        <el-option label="低置信度 (<60%)" value="low" />
      </el-select>
      
      <el-button :icon="Refresh" @click="$emit('refresh')">
        刷新
      </el-button>
    </div>

    <!-- 预测表格 -->
    <el-table
      :data="filteredData"
      v-loading="loading"
      stripe
      style="width: 100%"
      :height="500"
    >
      <el-table-column
        prop="name"
        label="律师姓名"
        width="150"
        fixed="left"
      >
        <template #default="{ row }">
          <span class="lawyer-name">{{ row.name }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="predicted_revenue"
        label="预测收入"
        width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <div class="revenue-cell">
            <span class="amount">¥{{ row.predicted_revenue.toLocaleString() }}</span>
            <div class="prediction-tag">
              <el-tag size="small" type="info">预测值</el-tag>
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="predicted_cases"
        label="预测案件数"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.predicted_cases }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="confidence_score"
        label="置信度"
        width="120"
        align="center"
        sortable
      >
        <template #default="{ row }">
          <div class="confidence-cell">
            <el-progress
              :percentage="row.confidence_score"
              :color="getConfidenceColor(row.confidence_score)"
              :show-text="false"
              :stroke-width="8"
            />
            <span class="confidence-text">{{ row.confidence_score }}%</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        label="预测准确性"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <el-tag :type="getAccuracyType(row.confidence_score)" size="small">
            {{ getAccuracyText(row.confidence_score) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column
        label="风险评估"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <div class="risk-assessment">
            <el-icon :class="getRiskClass(row)" class="risk-icon">
              <component :is="getRiskIcon(row)" />
            </el-icon>
            <span class="risk-text">{{ getRiskText(row) }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        label="建议策略"
        width="200"
      >
        <template #default="{ row }">
          <div class="strategy-cell">
            <el-tag
              v-for="strategy in getStrategies(row)"
              :key="strategy.text"
              :type="strategy.type"
              size="small"
              class="strategy-tag"
            >
              {{ strategy.text }}
            </el-tag>
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
            @click="handleViewForecastDetails(row)"
          >
            详细预测
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
import { Search, Refresh, Warning, SuccessFilled, InfoFilled } from '@element-plus/icons-vue'

interface LawyerForecastData {
  lawyer_id: string
  name: string
  predicted_revenue: number
  predicted_cases: number
  confidence_score: number
}

interface Props {
  data: LawyerForecastData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  refresh: []
}>()

const searchKeyword = ref('')
const confidenceFilter = ref('')

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

  // 置信度筛选
  if (confidenceFilter.value) {
    result = result.filter(item => {
      if (confidenceFilter.value === 'high') return item.confidence_score >= 80
      if (confidenceFilter.value === 'medium') return item.confidence_score >= 60 && item.confidence_score < 80
      if (confidenceFilter.value === 'low') return item.confidence_score < 60
      return true
    })
  }

  return result
})

// 获取置信度颜色
const getConfidenceColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 40) return '#e6a23c'
  return '#f56c6c'
}

// 获取准确性类型
const getAccuracyType = (score: number) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'primary'
  if (score >= 40) return 'warning'
  return 'danger'
}

// 获取准确性文本
const getAccuracyText = (score: number) => {
  if (score >= 80) return '高准确性'
  if (score >= 60) return '中等准确性'
  if (score >= 40) return '一般准确性'
  return '低准确性'
}

// 获取风险样式类
const getRiskClass = (row: LawyerForecastData) => {
  if (row.confidence_score >= 80) return 'risk-low'
  if (row.confidence_score >= 60) return 'risk-medium'
  return 'risk-high'
}

// 获取风险图标
const getRiskIcon = (row: LawyerForecastData) => {
  if (row.confidence_score >= 80) return SuccessFilled
  if (row.confidence_score >= 60) return InfoFilled
  return Warning
}

// 获取风险文本
const getRiskText = (row: LawyerForecastData) => {
  if (row.confidence_score >= 80) return '低风险'
  if (row.confidence_score >= 60) return '中等风险'
  return '高风险'
}

// 获取建议策略
const getStrategies = (row: LawyerForecastData) => {
  const strategies = []
  
  if (row.confidence_score >= 80) {
    strategies.push({ text: '保持现状', type: 'success' })
    if (row.predicted_revenue > 100000) {
      strategies.push({ text: '扩大业务', type: 'primary' })
    }
  } else if (row.confidence_score >= 60) {
    strategies.push({ text: '优化服务', type: 'warning' })
    strategies.push({ text: '提升效率', type: 'primary' })
  } else {
    strategies.push({ text: '重点关注', type: 'danger' })
    strategies.push({ text: '培训支持', type: 'warning' })
  }
  
  return strategies
}

// 处理置信度筛选
const handleConfidenceFilter = () => {
  // 筛选逻辑已在computed中处理
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

// 查看预测详情
const handleViewForecastDetails = (row: LawyerForecastData) => {
  // 这里可以打开详情对话框显示更详细的预测信息
  console.log('View forecast details:', row)
}
</script>

<style lang="scss" scoped>
.lawyer-forecast-table {
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: center;
  }
  
  .lawyer-name {
    font-weight: 600;
    color: var(--el-text-color-primary);
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
  
  .confidence-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    
    .confidence-text {
      font-size: 12px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
  
  .risk-assessment {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    
    .risk-icon {
      font-size: 16px;
      
      &.risk-low {
        color: #67c23a;
      }
      
      &.risk-medium {
        color: #e6a23c;
      }
      
      &.risk-high {
        color: #f56c6c;
      }
    }
    
    .risk-text {
      font-size: 10px;
      color: var(--el-text-color-secondary);
    }
  }
  
  .strategy-cell {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    
    .strategy-tag {
      margin: 2px 0;
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