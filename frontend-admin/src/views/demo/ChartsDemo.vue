<template>
  <div class="charts-demo">
    <el-card class="demo-card">
      <template #header>
        <div class="card-header">
          <span>实时图表组件演示</span>
          <div class="header-controls">
            <el-switch
              v-model="realtimeEnabled"
              active-text="实时更新"
              @change="toggleRealtime"
            />
            <el-button type="primary" @click="exportAllCharts">
              导出所有图表
            </el-button>
          </div>
        </div>
      </template>

      <div class="demo-section">
        <h3>折线图</h3>
        <p>支持实时数据更新、平滑曲线、区域填充等功能。</p>
        
        <div class="chart-controls">
          <el-button @click="addLineData">添加数据点</el-button>
          <el-button @click="exportChart('line')">导出图表</el-button>
          <el-switch v-model="lineChartSmooth" active-text="平滑曲线" />
          <el-switch v-model="lineChartArea" active-text="区域填充" />
        </div>
        
        <LineChart
          ref="lineChartRef"
          :data="lineChartData"
          :x-axis-data="lineChartXAxis"
          title="访问量趋势"
          subtitle="最近24小时"
          :height="'350px'"
          :smooth="lineChartSmooth"
          :area="lineChartArea"
          :realtime="realtimeEnabled"
          :realtime-interval="2000"
          :show-data-zoom="true"
          y-axis-name="访问量"
          x-axis-name="时间"
          @chart-ready="(chart) => charts.line = chart"
          @chart-click="handleChartClick"
        />
      </div>

      <div class="demo-section">
        <h3>柱状图</h3>
        <p>支持水平/垂直显示、堆叠模式、分组显示等。</p>
        
        <div class="chart-controls">
          <el-button @click="refreshBarData">刷新数据</el-button>
          <el-button @click="exportChart('bar')">导出图表</el-button>
          <el-switch v-model="barChartHorizontal" active-text="水平显示" />
          <el-switch v-model="barChartStack" active-text="堆叠模式" />
        </div>
        
        <BarChart
          ref="barChartRef"
          :data="barChartData"
          :x-axis-data="barChartXAxis"
          title="部门业绩统计"
          subtitle="本月数据"
          :height="'350px'"
          :horizontal="barChartHorizontal"
          :stack="barChartStack"
          :show-data-zoom="true"
          y-axis-name="业绩"
          x-axis-name="部门"
          @chart-ready="(chart) => charts.bar = chart"
          @chart-click="handleChartClick"
        />
      </div>

      <div class="demo-section">
        <h3>饼图</h3>
        <p>支持环形图、玫瑰图、标签显示等多种样式。</p>
        
        <div class="chart-controls">
          <el-button @click="refreshPieData">刷新数据</el-button>
          <el-button @click="exportChart('pie')">导出图表</el-button>
          <el-switch v-model="pieChartDoughnut" active-text="环形图" />
          <el-switch v-model="pieChartRose" active-text="玫瑰图" />
        </div>
        
        <PieChart
          ref="pieChartRef"
          :data="pieChartData"
          title="用户来源分布"
          subtitle="最近30天"
          :height="'400px'"
          :doughnut="pieChartDoughnut"
          :rose="pieChartRose"
          @chart-ready="(chart) => charts.pie = chart"
          @chart-click="handleChartClick"
        />
      </div>

      <div class="demo-section">
        <h3>组合图表</h3>
        <p>展示多种图表类型的组合使用。</p>
        
        <div class="chart-controls">
          <el-button @click="refreshComboData">刷新数据</el-button>
          <el-button @click="exportChart('combo')">导出图表</el-button>
        </div>
        
        <RealtimeChart
          ref="comboChartRef"
          :option="comboChartOption"
          :height="'400px'"
          :realtime="realtimeEnabled"
          @chart-ready="(chart) => charts.combo = chart"
          @chart-click="handleChartClick"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import RealtimeChart from '@/components/common/RealtimeChart.vue'
import { DataExporter } from '@/utils/export'
import type { ECharts, EChartsOption } from 'echarts'

// 图表引用
const lineChartRef = ref()
const barChartRef = ref()
const pieChartRef = ref()
const comboChartRef = ref()

// 图表实例
const charts = reactive<Record<string, ECharts>>({})

// 控制状态
const realtimeEnabled = ref(false)
const lineChartSmooth = ref(true)
const lineChartArea = ref(false)
const barChartHorizontal = ref(false)
const barChartStack = ref(false)
const pieChartDoughnut = ref(false)
const pieChartRose = ref(false)

// 折线图数据
const lineChartData = ref([
  {
    name: 'PC端',
    data: [] as Array<[number, number]>,
    color: '#5470c6'
  },
  {
    name: '移动端',
    data: [] as Array<[number, number]>,
    color: '#91cc75'
  }
])

const lineChartXAxis = ref<string[]>([])

// 柱状图数据
const barChartData = ref([
  {
    name: '本月',
    data: [
      { name: '技术部', value: 120 },
      { name: '产品部', value: 200 },
      { name: '运营部', value: 150 },
      { name: '市场部', value: 80 },
      { name: '销售部', value: 170 }
    ],
    color: '#5470c6'
  },
  {
    name: '上月',
    data: [
      { name: '技术部', value: 100 },
      { name: '产品部', value: 180 },
      { name: '运营部', value: 130 },
      { name: '市场部', value: 70 },
      { name: '销售部', value: 160 }
    ],
    color: '#91cc75'
  }
])

