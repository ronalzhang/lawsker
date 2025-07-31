<template>
  <div class="enhanced-virtual-table">
    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          class="search-input"
        />
        <el-button
          v-if="showRefresh"
          :icon="Refresh"
          @click="handleRefresh"
          :loading="refreshing"
        >
          刷新
        </el-button>
      </div>
      
      <div class="toolbar-right">
        <el-button
          v-if="showExport"
          :icon="Download"
          @click="handleExport"
          :loading="exporting"
        >
          导出
        </el-button>
        <el-dropdown v-if="showColumnSettings" @command="handleColumnCommand">
          <el-button :icon="Setting">
            列设置 <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="column in columns"
                :key="column.key"
                :command="{ action: 'toggle', column: column.key }"
              >
                <el-checkbox
                  :model-value="!hiddenColumns.includes(column.key)"
                  @change="toggleColumn(column.key)"
                >
                  {{ column.title }}
                </el-checkbox>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 过滤器 -->
    <div v-if="showFilters" class="table-filters">
      <div class="filter-row">
        <div
          v-for="filter in activeFilters"
          :key="filter.key"
          class="filter-item"
        >
          <label>{{ filter.label }}:</label>
          <component
            :is="getFilterComponent(filter.type)"
            v-model="filter.value"
            v-bind="filter.props"
            @change="handleFilterChange"
          />
        </div>
        <el-button
          v-if="hasActiveFilters"
          type="text"
          @click="clearFilters"
        >
          清除筛选
        </el-button>
      </div>
    </div>

    <!-- 虚拟表格 -->
    <VirtualTable
      :data="filteredData"
      :columns="visibleColumns"
      :row-height="rowHeight"
      :container-height="containerHeight"
      :row-key="rowKey"
      :loading="loading"
      :sort-by="sortBy"
      :sort-order="sortOrder"
      :selected-rows="selectedRows"
      @row-click="handleRowClick"
      @sort-change="handleSortChange"
      @selection-change="handleSelectionChange"
    >
      <!-- 传递所有插槽 -->
      <template v-for="(_, name) in $slots" #[name]="slotData">
        <slot :name="name" v-bind="slotData" />
      </template>
    </VirtualTable>

    <!-- 分页 -->
    <div v-if="showPagination" class="table-pagination">
      <div class="pagination-info">
        共 {{ totalCount }} 条记录，显示第 {{ (currentPage - 1) * pageSize + 1 }} - 
        {{ Math.min(currentPage * pageSize, totalCount) }} 条
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="totalCount"
        layout="sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Search, Refresh, Download, Setting, ArrowDown } from '@element-plus/icons-vue'
import VirtualTable from './VirtualTable.vue'
import { debounce } from 'lodash-es'

interface Column {
  key: string
  title: string
  width?: string
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, row: any, index: number) => any
}

interface Filter {
  key: string
  label: string
  type: 'input' | 'select' | 'date' | 'daterange'
  value: any
  options?: Array<{ label: string; value: any }>
  props?: Record<string, any>
}

interface Props {
  data: any[]
  columns: Column[]
  filters?: Filter[]
  rowHeight?: number
  containerHeight?: number
  rowKey?: string | ((row: any) => string | number)
  loading?: boolean
  showSearch?: boolean
  showRefresh?: boolean
  showExport?: boolean
  showColumnSettings?: boolean
  showFilters?: boolean
  showPagination?: boolean
  pageSize?: number
  pageSizes?: number[]
  remote?: boolean
  totalCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  rowHeight: 50,
  containerHeight: 400,
  rowKey: 'id',
  loading: false,
  showSearch: true,
  showRefresh: true,
  showExport: true,
  showColumnSettings: true,
  showFilters: true,
  showPagination: true,
  pageSize: 50,
  pageSizes: () => [20, 50, 100, 200],
  remote: false,
  totalCount: 0,
  filters: () => []
})

const emit = defineEmits<{
  'row-click': [row: any, index: number]
  'sort-change': [column: string, order: 'asc' | 'desc']
  'selection-change': [selectedRows: any[]]
  'search': [query: string]
  'filter-change': [filters: Record<string, any>]
  'refresh': []
  'export': []
  'page-change': [page: number, size: number]
}>()

// 响应式数据
const searchQuery = ref('')
const sortBy = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const selectedRows = ref<any[]>([])
const hiddenColumns = ref<string[]>([])
const activeFilters = ref<Filter[]>([...props.filters])
const currentPage = ref(1)
const pageSize = ref(props.pageSize)
const refreshing = ref(false)
const exporting = ref(false)

