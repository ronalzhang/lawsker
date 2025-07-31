/**
 * 前端性能优化工具
 */

// 图片懒加载
export class LazyImageLoader {
  private observer: IntersectionObserver | null = null
  private images: Set<HTMLImageElement> = new Set()

  constructor() {
    this.init()
  }

  private init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement
              this.loadImage(img)
              this.observer?.unobserve(img)
              this.images.delete(img)
            }
          })
        },
        {
          rootMargin: '50px'
        }
      )
    }
  }

  observe(img: HTMLImageElement) {
    if (this.observer) {
      this.observer.observe(img)
      this.images.add(img)
    } else {
      // 降级处理
      this.loadImage(img)
    }
  }

  private loadImage(img: HTMLImageElement) {
    const src = img.dataset.src
    if (src) {
      img.src = src
      img.removeAttribute('data-src')
      img.classList.add('loaded')
    }
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect()
      this.images.clear()
    }
  }
}

// 资源预加载
export class ResourcePreloader {
  private cache: Map<string, Promise<any>> = new Map()

  preloadImage(src: string): Promise<HTMLImageElement> {
    if (this.cache.has(src)) {
      return this.cache.get(src)!
    }

    const promise = new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = src
    })

    this.cache.set(src, promise)
    return promise
  }

  preloadScript(src: string): Promise<void> {
    if (this.cache.has(src)) {
      return this.cache.get(src)!
    }

    const promise = new Promise<void>((resolve, reject) => {
      const script = document.createElement('script')
      script.onload = () => resolve()
      script.onerror = reject
      script.src = src
      document.head.appendChild(script)
    })

    this.cache.set(src, promise)
    return promise
  }

  preloadCSS(href: string): Promise<void> {
    if (this.cache.has(href)) {
      return this.cache.get(href)!
    }

    const promise = new Promise<void>((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.onload = () => resolve()
      link.onerror = reject
      link.href = href
      document.head.appendChild(link)
    })

    this.cache.set(href, promise)
    return promise
  }
}

// 防抖函数
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      if (!immediate) func(...args)
    }

    const callNow = immediate && !timeout

    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)

    if (callNow) func(...args)
  }
}

// 节流函数
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

// 虚拟滚动优化
export class VirtualScrollOptimizer {
  private container: HTMLElement
  private itemHeight: number
  private visibleCount: number
  private totalCount: number
  private scrollTop = 0
  private startIndex = 0
  private endIndex = 0

  constructor(
    container: HTMLElement,
    itemHeight: number,
    visibleCount: number,
    totalCount: number
  ) {
    this.container = container
    this.itemHeight = itemHeight
    this.visibleCount = visibleCount
    this.totalCount = totalCount
    this.endIndex = Math.min(visibleCount, totalCount)
  }

  updateScrollPosition(scrollTop: number) {
    this.scrollTop = scrollTop
    this.startIndex = Math.floor(scrollTop / this.itemHeight)
    this.endIndex = Math.min(
      this.startIndex + this.visibleCount + 1,
      this.totalCount
    )
  }

  getVisibleRange() {
    return {
      start: this.startIndex,
      end: this.endIndex,
      offsetY: this.startIndex * this.itemHeight
    }
  }

  getTotalHeight() {
    return this.totalCount * this.itemHeight
  }
}

// 内存优化
export class MemoryOptimizer {
  private observers: Set<MutationObserver> = new Set()
  private intervals: Set<NodeJS.Timeout> = new Set()
  private listeners: Map<EventTarget, Map<string, EventListener>> = new Map()

  // 清理DOM观察器
  addMutationObserver(observer: MutationObserver) {
    this.observers.add(observer)
  }

  // 清理定时器
  addInterval(interval: NodeJS.Timeout) {
    this.intervals.add(interval)
  }

  // 管理事件监听器
  addEventListener(
    target: EventTarget,
    type: string,
    listener: EventListener,
    options?: boolean | AddEventListenerOptions
  ) {
    target.addEventListener(type, listener, options)
    
    if (!this.listeners.has(target)) {
      this.listeners.set(target, new Map())
    }
    this.listeners.get(target)!.set(type, listener)
  }

