<template>
  <div class="browser-stats-chart">
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
  data: Array<{
    name: string
    version: string
    count: number
    percentage: number
  }>
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
  
  if (!props.data || props.data.length === 0) {
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
  
  // 取前8个浏览器，其余归为"其他"
  const topBrowsers = props.data.slice(0, 8)
  const otherBrowsers = props.data.slice(8)
  
  let chartData = topBrowsers.map((browser, index) => ({
    value: browser.count,
    name: `${browser.name} ${browser.version}`,
    itemStyle: { color: getColor(index) }
  }))
  
  if (otherBrowsers.length > 0) {
    const otherCount = otherBrowsers.reduce((sum, browser) => sum + browser.count, 0)
    chartData.push({
      value: otherCount,
      name: '其他',
      itemStyle: { color: '#909399' }
    })
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.marker}${params.name}: ${params.value.toLocaleString()} (${params.percent}%)`
      }
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 20,
      bottom: 20,
      textStyle: {
        fontSize: 12
      },
      pageTextStyle: {
        color: '#666'
      }
    },
    series: [
      {
        name: '浏览器统计',
        type: 'pie',
        radius: ['30%', '60%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '14',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: chartData
      }
    ]
  }
  
  chartInstance.setOption(option, true)
}

const getColor = (index: number) => {
  const colors = [
    '#409eff', '#67c23a', '#e6a23c', '#f56c6c', 
    '#909399', '#c71585', '#ff6347', '#32cd32'
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

import { onUnmounted } from 'vue'
onUnmounted(cleanup)
</script>

<style lang="scss" scoped>
.browser-stats-chart {
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