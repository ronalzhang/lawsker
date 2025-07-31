import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import router from './router'
import './styles/index.scss'

// 性能优化工具
import { performanceMonitor } from './utils/performance'
import { initServiceWorker } from './utils/serviceWorker'

// 开始性能监控
performanceMonitor.mark('app-start')

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 应用挂载
app.mount('#app')

// 结束性能监控
performanceMonitor.mark('app-mounted')
performanceMonitor.measure('app-initialization', 'app-start', 'app-mounted')

// 初始化Service Worker
initServiceWorker()

// 页面加载完成后的性能统计
window.addEventListener('load', () => {
  setTimeout(() => {
    const loadMetrics = performanceMonitor.getPageLoadMetrics()
    console.log('Page Load Metrics:', loadMetrics)
    
    const resourceMetrics = performanceMonitor.getResourceMetrics()
    console.log('Resource Metrics:', resourceMetrics)
    
    const appInitStats = performanceMonitor.getStats('app-initialization')
    console.log('App Initialization Stats:', appInitStats)
  }, 1000)
})