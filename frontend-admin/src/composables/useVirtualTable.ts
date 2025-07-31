import { ref, computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

export interface TableColumn {
  key: string
  title: string
  width?: string
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, row: any, index: number) => any
}

export interface TableFilter {
  key: string
  label: string
  type: 'input' | 'select' | 'date' | 'daterange'
  value: any
  options?: Array<{ label: string; value: any }>
  props?: Record<string, any>
}

export interface TableState {
  data: any[]
  loading: boolean
  total: number
  currentPage: number
  pageSize: number
  sortBy: string
  sortOrder: 'asc' | 'desc'
  searchQuery: string
  filters: Record<string, any>
  selectedRows: any[]
}

export interface UseVirtualTableOptions {
  immediate?: boolean
  remote?: boolean
  defaultPageSize?: number
  defaultSort?: { column: string; order: 'asc' | 'desc' }
}

export function useVirtualTable<T = any>(
  fetchData?: (params: any) => Promise<{ data: T[]; total: number }>,
  options: UseVirtualTableOptions = {}
) {
  const {
    immediate = true,
    remote = false,
    defaultPageSize = 50,
    defaultSort
  } = options

  // 表格状态
  const state = reactive<TableState>({
    data: [],
    loading: false,
    total: 0,
    currentPage: 1,
    pageSize: defaultPageSize,
    sortBy: defaultSort?.column || '',
    sortOrder: defaultSort?.order || 'asc',
    searchQuery: '',
    filters: {},
    selectedRows: []
  })

  // 原始数据（用于本地模式）
  const rawData = ref<T[]>([])

  // 计算属性
  const hasData = computed(() => state.data.length > 0)
  const isEmpty = computed(() => !state.loading && state.data.length === 0)
  const hasSelection = computed(() => state.selectedRows.length > 0)

  // 获取查询参数
  const getQueryParams = () => {
    return {
      page: state.currentPage,
      pageSize: state.pageSize,
      sortBy: state.sortBy,
      sortOrder: state.sortOrder,
      search: state.searchQuery,
      ...state.filters
    }
  }

  // 加载数据
  const loadData = async (showLoading = true) => {
    if (!fetchData) {
      console.warn('fetchData function is not provided')
      return
    }

    if (showLoading) {
      state.loading = true
    }

    try {
      const params = getQueryParams()
      const result = await fetchData(params)
      
      state.data = result.data
      state.total = result.total
      
      // 如果是本地模式，保存原始数据
      if (!remote) {
        rawData.value = result.data
      }
    } catch (error) {
      console.error('Failed to load table data:', error)
      ElMessage.error('数据加载失败')
      state.data = []
      state.total = 0
    } finally {
      state.loading = false
    }
  }

  // 刷新数据
  const refresh = async () => {
    state.currentPage = 1
    await loadData()
  }

  // 重新加载（保持当前页）
  const reload = async () => {
    await loadData()
  }

  // 搜索
  const search = async (query: string) => {
    state.searchQuery = query
    state.currentPage = 1
    
    if (remote) {
      await loadData()
    }
  }

  // 排序
  const sort = async (column: string, order: 'asc' | 'desc') => {
    state.sortBy = column
    state.sortOrder = order
    state.currentPage = 1
    
    if (remote) {
      await loadData()
    }
  }

  // 筛选
  const filter = async (filters: Record<string, any>) => {
    state.filters = { ...filters }
    state.currentPage = 1
    
    if (remote) {
      await loadData()
    }
  }

  // 分页
  const changePage = async (page: number, size?: number) => {
    state.currentPage = page
    if (size) {
      state.pageSize = size
    }
    
    if (remote) {
      await loadData()
    }
  }

  // 选择行
  const selectRows = (rows: T[]) => {
    state.selectedRows = rows
  }

  // 选择所有行
  const selectAll = () => {
    state.selectedRows = [...state.data]
  }

  // 清除选择
  const clearSelection = () => {
    state.selectedRows = []
  }

  // 切换行选择
  const toggleRowSelection = (row: T, selected?: boolean) => {
    const index = state.selectedRows.findIndex(item => item === row)
    
    if (selected === undefined) {
      selected = index === -1
    }
    
    if (selected && index === -1) {
      state.selectedRows.push(row)
    } else if (!selected && index > -1) {
      state.selectedRows.splice(index, 1)
    }
  }

  // 导出数据
  const exportData = async (format: 'csv' | 'excel' = 'csv') => {
    try {
      const dataToExport = remote ? state.data : rawData.value
      
      if (format === 'csv') {
        await exportToCsv(dataToExport)
      } else {
        await exportToExcel(dataToExport)
      }
      
      ElMessage.success('导出成功')
    } catch (error) {
      console.error('Export failed:', error)
      ElMessage.error('导出失败')
    }
  }

  // 导出为CSV
  const exportToCsv = async (data: T[]) => {
    if (data.length === 0) return
    
    const headers = Object.keys(data[0] as object)
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => 
          JSON.stringify((row as any)[header] || '')
        ).join(',')
      )
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `table_data_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  // 导出为Excel（需要安装xlsx库）
  const exportToExcel = async (data: T[]) => {
    try {
      const XLSX = await import('xlsx')
      const ws = XLSX.utils.json_to_sheet(data)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
      XLSX.writeFile(wb, `table_data_${new Date().toISOString().split('T')[0]}.xlsx`)
    } catch (error) {
      console.error('Excel export requires xlsx library:', error)
      ElMessage.error('Excel导出需要安装xlsx库')
    }
  }

  // 重置状态
  const reset = () => {
    state.currentPage = 1
    state.pageSize = defaultPageSize
    state.sortBy = defaultSort?.column || ''
    state.sortOrder = defaultSort?.order || 'asc'
    state.searchQuery = ''
    state.filters = {}
    state.selectedRows = []
  }

  // 设置数据（用于本地模式）
  const setData = (data: T[]) => {
    rawData.value = data
    state.data = data
    state.total = data.length
  }

  // 监听器
  if (remote) {
    // 远程模式下监听状态变化自动加载数据
    watch(
      () => [state.currentPage, state.pageSize, state.sortBy, state.sortOrder],
      () => {
        if (!state.loading) {
          loadData(false)
        }
      },
      { deep: true }
    )
  }

  // 初始化
  if (immediate && fetchData) {
    loadData()
  }

  return {
    // 状态
    state,
    hasData,
    isEmpty,
    hasSelection,
    
    // 方法
    loadData,
    refresh,
    reload,
    search,
    sort,
    filter,
    changePage,
    selectRows,
    selectAll,
    clearSelection,
    toggleRowSelection,
    exportData,
    reset,
    setData,
    getQueryParams
  }
}

// 表格工具函数
export const tableUtils = {
  // 格式化文件大小
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  // 格式化日期
  formatDate: (date: string | Date, format = 'YYYY-MM-DD HH:mm:ss'): string => {
    const d = new Date(date)
    if (isNaN(d.getTime())) return '-'
    
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    const seconds = String(d.getSeconds()).padStart(2, '0')
    
    return format
      .replace('YYYY', year.toString())
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds)
  },

  // 格式化数字
  formatNumber: (num: number, decimals = 2): string => {
    if (isNaN(num)) return '-'
    return num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })
  },

  // 格式化百分比
  formatPercent: (num: number, decimals = 1): string => {
    if (isNaN(num)) return '-'
    return (num * 100).toFixed(decimals) + '%'
  },

  // 格式化状态
  formatStatus: (status: string, statusMap: Record<string, { text: string; type: string }>): { text: string; type: string } => {
    return statusMap[status] || { text: status, type: 'info' }
  },

  // 高亮搜索关键词
  highlightKeyword: (text: string, keyword: string): string => {
    if (!keyword) return text
    const regex = new RegExp(`(${keyword})`, 'gi')
    return text.replace(regex, '<mark>$1</mark>')
  }
}