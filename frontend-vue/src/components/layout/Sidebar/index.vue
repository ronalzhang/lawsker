<template>
  <aside class="lk-sidebar" :class="{ 'is-collapsed': collapsed }">
    <div class="lk-sidebar__header" v-if="showHeader">
      <div class="lk-sidebar__logo" v-if="!collapsed">
        <img src="/logo.png" alt="Lawsker" class="lk-sidebar__logo-img" />
        <span class="lk-sidebar__logo-text">律思客</span>
      </div>
      <el-button
        :icon="collapsed ? Expand : Fold"
        circle
        size="small"
        @click="handleToggle"
        class="lk-sidebar__toggle"
      />
    </div>

    <div class="lk-sidebar__content">
      <el-scrollbar>
        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          :unique-opened="uniqueOpened"
          :collapse-transition="false"
          @select="handleMenuSelect"
          @open="handleSubMenuOpen"
          @close="handleSubMenuClose"
        >
          <template v-for="item in menuItems" :key="item.index">
            <!-- 单级菜单 -->
            <el-menu-item
              v-if="!item.children"
              :index="item.index"
              :disabled="item.disabled"
            >
              <el-icon v-if="item.icon">
                <component :is="item.icon" />
              </el-icon>
              <template #title>
                <span>{{ item.title }}</span>
                <el-badge
                  v-if="item.badge"
                  :value="item.badge"
                  :type="item.badgeType"
                  class="lk-sidebar__badge"
                />
              </template>
            </el-menu-item>

            <!-- 多级菜单 -->
            <el-sub-menu
              v-else
              :index="item.index"
              :disabled="item.disabled"
            >
              <template #title>
                <el-icon v-if="item.icon">
                  <component :is="item.icon" />
                </el-icon>
                <span>{{ item.title }}</span>
                <el-badge
                  v-if="item.badge"
                  :value="item.badge"
                  :type="item.badgeType"
                  class="lk-sidebar__badge"
                />
              </template>
              
              <el-menu-item
                v-for="child in item.children"
                :key="child.index"
                :index="child.index"
                :disabled="child.disabled"
              >
                <el-icon v-if="child.icon">
                  <component :is="child.icon" />
                </el-icon>
                <template #title>
                  <span>{{ child.title }}</span>
                  <el-badge
                    v-if="child.badge"
                    :value="child.badge"
                    :type="child.badgeType"
                    class="lk-sidebar__badge"
                  />
                </template>
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </el-scrollbar>
    </div>

    <div class="lk-sidebar__footer" v-if="showFooter">
      <div class="lk-sidebar__user" v-if="user && !collapsed">
        <el-avatar :size="32" :src="user.avatar" />
        <div class="lk-sidebar__user-info">
          <div class="lk-sidebar__username">{{ user.name }}</div>
          <div class="lk-sidebar__user-role">{{ getRoleText(user.role) }}</div>
        </div>
      </div>
      
      <div class="lk-sidebar__actions">
        <el-tooltip content="设置" placement="top" v-if="collapsed">
          <el-button :icon="Setting" circle size="small" @click="handleSettings" />
        </el-tooltip>
        <el-button v-else size="small" @click="handleSettings">
          <el-icon><Setting /></el-icon>
          设置
        </el-button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  ElMenu,
  ElMenuItem,
  ElSubMenu,
  ElButton,
  ElIcon,
  ElScrollbar,
  ElAvatar,
  ElBadge,
  ElTooltip
} from 'element-plus'
import {
  Expand,
  Fold,
  Setting,
  House,
  Briefcase,
  UserFilled,
  Document,
  DataAnalysis,
  Tools,
  Bell,
  ChatDotRound
} from '@element-plus/icons-vue'

interface MenuItem {
  index: string
  title: string
  icon?: any
  path?: string
  disabled?: boolean
  badge?: string | number
  badgeType?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  children?: MenuItem[]
}

