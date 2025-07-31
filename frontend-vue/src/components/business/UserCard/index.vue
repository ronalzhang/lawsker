<template>
  <div class="lk-user-card" :class="{ 'is-clickable': clickable }" @click="handleClick">
    <div class="lk-user-card__avatar">
      <el-avatar
        :size="avatarSize"
        :src="user.avatar"
        :icon="UserFilled"
        :alt="user.name"
      />
      <div class="lk-user-card__status" v-if="showStatus">
        <el-badge
          :value="statusText"
          :type="statusType"
          :is-dot="statusDot"
        />
      </div>
    </div>

    <div class="lk-user-card__content">
      <div class="lk-user-card__header">
        <h4 class="lk-user-card__name">{{ user.name }}</h4>
        <div class="lk-user-card__role" v-if="user.role">
          <el-tag :type="getRoleType(user.role)" size="small">
            {{ getRoleText(user.role) }}
          </el-tag>
        </div>
      </div>

      <div class="lk-user-card__info">
        <div class="lk-user-card__item" v-if="user.email">
          <el-icon><Message /></el-icon>
          <span>{{ user.email }}</span>
        </div>
        <div class="lk-user-card__item" v-if="user.phone">
          <el-icon><Phone /></el-icon>
          <span>{{ user.phone }}</span>
        </div>
        <div class="lk-user-card__item" v-if="user.location">
          <el-icon><Location /></el-icon>
          <span>{{ user.location }}</span>
        </div>
      </div>

      <div class="lk-user-card__stats" v-if="showStats">
        <div class="lk-user-card__stat">
          <span class="lk-user-card__stat-value">{{ user.caseCount || 0 }}</span>
          <span class="lk-user-card__stat-label">案件数</span>
        </div>
        <div class="lk-user-card__stat">
          <span class="lk-user-card__stat-value">{{ user.rating || 0 }}</span>
          <span class="lk-user-card__stat-label">评分</span>
        </div>
        <div class="lk-user-card__stat" v-if="user.role === 'lawyer'">
          <span class="lk-user-card__stat-value">{{ user.experience || 0 }}</span>
          <span class="lk-user-card__stat-label">年经验</span>
        </div>
      </div>

      <div class="lk-user-card__actions" v-if="$slots.actions">
        <slot name="actions" :user="user" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElAvatar, ElBadge, ElTag, ElIcon } from 'element-plus'
import { UserFilled, Message, Phone, Location } from '@element-plus/icons-vue'

interface User {
  id: string | number
  name: string
  avatar?: string
  email?: string
  phone?: string
  location?: string
  role?: 'admin' | 'lawyer' | 'user'
  status?: 'online' | 'offline' | 'busy'
  caseCount?: number
  rating?: number
  experience?: number
}

interface Props {
  user: User
  avatarSize?: number
  showStatus?: boolean
  showStats?: boolean
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  avatarSize: 60,
  showStatus: false,
  showStats: false,
  clickable: false
})

const emit = defineEmits<{
  click: [user: User]
}>()

const statusText = computed(() => {
  const statusMap = {
    online: '在线',
    offline: '离线',
    busy: '忙碌'
  }
  return statusMap[props.user.status || 'offline']
})

const statusType = computed(() => {
  const typeMap = {
    online: 'success',
    offline: 'info',
    busy: 'warning'
  }
  return typeMap[props.user.status || 'offline'] as any
})

const statusDot = computed(() => {
  return props.user.status === 'online'
})

const getRoleType = (role: string) => {
  const typeMap = {
    admin: 'danger',
    lawyer: 'primary',
    user: 'info'
  }
  return typeMap[role as keyof typeof typeMap] || 'info'
}

const getRoleText = (role: string) => {
  const textMap = {
    admin: '管理员',
    lawyer: '律师',
    user: '用户'
  }
  return textMap[role as keyof typeof textMap] || '用户'
}

const handleClick = () => {
  if (props.clickable) {
    emit('click', props.user)
  }
}
</script>

<style scoped lang="scss">
.lk-user-card {
  display: flex;
  padding: 16px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: var(--el-border-radius-base);
  transition: all 0.3s;

  &.is-clickable {
    cursor: pointer;

    &:hover {
      border-color: var(--el-color-primary);
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    }
  }

  .lk-user-card__avatar {
    position: relative;
    margin-right: 16px;
    flex-shrink: 0;

    .lk-user-card__status {
      position: absolute;
      bottom: 0;
      right: 0;
    }
  }

  .lk-user-card__content {
    flex: 1;
    min-width: 0;
  }

  .lk-user-card__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;

    .lk-user-card__name {
      margin: 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--el-text-color-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .lk-user-card__role {
      flex-shrink: 0;
      margin-left: 8px;
    }
  }

  .lk-user-card__info {
    margin-bottom: 12px;

    .lk-user-card__item {
      display: flex;
      align-items: center;
      margin-bottom: 4px;
      font-size: 14px;
      color: var(--el-text-color-regular);

      .el-icon {
        margin-right: 6px;
        color: var(--el-text-color-secondary);
      }

      span {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  .lk-user-card__stats {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;

    .lk-user-card__stat {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;

      .lk-user-card__stat-value {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-color-primary);
        line-height: 1;
      }

      .lk-user-card__stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-top: 4px;
      }
    }
  }

  .lk-user-card__actions {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .lk-user-card {
    flex-direction: column;
    text-align: center;

    .lk-user-card__avatar {
      margin-right: 0;
      margin-bottom: 12px;
      align-self: center;
    }

    .lk-user-card__header {
      flex-direction: column;
      align-items: center;
      gap: 8px;
    }

    .lk-user-card__stats {
      justify-content: center;
    }
  }
}
</style>