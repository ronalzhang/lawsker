<template>
  <div class="export-demo">
    <el-card class="demo-card">
      <template #header>
        <div class="card-header">
          <span>数据导出功能演示</span>
          <el-button type="primary" @click="generateSampleData">
            生成示例数据
          </el-button>
        </div>
      </template>

      <div class="demo-section">
        <h3>表格数据导出</h3>
        <p>支持CSV、Excel、JSON等多种格式的数据导出。</p>
        
        <div class="export-controls">
          <el-button @click="exportData('csv')" :loading="exporting.csv">
            <el-icon><Download /></el-icon>
            导出CSV
          </el-button>
          <el-button @click="exportData('excel')" :loading="exporting.excel">
            <el-icon><Download /></el-icon>
            导出Excel
          </el-button>
          <el-button @click="exportData('json')" :loading="exporting.json">
            <el-icon><Download /></el-icon>
            导出JSON
          </el-button>
        </div>

        <EnhancedVirtualTable
          :data="tableData"
          :columns="tableColumns"
          :container-height="300"
          :show-pagination="true"
          :page-size="20"
          @export="handleTableExport"
        >
          <template #avatar="{ row }">
            <el-avatar :size="32" :src="row.avatar">
              {{ row.name.charAt(0) }}
            </el-avatar>
          </template>
          
          <template #status="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
          
          <template #salary="{ row }">
            ¥{{ formatNumber(row.salary) }}
          </template>
        </EnhancedVirtualTable>
      </div>

      <div class="demo-section">
        <h3>图表导出</h3>
        <p>支持PNG、JPEG、SVG等格式的图表导出。</p>
        
        <div class="export-controls">
          <el-button @click="exportChart('png')" :loading="exporting.chartPng">
            <el-icon><Picture /></el-icon>
            导出PNG
          </el-button>
          <el-button @click="exportChart('jpeg')" :loading="exporting.chartJpeg">
            <el-icon><Picture /></el-icon>
            导出JPEG
          </el-button>
          <el-button @click="exportChart('svg')" :loading="exporting.chartSvg">
            <el-icon><Picture /></el-icon>
            导出SVG
          </el-button>
        </div>

        <div class="chart-container">
          <LineChart
            ref="chartRef"
            :data="chartData"
            :x-axis-data="chartXAxis"
            title="月度销售趋势"
            subtitle="2024年数据"
            :height="'300px'"
            :smooth="true"
            :area="true"
            @chart-ready="handleChartReady"
          />
        </div>
      </div>

      <div class="demo-section">
        <h3>批量导出</h3>
        <p>支持批量导出多个图表和数据表。</p>
        
        <div class="export-controls">
          <el-button @click="exportMultipleCharts" :loading="exporting.multiple">
            <el-icon><FolderOpened /></el-icon>
            批量导出图表
          </el-button>
          <el-button @click="exportReport" :loading="exporting.report">
            <el-icon><Document /></el-icon>
            导出完整报表
          </el-button>
        </div>

        <div class="charts-grid">
          <div class="chart-item">
            <BarChart
              ref="barChartRef"
              :data="barChartData"
              :x-axis-data="barChartXAxis"
              title="部门业绩"
              :height="'250px'"
              @chart-ready="(chart) => charts.bar = chart"
            />
          </div>
          
          <div class="chart-item">
            <PieChart
              ref="pieChartRef"
              :data="pieChartData"
              title="用户分布"
              :height="'250px'"
              @chart-ready="(chart) => charts.pie = chart"
            />
          </div>
        </div>
      </div>

      <div class="demo-section">
        <h3>自定义导出选项</h3>
        <p>配置导出参数，如文件名、格式、编码等。</p>
        
        <el-form :model="exportOptions" label-width="120px" class="export-form">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="文件名前缀">
                <el-input v-model="exportOptions.filename" placeholder="export" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="日期格式">
                <el-select v-model="exportOptions.dateFormat">
                  <el-option label="YYYY-MM-DD" value="YYYY-MM-DD" />
                  <el-option label="YYYY/MM/DD" value="YYYY/MM/DD" />
                  <el-option label="DD/MM/YYYY" value="DD/MM/YYYY" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="包含表头">
                <el-switch v-model="exportOptions.includeHeaders" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="图片分辨率">
                <el-select v-model="exportOptions.pixelRatio">
                  <el-option label="1x" :value="1" />
                  <el-option label="2x" :value="2" />
                  <el-option label="3x" :value="3" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item>
            <el-button type="primary" @click="exportWithOptions">
              使用自定义选项导出
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Picture, FolderOpened, Document } from '@element-plus/icons-vue'
import EnhancedVirtualTable from '@/components/common/EnhancedVirtualTable.vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import { DataExporter } from '@/utils/export'
import type { ECharts } from 'echarts'

