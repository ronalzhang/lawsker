import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import {
  authGuard,
  titleGuard,
  progressGuard,
  finishProgress,
  emailVerificationGuard,
  lawyerVerificationGuard
} from './guards'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  // 认证相关路由
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: {
      title: '注册',
      requiresAuth: false
    }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/auth/ForgotPasswordView.vue'),
    meta: {
      title: '忘记密码',
      requiresAuth: false
    }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/auth/ResetPasswordView.vue'),
    meta: {
      title: '重置密码',
      requiresAuth: false
    }
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/auth/VerifyEmailView.vue'),
    meta: {
      title: '邮箱验证',
      requiresAuth: true
    }
  },
  // 主要应用路由
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/DashboardView.vue'),
    meta: {
      title: '工作台',
      requiresAuth: true
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/ProfileView.vue'),
    meta: {
      title: '个人中心',
      requiresAuth: true
    }
  },
  // 律师相关路由
  {
    path: '/lawyer',
    name: 'LawyerWorkspace',
    component: () => import('@/views/lawyer/LawyerWorkspaceView.vue'),
    meta: {
      title: '律师工作台',
      requiresAuth: true,
      requiresRole: 'lawyer',
      requiresLawyerVerification: true
    }
  },
  {
    path: '/lawyer/certification',
    name: 'LawyerCertification',
    component: () => import('@/views/lawyer/CertificationView.vue'),
    meta: {
      title: '律师认证',
      requiresAuth: true,
      requiresRole: 'lawyer'
    }
  },
  {
    path: '/lawyer/certification-pending',
    name: 'LawyerCertificationPending',
    component: () => import('@/views/lawyer/CertificationPendingView.vue'),
    meta: {
      title: '认证审核中',
      requiresAuth: true,
      requiresRole: 'lawyer'
    }
  },
  // 机构相关路由
  {
    path: '/institution',
    name: 'InstitutionWorkspace',
    component: () => import('@/views/institution/InstitutionWorkspaceView.vue'),
    meta: {
      title: '机构工作台',
      requiresAuth: true,
      requiresRole: 'institution'
    }
  },
  // 管理员路由
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/AdminDashboardView.vue'),
    meta: {
      title: '管理后台',
      requiresAuth: true,
      requiresRole: 'admin'
    }
  },
  // 案件管理
  {
    path: '/cases',
    name: 'Cases',
    component: () => import('@/views/cases/CaseListView.vue'),
    meta: {
      title: '案件管理',
      requiresAuth: true
    }
  },
  {
    path: '/cases/:id',
    name: 'CaseDetail',
    component: () => import('@/views/cases/CaseDetailView.vue'),
    meta: {
      title: '案件详情',
      requiresAuth: true
    }
  },
  // 任务管理
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/tasks/TaskListView.vue'),
    meta: {
      title: '任务管理',
      requiresAuth: true
    }
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: () => import('@/views/tasks/TaskDetailView.vue'),
    meta: {
      title: '任务详情',
      requiresAuth: true
    }
  },
  // 状态页面
  {
    path: '/pending',
    name: 'AccountPending',
    component: () => import('@/views/status/AccountPendingView.vue'),
    meta: {
      title: '账户审核中',
      requiresAuth: true
    }
  },
  // 错误页面
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/ForbiddenView.vue'),
    meta: {
      title: '访问被拒绝'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: {
      title: '页面不存在'
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

// 应用路由守卫
router.beforeEach(progressGuard)
router.beforeEach(titleGuard)
router.beforeEach(authGuard)
router.beforeEach(emailVerificationGuard)
router.beforeEach(lawyerVerificationGuard)

router.afterEach(finishProgress)

export default router