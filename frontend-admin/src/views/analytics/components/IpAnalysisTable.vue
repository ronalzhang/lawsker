<template>
  <div class="ip-analysis-table">
    <el-table
      :data="data"
      v-loading="loading"
      stripe
      style="width: 100%"
      :height="400"
    >
      <el-table-column
        prop="ip"
        label="IP地址"
        width="140"
        fixed="left"
      >
        <template #default="{ row }">
          <div class="ip-cell">
            <span class="ip-address">{{ row.ip }}</span>
            <el-tag
              v-if="row.is_suspicious"
              type="danger"
              size="small"
              class="suspicious-tag"
            >
              可疑
            </el-tag>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="country"
        label="国家"
        width="100"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <span class="country-cell">{{ row.country || '未知' }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="city"
        label="城市"
        width="120"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <span class="city-cell">{{ row.city || '未知' }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="requests"
        label="请求次数"
        width="100"
        align="right"
        sortable
      >
        <template #default="{ row }">
          <span class="number-cell">{{ row.requests.toLocaleString() }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        prop="last_seen"
        label="最后访问"
        width="160"
        sortable
      >
        <template #default="{ row }">
          <span class="time-cell">{{ formatTime(row.last_seen) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column
        label="操作"
        width="120"
        align="center"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button-group>
            <el-button
              size="small"
              type="primary"
              @click="handleViewDetails(row)"
            >
              详情
            </el-button>
            <el-button
              v-if="!row.is_suspicious"
              size="small"
              type="warning"
              @click="handleMarkSuspicious(row)"
            >
              标记
            </el-button>
            <el-button
              v-else
              size="small"
              type="success"
              @click="handleUnmarkSuspicious(row)"
            >
              取消
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="!loading && (!data || data.length === 0)" class="empty-state">
      <el-empty description="暂无数据" />
    </div>
    
    <!-- IP详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="IP详细信息"
      width="600px"
    >
      <div v-if="selectedIp" class="ip-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="IP地址">
            {{ selectedIp.ip }}
          </el-descriptions-item>
          <el-descriptions-item label="请求次数">
            {{ selectedIp.requests.toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="国家">
            {{ selectedIp.country || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="城市">
            {{ selectedIp.city || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后访问">
            {{ formatTime(selectedIp.last_seen) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedIp.is_suspicious ? 'danger' : 'success'">
              {{ selectedIp.is_suspicious ? '可疑IP' : '正常IP' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

interface IpData {
  ip: string
  country: string
  city: string
  requests: number
  last_seen: string
  is_suspicious: boolean
}

interface Props {
  data: IpData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  markSuspicious: [ip: string]
  unmarkSuspicious: [ip: string]
}>()

const detailDialogVisible = ref(false)
const selectedIp = ref<IpData | null>(null)

// 格式化时间
const formatTime = (timeStr: string) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm:ss')
}

// 查看IP详情
const handleViewDetails = (row: IpData) => {
  selectedIp.value = row
  detailDialogVisible.value = true
}

// 标记为可疑IP
const handleMarkSuspicious = async (row: IpData) => {
  try {
    await ElMessageBox.confirm(
      `确定要将IP地址 ${row.ip} 标记为可疑吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    emit('markSuspicious', row.ip)
    ElMessage.success('已标记为可疑IP')
  } catch {
    // 用户取消操作
  }
}

// 取消可疑标记
const handleUnmarkSuspicious = async (row: IpData) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消IP地址 ${row.ip} 的可疑标记吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    emit('unmarkSuspicious', row.ip)
    ElMessage.success('已取消可疑标记')
  } catch {
    // 用户取消操作
  }
}
</script>

<style lang="scss" scoped>
.ip-analysis-table {
  .ip-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .ip-address {
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 12px;
      font-weight: 600;
    }
    
    .suspicious-tag {
      align-self: flex-start;
    }
  }
  
  .country-cell,
  .city-cell {
    color: var(--el-text-color-primary);
  }
  
  .number-cell {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .time-cell {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .empty-state {
    padding: 40px 0;
  }
  
  .ip-details {
    :deep(.el-descriptions__label) {
      font-weight: 600;
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