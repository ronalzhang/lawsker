<template>
  <div class="lk-case-list">
    <div class="lk-case-list__header" v-if="showHeader">
      <h3 class="lk-case-list__title">{{ title }}</h3>
      <div class="lk-case-list__actions">
        <slot name="header-actions" />
      </div>
    </div>

    <div class="lk-case-list__filters" v-if="showFilters">
      <el-form :model="filters" inline>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable>
            <el-option label="全部" value="" />
            <el-option label="民事纠纷" value="civil" />
            <el-option label="刑事案件" value="criminal" />
            <el-option label="商事纠纷" value="commercial" />
            <el-option label="行政案件" value="administrative" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索案件标题或描述"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
    </div>

    <div class="lk-case-list__content" v-loading="loading">
      <div class="lk-case-list__empty" v-if="!cases.length && !loading">
        <el-empty :description="emptyText" />
      </div>

      <div class="lk-case-list__items" v-else>
        <div
          class="lk-case-item"
          v-for="caseItem in cases"
          :key="caseItem.id"
          @click="handleCaseClick(caseItem)"
        >
          <div class="lk-case-item__header">
            <h4 class="lk-case-item__title">{{ caseItem.title }}</h4>
            <div class="lk-case-item__status">
              <el-tag :type="getStatusType(caseItem.status)">
                {{ getStatusText(caseItem.status) }}
              </el-tag>
            </div>
          </div>

          <div class="lk-case-item__meta">
            <span class="lk-case-item__type">{{ getCaseTypeText(caseItem.type) }}</span>
            <span class="lk-case-item__date">{{ formatDate(caseItem.createdAt) }}</span>
            <span class="lk-case-item__amount" v-if="caseItem.amount">
              ¥{{ formatAmount(caseItem.amount) }}
            </span>
          </div>

          <div class="lk-case-item__description" v-if="caseItem.description">
            {{ caseItem.description }}
          </div>

          <div class="lk-case-item__participants">
            <div class="lk-case-item__client" v-if="caseItem.client">
              <el-avatar :size="24" :src="caseItem.client.avatar" />
              <span>{{ caseItem.client.name }}</span>
            </div>
            <div class="lk-case-item__lawyer" v-if="caseItem.lawyer">
              <el-avatar :size="24" :src="caseItem.lawyer.avatar" />
              <span>{{ caseItem.lawyer.name }}</span>
            </div>
          </div>

          <div class="lk-case-item__actions">
            <slot name="case-actions" :case="caseItem">
              <lk-button size="small" @click.stop="handleViewCase(caseItem)">
                查看详情
              </lk-button>
              <lk-button
                size="small"
                type="primary"
                v-if="caseItem.status === 'pending'"
                @click.stop="handleAcceptCase(caseItem)"
              >
                接受案件
              </lk-button>
            </slot>
          </div>
        </div>
      </div>
    </div>

    <div class="lk-case-list__pagination" v-if="showPagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElForm, ElFormItem, ElSelect, ElOption, ElInput, ElButton, ElIcon, ElEmpty, ElTag, ElAvatar, ElPagination } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import LkButton from '../../common/Button/index.vue'
import { formatDate, formatAmount } from '@/utils/format'

interface CaseParticipant {
  id: string | number
  name: string
  avatar?: string
}

interface CaseItem {
  id: string | number
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  type: 'civil' | 'criminal' | 'commercial' | 'administrative'
  amount?: number
  createdAt: string
  client?: CaseParticipant
  lawyer?: CaseParticipant
}

interface Props {
  cases: CaseItem[]
  loading?: boolean
  showHeader?: boolean
  title?: string
  showFilters?: boolean
  showPagination?: boolean
  total?: number
  emptyText?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  showHeader: true,
  title: '案件列表',
  showFilters: true,
  showPagination: true,
  total: 0,
  emptyText: '暂无案件数据'
})

const emit = defineEmits<{
  'case-click': [caseItem: CaseItem]
  'view-case': [caseItem: CaseItem]
  'accept-case': [caseItem: CaseItem]
  'filter-change': [filters: any]
  'page-change': [page: number]
  'size-change': [size: number]
}>()

const currentPage = ref(1)
const pageSize = ref(10)

const filters = reactive({
  status: '',
  type: '',
  keyword: ''
})

const getStatusType = (status: string) => {
  const typeMap = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getCaseTypeText = (type: string) => {
  const textMap = {
    civil: '民事纠纷',
    criminal: '刑事案件',
    commercial: '商事纠纷',
    administrative: '行政案件'
  }
  return textMap[type as keyof typeof textMap] || '其他'
}

const handleCaseClick = (caseItem: CaseItem) => {
  emit('case-click', caseItem)
}

const handleViewCase = (caseItem: CaseItem) => {
  emit('view-case', caseItem)
}

const handleAcceptCase = (caseItem: CaseItem) => {
  emit('accept-case', caseItem)
}

const handleSearch = () => {
  emit('filter-change', { ...filters })
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  emit('page-change', page)
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  emit('size-change', size)
}
</script>

<style scoped lang="scss">
.lk-case-list {
  .lk-case-list__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    .lk-case-list__title {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }

  .lk-case-list__filters {
    margin-bottom: 20px;
    padding: 16px;
    background: var(--el-bg-color-page);
    border-radius: var(--el-border-radius-base);

    .el-form {
      margin-bottom: 0;
    }

    .el-form-item {
      margin-bottom: 0;
    }
  }

  .lk-case-list__content {
    min-height: 200px;
  }

  .lk-case-list__empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
  }

  .lk-case-list__items {
    display: grid;
    gap: 16px;
  }

  .lk-case-item {
    padding: 20px;
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color-light);
    border-radius: var(--el-border-radius-base);
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      border-color: var(--el-color-primary);
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    }

    .lk-case-item__header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 12px;

      .lk-case-item__title {
        margin: 0;
        font-size: 16px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        flex: 1;
        margin-right: 12px;
      }

      .lk-case-item__status {
        flex-shrink: 0;
      }
    }

    .lk-case-item__meta {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 12px;
      font-size: 14px;
      color: var(--el-text-color-secondary);

      .lk-case-item__type {
        color: var(--el-color-primary);
        font-weight: 500;
      }

      .lk-case-item__amount {
        color: var(--el-color-danger);
        font-weight: 600;
      }
    }

    .lk-case-item__description {
      margin-bottom: 16px;
      color: var(--el-text-color-regular);
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .lk-case-item__participants {
      display: flex;
      align-items: center;
      gap: 20px;
      margin-bottom: 16px;

      .lk-case-item__client,
      .lk-case-item__lawyer {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        color: var(--el-text-color-regular);

        .el-avatar {
          flex-shrink: 0;
        }
      }
    }

    .lk-case-item__actions {
      display: flex;
      gap: 8px;
      padding-top: 16px;
      border-top: 1px solid var(--el-border-color-lighter);
    }
  }

  .lk-case-list__pagination {
    margin-top: 20px;
    text-align: right;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .lk-case-list {
    .lk-case-list__filters {
      .el-form {
        .el-form-item {
          display: block;
          margin-bottom: 16px;

          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }

    .lk-case-item {
      .lk-case-item__header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;

        .lk-case-item__title {
          margin-right: 0;
        }
      }

      .lk-case-item__meta {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
      }

      .lk-case-item__participants {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }

      .lk-case-item__actions {
        flex-direction: column;
        gap: 8px;
      }
    }

    .lk-case-list__pagination {
      text-align: center;
    }
  }
}
</style>