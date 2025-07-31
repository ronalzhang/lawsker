// Service Worker for offline caching and performance optimization

const CACHE_NAME = 'lawsker-admin-v1.0.0'
const STATIC_CACHE = 'lawsker-static-v1.0.0'
const DYNAMIC_CACHE = 'lawsker-dynamic-v1.0.0'

// 需要缓存的静态资源
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  // 这些路径会在构建时自动填充
]

// 需要缓存的API路径
const API_CACHE_PATTERNS = [
  /^\/api\/v1\/dashboard/,
  /^\/api\/v1\/users/,
  /^\/api\/v1\/analytics/,
]

// 不需要缓存的API路径
const NO_CACHE_PATTERNS = [
  /^\/api\/v1\/auth/,
  /^\/api\/v1\/security/,
  /^\/api\/v1\/websocket/,
]

// 安装事件
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...')
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('Caching static assets')
        return cache.addAll(STATIC_ASSETS)
      })
      .then(() => {
        return self.skipWaiting()
      })
  )
})

// 激活事件
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...')
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && 
                cacheName !== STATIC_CACHE && 
                cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName)
              return caches.delete(cacheName)
            }
          })
        )
      })
      .then(() => {
        return self.clients.claim()
      })
  )
})

// 拦截请求
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)
  
  // 只处理同源请求
  if (url.origin !== location.origin) {
    return
  }
  
  // 处理导航请求
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request))
    return
  }
  
  // 处理API请求
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleAPIRequest(request))
    return
  }
  
  // 处理静态资源请求
  event.respondWith(handleStaticRequest(request))
})

// 处理导航请求
async function handleNavigationRequest(request) {
  try {
    // 尝试从网络获取
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok) {
      // 缓存成功的响应
      const cache = await caches.open(DYNAMIC_CACHE)
      cache.put(request, networkResponse.clone())
      return networkResponse
    }
    
    throw new Error('Network response not ok')
  } catch (error) {
    // 网络失败时从缓存获取
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }
    
    // 返回离线页面
    return caches.match('/index.html')
  }
}

// 处理API请求
async function handleAPIRequest(request) {
  const url = new URL(request.url)
  
  // 检查是否不需要缓存
  if (NO_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    return fetch(request)
  }
  
  // 检查是否需要缓存
  const shouldCache = API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))
  
  if (!shouldCache) {
    return fetch(request)
  }
  
  // 对于GET请求，尝试缓存优先策略
  if (request.method === 'GET') {
    return handleCacheFirst(request)
  }
  
  // 对于其他请求，使用网络优先策略
  return handleNetworkFirst(request)
}

// 处理静态资源请求
async function handleStaticRequest(request) {
  // 对于静态资源，使用缓存优先策略
  return handleCacheFirst(request)
}

// 缓存优先策略
async function handleCacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      // 后台更新缓存
      updateCache(request)
      return cachedResponse
    }
    
    // 缓存中没有，从网络获取
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE)
      cache.put(request, networkResponse.clone())
    }
    
    return networkResponse
  } catch (error) {
    console.error('Cache first strategy failed:', error)
    throw error
  }
}

// 网络优先策略
async function handleNetworkFirst(request) {
  try {
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok && request.method === 'GET') {
      const cache = await caches.open(DYNAMIC_CACHE)
      cache.put(request, networkResponse.clone())
    }
    
    return networkResponse
  } catch (error) {
    // 网络失败时从缓存获取
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }
    
    throw error
  }
}

// 后台更新缓存
async function updateCache(request) {
  try {
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE)
      cache.put(request, networkResponse.clone())
    }
  } catch (error) {
    console.log('Background cache update failed:', error)
  }
}

// 消息处理
self.addEventListener('message', (event) => {
  const { type, payload } = event.data
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting()
      break
      
    case 'GET_CACHE_SIZE':
      getCacheSize().then(size => {
        event.ports[0].postMessage({ type: 'CACHE_SIZE', payload: size })
      })
      break
      
    case 'CLEAR_CACHE':
      clearCache(payload.cacheName).then(success => {
        event.ports[0].postMessage({ type: 'CACHE_CLEARED', payload: success })
      })
      break
      
    case 'PREFETCH_RESOURCES':
      prefetchResources(payload.urls).then(results => {
        event.ports[0].postMessage({ type: 'PREFETCH_COMPLETE', payload: results })
      })
      break
  }
})

// 获取缓存大小
async function getCacheSize() {
  const cacheNames = await caches.keys()
  let totalSize = 0
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName)
    const requests = await cache.keys()
    
    for (const request of requests) {
      const response = await cache.match(request)
      if (response) {
        const blob = await response.blob()
        totalSize += blob.size
      }
    }
  }
  
  return totalSize
}

// 清理缓存
async function clearCache(cacheName) {
  try {
    if (cacheName) {
      return await caches.delete(cacheName)
    } else {
      const cacheNames = await caches.keys()
      const deletePromises = cacheNames.map(name => caches.delete(name))
      await Promise.all(deletePromises)
      return true
    }
  } catch (error) {
    console.error('Clear cache failed:', error)
    return false
  }
}

// 预取资源
async function prefetchResources(urls) {
  const results = []
  const cache = await caches.open(DYNAMIC_CACHE)
  
  for (const url of urls) {
    try {
      const response = await fetch(url)
      if (response.ok) {
        await cache.put(url, response.clone())
        results.push({ url, success: true })
      } else {
        results.push({ url, success: false, error: 'Network error' })
      }
    } catch (error) {
      results.push({ url, success: false, error: error.message })
    }
  }
  
  return results
}

// 定期清理过期缓存
setInterval(async () => {
  try {
    const cache = await caches.open(DYNAMIC_CACHE)
    const requests = await cache.keys()
    const now = Date.now()
    const maxAge = 24 * 60 * 60 * 1000 // 24小时
    
    for (const request of requests) {
      const response = await cache.match(request)
      if (response) {
        const dateHeader = response.headers.get('date')
        if (dateHeader) {
          const responseDate = new Date(dateHeader).getTime()
          if (now - responseDate > maxAge) {
            await cache.delete(request)
            console.log('Deleted expired cache:', request.url)
          }
        }
      }
    }
  } catch (error) {
    console.error('Cache cleanup failed:', error)
  }
}, 60 * 60 * 1000) // 每小时执行一次