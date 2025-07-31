<template>
  <div class="case-trend-chart">
    <div v-if="loading" class="chart-loading">
      <el-skeleton :rows="6" animated />
    </div>
    
    <div v-else ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { ChartData } from '@/types'

interface Props {
  data: ChartData
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
  if (!chartInstance || !props.data.labels.length) return
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((param: any) => {
          result += `${param.marker}${param.seriesName}: ${param.value}<br/>`
        })
        return result
      }
    },
    legend: {
      data: props.data.datasets.map(dataset => dataset.label),
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.data.labels,
      axisLabel: {
        formatter: (value: string) => {
          // 格式化日期显示
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => value.toString()
      }
    },
    series: props.data.datasets.map((dataset, index) => ({
      name: dataset.label,
      type: 'bar',
      stack: 'total',
      emphasis: {
        focus: 'series'
      },
      data: dataset.data,
      itemStyle: {
        color: dataset.backgroundColor || getDefaultColor(index),
        borderColor: dataset.borderColor || getDefaultColor(index),
        borderWidth: 1
      }
    }))
  }
  
  chartInstance.setOption(option, true)
}

const getDefaultColor = (index: number) => {
  const colors = [
    '#409eff', // 蓝色 - 待处理
    '#e6a23c', // 橙色 - 进行中  
    '#67c23a', // 绿色 - 已完成
    '#f56c6c', // 红色 - 已取消
    '#909399'  // 灰色 - 其他
  ]
  return colors[index % colors.length]
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

// 组件卸载时清理
import { onUnmounted } from 'vue'
onUnmounted(cleanup)
</script>

<style lang="scss" scoped>
.case-trend-chart {
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