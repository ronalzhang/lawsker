<template>
  <div class="workspace-layout">
    <!-- 侧边栏 -->
    <lk-sidebar
      v-model:collapsed="sidebarCollapsed"
      :menu-items="menuItems"
      @menu-select="handleMenuSelect"
    />
    
    <!-- 主内容区 -->
    <div class="workspace-main" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- 顶部导航 -->
      <lk-header
        :show-nav="false"
        :notification-count="notificationCount"
        :message-count="messageCount"
        @notification-click="handleNotificationClick"
        @message-click="handleMessageClick"
        @user-command="handleUserCommand"
      />
      
      <!-- 面包屑导航 -->
      <div class="workspace-breadcrumb" v-if="showBreadcrumb">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item
            v-for="item in breadcrumbItems"
            :key="item.path"
            :to="item.path"
          >
            {{ item.title }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      
      <!-- 页面内容 -->
      <div class="workspace-content">
        <slot />
      </div>
    </div>
    
    <!-- 通知抽屉 -->
    <el-drawer
      v-model="notificationDrawerVisible"
      title="通知中心"
      direction="rtl"
      size="400px"
    >
      <div class="notification-drawer">
        <div class="notification-tabs">
          <el-tabs v-model="activeNotificationTab">
            <el-tab-pane label="全部" name="all" />
            <el-tab-pane label="未读" name="unread" />
            <el-tab-pane label="系统" name="system" />
          </el-tabs>
        </div>
        
        <div class="notification-list">
          <div
            v-for="notification in filteredNotifications"
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.read }"
            @click="handleNotificationRead(notification)"
          >
            <div class="notification-avatar">
              <el-avatar :size="32" :src="notification.avatar">
                <el-icon><Bell /></el-icon>
              </el-avatar>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">{{ formatRelativeTime(notification.created_at) }}</div>
            </div>
            <div class="notification-actions">
              <el-button
                v-if="!notification.read"
                type="primary"
                size="small"
                text
                @click.stop="markAsRead(notification.id)"
              >
                标记已读
              </el-button>
            </div>
          </div>
        </div>
        
        <div class="notification-footer">
          <el-button type="primary" text @click="markAllAsRead">
            全部标记为已读
          </el-button>
        </div>
      </div>
    </el-drawer>
    
    <!-- 消息抽屉 -->
    <el-drawer
      v-model="messageDrawerVisible"
      title="消息中心"
      direction="rtl"
      size="400px"
    >
      <div class="message-drawer">
        <!-- 消息列表 -->
        <div class="message-list">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-item"
            @click="handleMessageClick(message)"
          >
            <div class="message-avatar">
              <el-avatar :size="40" :src="message.sender.avatar">
                {{ message.sender.name.charAt(0) }}
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="message-sender">{{ message.sender.name }}</span>
                <span class="message-time">{{ formatRelativeTime(message.created_at) }}</span>
              </div>
              <div class="message-preview">{{ message.preview }}</div>
            </div>
            <div class="message-status">
              <el-badge v-if="message.unread_count > 0" :value="message.unread_count" />
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElDrawer,
  ElTabs,
  ElTabPane,
  ElAvatar,
  ElIcon,
  ElButton,
  ElBadge
} from 'element-plus'
import { Bell } from '@element-plus/icons-vue'
import { LkSidebar, LkHeader } from '@/components'
import { formatRelativeTime } from '@/utils/format'

interface BreadcrumbItem {
  title: string
  path?: string
}

interface Props {
  showBreadcrumb?: boolean
  breadcrumbItems?: BreadcrumbItem[]
  menuItems?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  showBreadcrumb: true,
  breadcrumbItems: () => [],
  menuItems: () => []
})

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const sidebarCollapsed = ref(false)
const notificationDrawerVisible = ref(false)
const messageDrawerVisible = ref(false)
const activeNotificationTab = ref('all')

const notifications = ref([
  {
    id: '1',
    title: '新任务分配',
    message: '您有一个新的法律咨询任务',
    type: 'task',
    read: false,
    avatar: '',
    created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString() // 30分钟前
  },
  {
    id: '2',
    title: '系统更新',
    message: '系统将于今晚进行维护更新',
    type: 'system',
    read: true,
    avatar: '',
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString() // 2小时前
  }
])

