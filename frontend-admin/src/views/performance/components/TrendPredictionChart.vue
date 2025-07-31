<template>
  <div class="trend-prediction-chart">
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
    date: string
    actual?: number
    predicted: number
    confidence_interval: {
      lower: number
      upper: number
    }
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
  
  // 分离历史数据和预测数据
  const actualData = props.data.filter(item => item.actual !== undefined)
  const predictedData = props.data.filter(item => item.predicted !== undefined)
  
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
          if (param.seriesName.includes('置信区间')) return
          const value = param.value
          result += `${param.marker}${param.seriesName}: ¥${value.toLocaleString()}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['历史数据', '预测数据', '置信区间'],
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
      data: props.data.map(item => item.date),
      axisLabel: {
        formatter: (value: string) => {
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
    series: [
      // 历史数据
      {
        name: '历史数据',
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#409eff'
        },
        showSymbol: true,
        symbolSize: 6,
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.actual || null),
        itemStyle: {
          color: '#409eff'
        }
      },
      // 预测数据
      {
        name: '预测数据',
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#67c23a',
          type: 'dashed'
        },
        showSymbol: true,
        symbolSize: 6,
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.predicted),
        itemStyle: {
          color: '#67c23a'
        }
      },
      // 置信区间上限
      {
        name: '置信区间上限',
        type: 'line',
        lineStyle: {
          opacity: 0
        },
        stack: 'confidence-band',
        symbol: 'none',
        data: props.data.map(item => item.confidence_interval.upper)
      },
      // 置信区间下限
      {
        name: '置信区间下限',
        type: 'line',
        lineStyle: {
          opacity: 0
        },
        areaStyle: {
          color: 'rgba(103, 194, 58, 0.2)'
        },
        stack: 'confidence-band',
        symbol: 'none',
        data: props.data.map(item => item.confidence_interval.lower)
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
.trend-prediction-chart {
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