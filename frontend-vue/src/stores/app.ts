import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 侧边栏状态
  const sidebarCollapsed = ref(false)
  
  // 主题模式
  const isDark = ref(false)
  
  // 页面加载状态
  const pageLoading = ref(false)
  
  // 设备类型
  const device = ref<'desktop' | 'tablet' | 'mobile'>('desktop')
  
  // 动作
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed
  }
  
  const toggleTheme = () => {
    isDark.value = !isDark.value
    // 切换Element Plus主题
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
    // 保存到localStorage
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }
  
  const setTheme = (theme: 'light' | 'dark') => {
    isDark.value = theme === 'dark'
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }
  
  const setPageLoading = (loading: boolean) => {
    pageLoading.value = loading
  }
  
  const setDevice = (deviceType: 'desktop' | 'tablet' | 'mobile') => {
    device.value = deviceType
  }
  
  // 初始化主题
  const initTheme = () => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      setTheme(savedTheme as 'light' | 'dark')
    } else {
      // 检查系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setTheme(prefersDark ? 'dark' : 'light')
    }
  }
  
  // 初始化设备类型检测
  const initDevice = () => {
    const checkDevice = () => {
      const width = window.innerWidth
      if (width < 768) {
        setDevice('mobile')
      } else if (width < 1024) {
        setDevice('tablet')
      } else {
        setDevice('desktop')
      }
    }
    
    checkDevice()
    window.addEventListener('resize', checkDevice)
  }
  
  return {
    // 状态
    sidebarCollapsed: readonly(sidebarCollapsed),
    isDark: readonly(isDark),
    pageLoading: readonly(pageLoading),
    device: readonly(device),
    
    // 动作
    toggleSidebar,
    setSidebarCollapsed,
    toggleTheme,
    setTheme,
    setPageLoading,
    setDevice,
    initTheme,
    initDevice
  }
})