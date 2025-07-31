import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'

// 权限检查函数
export function hasPermission(userRole: string, requiredRole?: string | string[]): boolean {
  if (!requiredRole) return true
  
  const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
  
  // 管理员拥有所有权限
  if (userRole === 'admin') return true
  
  return roles.includes(userRole)
}

// 认证守卫
export async function authGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) {
  const userStore = useUserStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      // 尝试从token恢复登录状态
      const restored = await userStore.checkLoginStatus()
      
      if (!restored) {
        ElMessage.warning('请先登录')
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
    
    // 检查角色权限
    if (to.meta.requiresRole) {
      const userRole = userStore.user?.role || ''
      if (!hasPermission(userRole, to.meta.requiresRole)) {
        ElMessage.error('您没有权限访问此页面')
        next({ path: '/dashboard' })
        return
      }
    }
    
    // 检查账户状态
    if (userStore.user?.status === 'inactive') {
      ElMessage.error('您的账户已被禁用，请联系管理员')
      next({ path: '/login' })
      return
    }
    
    if (userStore.user?.status === 'pending') {
      ElMessage.warning('您的账户正在审核中，请耐心等待')
      next({ path: '/pending' })
      return
    }
  }
  
  // 已登录用户访问登录/注册页面，重定向到工作台
  if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
    next({ path: '/dashboard' })
    return
  }
  
  next()
}

// 页面标题守卫
export function titleGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) {
  // 设置页面标题
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - Lawsker`
  } else {
    document.title = 'Lawsker - 法律服务O2O平台'
  }
  
  next()
}

// 进度条守卫
export function progressGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) {
  NProgress.start()
  next()
}

// 完成进度条
export function finishProgress() {
  NProgress.done()
}

// 邮箱验证守卫
export function emailVerificationGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) {
  const userStore = useUserStore()
  
  // 检查是否需要邮箱验证
  if (to.meta.requiresEmailVerification && userStore.user && !userStore.user.email_verified) {
    ElMessage.warning('请先验证您的邮箱地址')
    next({ path: '/verify-email' })
    return
  }
  
  next()
}

// 律师认证守卫
export function lawyerVerificationGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) {
  const userStore = useUserStore()
  
  // 检查律师是否需要认证
  if (to.meta.requiresLawyerVerification && 
      userStore.user?.role === 'lawyer' && 
      userStore.user?.certification_status !== 'approved') {
    
    if (userStore.user?.certification_status === 'pending') {
      ElMessage.info('您的律师认证正在审核中')
      next({ path: '/lawyer/certification-pending' })
    } else {
      ElMessage.warning('请先完成律师认证')
      next({ path: '/lawyer/certification' })
    }
    return
  }
  
  next()
}