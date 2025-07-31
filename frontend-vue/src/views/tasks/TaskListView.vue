<template>
  <workspace-layout :breadcrumb-items="breadcrumbItems">
    <div class="task-list-container">
      <!-- 页面头部 -->
      <div class="task-list-header">
        <div class="header-left">
          <h1>任务管理</h1>
          <p>管理和跟踪您的法律服务任务</p>
        </div>
        <div class="header-right">
          <lk-button
            v-if="userStore.userRole === 'user'"
            type="primary"
            @click="showCreateDialog = true"
          >
            <el-icon><Plus /></el-icon>
            发布任务
          </lk-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="task-stats">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="总任务数"
              :value="taskStore.stats.total"
              :icon="Document"
              color="primary"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="待处理"
              :value="taskStore.stats.pending"
              :icon="Clock"
              color="warning"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="进行中"
              :value="taskStore.stats.in_progress"
              :icon="Loading"
              color="info"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <data-card
              title="已完成"
              :value="taskStore.stats.completed"
              :icon="Check"
              color="success"
            />
          </el-col>
        </el-row>
      </div>

      <!-- 筛选和搜索 -->
      <el-card class="filter-card">
        <div class="filter-header">
          <h3>筛选条件</h3>
          <el-button type="text" @click="resetFilters">
            重置
          </el-button>
        </div>
        
        <el-form :model="filterForm" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="filterForm.keyword"
              placeholder="搜索任务标题或描述"
              clearable
              style="width: 300px"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="filterForm.status"
              placeholder="选择状态"
              multiple
              clearable
              style="width: 200px"
            >
              <el-option label="待处理" value="pending" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="类型">
            <el-select
              v-model="filterForm.type"
              placeholder="选择类型"
              multiple
              clearable
              style="width: 200px"
            >
              <el-option label="法律咨询" value="consultation" />
              <el-option label="合同审查" value="contract_review" />
              <el-option label="诉讼代理" value="litigation" />
              <el-option label="文档起草" value="document_draft" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="优先级">
            <el-select
              v-model="filterForm.priority"
              placeholder="选择优先级"
              multiple
              clearable
              style="width: 150px"
            >
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="金额范围">
            <el-input-number
              v-model="filterForm.amount_min"
              placeholder="最小金额"
              :min="0"
              style="width: 120px"
            />
            <span style="margin: 0 8px">-</span>
            <el-input-number
              v-model="filterForm.amount_max"
              placeholder="最大金额"
              :min="0"
              style="width: 120px"
            />
          </el-form-item>
          
          <el-form-item>
            <lk-button type="primary" @click="handleFilter">
              筛选
            </lk-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 任务列表 -->
      <el-card class="task-list-card">
        <template #header>
          <div class="card-header">
            <span>任务列表</span>
            <div class="header-actions">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button label="list">列表</el-radio-button>
                <el-radio-button label="grid">网格</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- 列表视图 -->
        <div v-if="viewMode === 'list'" class="list-view">
          <lk-table
            :data="taskStore.tasks"
            :loading="taskStore.loading"
            show-pagination
            :total="taskStore.pagination.total"
            @page-change="handlePageChange"
            @size-change="handleSizeChange"
          >
            <el-table-column prop="title" label="任务标题" min-width="200">
              <template #default="{ row }">
                <div class="task-title-cell">
                  <el-link
                    type="primary"
                    @click="handleViewTask(row)"
                  >
                    {{ row.title }}
                  </el-link>
                  <div class="task-tags">
                    <el-tag
                      v-for="tag in row.tags"
                      :key="tag"
                      size="small"
                      type="info"
                    >
                      {{ tag }}
                    </el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getTypeTagType(row.type)">
                  {{ getTypeText(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="priority" label="优先级" width="100">
              <template #default="{ row }">
                <el-tag :type="getPriorityTagType(row.priority)">
                  {{ getPriorityText(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="amount" label="金额" width="120">
              <template #default="{ row }">
                <span class="amount-text">
                  {{ formatAmount(row.amount) }}
                </span>
              </template>
            </el-table-column>
            
            <el-table-column prop="client" label="客户" width="150">
              <template #default="{ row }">
                <div class="client-cell">
                  <el-avatar :size="24" :src="row.client.avatar">
                    {{ row.client.name.charAt(0) }}
                  </el-avatar>
                  <span>{{ row.client.name }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="150">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button
                    type="primary"
                    size="small"
                    text
                    @click="handleViewTask(row)"
                  >
                    查看
                  </el-button>
                  
                  <el-button
                    v-if="canApply(row)"
                    type="success"
                    size="small"
                    text
                    @click="handleApplyTask(row)"
                  >
                    申请
                  </el-button>
                  
                  <el-button
                    v-if="canEdit(row)"
                    type="warning"
                    size="small"
                    text
                    @click="handleEditTask(row)"
                  >
                    编辑
                  </el-button>
                  
                  <el-dropdown
                    v-if="hasMoreActions(row)"
                    @command="(command) => handleMoreAction(command, row)"
                  >
                    <el-button type="info" size="small" text>
                      更多
                      <el-icon><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item
                          v-if="canComplete(row)"
                          command="complete"
                        >
                          完成任务
                        </el-dropdown-item>
                        <el-dropdown-item
                          v-if="canCancel(row)"
                          command="cancel"
                        >
                          取消任务
                        </el-dropdown-item>
                        <el-dropdown-item
                          v-if="canRate(row)"
                          command="rate"
                        >
                          评价任务
                        </el-dropdown-item>
                        <el-dropdown-item
                          v-if="canDelete(row)"
                          command="delete"
                          divided
                        >
                          删除任务
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </lk-table>
        </div>
        
        <!-- 网格视图 -->
        <div v-else class="grid-view">
          <div v-if="taskStore.loading" class="loading-state">
            <el-skeleton :rows="3" animated />
          </div>
          
          <div v-else-if="taskStore.tasks.length === 0" class="empty-state">
            <el-empty description="暂无任务数据" />
          </div>
          
          <div v-else class="task-grid">
            <div
              v-for="task in taskStore.tasks"
              :key="task.id"
              class="task-card"
              @click="handleViewTask(task)"
            >
              <div class="task-card-header">
                <div class="task-card-title">{{ task.title }}</div>
                <el-tag :type="getStatusTagType(task.status)" size="small">
                  {{ getStatusText(task.status) }}
                </el-tag>
              </div>
              
              <div class="task-card-content">
                <p class="task-description">{{ task.description }}</p>
                
                <div class="task-meta">
                  <div class="meta-item">
                    <el-icon><Document /></el-icon>
                    <span>{{ getTypeText(task.type) }}</span>
                  </div>
                  <div class="meta-item">
                    <el-icon><Money /></el-icon>
                    <span>{{ formatAmount(task.amount) }}</span>
                  </div>
                  <div class="meta-item">
                    <el-icon><User /></el-icon>
                    <span>{{ task.client.name }}</span>
                  </div>
                </div>
              </div>
              
              <div class="task-card-footer">
                <div class="task-time">
                  {{ formatRelativeTime(task.created_at) }}
                </div>
                <div class="task-actions">
                  <lk-button
                    v-if="canApply(task)"
                    type="primary"
                    size="small"
                    @click.stop="handleApplyTask(task)"
                  >
                    申请
                  </lk-button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="taskStore.pagination.current"
              v-model:page-size="taskStore.pagination.size"
              :page-sizes="[10, 20, 50, 100]"
              :total="taskStore.pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 创建任务对话框 -->
    <create-task-dialog
      v-model="showCreateDialog"
      @success="handleCreateSuccess"
    />
    
    <!-- 申请任务对话框 -->
    <apply-task-dialog
      v-model="showApplyDialog"
      :task="selectedTask"
      @success="handleApplySuccess"
    />
  </workspace-layout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useTaskStore } from '@/stores/task'
import {
  ElRow,
  ElCol,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElSelect,
  ElOption,
  ElInputNumber,
  ElButton,
  ElIcon,
  ElRadioGroup,
  ElRadioButton,
  ElTable,
  ElTableColumn,
  ElTag,
  ElLink,
  ElAvatar,
  ElDropdown,
  ElDropdownMenu,
  ElDropdownItem,
  ElPagination,
  ElSkeleton,
  ElEmpty
} from 'element-plus'
import {
  Plus,
  Search,
  Document,
  Clock,
  Loading,
  Check,
  ArrowDown,
  Money,
  User
} from '@element-plus/icons-vue'
import { WorkspaceLayout, DataCard, LkButton, LkTable } from '@/components'
import CreateTaskDialog from './components/CreateTaskDialog.vue'
import ApplyTaskDialog from './components/ApplyTaskDialog.vue'
import { formatAmount, formatDate, formatRelativeTime } from '@/utils/format'
import type { Task, TaskFilter } from '@/types/task'

const router = useRouter()
const userStore = useUserStore()
const taskStore = useTaskStore()

// 面包屑导航
const breadcrumbItems = [
  { title: '工作台', path: '/dashboard' },
  { title: '任务管理', path: '/tasks' }
]

// 响应式数据
const viewMode = ref<'list' | 'grid'>('list')
const showCreateDialog = ref(false)
const showApplyDialog = ref(false)
const selectedTask = ref<Task | null>(null)

const filterForm = reactive<TaskFilter>({
  keyword: '',
  status: [],
  type: [],
  priority: [],
  amount_min: undefined,
  amount_max: undefined
})

// 计算属性
const canApply = (task: Task) => {
  return userStore.userRole === 'lawyer' && 
         task.status === 'pending' && 
         !task.lawyer
}

const canEdit = (task: Task) => {
  return userStore.user?.id === task.client.id && 
         task.status === 'pending'
}

const canComplete = (task: Task) => {
  return (userStore.user?.id === task.lawyer?.id || 
          userStore.user?.id === task.client.id) && 
         task.status === 'in_progress'
}

const canCancel = (task: Task) => {
  return userStore.user?.id === task.client.id && 
         ['pending', 'in_progress'].includes(task.status)
}

const canRate = (task: Task) => {
  return userStore.user?.id === task.client.id && 
         task.status === 'completed' && 
         !task.rating
}

const canDelete = (task: Task) => {
  return userStore.user?.id === task.client.id && 
         task.status === 'pending'
}

const hasMoreActions = (task: Task) => {
  return canComplete(task) || canCancel(task) || canRate(task) || canDelete(task)
}

// 方法
const getStatusText = (status: string) => {
  const statusMap = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return statusMap[status as keyof typeof statusMap] || '未知'
}

const getStatusTagType = (status: string) => {
  const typeMap = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getTypeText = (type: string) => {
  const typeMap = {
    consultation: '法律咨询',
    contract_review: '合同审查',
    litigation: '诉讼代理',
    document_draft: '文档起草',
    other: '其他'
  }
  return typeMap[type as keyof typeof typeMap] || '其他'
}

const getTypeTagType = (type: string) => {
  const typeMap = {
    consultation: 'primary',
    contract_review: 'success',
    litigation: 'danger',
    document_draft: 'warning',
    other: 'info'
  }
  return typeMap[type as keyof typeof typeMap] || 'info'
}

const getPriorityText = (priority: string) => {
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return priorityMap[priority as keyof typeof priorityMap] || '中'
}

const getPriorityTagType = (priority: string) => {
  const typeMap = {
    low: 'info',
    medium: 'primary',
    high: 'warning',
    urgent: 'danger'
  }
  return typeMap[priority as keyof typeof typeMap] || 'primary'
}

const handleSearch = () => {
  if (filterForm.keyword) {
    taskStore.searchTasks({
      keyword: filterForm.keyword,
      page: 1,
      size: taskStore.pagination.size,
      filter: filterForm
    })
  } else {
    handleFilter()
  }
}

const handleFilter = () => {
  taskStore.setFilter(filterForm)
  taskStore.fetchTasks({
    page: 1,
    size: taskStore.pagination.size,
    filter: filterForm
  })
}

const resetFilters = () => {
  Object.keys(filterForm).forEach(key => {
    if (Array.isArray(filterForm[key as keyof TaskFilter])) {
      (filterForm[key as keyof TaskFilter] as any) = []
    } else {
      (filterForm[key as keyof TaskFilter] as any) = undefined
    }
  })
  filterForm.keyword = ''
  
  taskStore.clearFilter()
  taskStore.fetchTasks({
    page: 1,
    size: taskStore.pagination.size
  })
}

const handlePageChange = (page: number) => {
  taskStore.fetchTasks({
    page,
    size: taskStore.pagination.size,
    filter: taskStore.filter
  })
}

const handleSizeChange = (size: number) => {
  taskStore.fetchTasks({
    page: 1,
    size,
    filter: taskStore.filter
  })
}

const handleViewTask = (task: Task) => {
  router.push(`/tasks/${task.id}`)
}

const handleApplyTask = (task: Task) => {
  selectedTask.value = task
  showApplyDialog.value = true
}

const handleEditTask = (task: Task) => {
  router.push(`/tasks/${task.id}/edit`)
}

const handleMoreAction = async (command: string, task: Task) => {
  switch (command) {
    case 'complete':
      await taskStore.completeTask(task.id)
      break
    case 'cancel':
      await taskStore.cancelTask(task.id)
      break
    case 'rate':
      router.push(`/tasks/${task.id}/rate`)
      break
    case 'delete':
      await taskStore.deleteTask(task.id)
      break
  }
}

const handleCreateSuccess = () => {
  showCreateDialog.value = false
  taskStore.fetchTasks({
    page: 1,
    size: taskStore.pagination.size,
    filter: taskStore.filter
  })
}

const handleApplySuccess = () => {
  showApplyDialog.value = false
  selectedTask.value = null
}

onMounted(async () => {
  await Promise.all([
    taskStore.fetchTasks(),
    taskStore.fetchTaskStats()
  ])
})
</script>

<style lang="scss" scoped>
.task-list-container {
  padding: 24px;
}

.task-list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  
  .header-left {
    h1 {
      font-size: 28px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;
    }
    
    p {
      color: var(--el-text-color-secondary);
      margin: 0;
    }
  }
}

.task-stats {
  margin-bottom: 24px;
}

.filter-card {
  margin-bottom: 24px;
  
  .filter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }
  
  .el-form {
    .el-form-item {
      margin-bottom: 16px;
    }
  }
}

.task-list-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    span {
      font-size: 16px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }
  
  .list-view {
    .task-title-cell {
      .task-tags {
        margin-top: 4px;
        
        .el-tag {
          margin-right: 4px;
        }
      }
    }
    
    .client-cell {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .amount-text {
      font-weight: 600;
      color: var(--el-color-danger);
    }
    
    .action-buttons {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
  }
  
  .grid-view {
    .loading-state,
    .empty-state {
      padding: 40px 0;
      text-align: center;
    }
    
    .task-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
      
      .task-card {
        border: 1px solid var(--el-border-color-light);
        border-radius: 8px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          border-color: var(--el-color-primary);
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }
        
        .task-card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          
          .task-card-title {
            font-size: 16px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            flex: 1;
            margin-right: 12px;
            line-height: 1.4;
          }
        }
        
        .task-card-content {
          margin-bottom: 16px;
          
          .task-description {
            color: var(--el-text-color-regular);
            line-height: 1.5;
            margin: 0 0 12px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          
          .task-meta {
            display: flex;
            flex-direction: column;
            gap: 6px;
            
            .meta-item {
              display: flex;
              align-items: center;
              gap: 6px;
              font-size: 14px;
              color: var(--el-text-color-secondary);
              
              .el-icon {
                font-size: 16px;
              }
            }
          }
        }
        
        .task-card-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 16px;
          border-top: 1px solid var(--el-border-color-lighter);
          
          .task-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
    
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 24px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .task-list-container {
    padding: 16px;
  }
  
  .task-list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .filter-card {
    .el-form {
      .el-form-item {
        display: block;
        margin-bottom: 16px;
      }
    }
  }
  
  .task-grid {
    grid-template-columns: 1fr !important;
  }
}
</style>