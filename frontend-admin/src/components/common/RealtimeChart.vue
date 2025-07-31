<template>
  <div class="realtime-chart" ref="chartRef" :style="{ width, height }">
    <div v-if="loading" class="chart-loading">
      <el-loading-spinner />
      <span>图表加载中...</span>
    </div>
    <div v-if="error" class="chart-error">
      <el-icon><Warning /></el-icon>
      <span>{{ error }}</span>
      <el-button size="small" @click="retry">重试</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, shallowRef } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'

interface Props {
  option: EChartsOption
  width?: string
  height?: string
  loading?: boolean
  error?: string
  theme?: string
  autoResize?: boolean
  updateMode?: 'replace' | 'merge'
  notMerge?: boolean
  lazyUpdate?: boolean
  silent?: boolean
  animationDuration?: number
  realtime?: boolean
  realtimeInterval?: number
  maxDataPoints?: number
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  loading: false,
  error: '',
  theme: 'default',
  autoResize: true,
  updateMode: 'merge',
  notMerge: false,
  lazyUpdate: false,
  silent: false,
  animationDuration: 300,
  realtime: false,
  realtimeInterval: 1000,
  maxDataPoints: 100
})

const emit = defineEmits<{
  'chart-ready': [chart: ECharts]
  'chart-click': [params: any]
  'chart-mouseover': [params: any]
  'chart-mouseout': [params: any]
  'data-zoom': [params: any]
  'brush-selected': [params: any]
  'legend-select-changed': [params: any]
  'retry': []
}>()

const chartRef = ref<HTMLElement>()
const chart = shallowRef<ECharts>()
const resizeObserver = ref<ResizeObserver>()
const realtimeTimer = ref<number>()

// 初始化图表
const initChart = async () => {
  if (!chartRef.value) return

  try {
    // 销毁现有图表
    if (chart.value) {
      chart.value.dispose()
    }

    // 创建新图表
    chart.value = echarts.init(chartRef.value, props.theme, {
      renderer: 'canvas',
      useDirtyRect: true
    })

    // 设置配置项
    updateChart()

    // 绑定事件
    bindEvents()

    // 启动实时更新
    if (props.realtime) {
      startRealtimeUpdate()
    }

    emit('chart-ready', chart.value)
  } catch (error) {
    console.error('Chart initialization failed:', error)
  }
}

// 更新图表
const updateChart = () => {
  if (!chart.value || !props.option) return

  try {
    const option = { ...props.option }
    
    // 设置动画
    if (option.animation === undefined) {
      option.animation = true
      option.animationDuration = props.animationDuration
    }

    // 更新图表
    if (props.updateMode === 'replace') {
      chart.value.setOption(option, true, props.lazyUpdate)
    } else {
      chart.value.setOption(option, props.notMerge, props.lazyUpdate)
    }
  } catch (error) {
    console.error('Chart update failed:', error)
  }
}

// 绑定事件
const bindEvents = () => {
  if (!chart.value) return

  chart.value.on('click', (params) => emit('chart-click', params))
  chart.value.on('mouseover', (params) => emit('chart-mouseover', params))
  chart.value.on('mouseout', (params) => emit('chart-mouseout', params))
  chart.value.on('datazoom', (params) => emit('data-zoom', params))
  chart.value.on('brushselected', (params) => emit('brush-selected', params))
  chart.value.on('legendselectchanged', (params) => emit('legend-select-changed', params))
}

// 启动实时更新
const startRealtimeUpdate = () => {
  if (realtimeTimer.value) {
    clearInterval(realtimeTimer.value)
  }

  realtimeTimer.value = window.setInterval(() => {
    updateRealtimeData()
  }, props.realtimeInterval)
}

// 停止实时更新
const stopRealtimeUpdate = () => {
  if (realtimeTimer.value) {
    clearInterval(realtimeTimer.value)
    realtimeTimer.value = undefined
  }
}

// 更新实时数据
const updateRealtimeData = () => {
  if (!chart.value || !props.option) return

  try {
    const currentOption = chart.value.getOption()
    const series = currentOption.series as any[]

    if (series && series.length > 0) {
      series.forEach((s, index) => {
        if (s.data && Array.isArray(s.data)) {
          // 限制数据点数量
          if (s.data.length >= props.maxDataPoints) {
            s.data.shift()
          }

          // 添加新数据点（这里需要外部提供数据）
          // 实际使用时应该通过props或事件获取新数据
          const newDataPoint = generateRealtimeData(s.type)
          s.data.push(newDataPoint)
        }
      })

      chart.value.setOption(currentOption, false, false)
    }
  } catch (error) {
    console.error('Realtime update failed:', error)
  }
}

// 生成实时数据（示例）
const generateRealtimeData = (type: string) => {
  const now = new Date()
  const value = Math.random() * 100

  switch (type) {
    case 'line':
    case 'bar':
      return [now.getTime(), Math.floor(value)]
    case 'pie':
      return { name: `数据${now.getTime()}`, value: Math.floor(value) }
    default:
      return value
  }
}

// 调整图表大小
const resize = () => {
  if (chart.value) {
    chart.value.resize()
  }
}

// 重试
const retry = () => {
  emit('retry')
  nextTick(() => {
    initChart()
  })
}

// 设置ResizeObserver
const setupResizeObserver = () => {
  if (!props.autoResize || !chartRef.value) return

  resizeObserver.value = new ResizeObserver(() => {
    resize()
  })

  resizeObserver.value.observe(chartRef.value)
}

// 清理ResizeObserver
const cleanupResizeObserver = () => {
  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
    resizeObserver.value = undefined
  }
}

// 监听器
watch(() => props.option, updateChart, { deep: true })
watch(() => props.realtime, (newVal) => {
  if (newVal) {
    startRealtimeUpdate()
  } else {
    stopRealtimeUpdate()
  }
})

// 生命周期
onMounted(async () => {
  await nextTick()
  initChart()
  setupResizeObserver()
})

onUnmounted(() => {
  stopRealtimeUpdate()
  cleanupResizeObserver()
  
  if (chart.value) {
    chart.value.dispose()
  }
})

// 暴露方法
defineExpose({
  chart,
  resize,
  updateChart,
  startRealtimeUpdate,
  stopRealtimeUpdate
})
</script>

<style scoped>
.realtime-chart {
  position: relative;
  overflow: hidden;
}

.chart-loading,
.chart-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.chart-error {
  color: var(--el-color-danger);
}

.chart-error .el-icon {
  font-size: 24px;
}
</style>