  // 清理所有资源
  cleanup() {
    // 清理观察器
    this.observers.forEach(observer => observer.disconnect())
    this.observers.clear()

    // 清理定时器
    this.intervals.forEach(interval => clearInterval(interval))
    this.intervals.clear()

    // 清理事件监听器
    this.listeners.forEach((listeners, target) => {
      listeners.forEach((listener, type) => {
        target.removeEventListener(type, listener)
      })
    })
    this.listeners.clear()
  }
}

// 性能监控
export class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map()

  // 记录性能指标
  mark(name: string) {
    performance.mark(name)
  }

  // 测量性能
  measure(name: string, startMark: string, endMark?: string) {
    performance.measure(name, startMark, endMark)
    
    const entries = performance.getEntriesByName(name, 'measure')
    const latestEntry = entries[entries.length - 1]
    
    if (latestEntry) {
      if (!this.metrics.has(name)) {
        this.metrics.set(name, [])
      }
      this.metrics.get(name)!.push(latestEntry.duration)
    }
  }

  // 获取性能统计
  getStats(name: string) {
    const values = this.metrics.get(name) || []
    if (values.length === 0) return null

    const sum = values.reduce((a, b) => a + b, 0)
    const avg = sum / values.length
    const min = Math.min(...values)
    const max = Math.max(...values)

    return { avg, min, max, count: values.length }
  }

  // 清理性能数据
  clear() {
    performance.clearMarks()
    performance.clearMeasures()
    this.metrics.clear()
  }

  // 监控页面加载性能
  getPageLoadMetrics() {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    
    return {
      dns: navigation.domainLookupEnd - navigation.domainLookupStart,
      tcp: navigation.connectEnd - navigation.connectStart,
      request: navigation.responseStart - navigation.requestStart,
      response: navigation.responseEnd - navigation.responseStart,
      dom: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      load: navigation.loadEventEnd - navigation.loadEventStart,
      total: navigation.loadEventEnd - navigation.navigationStart
    }
  }

  // 监控资源加载性能
  getResourceMetrics() {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]
    
    return resources.map(resource => ({
      name: resource.name,
      duration: resource.duration,
      size: resource.transferSize,
      type: this.getResourceType(resource.name)
    }))
  }

  private getResourceType(url: string): string {
    if (url.match(/\.(js|mjs)$/)) return 'script'
    if (url.match(/\.css$/)) return 'stylesheet'
    if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) return 'image'
    if (url.match(/\.(woff|woff2|ttf|eot)$/)) return 'font'
    return 'other'
  }
}

// 缓存管理
export class CacheManager {
  private cache: Map<string, { data: any; expires: number }> = new Map()
  private maxSize: number
  private defaultTTL: number

  constructor(maxSize = 100, defaultTTL = 5 * 60 * 1000) {
    this.maxSize = maxSize
    this.defaultTTL = defaultTTL
  }

  set(key: string, data: any, ttl = this.defaultTTL) {
    // 如果缓存已满，删除最旧的条目
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }

    this.cache.set(key, {
      data,
      expires: Date.now() + ttl
    })
  }

  get(key: string) {
    const item = this.cache.get(key)
    
    if (!item) return null
    
    if (Date.now() > item.expires) {
      this.cache.delete(key)
      return null
    }
    
    return item.data
  }

  has(key: string): boolean {
    return this.get(key) !== null
  }

  delete(key: string) {
    return this.cache.delete(key)
  }

  clear() {
    this.cache.clear()
  }

  // 清理过期缓存
  cleanup() {
    const now = Date.now()
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expires) {
        this.cache.delete(key)
      }
    }
  }
}

// 全局实例
export const lazyImageLoader = new LazyImageLoader()
export const resourcePreloader = new ResourcePreloader()
export const performanceMonitor = new PerformanceMonitor()
export const cacheManager = new CacheManager()

// 页面可见性API
export function onVisibilityChange(callback: (visible: boolean) => void) {
  const handleVisibilityChange = () => {
    callback(!document.hidden)
  }

  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  return () => {
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  }
}

// 网络状态监控
export function onNetworkChange(callback: (online: boolean) => void) {
  const handleOnline = () => callback(true)
  const handleOffline = () => callback(false)

  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)

  return () => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  }
}