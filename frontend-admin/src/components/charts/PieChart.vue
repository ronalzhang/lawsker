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
  name: string
  value: number
  itemStyle?: any
  label?: any
  labelLine?: any
}

interface Props {
  data: DataPoint[]
  title?: string
  subtitle?: string
  width?: string
  height?: string
  loading?: boolean
  error?: string
  doughnut?: boolean
  rose?: boolean
  realtime?: boolean
  realtimeInterval?: number
  maxDataPoints?: number
  showLegend?: boolean
  showTooltip?: boolean
  showLabel?: boolean
  colors?: string[]
  radius?: string | [string, string]
  center?: [string, string]
  roseType?: 'radius' | 'area'
  tooltipFormatter?: (params: any) => string
  labelFormatter?: (params: any) => string
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  loading: false,
  error: '',
  doughnut: false,
  rose: false,
  realtime: false,
  realtimeInterval: 1000,
  maxDataPoints: 100,
  showLegend: true,
  showTooltip: true,
  showLabel: true,
  colors: () => ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'],
  radius: () => props.doughnut ? ['40%', '70%'] : '70%',
  center: () => ['50%', '50%'],
  roseType: 'radius'
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
      top: '5%',
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
      trigger: 'item',
      formatter: props.tooltipFormatter || '{a} <br/>{b}: {c} ({d}%)'
    } : undefined,
    
    legend: props.showLegend ? {
      type: 'scroll',
      orient: 'vertical',
      right: '5%',
      top: 'center',
      data: props.data.map(item => item.name),
      textStyle: {
        fontSize: 12
      }
    } : undefined,
    
    series: [
      {
        name: props.title || '数据',
        type: 'pie',
        radius: props.radius,
        center: props.center,
        data: props.data.map((item, index) => ({
          ...item,
          itemStyle: item.itemStyle || {
            color: props.colors[index % props.colors.length]
          }
        })),
        roseType: props.rose ? props.roseType : undefined,
        label: props.showLabel ? {
          show: true,
          formatter: props.labelFormatter || '{b}: {d}%',
          fontSize: 12,
          fontWeight: 'bold'
        } : {
          show: false
        },
        labelLine: props.showLabel ? {
          show: true,
          length: 15,
          length2: 10,
          smooth: true
        } : {
          show: false
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          },
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: (idx: number) => Math.random() * 200
      }
    ]
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