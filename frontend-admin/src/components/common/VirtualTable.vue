<template>
  <div class="virtual-table" ref="containerRef">
    <div class="table-header">
      <div class="table-row header-row">
        <div
          v-for="column in columns"
          :key="column.key"
          :class="['table-cell', 'header-cell', { sortable: column.sortable }]"
          :style="{ width: column.width || 'auto' }"
          @click="handleSort(column)"
        >
          <span>{{ column.title }}</span>
          <span v-if="column.sortable" class="sort-icon">
            <i
              :class="[
                'el-icon',
                getSortIcon(column.key)
              ]"
            ></i>
          </span>
        </div>
      </div>
    </div>
    
    <div
      class="table-body"
      ref="scrollContainerRef"
      @scroll="handleScroll"
      :style="{ height: `${containerHeight}px` }"
    >
      <div
        class="virtual-list"
        :style="{ height: `${totalHeight}px` }"
      >
        <div
          class="visible-items"
          :style="{ transform: `translateY(${offsetY}px)` }"
        >
          <div
            v-for="(item, index) in visibleItems"
            :key="getRowKey(item, startIndex + index)"
            :class="['table-row', 'data-row', { selected: isSelected(item) }]"
            @click="handleRowClick(item, startIndex + index)"
          >
            <div
              v-for="column in columns"
              :key="column.key"
              :class="['table-cell', 'data-cell']"
              :style="{ width: column.width || 'auto' }"
            >
              <slot
                :name="column.key"
                :row="item"
                :column="column"
                :index="startIndex + index"
              >
                {{ getCellValue(item, column) }}
              </slot>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loading-overlay">
      <el-loading-spinner />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

interface Column {
  key: string
  title: string
  width?: string
  sortable?: boolean
  render?: (value: any, row: any, index: number) => any
}

interface Props {
  data: any[]
  columns: Column[]
  rowHeight?: number
  containerHeight?: number
  rowKey?: string | ((row: any) => string | number)
  loading?: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  selectedRows?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  rowHeight: 50,
  containerHeight: 400,
  rowKey: 'id',
  loading: false,
  sortOrder: 'asc',
  selectedRows: () => []
})

const emit = defineEmits<{
  'row-click': [row: any, index: number]
  'sort-change': [column: string, order: 'asc' | 'desc']
  'selection-change': [selectedRows: any[]]
}>()

const containerRef = ref<HTMLElement>()
const scrollContainerRef = ref<HTMLElement>()
const scrollTop = ref(0)

// 计算属性
const totalHeight = computed(() => props.data.length * props.rowHeight)
const visibleCount = computed(() => Math.ceil(props.containerHeight / props.rowHeight) + 2)
const startIndex = computed(() => Math.floor(scrollTop.value / props.rowHeight))
const endIndex = computed(() => Math.min(startIndex.value + visibleCount.value, props.data.length))
const visibleItems = computed(() => props.data.slice(startIndex.value, endIndex.value))
const offsetY = computed(() => startIndex.value * props.rowHeight)

// 滚动处理
const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
}

// 排序处理
const handleSort = (column: Column) => {
  if (!column.sortable) return
  
  const newOrder = props.sortBy === column.key && props.sortOrder === 'asc' ? 'desc' : 'asc'
  emit('sort-change', column.key, newOrder)
}

const getSortIcon = (columnKey: string) => {
  if (props.sortBy !== columnKey) return 'el-icon-sort'
  return props.sortOrder === 'asc' ? 'el-icon-sort-up' : 'el-icon-sort-down'
}

// 行选择处理
const handleRowClick = (row: any, index: number) => {
  emit('row-click', row, index)
}

const isSelected = (row: any) => {
  const key = getRowKey(row, 0)
  return props.selectedRows.some(selectedRow => getRowKey(selectedRow, 0) === key)
}

// 获取行键值
const getRowKey = (row: any, index: number): string | number => {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row)
  }
  return row[props.rowKey] || index
}

// 获取单元格值
const getCellValue = (row: any, column: Column) => {
  if (column.render) {
    return column.render(row[column.key], row, 0)
  }
  
  const value = row[column.key]
  if (value === null || value === undefined) {
    return '-'
  }
  
  return value
}

// 监听数据变化，重置滚动位置
watch(() => props.data, () => {
  if (scrollContainerRef.value) {
    scrollContainerRef.value.scrollTop = 0
    scrollTop.value = 0
  }
})

onMounted(() => {
  // 初始化时确保容器高度正确
  nextTick(() => {
    if (scrollContainerRef.value) {
      scrollTop.value = scrollContainerRef.value.scrollTop
    }
  })
})
</script>

<style scoped>
.virtual-table {
  position: relative;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
}

.table-header {
  background-color: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color);
}

.table-row {
  display: flex;
  align-items: center;
}

.header-row {
  height: 50px;
  font-weight: 600;
}

.data-row {
  height: 50px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background-color 0.2s;
}

.data-row:hover {
  background-color: var(--el-bg-color-page);
}

.data-row.selected {
  background-color: var(--el-color-primary-light-9);
}

.table-cell {
  padding: 0 12px;
  display: flex;
  align-items: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-cell {
  justify-content: space-between;
  cursor: default;
}

.header-cell.sortable {
  cursor: pointer;
  user-select: none;
}

.header-cell.sortable:hover {
  background-color: var(--el-bg-color);
}

.sort-icon {
  margin-left: 4px;
  color: var(--el-text-color-secondary);
}

.table-body {
  overflow-y: auto;
  overflow-x: hidden;
}

.virtual-list {
  position: relative;
}

.visible-items {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

/* 滚动条样式 */
.table-body::-webkit-scrollbar {
  width: 8px;
}

.table-body::-webkit-scrollbar-track {
  background: var(--el-bg-color-page);
}

.table-body::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 4px;
}

.table-body::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}
</style>