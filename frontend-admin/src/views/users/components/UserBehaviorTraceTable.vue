<template>
  <div class="user-behavior-trace-table">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名"
        :prefix-icon="Search"
        @input="handleSearch"
        style="width: 300px;"
        clearable
      />
      
      <el-button :icon="Refresh" @click="$emit('refresh')">
        刷新
      </el-button>
    </div>

    <!-- 行为轨迹列表 -->
    <div class="behavior-traces">
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="!data || data.length === 0" class="empty-state">
        <el-empty description="暂无数据" />
      </div>
      
      <div v-else class="trace-list">
        <div v-for="trace in filteredData" :key="trace.user_id" class="trace-item">
          <!-- 用户信息头部 -->
          <div class="trace-header">
            <div class="user-info">
              <h4 class="username">{{ trace.username }}</h4>
              <div class="session-info">
                <span class="session-time">
                  {{ formatTime(trace.session_info.start_time) }} - 
                  {{ formatTime(trace.session_info.end_time) }}
                </span>
                <span class="session-duration">
                  时长: {{ formatDuration(trace.session_info.duration) }}
                </span>
                <span class="page-count">
                  访问页面: {{ trace.session_info.page_count }}
                </span>
              </div>
            </div>
            
            <div class="device-info">
              <el-tag size="small" type="info">{{ trace.session_info.device }}</el-tag>
              <el-tag size="small" type="primary">{{ trace.session_info.browser }}</el-tag>
            </div>
          </div>
          
          <!-- 行为轨迹时间线 -->
          <div class="trace-timeline">
            <el-timeline>
              <el-timeline-item
                v-for="(action, index) in trace.actions"
                :key="index"
                :timestamp="formatTime(action.timestamp)"
                placement="top"
                :type="getActionType(action.action)"
              >
                <div class="action-content">
                  <div class="action-header">
                    <span class="action-name">{{ action.action }}</span>
                    <span class="action-page">{{ action.page }}</span>
                  </div>
                  
                  <div class="action-details">
                    <span class="action-duration">
                      耗时: {{ formatDuration(action.duration) }}
                    </span>
                    
                    <div v-if="action.details" class="action-extra">
                      <el-popover
                        placement="top"
                        :width="300"
                        trigger="hover"
                      >
                        <template #reference>
                          <el-button size="small" type="text">查看详情</el-button>
                        </template>
                        <div class="details-content">
                          <pre>{{ JSON.stringify(action.details, null, 2) }}</pre>
                        </div>
                      </el-popover>
                    </div>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { UserBehaviorTrace } from '@/types'

interface Props {
  data: UserBehaviorTrace[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  refresh: []
}>()

const searchKeyword = ref('')

// 过滤数据
const filteredData = computed(() => {
  let result = props.data

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.username.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 格式化时间
const formatTime = (timeStr: string) => {
  return dayjs(timeStr).format('MM-DD HH:mm:ss')
}

// 格式化时长
const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}分钟`
  } else {
    return `${Math.round(seconds / 3600)}小时`
  }
}

// 获取操作类型
const getActionType = (action: string) => {
  // 根据操作类型返回不同的时间线节点类型
  if (action.includes('登录') || action.includes('login')) return 'success'
  if (action.includes('退出') || action.includes('logout')) return 'danger'
  if (action.includes('查看') || action.includes('view')) return 'primary'
  if (action.includes('创建') || action.includes('create')) return 'success'
  if (action.includes('删除') || action.includes('delete')) return 'danger'
  if (action.includes('编辑') || action.includes('edit')) return 'warning'
  return 'info'
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}
</script>

<style lang="scss" scoped>
.user-behavior-trace-table {
  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: center;
  }
  
  .behavior-traces {
    .loading-state {
      padding: 20px;
    }
    
    .empty-state {
      padding: 40px 0;
    }
    
    .trace-list {
      .trace-item {
        margin-bottom: 30px;
        border: 1px solid var(--el-border-color-light);
        border-radius: 8px;
        overflow: hidden;
        
        .trace-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 16px 20px;
          background-color: var(--el-bg-color-page);
          border-bottom: 1px solid var(--el-border-color-lighter);
          
          .user-info {
            .username {
              margin: 0 0 8px 0;
              color: var(--el-text-color-primary);
              font-size: 16px;
            }
            
            .session-info {
              display: flex;
              gap: 16px;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              
              .session-time {
                font-weight: 600;
              }
            }
          }
          
          .device-info {
            display: flex;
            gap: 8px;
            align-items: center;
          }
        }
        
        .trace-timeline {
          padding: 20px;
          
          :deep(.el-timeline) {
            .el-timeline-item__timestamp {
              font-size: 11px;
              color: var(--el-text-color-secondary);
            }
            
            .el-timeline-item__content {
              .action-content {
                .action-header {
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                  margin-bottom: 8px;
                  
                  .action-name {
                    font-weight: 600;
                    color: var(--el-text-color-primary);
                  }
                  
                  .action-page {
                    font-size: 12px;
                    color: var(--el-text-color-secondary);
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                  }
                }
                
                .action-details {
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                  
                  .action-duration {
                    font-size: 12px;
                    color: var(--el-text-color-secondary);
                  }
                  
                  .action-extra {
                    .details-content {
                      pre {
                        font-size: 12px;
                        color: var(--el-text-color-primary);
                        background-color: var(--el-bg-color-page);
                        padding: 8px;
                        border-radius: 4px;
                        margin: 0;
                        max-height: 200px;
                        overflow-y: auto;
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .user-behavior-trace-table {
    .trace-list {
      .trace-item {
        .trace-header {
          flex-direction: column;
          gap: 12px;
          align-items: flex-start;
          
          .user-info {
            .session-info {
              flex-direction: column;
              gap: 4px;
            }
          }
        }
      }
    }
  }
}
</style>