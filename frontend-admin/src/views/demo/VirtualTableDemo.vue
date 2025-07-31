<template>
  <div class="virtual-table-demo">
    <el-card class="demo-card">
      <template #header>
        <div class="card-header">
          <span>虚拟滚动表格演示</span>
          <el-button type="primary" @click="generateLargeDataset">
            生成大数据集 (10万条)
          </el-button>
        </div>
      </template>

      <div class="demo-section">
        <h3>基础虚拟表格</h3>
        <p>支持大数据量渲染，只渲染可见区域的行，提供流畅的滚动体验。</p>
        
        <VirtualTable
          :data="basicData"
          :columns="basicColumns"
          :container-height="300"
          :loading="basicLoading"
          @row-click="handleRowClick"
          @sort-change="handleSortChange"
        >
          <template #status="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
          
          <template #actions="{ row }">
            <el-button size="small" type="primary" @click="editRow(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteRow(row)">
              删除
            </el-button>
          </template>
        </VirtualTable>
      </div>

      <div class="demo-section">
        <h3>增强型虚拟表格</h3>
        <p>包含搜索、筛选、排序、分页、导出等完整功能。</p>
        
        <EnhancedVirtualTable
          :data="enhancedData"
          :columns="enhancedColumns"
          :filters="tableFilters"
          :container-height="400"
          :loading="enhancedLoading"
          :remote="false"
          :show-pagination="true"
          :page-size="50"
          @row-click="handleRowClick"
          @sort-change="handleSortChange"
          @search="handleSearch"
          @filter-change="handleFilterChange"
          @refresh="handleRefresh"
          @export="handleExport"
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
          
          <template #progress="{ row }">
            <el-progress
              :percentage="row.progress"
              :color="getProgressColor(row.progress)"
              :stroke-width="8"
            />
          </template>
          
          <template #actions="{ row }">
            <el-button size="small" type="primary" @click="editRow(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteRow(row)">
              删除
            </el-button>
          </template>
        </EnhancedVirtualTable>
      </div>

      <div class="demo-section">
        <h3>使用 Composable 的表格</h3>
        <p>使用 useVirtualTable composable 管理表格状态和数据操作。</p>
        
        <div class="composable-controls">
          <el-button @click="tableState.refresh()">刷新</el-button>
          <el-button @click="tableState.selectAll()">全选</el-button>
          <el-button @click="tableState.clearSelection()">清除选择</el-button>
          <el-button @click="tableState.exportData('csv')">导出CSV</el-button>
          <span class="selection-info">
            已选择 {{ tableState.hasSelection ? tableState.state.selectedRows.length : 0 }} 项
          </span>
        </div>
        
        <EnhancedVirtualTable
          :data="tableState.state.data"
          :columns="composableColumns"
          :loading="tableState.state.loading"
          :container-height="350"
          @row-click="handleComposableRowClick"
          @sort-change="tableState.sort"
          @search="tableState.search"
          @refresh="tableState.refresh"
          @export="() => tableState.exportData('csv')"
        >
          <template #name="{ row }">
            <div class="user-info">
              <el-avatar :size="24" :src="row.avatar">
                {{ row.name.charAt(0) }}
              </el-avatar>
              <span class="user-name">{{ row.name }}</span>
            </div>
          </template>
          
          <template #email="{ row }">
            <el-link :href="`mailto:${row.email}`" type="primary">
              {{ row.email }}
            </el-link>
          </template>
          
          <template #createdAt="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </EnhancedVirtualTable>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import VirtualTable from '@/components/common/VirtualTable.vue'
import EnhancedVirtualTable from '@/components/common/EnhancedVirtualTable.vue'
import { useVirtualTable, tableUtils } from '@/composables/useVirtualTable'

// 基础表格数据
const basicData = ref<any[]>([])
const basicLoading = ref(false)

const basicColumns = [
  { key: 'id', title: 'ID', width: '80px', sortable: true },
  { key: 'name', title: '姓名', width: '120px', sortable: true },
  { key: 'email', title: '邮箱', width: '200px' },
  { key: 'status', title: '状态', width: '100px', sortable: true },
  { key: 'actions', title: '操作', width: '150px' }
]

// 增强表格数据
const enhancedData = ref<any[]>([])
const enhancedLoading = ref(false)

const enhancedColumns = [
  { key: 'id', title: 'ID', width: '80px', sortable: true },
  { key: 'avatar', title: '头像', width: '80px' },
  { key: 'name', title: '姓名', width: '120px', sortable: true },
  { key: 'email', title: '邮箱', width: '200px', sortable: true },
  { key: 'department', title: '部门', width: '120px', sortable: true },
  { key: 'role', title: '角色', width: '100px', sortable: true },
  { key: 'status', title: '状态', width: '100px', sortable: true },
  { key: 'progress', title: '进度', width: '150px' },
  { key: 'createdAt', title: '创建时间', width: '180px', sortable: true },
  { key: 'actions', title: '操作', width: '150px' }
]

