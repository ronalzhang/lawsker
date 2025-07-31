<template>
  <div class="user-behavior-chart">
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
    action: string
    count: number
    percentage: number
    avg_duration: number
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
  
  // 取前10个行为
  const topBehaviors = props.data.slice(0, 10)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const data = params[0]
        const behavior = topBehaviors[data.dataIndex]
        return `
          ${data.marker}${data.name}<br/>
          执行次数: ${data.value.toLocaleString()}<br/>
          占比: ${behavior.percentage.toFixed(1)}%<br/>
          平均时长: ${formatDuration(behavior.avg_duration)}
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
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
    yAxis: {
      type: 'category',
      data: topBehaviors.map(item => item.action),
      axisLabel: {
        interval: 0,
        formatter: (value: string) => {
          // 限制标签长度
          return value.length > 12 ? value.substring(0, 12) + '...' : value
        }
      }
    },
    series: [
      {
        name: '执行次数',
        type: 'bar',
        data: topBehaviors.map((item, index) => ({
          value: item.count,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: getColor(index) },
              { offset: 1, color: getColor(index, 0.6) }
            ])
          }
        })),
        emphasis: {
          focus: 'series'
        },
        animationDelay: (idx: number) => idx * 100,
        label: {
          show: true,
          position: 'right',
          formatter: (params: any) => {
            const behavior = topBehaviors[params.dataIndex]
            return `${behavior.percentage.toFixed(1)}%`
          },
          fontSize: 10,
          color: '#666'
        }
      }
    ],
    animationEasing: 'elasticOut',
    animationDelayUpdate: (idx: number) => idx * 5
  }
  
  chartInstance.setOption(option, true)
}

const getColor = (index: number, opacity: number = 1) => {
  const colors = [
    '#409eff', '#67c23a', '#e6a23c', '#f56c6c', 
    '#909399', '#c71585', '#ff6347', '#32cd32',
    '#1e90ff', '#ff69b4'
  ]
  const color = colors[index % colors.length]
  
  if (opacity < 1) {
    // 转换为rgba格式
    const hex = color.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    return `rgba(${r}, ${g}, ${b}, ${opacity})`
  }
  
  return color
}

const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}分钟`
  } else {
    return `${Math.round(seconds / 3600)}小时`
  }
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
.user-behavior-chart {
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