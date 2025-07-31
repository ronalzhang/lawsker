<template>
  <RealtimeChart
    :option="chartOption"
    :width="width"
    :height="height"
    :loading="loading"
    :error="error"
    :realtime="realtime"
    :realtime-interval="realtimeInterval"
    :max-data-points="maxDataPoints"
    @chart-ready="handleChartReady"
    @chart-click="handleChartClick"
    @retry="handleRetry"
  />
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import RealtimeChart from '@/components/common/RealtimeChart.vue'
import type { EChartsOption } from 'echarts'

interface DataPoint {
  name?: string
  value: number | [number, number] | [string, number]
  itemStyle?: any
}

interface Series {
  name: string
  data: DataPoint[]
  color?: string
  type?: 'line' | 'bar'
  smooth?: boolean
  areaStyle?: any
  lineStyle?: any
  symbol?: string
  symbolSize?: number
}

interface Props {
  data: Series[]
  xAxisData?: string[]
  title?: string
  subtitle?: string
  width?: string
  height?: string
  loading?: boolean
  error?: string
  smooth?: boolean
  area?: boolean
  stack?: boolean
  realtime?: boolean
  realtimeInterval?: number
  maxDataPoints?: number
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  showDataZoom?: boolean
  colors?: string[]
  yAxisName?: string
  xAxisName?: string
  yAxisFormatter?: (value: any) => string
  tooltipFormatter?: (params: any) => string
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  loading: false,
  error: '',
  smooth: false,
  area: false,
  stack: false,
  realtime: false,
  realtimeInterval: 1000,
  maxDataPoints: 100,
  showGrid: true,
  showLegend: true,
  showTooltip: true,
  showDataZoom: false,
  colors: () => ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
})

const emit = defineEmits<{
  'chart-ready': [chart: any]
  'chart-click': [params: any]
  'retry': []
}>()

const chartOption = computed<EChartsOption>(() => {
  const option: EChartsOption = {
    color: props.colors,
    title: props.title ? {
      text: props.title,
      subtext: props.subtitle,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#666'
      }
    } : undefined,
    
    tooltip: props.showTooltip ? {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: props.tooltipFormatter
    } : undefined,
    
    legend: props.showLegend ? {
      data: props.data.map(s => s.name),
      bottom: 0
    } : undefined,
    
    grid: props.showGrid ? {
      left: '3%',
      right: '4%',
      bottom: props.showLegend ? '10%' : '3%',
      containLabel: true
    } : undefined,
    
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.xAxisData,
      name: props.xAxisName,
      nameLocation: 'middle',
      nameGap: 25,
      axisLine: {
        lineStyle: {
          color: '#d4d7de'
        }
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#606266'
      }
    },
    
    yAxis: {
      type: 'value',
      name: props.yAxisName,
      nameLocation: 'middle',
      nameGap: 40,
      nameRotate: 90,
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#606266',
        formatter: props.yAxisFormatter
      },
      splitLine: {
        lineStyle: {
          color: '#f0f2f5'
        }
      }
    },
    
    dataZoom: props.showDataZoom ? [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100,
        height: 30,
        bottom: 30
      }
    ] : undefined,
    
    series: props.data.map((series, index) => ({
      name: series.name,
      type: series.type || 'line',
      data: series.data,
      smooth: series.smooth ?? props.smooth,
      stack: props.stack ? 'total' : undefined,
      areaStyle: props.area || series.areaStyle ? (series.areaStyle || {}) : undefined,
      lineStyle: series.lineStyle || {
        width: 2
      },
      symbol: series.symbol || 'circle',
      symbolSize: series.symbolSize || 4,
      itemStyle: series.itemStyle || {
        color: series.color || props.colors[index % props.colors.length]
      },
      emphasis: {
        focus: 'series'
      },
      animationDelay: index * 100
    }))
  }
  
  return option
})

const handleChartReady = (chart: any) => {
  emit('chart-ready', chart)
}

const handleChartClick = (params: any) => {
  emit('chart-click', params)
}

const handleRetry = () => {
  emit('retry')
}

// 监听数据变化
watch(() => props.data, () => {
  // 数据变化时的处理逻辑
}, { deep: true })
</script>