<template>
  <div class="lk-table">
    <el-table
      ref="tableRef"
      :data="data"
      :height="height"
      :max-height="maxHeight"
      :stripe="stripe"
      :border="border"
      :size="size"
      :fit="fit"
      :show-header="showHeader"
      :highlight-current-row="highlightCurrentRow"
      :current-row-key="currentRowKey"
      :row-class-name="rowClassName"
      :row-style="rowStyle"
      :cell-class-name="cellClassName"
      :cell-style="cellStyle"
      :header-row-class-name="headerRowClassName"
      :header-row-style="headerRowStyle"
      :header-cell-class-name="headerCellClassName"
      :header-cell-style="headerCellStyle"
      :row-key="rowKey"
      :empty-text="emptyText"
      :default-expand-all="defaultExpandAll"
      :expand-row-keys="expandRowKeys"
      :default-sort="defaultSort"
      :tooltip-effect="tooltipEffect"
      :show-summary="showSummary"
      :sum-text="sumText"
      :summary-method="summaryMethod"
      :span-method="spanMethod"
      :select-on-indeterminate="selectOnIndeterminate"
      :indent="indent"
      :lazy="lazy"
      :load="load"
      :tree-props="treeProps"
      :table-layout="tableLayout"
      :scrollbar-always-on="scrollbarAlwaysOn"
      v-loading="loading"
      @select="handleSelect"
      @select-all="handleSelectAll"
      @selection-change="handleSelectionChange"
      @cell-mouse-enter="handleCellMouseEnter"
      @cell-mouse-leave="handleCellMouseLeave"
      @cell-click="handleCellClick"
      @cell-dblclick="handleCellDblclick"
      @row-click="handleRowClick"
      @row-contextmenu="handleRowContextmenu"
      @row-dblclick="handleRowDblclick"
      @header-click="handleHeaderClick"
      @header-contextmenu="handleHeaderContextmenu"
      @sort-change="handleSortChange"
      @filter-change="handleFilterChange"
      @current-change="handleCurrentChange"
      @header-dragend="handleHeaderDragend"
      @expand-change="handleExpandChange"
    >
      <slot />
    </el-table>

    <!-- 分页组件 -->
    <div class="lk-table__pagination" v-if="showPagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :small="paginationSmall"
        :disabled="paginationDisabled"
        :background="paginationBackground"
        :layout="paginationLayout"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElTable, ElPagination } from 'element-plus'
import type { TableInstance } from 'element-plus'

interface Props {
  data: any[]
  height?: string | number
  maxHeight?: string | number
  stripe?: boolean
  border?: boolean
  size?: 'large' | 'default' | 'small'
  fit?: boolean
  showHeader?: boolean
  highlightCurrentRow?: boolean
  currentRowKey?: string | number
  rowClassName?: string | ((row: any, rowIndex: number) => string)
  rowStyle?: any
  cellClassName?: string | ((row: any, column: any, rowIndex: number, columnIndex: number) => string)
  cellStyle?: any
  headerRowClassName?: string | ((row: any, rowIndex: number) => string)
  headerRowStyle?: any
  headerCellClassName?: string | ((row: any, column: any, rowIndex: number, columnIndex: number) => string)
  headerCellStyle?: any
  rowKey?: string | ((row: any) => string)
  emptyText?: string
  defaultExpandAll?: boolean
  expandRowKeys?: any[]
  defaultSort?: any
  tooltipEffect?: 'dark' | 'light'
  showSummary?: boolean
  sumText?: string
  summaryMethod?: (param: any) => any[]
  spanMethod?: (param: any) => any
  selectOnIndeterminate?: boolean
  indent?: number
  lazy?: boolean
  load?: (row: any, treeNode: any, resolve: (data: any[]) => void) => void
  treeProps?: any
  tableLayout?: 'fixed' | 'auto'
  scrollbarAlwaysOn?: boolean
  loading?: boolean
  // 分页相关
  showPagination?: boolean
  total?: number
  pageSize?: number
  pageSizes?: number[]
  paginationSmall?: boolean
  paginationDisabled?: boolean
  paginationBackground?: boolean
  paginationLayout?: string
}

const props = withDefaults(defineProps<Props>(), {
  stripe: false,
  border: true,
  size: 'default',
  fit: true,
  showHeader: true,
  highlightCurrentRow: false,
  emptyText: '暂无数据',
  defaultExpandAll: false,
  tooltipEffect: 'dark',
  showSummary: false,
  sumText: '合计',
  selectOnIndeterminate: true,
  indent: 16,
  lazy: false,
  tableLayout: 'fixed',
  scrollbarAlwaysOn: false,
  loading: false,
  showPagination: false,
  total: 0,
  pageSize: 10,
  pageSizes: () => [10, 20, 50, 100],
  paginationSmall: false,
  paginationDisabled: false,
  paginationBackground: true,
  paginationLayout: 'total, sizes, prev, pager, next, jumper'
})