// 组件引用
const chartRef = ref()
const barChartRef = ref()
const pieChartRef = ref()

// 图表实例
const charts = reactive<Record<string, ECharts>>({})
const mainChart = ref<ECharts>()

// 导出状态
const exporting = reactive({
  csv: false,
  excel: false,
  json: false,
  chartPng: false,
  chartJpeg: false,
  chartSvg: false,
  multiple: false,
  report: false
})

// 导出选项
const exportOptions = reactive({
  filename: 'export',
  dateFormat: 'YYYY-MM-DD',
  includeHeaders: true,
  pixelRatio: 2
})

// 表格数据
const tableData = ref<any[]>([])
const tableColumns = [
  { key: 'id', title: 'ID', width: '80px', sortable: true },
  { key: 'avatar', title: '头像', width: '80px' },
  { key: 'name', title: '姓名', width: '120px', sortable: true },
  { key: 'email', title: '邮箱', width: '200px', sortable: true },
  { key: 'department', title: '部门', width: '120px', sortable: true },
  { key: 'position', title: '职位', width: '120px', sortable: true },
  { key: 'salary', title: '薪资', width: '120px', sortable: true },
  { key: 'status', title: '状态', width: '100px', sortable: true },
  { key: 'joinDate', title: '入职日期', width: '120px', sortable: true }
]

// 图表数据
const chartData = ref([
  {
    name: '销售额',
    data: [
      { name: '1月', value: 120 },
      { name: '2月', value: 200 },
      { name: '3月', value: 150 },
      { name: '4月', value: 80 },
      { name: '5月', value: 170 },
      { name: '6月', value: 110 }
    ],
    color: '#5470c6'
  },
  {
    name: '利润',
    data: [
      { name: '1月', value: 60 },
      { name: '2月', value: 90 },
      { name: '3月', value: 75 },
      { name: '4月', value: 40 },
      { name: '5月', value: 85 },
      { name: '6月', value: 55 }
    ],
    color: '#91cc75'
  }
])

const chartXAxis = ref(['1月', '2月', '3月', '4月', '5月', '6月'])

const barChartData = ref([
  {
    name: '业绩',
    data: [
      { name: '技术部', value: 120 },
      { name: '产品部', value: 200 },
      { name: '运营部', value: 150 },
      { name: '市场部', value: 80 }
    ]
  }
])

const barChartXAxis = ref(['技术部', '产品部', '运营部', '市场部'])

const pieChartData = ref([
  { name: '新用户', value: 335 },
  { name: '老用户', value: 310 },
  { name: '活跃用户', value: 234 },
  { name: '沉默用户', value: 135 }
])

