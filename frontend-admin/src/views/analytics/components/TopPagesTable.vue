<template>
  <div class="top-pages-table">
    <el-table
      :data="data"
      v-loading="loading"
      stripe
      style="width: 100%"
      :height="400"
    >
      <el-table-column
        prop="path"
        label="页面路径"
        min-width="200"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <el-link type="primary" :href="row.path" target="_blank">
            {{ row.path }}
          </el-link>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="views"
        label="访问量"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.views.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="unique_views"
        label="独立访客"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.unique_views.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="bounce_rate"
        label="跳出率"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <el-tag
            :type="getBounceRateType(row.bounce_rate)"
            size="small"
          >
            {{ row.bounce_rate.toFixed(1) }}%
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column
        label="访问占比"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <div class="percentage-cell">
            <el-progress
              :percentage="getPercentage(row.views)"
              :show-text="false"
              :stroke-width="6"
              :color="getProgressColor(getPercentage(row.views))"
            />
            <span class="percentage-text">{{ getPercentage(row.views).toFixed(1) }}%</span>
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
import { computed } from 'vue'

interface Props {
  data: Array<{
    path: string
    views: number
    unique_views: number
    bounce_rate: number
  }>
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// 计算总访问量
const totalViews = computed(() => {
  return props.data.reduce((sum, item) => sum + item.views, 0)
})

// 获取访问占比
const getPercentage = (views: number) => {
  if (totalViews.value === 0) return 0
  return (views / totalViews.value) * 100
}

// 获取跳出率标签类型
const getBounceRateType = (bounceRate: number) => {
  if (bounceRate >= 70) return 'danger'
  if (bounceRate >= 50) return 'warning'
  return 'success'
}

// 获取进度条颜色
const getProgressColor = (percentage: number) => {
  if (percentage >= 50) return '#f56c6c'
  if (percentage >= 30) return '#e6a23c'
  if (percentage >= 20) return '#409eff'
  return '#67c23a'
}
</script>

<style lang="scss" scoped>
.top-pages-table {
  .number-cell {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .percentage-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    
    .percentage-text {
      font-size: 12px;
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