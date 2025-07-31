<template>
  <header class="lk-header">
    <div class="lk-header__container">
      <!-- Logo区域 -->
      <div class="lk-header__logo" @click="handleLogoClick">
        <img src="/logo.png" alt="Lawsker" class="lk-header__logo-img" />
        <span class="lk-header__logo-text">律思客</span>
      </div>

      <!-- 导航菜单 -->
      <nav class="lk-header__nav" v-if="showNav">
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :ellipsis="false"
          @select="handleMenuSelect"
        >
          <el-menu-item
            v-for="item in menuItems"
            :key="item.index"
            :index="item.index"
          >
            <el-icon v-if="item.icon">
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </el-menu>
      </nav>

      <!-- 搜索框 -->
      <div class="lk-header__search" v-if="showSearch">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索案件、律师..."
          :prefix-icon="Search"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearchClear"
        />
      </div>

      <!-- 右侧操作区 -->
      <div class="lk-header__actions">
        <!-- 通知 -->
        <div class="lk-header__notification" v-if="showNotification">
          <el-badge :value="notificationCount" :hidden="!notificationCount">
            <el-button
              :icon="Bell"
              circle
              @click="handleNotificationClick"
            />
          </el-badge>
        </div>

        <!-- 消息 -->
        <div class="lk-header__message" v-if="showMessage">
          <el-badge :value="messageCount" :hidden="!messageCount">
            <el-button
              :icon="ChatDotRound"
              circle
              @click="handleMessageClick"
            />
          </el-badge>
        </div>

        <!-- 用户菜单 -->
        <div class="lk-header__user" v-if="user">
          <el-dropdown @command="handleUserCommand">
            <div class="lk-header__user-info">
              <el-avatar :size="32" :src="user.avatar" />
              <span class="lk-header__username">{{ user.name }}</span>
              <el-icon class="lk-header__user-arrow">
                <ArrowDown />
              </el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- 登录按钮 -->
        <div class="lk-header__login" v-else>
          <lk-button @click="handleLogin">登录</lk-button>
          <lk-button type="primary" @click="handleRegister">注册</lk-button>
        </div>

        <!-- 移动端菜单按钮 -->
        <div class="lk-header__mobile-menu" v-if="showMobileMenu">
          <el-button
            :icon="Menu"
            circle
            @click="handleMobileMenuClick"
          />
        </div>
      </div>
    </div>

    <!-- 移动端抽屉菜单 -->
    <el-drawer
      v-model="mobileMenuVisible"
      title="菜单"
      direction="rtl"
      size="280px"
    >
      <el-menu
        :default-active="activeMenu"
        @select="handleMobileMenuSelect"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.index"
          :index="item.index"
        >
          <el-icon v-if="item.icon">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  ElMenu,
  ElMenuItem,
  ElInput,
  ElButton,
  ElBadge,
  ElAvatar,
  ElDropdown,
  ElDropdownMenu,
  ElDropdownItem,
  ElIcon,
  ElDrawer
} from 'element-plus'
import {
  Search,
  Bell,
  ChatDotRound,
  ArrowDown,
  User,
  Setting,
  SwitchButton,
  Menu,
  House,
  Briefcase,
  UserFilled,
  Document
} from '@element-plus/icons-vue'
import LkButton from '../../common/Button/index.vue'

interface MenuItem {
  index: string
  title: string
  icon?: any
  path?: string
}

interface Props {
  showNav?: boolean
  showSearch?: boolean
  showNotification?: boolean
  showMessage?: boolean
  showMobileMenu?: boolean
  menuItems?: MenuItem[]
  notificationCount?: number
  messageCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  showNav: true,
  showSearch: true,
  showNotification: true,
  showMessage: true,
  showMobileMenu: true,
  menuItems: () => [
    { index: '/', title: '首页', icon: House, path: '/' },
    { index: '/cases', title: '案件', icon: Briefcase, path: '/cases' },
    { index: '/lawyers', title: '律师', icon: UserFilled, path: '/lawyers' },
    { index: '/documents', title: '文档', icon: Document, path: '/documents' }
  ],
  notificationCount: 0,
  messageCount: 0
})

const emit = defineEmits<{
  'logo-click': []
  'menu-select': [index: string]
  'search': [keyword: string]
  'notification-click': []
  'message-click': []
  'user-command': [command: string]
  'login': []
  'register': []
}>()

