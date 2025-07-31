<template>
  <div class="pageview-trend-chart">
    <div v-if="loading" class="chart-loading">
      <el-skeleton :rows="6" animated />
    </div>
    
    <div v-else ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useAnalyticsStore } from '@/stores/analytics'

interface Props {
  period?: string
}

const props = withDefaults(defineProps<Props>(), {
  period: '7d'
})

const analyticsStore = useAnalyticsStore()
const chartRef = ref<HTMLElement>()
const loading = ref(false)
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = async () => {
  if (!chartInstance) return
  
  try {
    loading.value = true
    const trendData = await analyticsStore.fetchPageViewTrend(props.period)
    
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
            result += `${param.marker}${param.seriesName}: ${param.value.toLocaleString()}<br/>`
          })
          return result
        }
      },
      legend: {
        data: ['页面访问量', '独立访客'],
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
        data: trendData.labels || [],
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
            if (value >= 1000) {
              return `${(value / 1000).toFixed(1)}k`
            }
            return value.toString()
          }
        }
      },
      series: [
        {
          name: '页面访问量',
          type: 'line',
          smooth: true,
          lineStyle: {
            width: 3
          },
          showSymbol: false,
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
          data: trendData.pageViews || [],
          itemStyle: {
            color: '#409eff'
          }
        },
        {
          name: '独立访客',
          type: 'line',
          smooth: true,
          lineStyle: {
            width: 3
          },
          showSymbol: false,
          areaStyle: {
            opacity: 0.3,
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: '#67c23a'
              },
              {
                offset: 1,
                color: 'rgba(103, 194, 58, 0.1)'
              }
            ])
          },
          emphasis: {
            focus: 'series'
          },
          data: trendData.uniqueVisitors || [],
          itemStyle: {
            color: '#67c23a'
          }
        }
      ]
    }
    
    chartInstance.setOption(option, true)
  } catch (error) {
    console.error('Failed to load pageview trend data:', error)
  } finally {
    loading.value = false
  }
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听period变化
watch(() => props.period, () => {
  nextTick(() => {
    updateChart()
  })
})

onMounted(() => {
  nextTick(() => {
    initChart()
  })
  
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
.pageview-trend-chart {
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