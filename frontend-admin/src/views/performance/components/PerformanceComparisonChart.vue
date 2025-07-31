<template>
  <div class="performance-comparison-chart">
    <div v-if="loading" class="chart-loading">
      <el-skeleton :rows="6" animated />
    </div>
    
    <div v-else ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { PerformanceComparison } from '@/types'

interface Props {
  data: PerformanceComparison
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
  if (!chartInstance || !props.data.categories.length) return
  
  const categories = props.data.categories.map(item => item.category)
  const currentValues = props.data.categories.map(item => item.current_value)
  const previousValues = props.data.categories.map(item => item.previous_value)
  const growthRates = props.data.categories.map(item => item.growth_rate)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((param: any, index: number) => {
          if (param.seriesName === '增长率') {
            result += `${param.marker}${param.seriesName}: ${param.value.toFixed(1)}%<br/>`
          } else {
            result += `${param.marker}${param.seriesName}: ¥${param.value.toLocaleString()}<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: ['当前周期', '对比周期', '增长率'],
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
      data: categories,
      axisLabel: {
        interval: 0,
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '金额 (元)',
        position: 'left',
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
      {
        type: 'value',
        name: '增长率 (%)',
        position: 'right',
        axisLabel: {
          formatter: (value: number) => `${value}%`
        }
      }
    ],
    series: [
      {
        name: '当前周期',
        type: 'bar',
        emphasis: {
          focus: 'series'
        },
        data: currentValues.map((value, index) => ({
          value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#409eff' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.6)' }
            ])
          }
        }))
      },
      {
        name: '对比周期',
        type: 'bar',
        emphasis: {
          focus: 'series'
        },
        data: previousValues.map((value, index) => ({
          value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#909399' },
              { offset: 1, color: 'rgba(144, 147, 153, 0.6)' }
            ])
          }
        }))
      },
      {
        name: '增长率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        lineStyle: {
          width: 3
        },
        showSymbol: true,
        symbolSize: 8,
        emphasis: {
          focus: 'series'
        },
        data: growthRates.map(rate => ({
          value: rate,
          itemStyle: {
            color: rate >= 0 ? '#67c23a' : '#f56c6c'
          }
        })),
        itemStyle: {
          color: '#e6a23c'
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
.performance-comparison-chart {
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