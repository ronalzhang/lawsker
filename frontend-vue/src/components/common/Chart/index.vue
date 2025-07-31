<template>
  <div class="lk-chart" :style="{ height: height }">
    <div ref="chartRef" class="lk-chart__container" />
    
    <div v-if="loading" class="lk-chart__loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    
    <div v-if="error" class="lk-chart__error">
      <el-icon class="error-icon"><Warning /></el-icon>
      <span>{{ error }}</span>
    </div>
    
    <div v-if="!loading && !error && isEmpty" class="lk-chart__empty">
      <el-empty description="暂无数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { ElIcon, ElEmpty } from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  option: EChartsOption
  height?: string
  loading?: boolean
  error?: string
  theme?: string
  autoResize?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  loading: false,
  theme: 'default',
  autoResize: true
})

const emit = defineEmits<{
  chartReady: [chart: echarts.ECharts]
  chartClick: [params: any]
  chartHover: [params: any]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const isEmpty = computed(() => {
  if (!props.option || props.loading || props.error) return false
  
  // 检查是否有数据
  const series = props.option.series
  if (!series || !Array.isArray(series)) return true
  
  return series.every((s: any) => {
    if (!s.data || !Array.isArray(s.data)) return true
    return s.data.length === 0
  })
})

const initChart = async () => {
  if (!chartRef.value) return
  
  await nextTick()
  
  // 销毁现有实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  
  // 创建新实例
  chartInstance = echarts.init(chartRef.value, props.theme)
  
  // 设置配置项
  if (props.option && !isEmpty.value) {
    chartInstance.setOption(props.option, true)
  }
  
  // 绑定事件
  chartInstance.on('click', (params) => {
    emit('chartClick', params)
  })
  
  chartInstance.on('mouseover', (params) => {
    emit('chartHover', params)
  })
  
  // 发出就绪事件
  emit('chartReady', chartInstance)
  
  // 设置自动调整大小
  if (props.autoResize) {
    setupResize()
  }
}

const setupResize = () => {
  if (!chartRef.value || !chartInstance) return
  
  // 使用 ResizeObserver 监听容器大小变化
  resizeObserver = new ResizeObserver(() => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
  
  resizeObserver.observe(chartRef.value)
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const updateChart = () => {
  if (!chartInstance || isEmpty.value) return
  
  chartInstance.setOption(props.option, true)
}

// 监听配置项变化
watch(
  () => props.option,
  () => {
    if (chartInstance && !isEmpty.value) {
      updateChart()
    }
  },
  { deep: true }
)

// 监听加载状态
watch(
  () => props.loading,
  (loading) => {
    if (chartInstance) {
      if (loading) {
        chartInstance.showLoading('default', {
          text: '加载中...',
          color: '#409eff',
          textColor: '#000',
          maskColor: 'rgba(255, 255, 255, 0.8)',
          zlevel: 0
        })
      } else {
        chartInstance.hideLoading()
      }
    }
  }
)

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  
  window.removeEventListener('resize', handleResize)
  
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

// 暴露方法
defineExpose({
  getChart: () => chartInstance,
  resize: () => chartInstance?.resize(),
  refresh: updateChart
})
</script>

<style scoped lang="scss">
.lk-chart {
  position: relative;
  width: 100%;
  
  .lk-chart__container {
    width: 100%;
    height: 100%;
  }
  
  .lk-chart__loading,
  .lk-chart__error,
  .lk-chart__empty {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.9);
    z-index: 10;
  }
  
  .lk-chart__loading {
    .loading-icon {
      font-size: 32px;
      color: var(--el-color-primary);
      margin-bottom: 12px;
      animation: rotating 2s linear infinite;
    }
    
    span {
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
  }
  
  .lk-chart__error {
    .error-icon {
      font-size: 32px;
      color: var(--el-color-danger);
      margin-bottom: 12px;
    }
    
    span {
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
  }
  
  .lk-chart__empty {
    background: transparent;
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
</style>