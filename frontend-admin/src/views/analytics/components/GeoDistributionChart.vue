<template>
  <div class="geo-distribution-chart">
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
    country: string
    region: string
    city: string
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
  
  // 按国家聚合数据
  const countryData = new Map()
  props.data.forEach(item => {
    const country = item.country || '未知'
    if (countryData.has(country)) {
      countryData.set(country, countryData.get(country) + item.count)
    } else {
      countryData.set(country, item.count)
    }
  })
  
  // 转换为图表数据
  const chartData = Array.from(countryData.entries())
    .map(([country, count]) => ({
      name: country,
      value: count
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10) // 只显示前10个国家
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const total = chartData.reduce((sum, item) => sum + item.value, 0)
        const percentage = ((params.value / total) * 100).toFixed(1)
        return `${params.marker}${params.name}: ${params.value.toLocaleString()} (${percentage}%)`
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
      data: chartData.map(item => item.name),
      axisLabel: {
        interval: 0,
        formatter: (value: string) => {
          // 限制标签长度
          return value.length > 8 ? value.substring(0, 8) + '...' : value
        }
      }
    },
    series: [
      {
        name: '访问量',
        type: 'bar',
        data: chartData.map((item, index) => ({
          value: item.value,
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
        animationDelay: (idx: number) => idx * 100
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
.geo-distribution-chart {
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