const messages = ref([
  {
    id: '1',
    sender: {
      id: '1',
      name: '张律师',
      avatar: ''
    },
    preview: '关于您的合同审查问题，我已经完成了初步审查...',
    unread_count: 2,
    created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString() // 15分钟前
  }
])

const notificationCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

const messageCount = computed(() => {
  return messages.value.reduce((total, msg) => total + msg.unread_count, 0)
})

const filteredNotifications = computed(() => {
  switch (activeNotificationTab.value) {
    case 'unread':
      return notifications.value.filter(n => !n.read)
    case 'system':
      return notifications.value.filter(n => n.type === 'system')
    default:
      return notifications.value
  }
})

const handleMenuSelect = (index: string) => {
  // 菜单选择处理
}

const handleNotificationClick = () => {
  notificationDrawerVisible.value = true
}

const handleMessageClick = () => {
  messageDrawerVisible.value = true
}

const handleUserCommand = (command: string) => {
  // 用户命令处理
}

const handleNotificationRead = (notification: any) => {
  if (!notification.read) {
    markAsRead(notification.id)
  }
  // 处理通知点击事件
}

const markAsRead = (notificationId: string) => {
  const notification = notifications.value.find(n => n.id === notificationId)
  if (notification) {
    notification.read = true
  }
}

const markAllAsRead = () => {
  notifications.value.forEach(n => {
    n.read = true
  })
}

onMounted(() => {
  // 初始化数据
})
</script>

<style scoped lang="scss">
.workspace-layout {
  display: flex;
  height: 100vh;
  background: var(--el-bg-color-page);
}

.workspace-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px;
  transition: margin-left 0.3s;
  
  &.sidebar-collapsed {
    margin-left: 64px;
  }
}

.workspace-breadcrumb {
  padding: 12px 24px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
}

.workspace-content {
  flex: 1;
  overflow: auto;
}

.notification-drawer {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .notification-tabs {
    border-bottom: 1px solid var(--el-border-color-light);
    margin-bottom: 16px;
  }
  
  .notification-list {
    flex: 1;
    overflow-y: auto;
    
    .notification-item {
      display: flex;
      padding: 16px;
      border-bottom: 1px solid var(--el-border-color-lighter);
      cursor: pointer;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: var(--el-bg-color-page);
      }
      
      &.unread {
        background-color: var(--el-color-primary-light-9);
        border-left: 3px solid var(--el-color-primary);
      }
      
      .notification-avatar {
        margin-right: 12px;
        flex-shrink: 0;
      }
      
      .notification-content {
        flex: 1;
        min-width: 0;
        
        .notification-title {
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .notification-message {
          font-size: 14px;
          color: var(--el-text-color-regular);
          margin-bottom: 8px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .notification-time {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .notification-actions {
        flex-shrink: 0;
        margin-left: 8px;
      }
    }
  }
  
  .notification-footer {
    padding: 16px;
    border-top: 1px solid var(--el-border-color-light);
    text-align: center;
  }
}

.message-drawer {
  height: 100%;
  
  .message-list {
    .message-item {
      display: flex;
      align-items: center;
      padding: 16px;
      border-bottom: 1px solid var(--el-border-color-lighter);
      cursor: pointer;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: var(--el-bg-color-page);
      }
      
      .message-avatar {
        margin-right: 12px;
        flex-shrink: 0;
      }
      
      .message-content {
        flex: 1;
        min-width: 0;
        
        .message-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
          
          .message-sender {
            font-weight: 500;
            color: var(--el-text-color-primary);
          }
          
          .message-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
        
        .message-preview {
          font-size: 14px;
          color: var(--el-text-color-regular);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
      
      .message-status {
        flex-shrink: 0;
        margin-left: 8px;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .workspace-main {
    margin-left: 0;
    
    &.sidebar-collapsed {
      margin-left: 0;
    }
  }
}
</style>