const tableFilters = [
  {
    key: 'status',
    label: '状态',
    type: 'select' as const,
    value: '',
    options: [
      { label: '全部', value: '' },
      { label: '活跃', value: 'active' },
      { label: '禁用', value: 'disabled' },
      { label: '待审核', value: 'pending' }
    ]
  },
  {
    key: 'department',
    label: '部门',
    type: 'select' as const,
    value: '',
    options: [
      { label: '全部', value: '' },
      { label: '技术部', value: '技术部' },
      { label: '产品部', value: '产品部' },
      { label: '运营部', value: '运营部' },
      { label: '市场部', value: '市场部' }
    ]
  },
  {
    key: 'createdAt',
    label: '创建时间',
    type: 'daterange' as const,
    value: [],
    props: {
      type: 'daterange',
      'range-separator': '至',
      'start-placeholder': '开始日期',
      'end-placeholder': '结束日期'
    }
  }
]

// Composable 表格
const composableColumns = [
  { key: 'id', title: 'ID', width: '80px', sortable: true },
  { key: 'name', title: '姓名', width: '150px', sortable: true },
  { key: 'email', title: '邮箱', width: '200px', sortable: true },
  { key: 'phone', title: '电话', width: '150px' },
  { key: 'company', title: '公司', width: '150px', sortable: true },
  { key: 'createdAt', title: '创建时间', width: '180px', sortable: true }
]

// 使用 composable
const tableState = useVirtualTable(
  async (params) => {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const mockData = generateMockData(1000)
    let filteredData = [...mockData]
    
    // 搜索
    if (params.search) {
      filteredData = filteredData.filter(item =>
        item.name.toLowerCase().includes(params.search.toLowerCase()) ||
        item.email.toLowerCase().includes(params.search.toLowerCase())
      )
    }
    
    // 排序
    if (params.sortBy) {
      filteredData.sort((a, b) => {
        const aVal = a[params.sortBy]
        const bVal = b[params.sortBy]
        const comparison = aVal > bVal ? 1 : -1
        return params.sortOrder === 'asc' ? comparison : -comparison
      })
    }
    
    // 分页
    const start = (params.page - 1) * params.pageSize
    const end = start + params.pageSize
    const pageData = filteredData.slice(start, end)
    
    return {
      data: pageData,
      total: filteredData.length
    }
  },
  { remote: true, defaultPageSize: 50 }
)

// 工具函数
const { formatDate } = tableUtils

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    active: 'success',
    disabled: 'danger',
    pending: 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    active: '活跃',
    disabled: '禁用',
    pending: '待审核'
  }
  return textMap[status] || status
}

const getProgressColor = (progress: number) => {
  if (progress < 30) return '#f56c6c'
  if (progress < 70) return '#e6a23c'
  return '#67c23a'
}

// 生成模拟数据
const generateMockData = (count: number) => {
  const departments = ['技术部', '产品部', '运营部', '市场部', '人事部']
  const roles = ['工程师', '产品经理', '运营专员', '市场专员', '人事专员']
  const statuses = ['active', 'disabled', 'pending']
  const companies = ['阿里巴巴', '腾讯', '百度', '字节跳动', '美团', '滴滴', '京东', '网易']
  
  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    name: `用户${index + 1}`,
    email: `user${index + 1}@example.com`,
    phone: `138${String(index).padStart(8, '0')}`,
    company: companies[Math.floor(Math.random() * companies.length)],
    department: departments[Math.floor(Math.random() * departments.length)],
    role: roles[Math.floor(Math.random() * roles.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    progress: Math.floor(Math.random() * 100),
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${index}`,
    createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString()
  }))
}

// 事件处理
const handleRowClick = (row: any, index: number) => {
  console.log('Row clicked:', row, index)
  ElMessage.info(`点击了第 ${index + 1} 行: ${row.name}`)
}

const handleSortChange = (column: string, order: 'asc' | 'desc') => {
  console.log('Sort changed:', column, order)
  ElMessage.info(`按 ${column} ${order === 'asc' ? '升序' : '降序'} 排序`)
}

const handleSearch = (query: string) => {
  console.log('Search:', query)
  ElMessage.info(`搜索: ${query}`)
}

const handleFilterChange = (filters: Record<string, any>) => {
  console.log('Filters changed:', filters)
  ElMessage.info('筛选条件已更新')
}

const handleRefresh = () => {
  console.log('Refresh triggered')
  ElMessage.success('数据已刷新')
}

const handleExport = () => {
  console.log('Export triggered')
  ElMessage.success('数据导出中...')
}

const handleComposableRowClick = (row: any, index: number) => {
  tableState.toggleRowSelection(row)
}

const editRow = (row: any) => {
  ElMessage.info(`编辑用户: ${row.name}`)
}

const deleteRow = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    ElMessage.success('删除成功')
  } catch {
    ElMessage.info('已取消删除')
  }
}

const generateLargeDataset = () => {
  basicLoading.value = true
  enhancedLoading.value = true
  
  setTimeout(() => {
    const largeData = generateMockData(100000)
    basicData.value = largeData.slice(0, 1000)
    enhancedData.value = largeData
    
    basicLoading.value = false
    enhancedLoading.value = false
    
    ElMessage.success('大数据集生成完成！')
  }, 1000)
}

// 初始化
onMounted(() => {
  const initialData = generateMockData(500)
  basicData.value = initialData.slice(0, 100)
  enhancedData.value = initialData
})
</script>

<style scoped>
.virtual-table-demo {
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

.composable-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
}

.selection-info {
  margin-left: auto;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-weight: 500;
}
</style>