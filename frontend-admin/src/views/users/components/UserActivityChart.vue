<template>
  <div class="user-activity-chart">
    <div v-if="loading" class="chart-loading">
      <el-skeleton :rows="6" animated />
    </div>
    
    <div v-else ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

interface Props {
  data: {
    active_users: number
    inactive_users: number
    new_users_retention: number
    avg_session_duration: number
  }
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return
  
  const total = props.data.active_users + props.data.inactive_users
  
  if (total === 0) {
    // 显示空状态
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    chartInstance.setOption(option, true)
    return
  }
  
  const chartData = [
    {
      value: props.data.active_users,
      name: '活跃用户',
      itemStyle: { color: '#67c23a' }
    },
    {
      value: props.data.inactive_users,
      name: '非活跃用户',
      itemStyle: { color: '#f56c6c' }
    }
  ]
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const percentage = ((params.value / total) * 100).toFixed(1)
        return `${params.marker}${params.name}: ${params.value.toLocaleString()} (${percentage}%)`
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '用户活跃度',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['65%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: 'outside',
          formatter: (params: any) => {
            const percentage = ((params.value / total) * 100).toFixed(1)
            return `${percentage}%`
          }
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        data: chartData
      }
    ],
    // 添加统计信息
    graphic: [
      {
        type: 'text',
        left: '65%',
        top: '45%',
        style: {
          text: `总用户: ${total.toLocaleString()}`,
          textAlign: 'center',
          fill: '#666',
          fontSize: 12
        }
      },
      {
        type: 'text',
        left: '65%',
        top: '55%',
        style: {
          text: `留存率: ${props.data.new_users_retention.toFixed(1)}%`,
          textAlign: 'center',
          fill: '#666',
          fontSize: 12
        }
      }
    ]
  }
  
  chartInstance.setOption(option, true)
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    updateChart()
  })
}, { deep: true })

// 监听加载状态
watch(() => props.loading, (newLoading) => {
  if (!newLoading && chartRef.value && !chartInstance) {
    nextTick(() => {
      initChart()
    })
  }
})

onMounted(() => {
  if (!props.loading) {
    nextTick(() => {
      initChart()
    })
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', resizeChart)
})

// 清理
const cleanup = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', resizeChart)
}

import { onUnmounted } from 'vue'
onUnmounted(cleanup)
</script>

<style lang="scss" scoped>
.user-activity-chart {
  width: 100%;
  height: 100%;
  
  .chart-container {
    width: 100%;
    height: 100%;
  }
  
  .chart-loading {
    padding: 20px;
  }
}
</style>