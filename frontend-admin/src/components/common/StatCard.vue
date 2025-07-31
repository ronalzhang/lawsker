<template>
  <el-card class="stat-card" :class="cardClass" shadow="hover">
    <div class="stat-content">
      <div class="stat-icon" :style="{ backgroundColor: iconColor }">
        <el-icon>
          <component :is="icon" />
        </el-icon>
      </div>
      
      <div class="stat-info">
        <div class="stat-value">
          <span class="value-number">{{ formattedValue }}</span>
          <span v-if="unit" class="value-unit">{{ unit }}</span>
        </div>
        
        <div class="stat-label">{{ title }}</div>
        
        <div v-if="trend !== undefined" class="stat-trend">
          <el-icon class="trend-icon" :class="trendClass">
            <component :is="trendIcon" />
          </el-icon>
          <span class="trend-text">{{ Math.abs(trend) }}%</span>
          <span class="trend-label">{{ trendLabel }}</span>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="stat-loading">
      <el-skeleton :rows="2" animated />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TrendCharts, Bottom } from '@element-plus/icons-vue'

interface Props {
  title: string
  value: number | string
  unit?: string
  trend?: number
  trendLabel?: string
  icon: any
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary',
  loading: false,
  trendLabel: '较上期'
})

const cardClass = computed(() => {
  return [`stat-card--${props.color}`]
})

const iconColor = computed(() => {
  const colorMap = {
    primary: '#409eff',
    success: '#67c23a',
    warning: '#e6a23c',
    danger: '#f56c6c',
    info: '#909399'
  }
  return colorMap[props.color]
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})

const trendClass = computed(() => {
  if (props.trend === undefined) return ''
  
  return {
    'trend-up': props.trend > 0,
    'trend-down': props.trend < 0,
    'trend-flat': props.trend === 0
  }
})

const trendIcon = computed(() => {
  if (props.trend === undefined) return null
  
  if (props.trend > 0) return TrendCharts
  if (props.trend < 0) return Bottom
  return TrendCharts
})
</script>

<style lang="scss" scoped>
.stat-card {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  
  &--primary {
    border-left: 4px solid #409eff;
  }
  
  &--success {
    border-left: 4px solid #67c23a;
  }
  
  &--warning {
    border-left: 4px solid #e6a23c;
  }
  
  &--danger {
    border-left: 4px solid #f56c6c;
  }
  
  &--info {
    border-left: 4px solid #909399;
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
    
    .el-icon {
      font-size: 28px;
    }
  }
  
  .stat-info {
    flex: 1;
    
    .stat-value {
      display: flex;
      align-items: baseline;
      margin-bottom: 8px;
      
      .value-number {
        font-size: 28px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        line-height: 1;
      }
      
      .value-unit {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin-left: 4px;
      }
    }
    
    .stat-label {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin-bottom: 8px;
    }
    
    .stat-trend {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      
      .trend-icon {
        &.trend-up {
          color: #67c23a;
        }
        
        &.trend-down {
          color: #f56c6c;
        }
        
        &.trend-flat {
          color: #909399;
        }
      }
      
      .trend-text {
        font-weight: 500;
      }
      
      .trend-label {
        color: var(--el-text-color-secondary);
      }
    }
  }
}

.stat-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
</style>