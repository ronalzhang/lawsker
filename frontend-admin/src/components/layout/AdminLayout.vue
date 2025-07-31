<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <div class="admin-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo" @click="$router.push('/dashboard')">
          <img src="/logo.png" alt="Lawsker" class="logo-img" />
          <span v-if="!sidebarCollapsed" class="logo-text">Lawsker 管理后台</span>
        </div>
        <el-button
          :icon="sidebarCollapsed ? Expand : Fold"
          circle
          size="small"
          @click="toggleSidebar"
        />
      </div>
      
      <el-scrollbar class="sidebar-content">
        <el-menu
          :default-active="activeMenu"
          :collapse="sidebarCollapsed"
          :unique-opened="true"
          router
        >
          <template v-for="route in menuRoutes" :key="route.path">
            <el-sub-menu
              v-if="route.children && route.children.length > 0"
              :index="route.path"
            >
              <template #title>
                <el-icon v-if="route.meta?.icon">
                  <component :is="route.meta.icon" />
                </el-icon>
                <span>{{ route.meta?.title }}</span>
              </template>
              
              <el-menu-item
                v-for="child in route.children"
                :key="child.path"
                :index="child.path"
              >
                <el-icon v-if="child.meta?.icon">
                  <component :is="child.meta.icon" />
                </el-icon>
                <span>{{ child.meta?.title }}</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-menu-item v-else :index="route.path">
              <el-icon v-if="route.meta?.icon">
                <component :is="route.meta.icon" />
              </el-icon>
              <span>{{ route.meta?.title }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </div>
    
    <!-- 主内容区 -->
    <div class="admin-main" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- 顶部导航 -->
      <div class="admin-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 全屏切换 -->
          <el-tooltip content="全屏" placement="bottom">
            <el-button
              :icon="FullScreen"
              circle
              @click="toggleFullscreen"
            />
          </el-tooltip>
          
          <!-- 主题切换 -->
          <el-tooltip content="切换主题" placement="bottom">
            <el-button
              :icon="isDark ? Sunny : Moon"
              circle
              @click="toggleTheme"
            />
          </el-tooltip>
          
          <!-- 用户菜单 -->
          <el-dropdown @command="handleUserCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar">
                {{ userStore.user?.username?.charAt(0) }}
              </el-avatar>
              <span class="username">{{ userStore.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
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
      </div>
      
      <!-- 页面内容 -->
      <div class="admin-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  Expand,
  Fold,
  FullScreen,
  Sunny,
  Moon,
  ArrowDown,
  User,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const sidebarCollapsed = ref(false)
const isDark = ref(false)

// 计算属性
const activeMenu = computed(() => route.path)

const menuRoutes = computed(() => {
  return router.getRoutes().filter(route => 
    route.meta?.title && 
    !route.meta?.hideInMenu && 
    route.meta?.requiresAuth &&
    (!route.meta?.permission || userStore.hasPermission(route.meta.permission as string))
  )
})

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    title: item.meta?.title,
    path: item.path
  }))
})

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('admin_sidebar_collapsed', String(sidebarCollapsed.value))
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('admin_theme', isDark.value ? 'dark' : 'light')
}

const handleUserCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/system/settings')
      break
    case 'logout':
      userStore.logout()
      router.push('/login')
      break
  }
}

onMounted(() => {
  // 恢复侧边栏状态
  const savedCollapsed = localStorage.getItem('admin_sidebar_collapsed')
  if (savedCollapsed) {
    sidebarCollapsed.value = savedCollapsed === 'true'
  }
  
  // 恢复主题状态
  const savedTheme = localStorage.getItem('admin_theme')
  if (savedTheme) {
    isDark.value = savedTheme === 'dark'
    document.documentElement.classList.toggle('dark', isDark.value)
  }
})
</script>

<style lang="scss" scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  background: var(--el-bg-color-page);
}

.admin-sidebar {
  width: 240px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  
  &.collapsed {
    width: 64px;
  }
  
  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    height: 60px;
    
    .logo {
      display: flex;
      align-items: center;
      cursor: pointer;
      flex: 1;
      
      .logo-img {
        width: 28px;
        height: 28px;
        margin-right: 8px;
      }
      
      .logo-text {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-color-primary);
        white-space: nowrap;
      }
    }
  }
  
  .sidebar-content {
    flex: 1;
    
    :deep(.el-menu) {
      border-right: none;
      
      .el-menu-item,
      .el-sub-menu__title {
        height: 48px;
        line-height: 48px;
        
        &.is-active {
          background-color: var(--el-color-primary-light-9);
          color: var(--el-color-primary);
          border-right: 3px solid var(--el-color-primary);
        }
      }
    }
  }
}

.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px;
  transition: margin-left 0.3s;
  
  &.sidebar-collapsed {
    margin-left: 64px;
  }
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 24px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  
  .header-left {
    flex: 1;
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: var(--el-bg-color-page);
      }
      
      .username {
        font-size: 14px;
        color: var(--el-text-color-primary);
      }
    }
  }
}

.admin-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

// 响应式设计
@media (max-width: 768px) {
  .admin-main {
    margin-left: 0;
    
    &.sidebar-collapsed {
      margin-left: 0;
    }
  }
  
  .admin-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1001;
    height: 100vh;
    transform: translateX(-100%);
    transition: transform 0.3s;
    
    &.mobile-open {
      transform: translateX(0);
    }
  }
}
</style>