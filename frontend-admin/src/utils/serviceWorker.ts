/**
 * Service Worker 注册和管理工具
 */

export interface ServiceWorkerManager {
  register(): Promise<ServiceWorkerRegistration | null>
  unregister(): Promise<boolean>
  update(): Promise<void>
  getCacheSize(): Promise<number>
  clearCache(cacheName?: string): Promise<boolean>
  prefetchResources(urls: string[]): Promise<Array<{ url: string; success: boolean; error?: string }>>
  onUpdateAvailable(callback: () => void): void
  onControllerChange(callback: () => void): void
}

class ServiceWorkerManagerImpl implements ServiceWorkerManager {
  private registration: ServiceWorkerRegistration | null = null
  private updateCallbacks: Array<() => void> = []
  private controllerCallbacks: Array<() => void> = []

  constructor() {
    this.setupEventListeners()
  }

  private setupEventListeners() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        this.controllerCallbacks.forEach(callback => callback())
      })
    }
  }

  async register(): Promise<ServiceWorkerRegistration | null> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker not supported')
      return null
    }

    try {
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      })

      console.log('Service Worker registered successfully')

      // 监听更新
      this.registration.addEventListener('updatefound', () => {
        const newWorker = this.registration!.installing
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // 新版本可用
              this.updateCallbacks.forEach(callback => callback())
            }
          })
        }
      })

      return this.registration
    } catch (error) {
      console.error('Service Worker registration failed:', error)
      return null
    }
  }

  async unregister(): Promise<boolean> {
    if (!this.registration) {
      return false
    }

    try {
      const result = await this.registration.unregister()
      console.log('Service Worker unregistered successfully')
      return result
    } catch (error) {
      console.error('Service Worker unregistration failed:', error)
      return false
    }
  }

  async update(): Promise<void> {
    if (!this.registration) {
      throw new Error('Service Worker not registered')
    }

    try {
      await this.registration.update()
      console.log('Service Worker update check completed')
    } catch (error) {
      console.error('Service Worker update failed:', error)
      throw error
    }
  }

  async getCacheSize(): Promise<number> {
    if (!navigator.serviceWorker.controller) {
      return 0
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel()
      
      messageChannel.port1.onmessage = (event) => {
        if (event.data.type === 'CACHE_SIZE') {
          resolve(event.data.payload)
        }
      }

      navigator.serviceWorker.controller.postMessage(
        { type: 'GET_CACHE_SIZE' },
        [messageChannel.port2]
      )
    })
  }

  async clearCache(cacheName?: string): Promise<boolean> {
    if (!navigator.serviceWorker.controller) {
      return false
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel()
      
      messageChannel.port1.onmessage = (event) => {
        if (event.data.type === 'CACHE_CLEARED') {
          resolve(event.data.payload)
        }
      }

      navigator.serviceWorker.controller.postMessage(
        { type: 'CLEAR_CACHE', payload: { cacheName } },
        [messageChannel.port2]
      )
    })
  }

  async prefetchResources(urls: string[]): Promise<Array<{ url: string; success: boolean; error?: string }>> {
    if (!navigator.serviceWorker.controller) {
      return urls.map(url => ({ url, success: false, error: 'Service Worker not available' }))
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel()
      
      messageChannel.port1.onmessage = (event) => {
        if (event.data.type === 'PREFETCH_COMPLETE') {
          resolve(event.data.payload)
        }
      }

      navigator.serviceWorker.controller.postMessage(
        { type: 'PREFETCH_RESOURCES', payload: { urls } },
        [messageChannel.port2]
      )
    })
  }

  onUpdateAvailable(callback: () => void): void {
    this.updateCallbacks.push(callback)
  }

  onControllerChange(callback: () => void): void {
    this.controllerCallbacks.push(callback)
  }

  // 跳过等待，立即激活新版本
  skipWaiting(): void {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' })
    }
  }

  // 检查是否有更新可用
  isUpdateAvailable(): boolean {
    return this.registration?.waiting !== null || false
  }

  // 获取Service Worker状态
  getStatus(): string {
    if (!('serviceWorker' in navigator)) {
      return 'not_supported'
    }

    if (!this.registration) {
      return 'not_registered'
    }

    if (this.registration.active) {
      return 'active'
    }

    if (this.registration.installing) {
      return 'installing'
    }

    if (this.registration.waiting) {
      return 'waiting'
    }

    return 'unknown'
  }
}

// 全局实例
export const serviceWorkerManager = new ServiceWorkerManagerImpl()

// 自动注册Service Worker
export async function initServiceWorker() {
  if (process.env.NODE_ENV === 'production') {
    try {
      await serviceWorkerManager.register()
      
      // 监听更新
      serviceWorkerManager.onUpdateAvailable(() => {
        console.log('New version available')
        // 可以在这里显示更新提示
        if (confirm('发现新版本，是否立即更新？')) {
          serviceWorkerManager.skipWaiting()
          window.location.reload()
        }
      })

      // 监听控制器变化
      serviceWorkerManager.onControllerChange(() => {
        console.log('Service Worker controller changed')
        window.location.reload()
      })

    } catch (error) {
      console.error('Service Worker initialization failed:', error)
    }
  }
}

// 缓存管理工具
export class CacheUtils {
  static async getCacheInfo() {
    const size = await serviceWorkerManager.getCacheSize()
    const status = serviceWorkerManager.getStatus()
    const updateAvailable = serviceWorkerManager.isUpdateAvailable()

    return {
      size: this.formatBytes(size),
      status,
      updateAvailable
    }
  }

  static async clearAllCache(): Promise<boolean> {
    return serviceWorkerManager.clearCache()
  }

  static async prefetchCriticalResources() {
    const criticalUrls = [
      '/api/v1/dashboard/stats',
      '/api/v1/users/me',
      // 添加其他关键资源
    ]

    return serviceWorkerManager.prefetchResources(criticalUrls)
  }

  private static formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B'
    
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
}

// 网络状态监控
export class NetworkMonitor {
  private callbacks: Array<(online: boolean) => void> = []
  private _isOnline = navigator.onLine

  constructor() {
    this.setupEventListeners()
  }

  private setupEventListeners() {
    window.addEventListener('online', () => {
      this._isOnline = true
      this.notifyCallbacks(true)
    })

    window.addEventListener('offline', () => {
      this._isOnline = false
      this.notifyCallbacks(false)
    })
  }

  private notifyCallbacks(online: boolean) {
    this.callbacks.forEach(callback => callback(online))
  }

  get isOnline(): boolean {
    return this._isOnline
  }

  onStatusChange(callback: (online: boolean) => void): () => void {
    this.callbacks.push(callback)
    
    // 返回取消监听的函数
    return () => {
      const index = this.callbacks.indexOf(callback)
      if (index > -1) {
        this.callbacks.splice(index, 1)
      }
    }
  }

  // 检测网络连接质量
  async checkConnectionQuality(): Promise<'fast' | 'slow' | 'offline'> {
    if (!this._isOnline) {
      return 'offline'
    }

    try {
      const start = performance.now()
      await fetch('/api/health', { 
        method: 'HEAD',
        cache: 'no-cache'
      })
      const duration = performance.now() - start

      return duration < 1000 ? 'fast' : 'slow'
    } catch {
      return 'offline'
    }
  }
}

// 全局网络监控实例
export const networkMonitor = new NetworkMonitor()