// 生成示例数据
const generateSampleData = () => {
  const departments = ['技术部', '产品部', '运营部', '市场部', '人事部']
  const positions = ['工程师', '产品经理', '运营专员', '市场专员', '人事专员']
  const statuses = ['active', 'inactive', 'pending']
  
  const data = Array.from({ length: 100 }, (_, index) => ({
    id: index + 1,
    name: `员工${index + 1}`,
    email: `employee${index + 1}@company.com`,
    department: departments[Math.floor(Math.random() * departments.length)],
    position: positions[Math.floor(Math.random() * positions.length)],
    salary: Math.floor(Math.random() * 50000) + 50000,
    status: statuses[Math.floor(Math.random() * statuses.length)],
    joinDate: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${index}`
  }))
  
  tableData.value = data
  ElMessage.success('示例数据生成完成')
}

// 导出表格数据
const exportData = async (format: 'csv' | 'excel' | 'json') => {
  if (tableData.value.length === 0) {
    ElMessage.warning('请先生成示例数据')
    return
  }

  exporting[format] = true
  
  try {
    const filename = `${exportOptions.filename}_${Date.now()}`
    
    switch (format) {
      case 'csv':
        await DataExporter.exportToCsv(tableData.value, {
          filename: `${filename}.csv`,
          includeHeaders: exportOptions.includeHeaders,
          dateFormat: exportOptions.dateFormat
        })
        break
      case 'excel':
        await DataExporter.exportToExcel(tableData.value, {
          filename: `${filename}.xlsx`,
          sheetName: '员工数据',
          includeHeaders: exportOptions.includeHeaders,
          dateFormat: exportOptions.dateFormat
        })
        break
      case 'json':
        await DataExporter.exportToJson(tableData.value, {
          filename: `${filename}.json`
        })
        break
    }
  } catch (error) {
    console.error(`${format.toUpperCase()} export failed:`, error)
  } finally {
    exporting[format] = false
  }
}

// 导出图表
const exportChart = async (format: 'png' | 'jpeg' | 'svg') => {
  if (!mainChart.value) {
    ElMessage.warning('图表未准备就绪')
    return
  }

  const loadingKey = `chart${format.charAt(0).toUpperCase() + format.slice(1)}` as keyof typeof exporting
  exporting[loadingKey] = true

  try {
    const filename = `${exportOptions.filename}_chart_${Date.now()}.${format}`
    
    if (format === 'svg') {
      await DataExporter.exportChartAsSvg(mainChart.value, { filename })
    } else {
      await DataExporter.exportChartAsImage(mainChart.value, {
        filename,
        format,
        pixelRatio: exportOptions.pixelRatio,
        backgroundColor: '#ffffff'
      })
    }
  } catch (error) {
    console.error(`Chart ${format} export failed:`, error)
  } finally {
    exporting[loadingKey] = false
  }
}

// 批量导出图表
const exportMultipleCharts = async () => {
  const chartList = Object.entries(charts)
    .filter(([_, chart]) => chart)
    .map(([name, chart]) => ({ chart, name }))

  if (chartList.length === 0) {
    ElMessage.warning('没有可导出的图表')
    return
  }

  exporting.multiple = true

  try {
    await DataExporter.exportMultipleCharts(chartList, {
      format: 'png',
      pixelRatio: exportOptions.pixelRatio,
      backgroundColor: '#ffffff'
    })
  } catch (error) {
    console.error('Multiple charts export failed:', error)
  } finally {
    exporting.multiple = false
  }
}

// 导出完整报表
const exportReport = async () => {
  if (tableData.value.length === 0) {
    ElMessage.warning('请先生成示例数据')
    return
  }

  exporting.report = true

  try {
    const chartList = Object.entries(charts)
      .filter(([_, chart]) => chart)
      .map(([name, chart]) => ({ chart, name }))

    await DataExporter.exportReport({
      title: '员工数据分析报表',
      description: '包含员工基本信息和相关统计图表',
      tables: [
        {
          name: '员工数据',
          data: tableData.value,
          headers: tableColumns.map(col => col.key)
        }
      ],
      charts: chartList
    }, {
      filename: `${exportOptions.filename}_report_${Date.now()}.xlsx`
    })
  } catch (error) {
    console.error('Report export failed:', error)
  } finally {
    exporting.report = false
  }
}

// 使用自定义选项导出
const exportWithOptions = async () => {
  if (tableData.value.length === 0) {
    ElMessage.warning('请先生成示例数据')
    return
  }

  try {
    await DataExporter.exportToExcel(tableData.value, {
      filename: `${exportOptions.filename}_custom_${Date.now()}.xlsx`,
      sheetName: '自定义导出',
      includeHeaders: exportOptions.includeHeaders,
      dateFormat: exportOptions.dateFormat
    })
  } catch (error) {
    console.error('Custom export failed:', error)
  }
}

// 表格导出处理
const handleTableExport = () => {
  exportData('excel')
}

// 图表准备就绪
const handleChartReady = (chart: ECharts) => {
  mainChart.value = chart
}

// 工具函数
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    active: 'success',
    inactive: 'danger',
    pending: 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    active: '在职',
    inactive: '离职',
    pending: '待入职'
  }
  return textMap[status] || status
}

const formatNumber = (num: number) => {
  return num.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  generateSampleData()
})
</script>

<style scoped>
.export-demo {
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

.export-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
  flex-wrap: wrap;
}

.chart-container {
  margin-top: 16px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-top: 16px;
}

.chart-item {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 16px;
}

.export-form {
  max-width: 600px;
  margin-top: 16px;
  padding: 20px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .export-controls {
    justify-content: center;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>