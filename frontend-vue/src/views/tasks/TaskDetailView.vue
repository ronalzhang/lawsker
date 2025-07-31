<template>
  <workspace-layout :breadcrumb-items="breadcrumbItems">
    <div class="task-detail-container" v-loading="taskStore.loading">
      <div v-if="task" class="task-detail-content">
        <!-- 任务头部 -->
        <div class="task-header">
          <div class="header-left">
            <h1>{{ task.title }}</h1>
            <div class="task-meta">
              <el-tag :type="getStatusTagType(task.status)" size="large">
                {{ getStatusText(task.status) }}
              </el-tag>
              <el-tag :type="getTypeTagType(task.type)">
                {{ getTypeText(task.type) }}
              </el-tag>
              <el-tag :type="getPriorityTagType(task.priority)">
                {{ getPriorityText(task.priority) }}
              </el-tag>
            </div>
          </div>
          <div class="header-right">
            <div class="task-amount">
              <span class="amount-label">任务金额</span>
              <span class="amount-value">{{ formatAmount(task.amount) }}</span>
            </div>
          </div>
        </div>

        <el-row :gutter="24">
          <!-- 左侧主要内容 -->
          <el-col :xs="24" :lg="16">
            <!-- 任务描述 -->
            <el-card class="task-description">
              <template #header>
                <span>任务描述</span>
              </template>
              <div class="description-content">
                <p>{{ task.description }}</p>
                <div v-if="task.requirements" class="requirements">
                  <h4>具体要求</h4>
                  <div v-html="task.requirements" />
                </div>
              </div>
            </el-card>

            <!-- 任务附件 -->
            <el-card v-if="task.attachments?.length" class="task-attachments">
              <template #header>
                <span>相关附件</span>
              </template>
              <div class="attachment-list">
                <div
                  v-for="attachment in task.attachments"
                  :key="attachment.id"
                  class="attachment-item"
                >
                  <div class="attachment-info">
                    <el-icon class="attachment-icon">
                      <Document />
                    </el-icon>
                    <div class="attachment-details">
                      <div class="attachment-name">{{ attachment.name }}</div>
                      <div class="attachment-meta">
                        {{ formatFileSize(attachment.size) }} • 
                        {{ formatDate(attachment.uploaded_at) }}
                      </div>
                    </div>
                  </div>
                  <div class="attachment-actions">
                    <el-button
                      type="primary"
                      size="small"
                      text
                      @click="downloadAttachment(attachment)"
                    >
                      下载
                    </el-button>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 任务进度 -->
            <el-card v-if="task.milestones?.length" class="task-progress">
              <template #header>
                <span>任务进度</span>
              </template>
              <div class="progress-content">
                <el-progress
                  :percentage="task.progress || 0"
                  :stroke-width="8"
                  :show-text="true"
                />
                <div class="milestones">
                  <div
                    v-for="milestone in task.milestones"
                    :key="milestone.id"
                    class="milestone-item"
                    :class="{ completed: milestone.status === 'completed' }"
                  >
                    <div class="milestone-icon">
                      <el-icon v-if="milestone.status === 'completed'">
                        <Check />
                      </el-icon>
                      <el-icon v-else>
                        <Clock />
                      </el-icon>
                    </div>
                    <div class="milestone-content">
                      <div class="milestone-title">{{ milestone.title }}</div>
                      <div class="milestone-description">{{ milestone.description }}</div>
                      <div class="milestone-time">
                        <span v-if="milestone.due_date">
                          截止时间：{{ formatDate(milestone.due_date) }}
                        </span>
                        <span v-if="milestone.completed_at">
                          完成时间：{{ formatDate(milestone.completed_at) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 申请列表（仅客户可见） -->
            <el-card
              v-if="isClient && task.status === 'pending'"
              class="task-applications"
            >
              <template #header>
                <div class="card-header">
                  <span>律师申请</span>
                  <el-badge :value="applications.length" />
                </div>
              </template>
              
              <div v-if="applications.length === 0" class="empty-state">
                <el-empty description="暂无律师申请" />
              </div>
              
              <div v-else class="application-list">
                <div
                  v-for="application in applications"
                  :key="application.id"
                  class="application-item"
                >
                  <div class="application-header">
                    <div class="lawyer-info">
                      <el-avatar :size="40" :src="application.lawyer.avatar">
                        {{ application.lawyer.name.charAt(0) }}
                      </el-avatar>
                      <div class="lawyer-details">
                        <div class="lawyer-name">{{ application.lawyer.name }}</div>
                        <div class="lawyer-meta">
                          <el-rate
                            v-model="application.lawyer.rating"
                            disabled
                            size="small"
                          />
                          <span>{{ application.lawyer.experience_years }}年经验</span>
                        </div>
                      </div>
                    </div>
                    <div class="application-amount">
                      {{ formatAmount(application.quoted_amount) }}
                    </div>
                  </div>
                  
                  <div class="application-content">
                    <p>{{ application.proposal }}</p>
                    <div class="application-meta">
                      <span>预计用时：{{ application.estimated_duration }}天</span>
                      <span>申请时间：{{ formatRelativeTime(application.applied_at) }}</span>
                    </div>
                  </div>
                  
                  <div class="application-actions">
                    <lk-button
                      type="success"
                      size="small"
                      @click="handleAcceptApplication(application)"
                    >
                      接受
                    </lk-button>
                    <lk-button
                      size="small"
                      @click="handleRejectApplication(application)"
                    >
                      拒绝
                    </lk-button>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 评价区域 -->
            <el-card v-if="task.rating" class="task-rating">
              <template #header>
                <span>任务评价</span>
              </template>
              <div class="rating-content">
                <div class="rating-score">
                  <el-rate v-model="task.rating" disabled size="large" />
                  <span class="rating-text">{{ task.rating }}/5</span>
                </div>
                <div class="rating-review">
                  <p>{{ task.review }}</p>
                  <div class="rating-time">
                    评价时间：{{ formatDate(task.review_date!) }}
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧信息栏 -->
          <el-col :xs="24" :lg="8">
            <!-- 任务信息 -->
            <el-card class="task-info">
              <template #header>
                <span>任务信息</span>
              </template>
              <div class="info-list">
                <div class="info-item">
                  <span class="info-label">创建时间</span>
                  <span class="info-value">{{ formatDate(task.created_at) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">更新时间</span>
                  <span class="info-value">{{ formatDate(task.updated_at) }}</span>
                </div>
                <div v-if="task.deadline" class="info-item">
                  <span class="info-label">截止时间</span>
                  <span class="info-value">{{ formatDate(task.deadline) }}</span>
                </div>
                <div v-if="task.location" class="info-item">
                  <span class="info-label">地点</span>
                  <span class="info-value">{{ task.location }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">浏览次数</span>
                  <span class="info-value">{{ task.view_count || 0 }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">申请次数</span>
                  <span class="info-value">{{ task.application_count || 0 }}</span>
                </div>
              </div>
            </el-card>

            <!-- 客户信息 -->
            <el-card class="client-info">
              <template #header>
                <span>客户信息</span>
              </template>
              <user-card
                :user="task.client"
                :show-stats="false"
                :clickable="false"
              />
            </el-card>

            <!-- 律师信息 -->
            <el-card v-if="task.lawyer" class="lawyer-info">
              <template #header>
                <span>承接律师</span>
              </template>
              <user-card
                :user="task.lawyer"
                :show-stats="true"
                :clickable="false"
              />
            </el-card>

            <!-- 操作按钮 -->
            <el-card class="task-actions">
              <template #header>
                <span>操作</span>
              </template>
              <div class="action-list">
                <lk-button
                  v-if="canApply"
                  type="primary"
                  size="large"
                  block
                  @click="showApplyDialog = true"
                >
                  申请任务
                </lk-button>
                
                <lk-button
                  v-if="canEdit"
                  type="warning"
                  size="large"
                  block
                  @click="handleEditTask"
                >
                  编辑任务
                </lk-button>
                
                <lk-button
                  v-if="canComplete"
                  type="success"
                  size="large"
                  block
                  @click="handleCompleteTask"
                >
                  完成任务
                </lk-button>
                
                <lk-button
                  v-if="canCancel"
                  type="danger"
                  size="large"
                  block
                  @click="handleCancelTask"
                >
                  取消任务
                </lk-button>
                
                <lk-button
                  v-if="canRate"
                  type="primary"
                  size="large"
                  block
                  @click="showRatingDialog = true"
                >
                  评价任务
                </lk-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <div v-else class="empty-state">
        <el-empty description="任务不存在或已被删除" />
      </div>
    </div>
    
    <!-- 申请任务对话框 -->
    <apply-task-dialog
      v-model="showApplyDialog"
      :task="task"
      @success="handleApplySuccess"
    />
    
    <!-- 评价对话框 -->
    <rating-dialog
      v-model="showRatingDialog"
      :task="task"
      @success="handleRatingSuccess"
    />
  </workspace-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useTaskStore } from '@/stores/task'
import {
  ElRow,
  ElCol,
  ElCard,
  ElTag,
  ElIcon,
  ElProgress,
  ElBadge,
  ElEmpty,
  ElAvatar,
  ElRate,
  ElButton
} from 'element-plus'
import {
  Document,
  Check,
  Clock
} from '@element-plus/icons-vue'
import { WorkspaceLayout, UserCard, LkButton } from '@/components'
import ApplyTaskDialog from './components/ApplyTaskDialog.vue'
import RatingDialog from './components/RatingDialog.vue'
import { formatAmount, formatDate, formatRelativeTime, formatFileSize } from '@/utils/format'
import type { TaskApplication } from '@/types/task'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const taskStore = useTaskStore()

// 响应式数据
const showApplyDialog = ref(false)
const showRatingDialog = ref(false)
const applications = ref<TaskApplication[]>([])

// 计算属性
const task = computed(() => taskStore.currentTask)

const breadcrumbItems = computed(() => [
  { title: '工作台', path: '/dashboard' },
  { title: '任务管理', path: '/tasks' },
  { title: task.value?.title || '任务详情' }
])

const isClient = computed(() => {
  return userStore.user?.id === task.value?.client.id
})

const isLawyer = computed(() => {
  return userStore.user?.id === task.value?.lawyer?.id
})

const canApply = computed(() => {
  return userStore.userRole === 'lawyer' && 
         task.value?.status === 'pending' && 
         !task.value?.lawyer &&
         userStore.user?.id !== task.value?.client.id
})

const canEdit = computed(() => {
  return isClient.value && task.value?.status === 'pending'
})

const canComplete = computed(() => {
  return (isLawyer.value || isClient.value) && 
         task.value?.status === 'in_progress'
})

const canCancel = computed(() => {
  return isClient.value && 
         ['pending', 'in_progress'].includes(task.value?.status || '')
})

const canRate = computed(() => {
  return isClient.value && 
         task.value?.status === 'completed' && 
         !task.value?.rating
})

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

const downloadAttachment = (attachment: any) => {
  window.open(attachment.url, '_blank')
}

const handleEditTask = () => {
  router.push(`/tasks/${task.value?.id}/edit`)
}

const handleCompleteTask = async () => {
  if (task.value) {
    await taskStore.completeTask(task.value.id)
  }
}

const handleCancelTask = async () => {
  if (task.value) {
    await taskStore.cancelTask(task.value.id)
  }
}

const handleAcceptApplication = async (application: TaskApplication) => {
  // 实现接受申请逻辑
}

const handleRejectApplication = async (application: TaskApplication) => {
  // 实现拒绝申请逻辑
}

const handleApplySuccess = () => {
  showApplyDialog.value = false
}

const handleRatingSuccess = () => {
  showRatingDialog.value = false
}

onMounted(async () => {
  const taskId = route.params.id as string
  if (taskId) {
    await taskStore.fetchTask(taskId)
    
    // 如果是客户且任务状态为待处理，加载申请列表
    if (isClient.value && task.value?.status === 'pending') {
      // 加载申请列表的逻辑
    }
  }
})
</script>

<style lang="scss" scoped>
.task-detail-container {
  padding: 24px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  
  .header-left {
    flex: 1;
    
    h1 {
      font-size: 28px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 16px 0;
      line-height: 1.2;
    }
    
    .task-meta {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
  }
  
  .header-right {
    .task-amount {
      text-align: right;
      
      .amount-label {
        display: block;
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin-bottom: 4px;
      }
      
      .amount-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-color-danger);
      }
    }
  }
}

.task-description,
.task-attachments,
.task-progress,
.task-applications,
.task-rating {
  margin-bottom: 24px;
  
  .description-content {
    line-height: 1.6;
    
    .requirements {
      margin-top: 24px;
      padding-top: 24px;
      border-top: 1px solid var(--el-border-color-lighter);
      
      h4 {
        margin: 0 0 12px 0;
        color: var(--el-text-color-primary);
      }
    }
  }
  
  .attachment-list {
    .attachment-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .attachment-info {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .attachment-icon {
          font-size: 24px;
          color: var(--el-color-primary);
        }
        
        .attachment-details {
          .attachment-name {
            font-weight: 500;
            color: var(--el-text-color-primary);
          }
          
          .attachment-meta {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            margin-top: 2px;
          }
        }
      }
    }
  }
  
  .progress-content {
    .milestones {
      margin-top: 24px;
      
      .milestone-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px 0;
        border-bottom: 1px solid var(--el-border-color-lighter);
        
        &:last-child {
          border-bottom: none;
        }
        
        &.completed {
          .milestone-icon {
            color: var(--el-color-success);
          }
          
          .milestone-title {
            color: var(--el-color-success);
          }
        }
        
        .milestone-icon {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          background: var(--el-bg-color-page);
          color: var(--el-text-color-secondary);
          flex-shrink: 0;
        }
        
        .milestone-content {
          flex: 1;
          
          .milestone-title {
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }
          
          .milestone-description {
            color: var(--el-text-color-regular);
            margin-bottom: 8px;
          }
          
          .milestone-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
  
  .application-list {
    .application-item {
      padding: 20px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .application-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .lawyer-info {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .lawyer-details {
            .lawyer-name {
              font-weight: 500;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }
            
            .lawyer-meta {
              display: flex;
              align-items: center;
              gap: 8px;
              font-size: 14px;
              color: var(--el-text-color-secondary);
            }
          }
        }
        
        .application-amount {
          font-size: 18px;
          font-weight: 600;
          color: var(--el-color-danger);
        }
      }
      
      .application-content {
        margin-bottom: 16px;
        
        p {
          color: var(--el-text-color-regular);
          line-height: 1.5;
          margin: 0 0 8px 0;
        }
        
        .application-meta {
          display: flex;
          gap: 16px;
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .application-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
  
  .rating-content {
    .rating-score {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      
      .rating-text {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
    
    .rating-review {
      p {
        color: var(--el-text-color-regular);
        line-height: 1.6;
        margin: 0 0 8px 0;
      }
      
      .rating-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

.task-info,
.client-info,
.lawyer-info,
.task-actions {
  margin-bottom: 24px;
  
  .info-list {
    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .info-label {
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }
      
      .info-value {
        color: var(--el-text-color-primary);
        font-weight: 500;
      }
    }
  }
  
  .action-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

// 响应式设计
@media (max-width: 768px) {
  .task-detail-container {
    padding: 16px;
  }
  
  .task-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    
    .header-right {
      width: 100%;
      
      .task-amount {
        text-align: left;
      }
    }
  }
  
  .application-header {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 12px;
  }
}
</style>