interface Props {
  collapsed?: boolean
  showHeader?: boolean
  showFooter?: boolean
  uniqueOpened?: boolean
  menuItems?: MenuItem[]
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  showHeader: true,
  showFooter: true,
  uniqueOpened: true,
  menuItems: () => [
    {
      index: '/',
      title: '工作台',
      icon: House,
      path: '/'
    },
    {
      index: '/cases',
      title: '案件管理',
      icon: Briefcase,
      children: [
        { index: '/cases/list', title: '案件列表', path: '/cases/list' },
        { index: '/cases/my', title: '我的案件', path: '/cases/my' },
        { index: '/cases/create', title: '创建案件', path: '/cases/create' }
      ]
    },
    {
      index: '/lawyers',
      title: '律师管理',
      icon: UserFilled,
      children: [
        { index: '/lawyers/list', title: '律师列表', path: '/lawyers/list' },
        { index: '/lawyers/applications', title: '认证申请', path: '/lawyers/applications', badge: 3, badgeType: 'danger' }
      ]
    },
    {
      index: '/documents',
      title: '文档中心',
      icon: Document,
      path: '/documents'
    },
    {
      index: '/analytics',
      title: '数据分析',
      icon: DataAnalysis,
      children: [
        { index: '/analytics/overview', title: '数据概览', path: '/analytics/overview' },
        { index: '/analytics/cases', title: '案件统计', path: '/analytics/cases' },
        { index: '/analytics/users', title: '用户分析', path: '/analytics/users' }
      ]
    },
    {
      index: '/notifications',
      title: '通知中心',
      icon: Bell,
      path: '/notifications',
      badge: 5,
      badgeType: 'warning'
    },
    {
      index: '/messages',
      title: '消息中心',
      icon: ChatDotRound,
      path: '/messages',
      badge: 2,
      badgeType: 'primary'
    },
    {
      index: '/system',
      title: '系统管理',
      icon: Tools,
      children: [
        { index: '/system/users', title: '用户管理', path: '/system/users' },
        { index: '/system/roles', title: '角色权限', path: '/system/roles' },
        { index: '/system/settings', title: '系统设置', path: '/system/settings' }
      ]
    }
  ]
})

const emit = defineEmits<{
  'update:collapsed': [collapsed: boolean]
  'menu-select': [index: string]
  'submenu-open': [index: string]
  'submenu-close': [index: string]
  'settings': []
}>()

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const activeMenu = computed(() => router.currentRoute.value.path)

const handleToggle = () => {
  emit('update:collapsed', !props.collapsed)
}

const handleMenuSelect = (index: string) => {
  emit('menu-select', index)
  
  // 查找菜单项并导航
  const findMenuItem = (items: MenuItem[], targetIndex: string): MenuItem | null => {
    for (const item of items) {
      if (item.index === targetIndex) {
        return item
      }
      if (item.children) {
        const found = findMenuItem(item.children, targetIndex)
        if (found) return found
      }
    }
    return null
  }
  
  const menuItem = findMenuItem(props.menuItems, index)
  if (menuItem?.path) {
    router.push(menuItem.path)
  }
}

const handleSubMenuOpen = (index: string) => {
  emit('submenu-open', index)
}

const handleSubMenuClose = (index: string) => {
  emit('submenu-close', index)
}

const handleSettings = () => {
  emit('settings')
  router.push('/settings')
}

const getRoleText = (role?: string) => {
  const roleMap = {
    admin: '管理员',
    lawyer: '律师',
    user: '用户'
  }
  return roleMap[role as keyof typeof roleMap] || '用户'
}
</script>

<style scoped lang="scss">
.lk-sidebar {
  width: 240px;
  height: 100vh;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;

  &.is-collapsed {
    width: 64px;
  }

  .lk-sidebar__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    height: 60px;
    box-sizing: border-box;

    .lk-sidebar__logo {
      display: flex;
      align-items: center;
      flex: 1;

      .lk-sidebar__logo-img {
        width: 28px;
        height: 28px;
        margin-right: 8px;
      }

      .lk-sidebar__logo-text {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-color-primary);
      }
    }

    .lk-sidebar__toggle {
      flex-shrink: 0;
    }
  }

  .lk-sidebar__content {
    flex: 1;
    overflow: hidden;

    :deep(.el-menu) {
      border-right: none;
      background: transparent;

      .el-menu-item,
      .el-sub-menu__title {
        height: 48px;
        line-height: 48px;
        color: var(--el-text-color-regular);

        &:hover {
          background-color: var(--el-color-primary-light-9);
          color: var(--el-color-primary);
        }

        &.is-active {
          background-color: var(--el-color-primary-light-8);
          color: var(--el-color-primary);
          border-right: 3px solid var(--el-color-primary);
        }

        .el-icon {
          margin-right: 8px;
          width: 16px;
          text-align: center;
        }
      }

      .el-sub-menu {
        .el-menu-item {
          padding-left: 48px !important;
          
          &.is-active {
            background-color: var(--el-color-primary-light-9);
          }
        }
      }

      &.el-menu--collapse {
        .el-menu-item,
        .el-sub-menu__title {
          padding: 0 20px;
          text-align: center;

          .el-icon {
            margin-right: 0;
          }
        }
      }
    }

    .lk-sidebar__badge {
      margin-left: auto;
    }
  }

  .lk-sidebar__footer {
    padding: 16px;
    border-top: 1px solid var(--el-border-color-lighter);

    .lk-sidebar__user {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      padding: 8px;
      background: var(--el-bg-color-page);
      border-radius: var(--el-border-radius-base);

      .lk-sidebar__user-info {
        margin-left: 8px;
        flex: 1;
        min-width: 0;

        .lk-sidebar__username {
          font-size: 14px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .lk-sidebar__user-role {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }

    .lk-sidebar__actions {
      text-align: center;

      .el-button {
        width: 100%;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .lk-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1001;
    transform: translateX(-100%);
    transition: transform 0.3s;

    &.is-mobile-open {
      transform: translateX(0);
    }
  }
}
</style>