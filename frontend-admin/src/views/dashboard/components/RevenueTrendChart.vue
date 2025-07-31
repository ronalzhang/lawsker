<template>
  <div class="revenue-trend-chart">
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
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((param: any) => {
          const value = param.value
          const formattedValue = typeof value === 'number' ? 
            `¥${value.toLocaleString()}` : value
          result += `${param.marker}${param.seriesName}: ${formattedValue}<br/>`
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
      boundaryGap: false,
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
        formatter: (value: number) => {
          if (value >= 10000) {
            return `¥${(value / 10000).toFixed(1)}万`
          } else if (value >= 1000) {
            return `¥${(value / 1000).toFixed(1)}k`
          }
          return `¥${value}`
        }
      }
    },
    series: props.data.datasets.map((dataset, index) => {
      const baseColor = dataset.borderColor || getDefaultColor(index)
      
      return {
        name: dataset.label,
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 4
        },
        showSymbol: true,
        symbolSize: 8,
        emphasis: {
          focus: 'series'
        },
        data: dataset.data,
        itemStyle: {
          color: baseColor
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: baseColor
            },
            {
              offset: 1,
              color: 'rgba(255, 255, 255, 0.1)'
            }
          ]),
          opacity: 0.4
        }
      }
    }))
  }
  
  chartInstance.setOption(option, true)
}

const getDefaultColor = (index: number) => {
  const colors = [
    '#f56c6c', // 红色 - 总收入
    '#67c23a', // 绿色 - 律师费用
    '#409eff', // 蓝色 - 平台佣金
    '#e6a23c', // 橙色 - 其他收入
    '#909399'  // 灰色 - 退款
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
.revenue-trend-chart {
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