// 计算属性
const visibleColumns = computed(() => 
  props.columns.filter(col => !hiddenColumns.value.includes(col.key))
)

const hasActiveFilters = computed(() => 
  activeFilters.value.some(filter => 
    filter.value !== null && filter.value !== undefined && filter.value !== ''
  )
)

const filteredData = computed(() => {
  if (props.remote) {
    return props.data
  }

  let result = [...props.data]

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(row =>
      Object.values(row).some(value =>
        String(value).toLowerCase().includes(query)
      )
    )
  }

  // 自定义过滤
  activeFilters.value.forEach(filter => {
    if (filter.value !== null && filter.value !== undefined && filter.value !== '') {
      result = result.filter(row => {
        const cellValue = row[filter.key]
        switch (filter.type) {
          case 'input':
            return String(cellValue).toLowerCase().includes(String(filter.value).toLowerCase())
          case 'select':
            return cellValue === filter.value
          case 'date':
            return new Date(cellValue).toDateString() === new Date(filter.value).toDateString()
          case 'daterange':
            const date = new Date(cellValue)
            return date >= new Date(filter.value[0]) && date <= new Date(filter.value[1])
          default:
            return true
        }
      })
    }
  })

  // 排序
  if (sortBy.value) {
    result.sort((a, b) => {
      const aVal = a[sortBy.value]
      const bVal = b[sortBy.value]
      
      if (aVal === bVal) return 0
      
      const comparison = aVal > bVal ? 1 : -1
      return sortOrder.value === 'asc' ? comparison : -comparison
    })
  }

  return result
})

const totalCount = computed(() => 
  props.remote ? props.totalCount : filteredData.value.length
)

// 事件处理
const handleSearch = debounce((query: string) => {
  if (props.remote) {
    emit('search', query)
  }
}, 300)

const handleSortChange = (column: string, order: 'asc' | 'desc') => {
  sortBy.value = column
  sortOrder.value = order
  emit('sort-change', column, order)
}

const handleRowClick = (row: any, index: number) => {
  emit('row-click', row, index)
}

const handleSelectionChange = (rows: any[]) => {
  selectedRows.value = rows
  emit('selection-change', rows)
}

const handleFilterChange = () => {
  const filterValues = activeFilters.value.reduce((acc, filter) => {
    if (filter.value !== null && filter.value !== undefined && filter.value !== '') {
      acc[filter.key] = filter.value
    }
    return acc
  }, {} as Record<string, any>)
  
  emit('filter-change', filterValues)
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    emit('refresh')
  } finally {
    refreshing.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    emit('export')
  } finally {
    exporting.value = false
  }
}

const handleColumnCommand = (command: { action: string; column: string }) => {
  if (command.action === 'toggle') {
    toggleColumn(command.column)
  }
}

const toggleColumn = (columnKey: string) => {
  const index = hiddenColumns.value.indexOf(columnKey)
  if (index > -1) {
    hiddenColumns.value.splice(index, 1)
  } else {
    hiddenColumns.value.push(columnKey)
  }
}

const clearFilters = () => {
  activeFilters.value.forEach(filter => {
    filter.value = filter.type === 'daterange' ? [] : ''
  })
  handleFilterChange()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  emit('page-change', currentPage.value, size)
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  emit('page-change', page, pageSize.value)
}

const getFilterComponent = (type: string) => {
  switch (type) {
    case 'select':
      return 'el-select'
    case 'date':
      return 'el-date-picker'
    case 'daterange':
      return 'el-date-picker'
    default:
      return 'el-input'
  }
}

// 监听器
watch(() => props.filters, (newFilters) => {
  activeFilters.value = [...newFilters]
}, { deep: true })

onMounted(() => {
  // 初始化时如果是远程模式，触发数据加载
  if (props.remote) {
    emit('page-change', currentPage.value, pageSize.value)
  }
})
</script>

<style scoped>
.enhanced-virtual-table {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 300px;
}

.table-filters {
  padding: 16px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.table-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
}

.pagination-info {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

@media (max-width: 768px) {
  .table-toolbar {
    flex-direction: column;
    gap: 12px;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: center;
  }
  
  .search-input {
    width: 100%;
  }
  
  .table-pagination {
    flex-direction: column;
    gap: 12px;
  }
}
</style>