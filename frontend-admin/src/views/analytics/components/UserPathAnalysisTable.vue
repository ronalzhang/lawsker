<template>
  <div class="user-path-analysis-table">
    <el-tabs v-model="activeTab" type="card">
      <!-- 常见路径 -->
      <el-tab-pane label="常见路径" name="commonPaths">
        <el-table
          :data="data.commonPaths"
          v-loading="loading"
          stripe
          style="width: 100%"
          :height="350"
        >
          <el-table-column
            label="用户路径"
            min-width="300"
          >
            <template #default="{ row }">
              <div class="path-cell">
                <div class="path-flow">
                  <span
                    v-for="(page, index) in row.path"
                    :key="index"
                    class="path-item"
                  >
                    <el-tag size="small" type="info">{{ page }}</el-tag>
                    <el-icon v-if="index < row.path.length - 1" class="arrow-icon">
                      <ArrowRight />
                    </el-icon>
                  </span>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="count"
            label="访问次数"
            width="100"
            align="right"
            sortable
          >
            <template #default="{ row }">
              <span class="number-cell">{{ row.count.toLocaleString() }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="conversion_rate"
            label="转化率"
            width="100"
            align="right"
            sortable
          >
            <template #default="{ row }">
              <el-tag
                :type="getConversionRateType(row.conversion_rate)"
                size="small"
              >
                {{ row.conversion_rate.toFixed(1) }}%
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <!-- 入口页面 -->
      <el-tab-pane label="入口页面" name="entryPages">
        <el-table
          :data="data.entryPages"
          v-loading="loading"
          stripe
          style="width: 100%"
          :height="350"
        >
          <el-table-column
            prop="page"
            label="页面路径"
            min-width="200"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <el-link type="primary" :href="row.page" target="_blank">
                {{ row.page }}
              </el-link>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="count"
            label="入口次数"
            width="100"
            align="right"
            sortable
          >
            <template #default="{ row }">
              <span class="number-cell">{{ row.count.toLocaleString() }}</span>
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
            label="入口占比"
            width="120"
            align="center"
          >
            <template #default="{ row }">
              <div class="percentage-cell">
                <el-progress
                  :percentage="getEntryPercentage(row.count)"
                  :show-text="false"
                  :stroke-width="6"
                  :color="getProgressColor(getEntryPercentage(row.count))"
                />
                <span class="percentage-text">{{ getEntryPercentage(row.count).toFixed(1) }}%</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <!-- 退出页面 -->
      <el-tab-pane label="退出页面" name="exitPages">
        <el-table
          :data="data.exitPages"
          v-loading="loading"
          stripe
          style="width: 100%"
          :height="350"
        >
          <el-table-column
            prop="page"
            label="页面路径"
            min-width="200"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <el-link type="primary" :href="row.page" target="_blank">
                {{ row.page }}
              </el-link>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="count"
            label="退出次数"
            width="100"
            align="right"
            sortable
          >
            <template #default="{ row }">
              <span class="number-cell">{{ row.count.toLocaleString() }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="exit_rate"
            label="退出率"
            width="100"
            align="right"
            sortable
          >
            <template #default="{ row }">
              <el-tag
                :type="getExitRateType(row.exit_rate)"
                size="small"
              >
                {{ row.exit_rate.toFixed(1) }}%
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column
            label="退出占比"
            width="120"
            align="center"
          >
            <template #default="{ row }">
              <div class="percentage-cell">
                <el-progress
                  :percentage="getExitPercentage(row.count)"
                  :show-text="false"
                  :stroke-width="6"
                  :color="getProgressColor(getExitPercentage(row.count))"
                />
                <span class="percentage-text">{{ getExitPercentage(row.count).toFixed(1) }}%</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
    
    <div v-if="!loading && isEmpty" class="empty-state">
      <el-empty description="暂无数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import type { UserPathAnalysis } from '@/types'

interface Props {
  data: UserPathAnalysis
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const activeTab = ref('commonPaths')

// 检查是否为空数据
const isEmpty = computed(() => {
  return (!props.data.commonPaths || props.data.commonPaths.length === 0) &&
         (!props.data.entryPages || props.data.entryPages.length === 0) &&
         (!props.data.exitPages || props.data.exitPages.length === 0)
})

// 计算入口页面总数
const totalEntryCount = computed(() => {
  return props.data.entryPages?.reduce((sum, item) => sum + item.count, 0) || 0
})

// 计算退出页面总数
const totalExitCount = computed(() => {
  return props.data.exitPages?.reduce((sum, item) => sum + item.count, 0) || 0
})

// 获取入口占比
const getEntryPercentage = (count: number) => {
  if (totalEntryCount.value === 0) return 0
  return (count / totalEntryCount.value) * 100
}

// 获取退出占比
const getExitPercentage = (count: number) => {
  if (totalExitCount.value === 0) return 0
  return (count / totalExitCount.value) * 100
}

// 获取转化率标签类型
const getConversionRateType = (rate: number) => {
  if (rate >= 80) return 'success'
  if (rate >= 60) return 'primary'
  if (rate >= 40) return 'warning'
  return 'danger'
}

// 获取跳出率标签类型
const getBounceRateType = (bounceRate: number) => {
  if (bounceRate >= 70) return 'danger'
  if (bounceRate >= 50) return 'warning'
  return 'success'
}

// 获取退出率标签类型
const getExitRateType = (exitRate: number) => {
  if (exitRate >= 70) return 'danger'
  if (exitRate >= 50) return 'warning'
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
.user-path-analysis-table {
  .path-cell {
    .path-flow {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      
      .path-item {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .arrow-icon {
          color: var(--el-text-color-secondary);
          font-size: 14px;
        }
      }
    }
  }
  
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
  
  :deep(.el-tabs) {
    .el-tabs__header {
      margin-bottom: 20px;
    }
    
    .el-tabs__content {
      padding: 0;
    }
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