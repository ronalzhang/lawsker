<template>
  <div class="lawyer-certification-chart">
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
    total_lawyers: number
    verified: number
    pending: number
    rejected: number
    verification_rate: number
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
  
  const total = props.data.total_lawyers
  
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
      value: props.data.verified,
      name: '已认证',
      itemStyle: { color: '#67c23a' }
    },
    {
      value: props.data.pending,
      name: '待审核',
      itemStyle: { color: '#e6a23c' }
    },
    {
      value: props.data.rejected,
      name: '已拒绝',
      itemStyle: { color: '#f56c6c' }
    }
  ].filter(item => item.value > 0)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const percentage = ((params.value / total) * 100).toFixed(1)
        return `${params.marker}${params.name}: ${params.value.toLocaleString()} (${percentage}%)`
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '律师认证状态',
        type: 'pie',
        radius: ['30%', '60%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: 'outside',
          formatter: (params: any) => {
            const percentage = ((params.value / total) * 100).toFixed(1)
            return `${params.name}\n${percentage}%`
          }
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '14',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        data: chartData
      }
    ],
    // 添加中心统计信息
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '40%',
        style: {
          text: `总律师数`,
          textAlign: 'center',
          fill: '#666',
          fontSize: 12
        }
      },
      {
        type: 'text',
        left: 'center',
        top: '50%',
        style: {
          text: total.toLocaleString(),
          textAlign: 'center',
          fill: '#333',
          fontSize: 18,
          fontWeight: 'bold'
        }
      },
      {
        type: 'text',
        left: 'center',
        top: '60%',
        style: {
          text: `认证率: ${props.data.verification_rate.toFixed(1)}%`,
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
.lawyer-certification-chart {
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