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
import { computed } from 'vue'
import RealtimeChart from '@/components/common/RealtimeChart.vue'
import type { EChartsOption } from 'echarts'

interface DataPoint {
  name?: string
  value: number
  itemStyle?: any
}

interface Series {
  name: string
  data: DataPoint[]
  color?: string
  barWidth?: string | number
  barMaxWidth?: string | number
  barGap?: string
  barCategoryGap?: string
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
  horizontal?: boolean
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
  barWidth?: string | number
  barMaxWidth?: string | number
  barGap?: string
  barCategoryGap?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  loading: false,
  error: '',
  horizontal: false,
  stack: false,
  realtime: false,
  realtimeInterval: 1000,
  maxDataPoints: 100,
  showGrid: true,
  showLegend: true,
  showTooltip: true,
  showDataZoom: false,
  colors: () => ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'],
  barWidth: 'auto',
  barGap: '10%',
  barCategoryGap: '20%'
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
        type: 'shadow'
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
      type: props.horizontal ? 'value' : 'category',
      data: props.horizontal ? undefined : props.xAxisData,
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
        color: '#606266',
        formatter: props.horizontal ? props.yAxisFormatter : undefined
      },
      splitLine: props.horizontal ? {
        lineStyle: {
          color: '#f0f2f5'
        }
      } : undefined
    },
    
    yAxis: {
      type: props.horizontal ? 'category' : 'value',
      data: props.horizontal ? props.xAxisData : undefined,
      name: props.yAxisName,
      nameLocation: 'middle',
      nameGap: 40,
      nameRotate: props.horizontal ? 0 : 90,
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#606266',
        formatter: props.horizontal ? undefined : props.yAxisFormatter
      },
      splitLine: props.horizontal ? undefined : {
        lineStyle: {
          color: '#f0f2f5'
        }
      }
    },
    
    dataZoom: props.showDataZoom ? [
      {
        type: 'inside',
        start: 0,
        end: 100,
        orient: props.horizontal ? 'vertical' : 'horizontal'
      },
      {
        start: 0,
        end: 100,
        height: props.horizontal ? undefined : 30,
        width: props.horizontal ? 30 : undefined,
        bottom: props.horizontal ? undefined : 30,
        right: props.horizontal ? 30 : undefined,
        orient: props.horizontal ? 'vertical' : 'horizontal'
      }
    ] : undefined,
    
    series: props.data.map((series, index) => ({
      name: series.name,
      type: 'bar',
      data: series.data,
      stack: props.stack ? 'total' : undefined,
      barWidth: series.barWidth || props.barWidth,
      barMaxWidth: series.barMaxWidth || props.barMaxWidth,
      barGap: series.barGap || props.barGap,
      barCategoryGap: series.barCategoryGap || props.barCategoryGap,
      itemStyle: {
        color: series.color || props.colors[index % props.colors.length],
        borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
      },
      emphasis: {
        focus: 'series',
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      animationDelay: index * 100,
      animationDuration: 800,
      animationEasing: 'elasticOut'
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
</script>