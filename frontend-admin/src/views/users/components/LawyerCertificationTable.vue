<template>
  <div class="lawyer-certification-table">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="statusFilter" @change="handleStatusFilter" placeholder="筛选状态" clearable>
        <el-option label="全部" value="" />
        <el-option label="待审核" value="pending" />
        <el-option label="已认证" value="verified" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      
      <el-input
        v-model="searchKeyword"
        placeholder="搜索律师姓名或执照号"
        :prefix-icon="Search"
        @input="handleSearch"
        style="width: 300px;"
        clearable
      />
      
      <el-button :icon="Refresh" @click="$emit('refresh')">
        刷新
      </el-button>
    </div>

    <!-- 表格 -->
    <el-table
      :data="filteredData"
      v-loading="loading"
      stripe
      style="width: 100%"
      :height="500"
    >
      <el-table-column
        prop="name"
        label="律师姓名"
        width="120"
        fixed="left"
      >
        <template #default="{ row }">
          <div class="lawyer-info">
            <span class="name">{{ row.name }}</span>
            <span class="license">{{ row.license_number }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="email"
        label="邮箱"
        width="200"
        show-overflow-tooltip
      />
      
      <el-table-column
        prop="phone"
        label="电话"
        width="130"
      />
      
      <el-table-column
        prop="status"
        label="状态"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="submitted_at"
        label="提交时间"
        width="160"
        sortable
      >
        <template #default="{ row }">
          <span class="time-cell">{{ formatTime(row.submitted_at) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="reviewed_at"
        label="审核时间"
        width="160"
        sortable
      >
        <template #default="{ row }">
          <span class="time-cell">
            {{ row.reviewed_at ? formatTime(row.reviewed_at) : '-' }}
          </span>
        </template>
      </el-table-column>
      
      <el-table-column
        label="证件材料"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <el-button
            size="small"
            type="primary"
            @click="handleViewDocuments(row)"
          >
            查看材料
          </el-button>
        </template>
      </el-table-column>
      
      <el-table-column
        label="操作"
        width="200"
        align="center"
        fixed="right"
      >
        <template #default="{ row }">
          <div v-if="row.status === 'pending'" class="action-buttons">
            <el-button
              size="small"
              type="success"
              @click="handleApprove(row)"
            >
              通过
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleReject(row)"
            >
              拒绝
            </el-button>
          </div>
          <div v-else class="action-buttons">
            <el-button
              size="small"
              type="info"
              @click="handleViewDetails(row)"
            >
              查看详情
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="!loading && (!data || data.length === 0)" class="empty-state">
      <el-empty description="暂无数据" />
    </div>

    <!-- 证件材料查看对话框 -->
    <el-dialog
      v-model="documentsDialogVisible"
      title="证件材料"
      width="800px"
    >
      <div v-if="selectedLawyer" class="documents-viewer">
        <div v-for="doc in selectedLawyer.documents" :key="doc.type" class="document-item">
          <div class="document-header">
            <span class="document-type">{{ doc.type }}</span>
            <el-tag :type="getDocumentStatusType(doc.status)" size="small">
              {{ getDocumentStatusText(doc.status) }}
            </el-tag>
          </div>
          <div class="document-content">
            <img :src="doc.url" :alt="doc.type" class="document-image" />
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="documentsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 审核操作对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      :title="reviewAction === 'approve' ? '通过认证' : '拒绝认证'"
      width="500px"
    >
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item v-if="reviewAction === 'approve'" label="备注">
          <el-input
            v-model="reviewForm.note"
            type="textarea"
            :rows="3"
            placeholder="可选择添加备注信息"
          />
        </el-form-item>
        
        <el-form-item v-if="reviewAction === 'reject'" label="拒绝原因" required>
          <el-input
            v-model="reviewForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入拒绝原因"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button
          :type="reviewAction === 'approve' ? 'success' : 'danger'"
          @click="handleConfirmReview"
          :disabled="reviewAction === 'reject' && !reviewForm.reason"
        >
          确认{{ reviewAction === 'approve' ? '通过' : '拒绝' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { LawyerCertificationData } from '@/types'

interface Props {
  data: LawyerCertificationData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  approve: [lawyerId: string, note?: string]
  reject: [lawyerId: string, reason: string]
  refresh: []
}>()

const statusFilter = ref('')
const searchKeyword = ref('')
const documentsDialogVisible = ref(false)
const reviewDialogVisible = ref(false)
const selectedLawyer = ref<LawyerCertificationData | null>(null)
const reviewAction = ref<'approve' | 'reject'>('approve')
const reviewForm = ref({
  note: '',
  reason: ''
})

// 过滤数据
const filteredData = computed(() => {
  let result = props.data

  // 状态筛选
  if (statusFilter.value) {
    result = result.filter(item => item.status === statusFilter.value)
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.name.toLowerCase().includes(keyword) ||
      item.license_number.toLowerCase().includes(keyword) ||
      item.email.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 格式化时间
const formatTime = (timeStr: string) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
}

// 获取状态类型
const getStatusType = (status: string) => {
  const typeMap = {
    pending: 'warning',
    verified: 'success',
    rejected: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap = {
    pending: '待审核',
    verified: '已认证',
    rejected: '已拒绝'
  }
  return textMap[status as keyof typeof textMap] || status
}

// 获取文档状态类型
const getDocumentStatusType = (status: string) => {
  const typeMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

// 获取文档状态文本
const getDocumentStatusText = (status: string) => {
  const textMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return textMap[status as keyof typeof textMap] || status
}

// 处理状态筛选
const handleStatusFilter = () => {
  // 筛选逻辑已在computed中处理
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

// 查看证件材料
const handleViewDocuments = (row: LawyerCertificationData) => {
  selectedLawyer.value = row
  documentsDialogVisible.value = true
}

// 查看详情
const handleViewDetails = (row: LawyerCertificationData) => {
  selectedLawyer.value = row
  documentsDialogVisible.value = true
}

// 通过认证
const handleApprove = (row: LawyerCertificationData) => {
  selectedLawyer.value = row
  reviewAction.value = 'approve'
  reviewForm.value = { note: '', reason: '' }
  reviewDialogVisible.value = true
}

// 拒绝认证
const handleReject = (row: LawyerCertificationData) => {
  selectedLawyer.value = row
  reviewAction.value = 'reject'
  reviewForm.value = { note: '', reason: '' }
  reviewDialogVisible.value = true
}

// 确认审核
const handleConfirmReview = () => {
  if (!selectedLawyer.value) return

  if (reviewAction.value === 'approve') {
    emit('approve', selectedLawyer.value.id, reviewForm.value.note)
  } else {
    emit('reject', selectedLawyer.value.id, reviewForm.value.reason)
  }

  reviewDialogVisible.value = false
}
</script>

<style lang="scss" scoped>
.lawyer-certification-table {
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: center;
  }
  
  .lawyer-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .name {
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    .license {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    }
  }
  
  .time-cell {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
    justify-content: center;
  }
  
  .empty-state {
    padding: 40px 0;
  }
  
  .documents-viewer {
    .document-item {
      margin-bottom: 20px;
      
      .document-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        
        .document-type {
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }
      
      .document-content {
        .document-image {
          max-width: 100%;
          max-height: 400px;
          border: 1px solid var(--el-border-color);
          border-radius: 4px;
        }
      }
    }
  }
  
  :deep(.el-table) {
    .el-table__row {
      &:hover {
        background-color: var(--el-table-row-hover-bg-color);
      }
    }
    
    .el-table__header {
      th {
        background-color: var(--el-bg-color-page);
        color: var(--el-text-color-primary);
        font-weight: 600;
      }
    }
  }
}
</style>