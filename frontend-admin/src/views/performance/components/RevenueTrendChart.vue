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

interface Props {
  data: Array<{
    month: string
    revenue: number
    commission: number
    cases: number
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
  if (!chartInstance || !props.data.length) return
  
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
          if (param.seriesName === '案件数量') {
            result += `${param.marker}${param.seriesName}: ${param.value}<br/>`
          } else {
            result += `${param.marker}${param.seriesName}: ¥${param.value.toLocaleString()}<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: ['总收入', '平台佣金', '案件数量'],
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
      data: props.data.map(item => item.month),
      axisLabel: {
        formatter: (value: string) => {
          // 格式化月份显示
          const date = new Date(value)
          return `${date.getMonth() + 1}月`
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '收入 (元)',
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
        name: '案件数量',
        position: 'right',
        axisLabel: {
          formatter: (value: number) => value.toString()
        }
      }
    ],
    series: [
      {
        name: '总收入',
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 4
        },
        showSymbol: true,
        symbolSize: 8,
        areaStyle: {
          opacity: 0.3,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: '#409eff'
            },
            {
              offset: 1,
              color: 'rgba(64, 158, 255, 0.1)'
            }
          ])
        },
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.revenue),
        itemStyle: {
          color: '#409eff'
        }
      },
      {
        name: '平台佣金',
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 3
        },
        showSymbol: true,
        symbolSize: 6,
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.commission),
        itemStyle: {
          color: '#67c23a'
        }
      },
      {
        name: '案件数量',
        type: 'bar',
        yAxisIndex: 1,
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.cases),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#e6a23c' },
            { offset: 1, color: 'rgba(230, 162, 60, 0.6)' }
          ])
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