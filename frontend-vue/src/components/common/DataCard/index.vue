<template>
  <div class="lk-data-card" :class="cardClass">
    <div class="lk-data-card__header" v-if="$slots.header || title">
      <slot name="header">
        <div class="lk-data-card__title">
          <el-icon v-if="icon" class="lk-data-card__icon">
            <component :is="icon" />
          </el-icon>
          <span>{{ title }}</span>
        </div>
        <div class="lk-data-card__extra" v-if="$slots.extra">
          <slot name="extra" />
        </div>
      </slot>
    </div>
    
    <div class="lk-data-card__content">
      <div class="lk-data-card__main">
        <div class="lk-data-card__value">
          <span class="lk-data-card__number">{{ formattedValue }}</span>
          <span class="lk-data-card__unit" v-if="unit">{{ unit }}</span>
        </div>
        
        <div class="lk-data-card__trend" v-if="trend !== undefined">
          <el-icon class="lk-data-card__trend-icon" :class="trendClass">
            <component :is="trendIcon" />
          </el-icon>
          <span class="lk-data-card__trend-text">{{ Math.abs(trend) }}%</span>
        </div>
      </div>
      
      <div class="lk-data-card__description" v-if="description">
        {{ description }}
      </div>
      
      <div class="lk-data-card__footer" v-if="$slots.footer">
        <slot name="footer" />
      </div>
    </div>
    
    <div class="lk-data-card__loading" v-if="loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElIcon } from 'element-plus'
import { Loading, TrendCharts, Bottom } from '@element-plus/icons-vue'
import { formatNumber } from '@/utils/format'

interface Props {
  title?: string
  value?: number | string
  unit?: string
  description?: string
  trend?: number
  icon?: any
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  size?: 'small' | 'default' | 'large'
  loading?: boolean
  bordered?: boolean
  hoverable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary',
  size: 'default',
  loading: false,
  bordered: true,
  hoverable: true
})

const cardClass = computed(() => {
  return [
    `lk-data-card--${props.color}`,
    `lk-data-card--${props.size}`,
    {
      'lk-data-card--bordered': props.bordered,
      'lk-data-card--hoverable': props.hoverable,
      'lk-data-card--loading': props.loading
    }
  ]
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return formatNumber(props.value)
  }
  return props.value || '0'
})

const trendClass = computed(() => {
  if (props.trend === undefined) return ''
  
  return {
    'lk-data-card__trend-icon--up': props.trend > 0,
    'lk-data-card__trend-icon--down': props.trend < 0,
    'lk-data-card__trend-icon--flat': props.trend === 0
  }
})

const trendIcon = computed(() => {
  if (props.trend === undefined) return null
  
  if (props.trend > 0) return TrendCharts
  if (props.trend < 0) return Bottom
  return TrendCharts
})
</script>

<style scoped lang="scss">
.lk-data-card {
  position: relative;
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  padding: 20px;
  transition: all 0.3s;
  
  &--bordered {
    border: 1px solid var(--el-border-color-light);
  }
  
  &--hoverable {
    cursor: pointer;
    
    &:hover {
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }
  }
  
  &--loading {
    pointer-events: none;
  }
  
  // 尺寸变体
  &--small {
    padding: 16px;
    
    .lk-data-card__number {
      font-size: 20px;
    }
    
    .lk-data-card__title {
      font-size: 14px;
    }
  }
  
  &--large {
    padding: 24px;
    
    .lk-data-card__number {
      font-size: 32px;
    }
    
    .lk-data-card__title {
      font-size: 18px;
    }
  }
  
  // 颜色变体
  &--primary {
    .lk-data-card__icon {
      color: var(--el-color-primary);
    }
    
    .lk-data-card__number {
      color: var(--el-color-primary);
    }
  }
  
  &--success {
    .lk-data-card__icon {
      color: var(--el-color-success);
    }
    
    .lk-data-card__number {
      color: var(--el-color-success);
    }
  }
  
  &--warning {
    .lk-data-card__icon {
      color: var(--el-color-warning);
    }
    
    .lk-data-card__number {
      color: var(--el-color-warning);
    }
  }
  
  &--danger {
    .lk-data-card__icon {
      color: var(--el-color-danger);
    }
    
    .lk-data-card__number {
      color: var(--el-color-danger);
    }
  }
  
  &--info {
    .lk-data-card__icon {
      color: var(--el-color-info);
    }
    
    .lk-data-card__number {
      color: var(--el-color-info);
    }
  }
}

.lk-data-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .lk-data-card__title {
    display: flex;
    align-items: center;
    font-size: 16px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    
    .lk-data-card__icon {
      margin-right: 8px;
      font-size: 18px;
    }
  }
}

.lk-data-card__content {
  .lk-data-card__main {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 8px;
    
    .lk-data-card__value {
      display: flex;
      align-items: baseline;
      
      .lk-data-card__number {
        font-size: 28px;
        font-weight: 600;
        line-height: 1;
        margin-right: 4px;
      }
      
      .lk-data-card__unit {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
    
    .lk-data-card__trend {
      display: flex;
      align-items: center;
      font-size: 14px;
      
      .lk-data-card__trend-icon {
        margin-right: 4px;
        
        &--up {
          color: var(--el-color-success);
        }
        
        &--down {
          color: var(--el-color-danger);
        }
        
        &--flat {
          color: var(--el-color-info);
        }
      }
      
      .lk-data-card__trend-text {
        font-weight: 500;
      }
    }
  }
  
  .lk-data-card__description {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    line-height: 1.4;
  }
  
  .lk-data-card__footer {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

.lk-data-card__loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--el-border-radius-base);
  
  .loading-icon {
    font-size: 24px;
    color: var(--el-color-primary);
    animation: rotating 2s linear infinite;
  }
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .lk-data-card {
    padding: 16px;
    
    .lk-data-card__main {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
    
    .lk-data-card__number {
      font-size: 24px !important;
    }
  }
}
</style>