const router = useRouter()
const userStore = useUserStore()

const searchKeyword = ref('')
const mobileMenuVisible = ref(false)

const user = computed(() => userStore.user)
const activeMenu = computed(() => router.currentRoute.value.path)

const handleLogoClick = () => {
  emit('logo-click')
  router.push('/')
}

const handleMenuSelect = (index: string) => {
  emit('menu-select', index)
  const menuItem = props.menuItems.find(item => item.index === index)
  if (menuItem?.path) {
    router.push(menuItem.path)
  }
}

const handleMobileMenuSelect = (index: string) => {
  mobileMenuVisible.value = false
  handleMenuSelect(index)
}

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    emit('search', searchKeyword.value.trim())
  }
}

const handleSearchClear = () => {
  searchKeyword.value = ''
  emit('search', '')
}

const handleNotificationClick = () => {
  emit('notification-click')
}

const handleMessageClick = () => {
  emit('message-click')
}

const handleUserCommand = (command: string) => {
  emit('user-command', command)
  
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      userStore.logout()
      router.push('/login')
      break
  }
}

const handleLogin = () => {
  emit('login')
  router.push('/login')
}

const handleRegister = () => {
  emit('register')
  router.push('/register')
}

const handleMobileMenuClick = () => {
  mobileMenuVisible.value = true
}
</script>

<style scoped lang="scss">
.lk-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .lk-header__container {
    display: flex;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    height: 60px;
  }

  .lk-header__logo {
    display: flex;
    align-items: center;
    cursor: pointer;
    margin-right: 40px;
    flex-shrink: 0;

    .lk-header__logo-img {
      width: 32px;
      height: 32px;
      margin-right: 8px;
    }

    .lk-header__logo-text {
      font-size: 20px;
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }

  .lk-header__nav {
    flex: 1;
    margin-right: 20px;

    :deep(.el-menu) {
      border-bottom: none;
      background: transparent;

      .el-menu-item {
        border-bottom: 2px solid transparent;
        color: var(--el-text-color-regular);

        &:hover,
        &.is-active {
          color: var(--el-color-primary);
          border-bottom-color: var(--el-color-primary);
          background: transparent;
        }
      }
    }
  }

  .lk-header__search {
    margin-right: 20px;
    width: 300px;
    flex-shrink: 0;

    .el-input {
      :deep(.el-input__wrapper) {
        border-radius: 20px;
      }
    }
  }

  .lk-header__actions {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;

    .lk-header__notification,
    .lk-header__message {
      .el-button {
        color: var(--el-text-color-regular);

        &:hover {
          color: var(--el-color-primary);
        }
      }
    }

    .lk-header__user {
      .lk-header__user-info {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: var(--el-border-radius-base);
        transition: background-color 0.3s;

        &:hover {
          background-color: var(--el-bg-color-page);
        }

        .lk-header__username {
          font-size: 14px;
          color: var(--el-text-color-primary);
          max-width: 100px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .lk-header__user-arrow {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }

    .lk-header__login {
      display: flex;
      gap: 8px;

      .lk-button + .lk-button {
        margin-left: 0;
      }
    }

    .lk-header__mobile-menu {
      display: none;
    }
  }
}

// 响应式设计
@media (max-width: 1024px) {
  .lk-header {
    .lk-header__search {
      width: 200px;
    }
  }
}

@media (max-width: 768px) {
  .lk-header {
    .lk-header__container {
      padding: 0 16px;
    }

    .lk-header__logo {
      margin-right: 20px;

      .lk-header__logo-text {
        display: none;
      }
    }

    .lk-header__nav {
      display: none;
    }

    .lk-header__search {
      display: none;
    }

    .lk-header__actions {
      .lk-header__notification,
      .lk-header__message {
        display: none;
      }

      .lk-header__user {
        .lk-header__user-info {
          .lk-header__username {
            display: none;
          }
        }
      }

      .lk-header__mobile-menu {
        display: block;
      }
    }
  }
}

@media (max-width: 480px) {
  .lk-header {
    .lk-header__container {
      padding: 0 12px;
    }

    .lk-header__logo {
      margin-right: 12px;
    }

    .lk-header__actions {
      gap: 8px;
    }
  }
}
</style>