const emit = defineEmits<{
  select: [selection: any[], row: any]
  'select-all': [selection: any[]]
  'selection-change': [selection: any[]]
  'cell-mouse-enter': [row: any, column: any, cell: any, event: Event]
  'cell-mouse-leave': [row: any, column: any, cell: any, event: Event]
  'cell-click': [row: any, column: any, cell: any, event: Event]
  'cell-dblclick': [row: any, column: any, cell: any, event: Event]
  'row-click': [row: any, column: any, event: Event]
  'row-contextmenu': [row: any, column: any, event: Event]
  'row-dblclick': [row: any, column: any, event: Event]
  'header-click': [column: any, event: Event]
  'header-contextmenu': [column: any, event: Event]
  'sort-change': [param: any]
  'filter-change': [filters: any]
  'current-change': [currentRow: any, oldCurrentRow: any]
  'header-dragend': [newWidth: number, oldWidth: number, column: any, event: Event]
  'expand-change': [row: any, expandedRows: any[]]
  'size-change': [size: number]
  'page-change': [page: number]
}>()

const tableRef = ref<TableInstance>()
const currentPage = ref(1)

// 表格方法
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

const toggleRowSelection = (row: any, selected?: boolean) => {
  tableRef.value?.toggleRowSelection(row, selected)
}

const toggleAllSelection = () => {
  tableRef.value?.toggleAllSelection()
}

const toggleRowExpansion = (row: any, expanded?: boolean) => {
  tableRef.value?.toggleRowExpansion(row, expanded)
}

const setCurrentRow = (row: any) => {
  tableRef.value?.setCurrentRow(row)
}

const clearSort = () => {
  tableRef.value?.clearSort()
}

const clearFilter = (columnKeys?: string[]) => {
  tableRef.value?.clearFilter(columnKeys)
}

const doLayout = () => {
  tableRef.value?.doLayout()
}

const sort = (prop: string, order: string) => {
  tableRef.value?.sort(prop, order)
}

// 事件处理
const handleSelect = (selection: any[], row: any) => {
  emit('select', selection, row)
}

const handleSelectAll = (selection: any[]) => {
  emit('select-all', selection)
}

const handleSelectionChange = (selection: any[]) => {
  emit('selection-change', selection)
}

const handleCellMouseEnter = (row: any, column: any, cell: any, event: Event) => {
  emit('cell-mouse-enter', row, column, cell, event)
}

const handleCellMouseLeave = (row: any, column: any, cell: any, event: Event) => {
  emit('cell-mouse-leave', row, column, cell, event)
}

const handleCellClick = (row: any, column: any, cell: any, event: Event) => {
  emit('cell-click', row, column, cell, event)
}

const handleCellDblclick = (row: any, column: any, cell: any, event: Event) => {
  emit('cell-dblclick', row, column, cell, event)
}

const handleRowClick = (row: any, column: any, event: Event) => {
  emit('row-click', row, column, event)
}

const handleRowContextmenu = (row: any, column: any, event: Event) => {
  emit('row-contextmenu', row, column, event)
}

const handleRowDblclick = (row: any, column: any, event: Event) => {
  emit('row-dblclick', row, column, event)
}

const handleHeaderClick = (column: any, event: Event) => {
  emit('header-click', column, event)
}

const handleHeaderContextmenu = (column: any, event: Event) => {
  emit('header-contextmenu', column, event)
}

const handleSortChange = (param: any) => {
  emit('sort-change', param)
}

const handleFilterChange = (filters: any) => {
  emit('filter-change', filters)
}

const handleCurrentChange = (currentRow: any, oldCurrentRow: any) => {
  emit('current-change', currentRow, oldCurrentRow)
}

const handleHeaderDragend = (newWidth: number, oldWidth: number, column: any, event: Event) => {
  emit('header-dragend', newWidth, oldWidth, column, event)
}

const handleExpandChange = (row: any, expandedRows: any[]) => {
  emit('expand-change', row, expandedRows)
}

const handleSizeChange = (size: number) => {
  emit('size-change', size)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  emit('page-change', page)
}

defineExpose({
  clearSelection,
  toggleRowSelection,
  toggleAllSelection,
  toggleRowExpansion,
  setCurrentRow,
  clearSort,
  clearFilter,
  doLayout,
  sort
})
</script>

<style scoped lang="scss">
.lk-table {
  .lk-table__pagination {
    margin-top: 20px;
    text-align: right;
  }

  :deep(.el-table) {
    .el-table__header-wrapper {
      th {
        background-color: var(--el-bg-color-page);
        color: var(--el-text-color-primary);
        font-weight: 500;
      }
    }

    .el-table__body-wrapper {
      .el-table__row {
        &:hover {
          background-color: var(--el-table-row-hover-bg-color);
        }

        &.current-row {
          background-color: var(--el-color-primary-light-9);
        }
      }
    }

    .el-table__empty-block {
      min-height: 200px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .lk-table {
    .lk-table__pagination {
      text-align: center;

      :deep(.el-pagination) {
        .el-pagination__sizes,
        .el-pagination__jump {
          display: none;
        }
      }
    }
  }
}
</style>