const barChartXAxis = ref(['技术部', '产品部', '运营部', '市场部', '销售部'])

// 饼图数据
const pieChartData = ref([
  { name: '直接访问', value: 335 },
  { name: '邮件营销', value: 310 },
  { name: '联盟广告', value: 234 },
  { name: '视频广告', value: 135 },
  { name: '搜索引擎', value: 1548 }
])

// 组合图表配置
const comboChartOption = computed<EChartsOption>(() => ({
  title: {
    text: '销售数据分析',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
    }
  },
  legend: {
    data: ['销售额', '利润率'],
    bottom: 0
  },
  xAxis: {
    type: 'category',
    data: ['1月', '2月', '3月', '4月', '5月', '6月']
  },
  yAxis: [
    {
      type: 'value',
      name: '销售额',
      position: 'left',
      axisLabel: {
        formatter: '{value} 万'
      }
    },
    {
      type: 'value',
      name: '利润率',
      position: 'right',
      axisLabel: {
        formatter: '{value} %'
      }
    }
  ],
  series: [
    {
      name: '销售额',
      type: 'bar',
      data: [120, 200, 150, 80, 170, 110],
      itemStyle: {
        color: '#5470c6'
      }
    },
    {
      name: '利润率',
      type: 'line',
      yAxisIndex: 1,
      data: [15, 23, 18, 12, 25, 20],
      itemStyle: {
        color: '#91cc75'
      },
      smooth: true
    }
  ]
}))

// 生成折线图数据
const generateLineData = () => {
  const now = Date.now()
  const data1: Array<[number, number]> = []
  const data2: Array<[number, number]> = []
  const xAxis: string[] = []

  for (let i = 23; i >= 0; i--) {
    const time = now - i * 60 * 60 * 1000
    const hour = new Date(time).getHours()
    
    data1.push([time, Math.floor(Math.random() * 1000) + 500])
    data2.push([time, Math.floor(Math.random() * 800) + 300])
    xAxis.push(`${hour}:00`)
  }

  lineChartData.value[0].data = data1
  lineChartData.value[1].data = data2
  lineChartXAxis.value = xAxis
}

// 添加折线图数据点
const addLineData = () => {
  const now = Date.now()
  const hour = new Date(now).getHours()
  
  lineChartData.value[0].data.push([now, Math.floor(Math.random() * 1000) + 500])
  lineChartData.value[1].data.push([now, Math.floor(Math.random() * 800) + 300])
  lineChartXAxis.value.push(`${hour}:${new Date(now).getMinutes()}`)
  
  // 限制数据点数量
  if (lineChartData.value[0].data.length > 50) {
    lineChartData.value[0].data.shift()
    lineChartData.value[1].data.shift()
    lineChartXAxis.value.shift()
  }
}

// 刷新柱状图数据
const refreshBarData = () => {
  barChartData.value.forEach(series => {
    series.data.forEach(item => {
      item.value = Math.floor(Math.random() * 200) + 50
    })
  })
}

// 刷新饼图数据
const refreshPieData = () => {
  pieChartData.value.forEach(item => {
    item.value = Math.floor(Math.random() * 1000) + 100
  })
}

// 刷新组合图数据
const refreshComboData = () => {
  // 触发响应式更新
  const newOption = { ...comboChartOption.value }
  if (newOption.series) {
    (newOption.series as any[]).forEach(series => {
      if (series.type === 'bar') {
        series.data = series.data.map(() => Math.floor(Math.random() * 200) + 50)
      } else if (series.type === 'line') {
        series.data = series.data.map(() => Math.floor(Math.random() * 30) + 10)
      }
    })
  }
}

// 切换实时更新
const toggleRealtime = (enabled: boolean) => {
  if (enabled) {
    ElMessage.success('实时更新已启用')
  } else {
    ElMessage.info('实时更新已停用')
  }
}

// 导出单个图表
const exportChart = async (type: string) => {
  const chart = charts[type]
  if (!chart) {
    ElMessage.warning('图表未准备就绪')
    return
  }

  try {
    await DataExporter.exportChartAsImage(chart, {
      filename: `${type}_chart_${Date.now()}.png`,
      format: 'png',
      backgroundColor: '#ffffff',
      pixelRatio: 2
    })
  } catch (error) {
    console.error('Chart export failed:', error)
  }
}

// 导出所有图表
const exportAllCharts = async () => {
  const chartList = Object.entries(charts)
    .filter(([_, chart]) => chart)
    .map(([name, chart]) => ({ chart, name }))

  if (chartList.length === 0) {
    ElMessage.warning('没有可导出的图表')
    return
  }

  try {
    await DataExporter.exportMultipleCharts(chartList, {
      format: 'png',
      backgroundColor: '#ffffff',
      pixelRatio: 2
    })
  } catch (error) {
    console.error('Multiple charts export failed:', error)
  }
}

// 图表点击事件
const handleChartClick = (params: any) => {
  console.log('Chart clicked:', params)
  ElMessage.info(`点击了: ${params.name || params.seriesName}`)
}

// 初始化
onMounted(() => {
  generateLineData()
})
</script>

<style scoped>
.charts-demo {
  padding: 20px;
}

.demo-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.demo-section {
  margin-bottom: 40px;
}

.demo-section h3 {
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.demo-section p {
  margin-bottom: 16px;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-controls {
    width: 100%;
    justify-content: center;
  }
  
  .chart-controls {
    justify-content: center;
  }
}
</style>