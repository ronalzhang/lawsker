import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: {
      title: '管理员登录',
      requiresAuth: false,
      layout: 'blank'
    }
  },
  {
    path: '/',
    component: () => import('@/components/layout/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import(/* webpackChunkName: "dashboard" */ '@/views/dashboard/DashboardOverview.vue'),
        meta: {
          title: '数据概览',
          requiresAuth: true,
          icon: 'DataAnalysis'
        }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import(/* webpackChunkName: "users" */ '@/views/users/UserListView.vue'),
        meta: {
          title: '用户管理',
          requiresAuth: true,
          permission: 'user:read',
          icon: 'User'
        }
      },
      {
        path: 'lawyers',
        name: 'Lawyers',
        component: () => import('@/views/lawyers/LawyerListView.vue'),
        meta: {
          title: '律师管理',
          requiresAuth: true,
          permission: 'lawyer:read',
          icon: 'UserFilled'
        }
      },
      {
        path: 'cases',
        name: 'Cases',
        component: () => import('@/views/cases/CaseListView.vue'),
        meta: {
          title: '案件管理',
          requiresAuth: true,
          permission: 'case:read',
          icon: 'Briefcase'
        }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import(/* webpackChunkName: "analytics" */ '@/views/analytics/AnalyticsView.vue'),
        meta: {
          title: '数据分析',
          requiresAuth: true,
          permission: 'analytics:read',
          icon: 'TrendCharts'
        }
      },
      {
        path: 'system',
        name: 'System',
        redirect: '/system/settings',
        meta: {
          title: '系统管理',
          requiresAuth: true,
          permission: 'system:read',
          icon: 'Setting'
        },
        children: [
          {
            path: 'settings',
            name: 'SystemSettings',
            component: () => import('@/views/system/SettingsView.vue'),
            meta: {
              title: '系统设置',
              requiresAuth: true,
              permission: 'system:settings'
            }
          },
          {
            path: 'admins',
            name: 'AdminUsers',
            component: () => import('@/views/system/AdminUsersView.vue'),
            meta: {
              title: '管理员管理',
              requiresAuth: true,
              permission: 'admin:read'
            }
          },
          {
            path: 'logs',
            name: 'SystemLogs',
            component: () => import('@/views/system/LogsView.vue'),
            meta: {
              title: '系统日志',
              requiresAuth: true,
              permission: 'system:logs'
            }
          }
        ]
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: {
          title: '个人中心',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'demo',
        name: 'Demo',
        redirect: '/demo/virtual-table',
        meta: {
          title: '组件演示',
          requiresAuth: true,
          icon: 'Grid',
          hideInMenu: process.env.NODE_ENV === 'production'
        },
        children: [
          {
            path: 'virtual-table',
            name: 'VirtualTableDemo',
            component: () => import('@/views/demo/VirtualTableDemo.vue'),
            meta: {
              title: '虚拟滚动表格',
              requiresAuth: true
            }
          },
          {
            path: 'charts',
            name: 'ChartsDemo',
            component: () => import('@/views/demo/ChartsDemo.vue'),
            meta: {
              title: '实时图表',
              requiresAuth: true
            }
          },
          {
            path: 'export',
            name: 'ExportDemo',
            component: () => import('@/views/demo/ExportDemo.vue'),
            meta: {
              title: '数据导出',
              requiresAuth: true
            }
          }
        ]
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: {
      title: '页面不存在',
      hideInMenu: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  
  const userStore = useUserStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - Lawsker 管理后台`
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      // 尝试从本地存储恢复登录状态
      const restored = await userStore.checkLoginStatus()
      
      if (!restored) {
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
    
    // 检查权限
    if (to.meta.permission && !userStore.hasPermission(to.meta.permission as string)) {
      ElMessage.error('您没有权限访问此页面')
      next({ path: '/dashboard' })
      return
    }
  }
  
  // 已登录用户访问登录页面，重定向到首页
  if (to.path === '/login' && userStore.isLoggedIn) {
    next({ path: '/dashboard' })
    return
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router