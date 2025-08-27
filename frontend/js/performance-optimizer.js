/**
 * Lawsker 数据可视化性能优化器
 * 专注于提升图表渲染性能和用户体验
 */

class PerformanceOptimizer {
    constructor() {
        this.chartCache = new Map();
        this.dataCache = new Map();
        this.renderQueue = [];
        this.isRendering = false;
        this.performanceMetrics = {
            renderTimes: [],
            loadTimes: [],
            interactionTimes: []
        };
        this.observers = new Map();
        this.init();
    }

    init() {
        this.setupIntersectionObserver();
        this.setupPerformanceMonitoring();
        this.setupDataPreloading();
        this.setupMemoryManagement();
        this.setupProgressiveLoading();
    }

    // 懒加载和交叉观察器
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.chartObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadChart(entry.target);
                        this.chartObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px',
                threshold: 0.1
            });

            // 观察所有图表容器
            document.addEventListener('DOMContentLoaded', () => {
                const chartContainers = document.querySelectorAll('.chart-container');
                chartContainers.forEach(container => {
                    this.chartObserver.observe(container);
                });
            });
        }
    }

    // 性能监控
    setupPerformanceMonitoring() {
        // 监控渲染性能
        this.performanceObserver = new PerformanceObserver((list) => {
            list.getEntries().forEach(entry => {
                if (entry.entryType === 'measure') {
                    this.recordMetric(entry.name, entry.duration);
                }
            });
        });

        if ('PerformanceObserver' in window) {
            this.performanceObserver.observe({ entryTypes: ['measure', 'navigation'] });
        }

        // 监控内存使用
        if ('memory' in performance) {
            setInterval(() => {
                this.monitorMemoryUsage();
            }, 30000);
        }
    }

    // 数据预加载
    setupDataPreloading() {
        this.dataPreloader = {
            preloadQueue: [],
            isPreloading: false,
            
            async preloadData(endpoint, priority = 'normal') {
                if (this.dataCache.has(endpoint)) {
                    return this.dataCache.get(endpoint);
                }

                const preloadItem = {
                    endpoint,
                    priority,
                    timestamp: Date.now()
                };

                this.preloadQueue.push(preloadItem);
                this.processPreloadQueue();
            },

            async processPreloadQueue() {
                if (this.isPreloading || this.preloadQueue.length === 0) return;

                this.isPreloading = true;
                
                // 按优先级排序
                this.preloadQueue.sort((a, b) => {
                    const priorityOrder = { high: 3, normal: 2, low: 1 };
                    return priorityOrder[b.priority] - priorityOrder[a.priority];
                });

                while (this.preloadQueue.length > 0) {
                    const item = this.preloadQueue.shift();
                    try {
                        await this.fetchAndCacheData(item.endpoint);
                    } catch (error) {
                        console.warn(`预加载数据失败: ${item.endpoint}`, error);
                    }
                }

                this.isPreloading = false;
            },

            async fetchAndCacheData(endpoint) {
                const startTime = performance.now();
                
                try {
                    // 模拟数据获取
                    const data = await this.simulateDataFetch(endpoint);
                    this.dataCache.set(endpoint, {
                        data,
                        timestamp: Date.now(),
                        ttl: 300000 // 5分钟缓存
                    });

                    const loadTime = performance.now() - startTime;
                    this.recordMetric('data-load', loadTime);
                    
                    return data;
                } catch (error) {
                    throw new Error(`数据获取失败: ${endpoint}`);
                }
            },

            simulateDataFetch(endpoint) {
                return new Promise((resolve) => {
                    // 模拟网络延迟
                    const delay = Math.random() * 500 + 100;
                    setTimeout(() => {
                        resolve(this.generateMockData(endpoint));
                    }, delay);
                });
            },

            generateMockData(endpoint) {
                // 根据端点生成模拟数据
                const dataTypes = {
                    'user-growth': this.generateUserGrowthData(),
                    'lawyer-levels': this.generateLawyerLevelData(),
                    'case-efficiency': this.generateCaseEfficiencyData(),
                    'revenue-sources': this.generateRevenueSourceData()
                };

                return dataTypes[endpoint] || { message: 'No data available' };
            },

            generateUserGrowthData() {
                const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
                return {
                    labels: months,
                    datasets: [{
                        label: '新增用户',
                        data: months.map(() => Math.floor(Math.random() * 5000) + 1000)
                    }, {
                        label: '活跃用户',
                        data: months.map(() => Math.floor(Math.random() * 3000) + 800)
                    }]
                };
            },

            generateLawyerLevelData() {
                return [
                    { value: 435, name: '见习律师' },
                    { value: 310, name: '初级律师' },
                    { value: 234, name: '中级律师' },
                    { value: 135, name: '高级律师' },
                    { value: 89, name: '资深律师' },
                    { value: 45, name: '专家律师' },
                    { value: 23, name: '首席律师' },
                    { value: 12, name: '合伙人' }
                ];
            },

            generateCaseEfficiencyData() {
                const categories = ['咨询类', '合同类', '诉讼类', '企业法务', '知识产权', '刑事辩护', '婚姻家庭'];
                return {
                    categories,
                    series: [{
                        name: '平均处理时间(小时)',
                        data: categories.map(() => Math.random() * 30 + 5)
                    }, {
                        name: '客户满意度(%)',
                        data: categories.map(() => Math.random() * 15 + 85)
                    }]
                };
            },

            generateRevenueSourceData() {
                return [
                    { value: 1280000, name: '会员订阅' },
                    { value: 854000, name: '案件费用' },
                    { value: 427000, name: 'Credits购买' },
                    { value: 228000, name: '企业服务' },
                    { value: 57000, name: '其他' }
                ];
            }
        };
    }

    // 内存管理
    setupMemoryManagement() {
        this.memoryManager = {
            maxCacheSize: 50, // 最大缓存项目数
            cleanupInterval: 300000, // 5分钟清理一次

            startCleanup() {
                setInterval(() => {
                    this.cleanupExpiredCache();
                    this.cleanupOldCharts();
                }, this.cleanupInterval);
            },

            cleanupExpiredCache() {
                const now = Date.now();
                for (const [key, value] of this.dataCache.entries()) {
                    if (now - value.timestamp > value.ttl) {
                        this.dataCache.delete(key);
                    }
                }
            },

            cleanupOldCharts() {
                if (this.chartCache.size > this.maxCacheSize) {
                    const entries = Array.from(this.chartCache.entries());
                    entries.sort((a, b) => a[1].lastAccessed - b[1].lastAccessed);
                    
                    // 删除最旧的图表
                    const toDelete = entries.slice(0, entries.length - this.maxCacheSize);
                    toDelete.forEach(([key, chart]) => {
                        if (chart.instance && chart.instance.destroy) {
                            chart.instance.destroy();
                        }
                        this.chartCache.delete(key);
                    });
                }
            },

            getMemoryUsage() {
                if ('memory' in performance) {
                    return {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    };
                }
                return null;
            }
        };

        this.memoryManager.startCleanup();
    }

    // 渐进式加载
    setupProgressiveLoading() {
        this.progressiveLoader = {
            loadingStates: new Map(),

            async loadChartProgressively(containerId, chartConfig) {
                const container = document.getElementById(containerId);
                if (!container) return;

                // 显示加载状态
                this.showLoadingState(container);

                try {
                    // 第一阶段：加载基础结构
                    await this.loadChartStructure(container, chartConfig);
                    
                    // 第二阶段：加载数据
                    await this.loadChartData(container, chartConfig);
                    
                    // 第三阶段：应用样式和动画
                    await this.applyChartStyling(container, chartConfig);
                    
                    // 完成加载
                    this.hideLoadingState(container);
                    
                } catch (error) {
                    this.showErrorState(container, error);
                }
            },

            showLoadingState(container) {
                container.innerHTML = `
                    <div class="progressive-loading">
                        <div class="loading-skeleton">
                            <div class="skeleton-header"></div>
                            <div class="skeleton-chart"></div>
                            <div class="skeleton-legend"></div>
                        </div>
                        <div class="loading-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 0%"></div>
                            </div>
                            <span class="progress-text">正在加载图表...</span>
                        </div>
                    </div>
                `;
            },

            async loadChartStructure(container, config) {
                return new Promise(resolve => {
                    setTimeout(() => {
                        this.updateProgress(container, 33, '正在构建图表结构...');
                        resolve();
                    }, 200);
                });
            },

            async loadChartData(container, config) {
                return new Promise(resolve => {
                    setTimeout(() => {
                        this.updateProgress(container, 66, '正在加载数据...');
                        resolve();
                    }, 300);
                });
            },

            async applyChartStyling(container, config) {
                return new Promise(resolve => {
                    setTimeout(() => {
                        this.updateProgress(container, 100, '正在应用样式...');
                        resolve();
                    }, 200);
                });
            },

            updateProgress(container, percentage, text) {
                const progressFill = container.querySelector('.progress-fill');
                const progressText = container.querySelector('.progress-text');
                
                if (progressFill) {
                    progressFill.style.width = `${percentage}%`;
                }
                if (progressText) {
                    progressText.textContent = text;
                }
            },

            hideLoadingState(container) {
                const loadingElement = container.querySelector('.progressive-loading');
                if (loadingElement) {
                    loadingElement.style.opacity = '0';
                    setTimeout(() => {
                        container.innerHTML = '<canvas></canvas>';
                    }, 300);
                }
            },

            showErrorState(container, error) {
                container.innerHTML = `
                    <div class="error-state">
                        <div class="error-icon">⚠️</div>
                        <div class="error-message">图表加载失败</div>
                        <div class="error-details">${error.message}</div>
                        <button class="retry-btn" onclick="retryLoadChart('${container.id}')">
                            重试
                        </button>
                    </div>
                `;
            }
        };
    }

    // 加载图表
    async loadChart(container) {
        const chartId = container.id;
        const startTime = performance.now();

        performance.mark(`chart-load-start-${chartId}`);

        try {
            // 检查缓存
            if (this.chartCache.has(chartId)) {
                const cachedChart = this.chartCache.get(chartId);
                cachedChart.lastAccessed = Date.now();
                return cachedChart.instance;
            }

            // 渐进式加载
            await this.progressiveLoader.loadChartProgressively(chartId, {});

            // 创建图表实例
            const chartInstance = await this.createChartInstance(container);

            // 缓存图表
            this.chartCache.set(chartId, {
                instance: chartInstance,
                created: Date.now(),
                lastAccessed: Date.now()
            });

            performance.mark(`chart-load-end-${chartId}`);
            performance.measure(`chart-load-${chartId}`, `chart-load-start-${chartId}`, `chart-load-end-${chartId}`);

            const loadTime = performance.now() - startTime;
            this.recordMetric('chart-load', loadTime);

            return chartInstance;

        } catch (error) {
            console.error(`图表加载失败: ${chartId}`, error);
            this.showErrorFallback(container);
        }
    }

    // 创建图表实例
    async createChartInstance(container) {
        const chartType = this.detectChartType(container);
        
        switch (chartType) {
            case 'line':
                return this.createLineChart(container);
            case 'pie':
                return this.createPieChart(container);
            case 'bar':
                return this.createBarChart(container);
            default:
                return this.createDefaultChart(container);
        }
    }

    detectChartType(container) {
        const id = container.id;
        if (id.includes('growth') || id.includes('trend')) return 'line';
        if (id.includes('level') || id.includes('distribution')) return 'pie';
        if (id.includes('efficiency') || id.includes('comparison')) return 'bar';
        return 'line';
    }

    // 创建折线图
    createLineChart(container) {
        return new Promise((resolve) => {
            const canvas = container.querySelector('canvas');
            if (!canvas) {
                container.innerHTML = '<canvas></canvas>';
            }
            
            // 模拟图表创建
            setTimeout(() => {
                const mockChart = {
                    type: 'line',
                    container: container,
                    destroy: () => {
                        container.innerHTML = '';
                    },
                    update: () => {
                        console.log('Chart updated');
                    },
                    resize: () => {
                        console.log('Chart resized');
                    }
                };
                resolve(mockChart);
            }, 100);
        });
    }

    // 创建饼图
    createPieChart(container) {
        return new Promise((resolve) => {
            // 模拟ECharts饼图创建
            setTimeout(() => {
                const mockChart = {
                    type: 'pie',
                    container: container,
                    dispose: () => {
                        container.innerHTML = '';
                    },
                    setOption: (option) => {
                        console.log('Chart option set', option);
                    },
                    resize: () => {
                        console.log('Chart resized');
                    }
                };
                resolve(mockChart);
            }, 150);
        });
    }

    // 创建柱状图
    createBarChart(container) {
        return new Promise((resolve) => {
            setTimeout(() => {
                const mockChart = {
                    type: 'bar',
                    container: container,
                    dispose: () => {
                        container.innerHTML = '';
                    },
                    setOption: (option) => {
                        console.log('Chart option set', option);
                    },
                    resize: () => {
                        console.log('Chart resized');
                    }
                };
                resolve(mockChart);
            }, 120);
        });
    }

    // 创建默认图表
    createDefaultChart(container) {
        return this.createLineChart(container);
    }

    // 记录性能指标
    recordMetric(type, duration) {
        if (!this.performanceMetrics[type]) {
            this.performanceMetrics[type] = [];
        }
        
        this.performanceMetrics[type].push({
            duration,
            timestamp: Date.now()
        });

        // 保持最近100条记录
        if (this.performanceMetrics[type].length > 100) {
            this.performanceMetrics[type] = this.performanceMetrics[type].slice(-100);
        }

        // 实时性能分析
        this.analyzePerformance(type);
    }

    // 性能分析
    analyzePerformance(type) {
        const metrics = this.performanceMetrics[type];
        if (metrics.length < 5) return;

        const recent = metrics.slice(-10);
        const average = recent.reduce((sum, m) => sum + m.duration, 0) / recent.length;
        
        // 性能阈值检查
        const thresholds = {
            'chart-load': 2000,
            'data-load': 1000,
            'render': 500
        };

        if (average > thresholds[type]) {
            console.warn(`性能警告: ${type} 平均耗时 ${average.toFixed(2)}ms，超过阈值 ${thresholds[type]}ms`);
            this.optimizePerformance(type);
        }
    }

    // 性能优化
    optimizePerformance(type) {
        switch (type) {
            case 'chart-load':
                this.optimizeChartLoading();
                break;
            case 'data-load':
                this.optimizeDataLoading();
                break;
            case 'render':
                this.optimizeRendering();
                break;
        }
    }

    optimizeChartLoading() {
        // 增加预加载
        this.dataPreloader.preloadData('user-growth', 'high');
        this.dataPreloader.preloadData('lawyer-levels', 'high');
        
        // 减少同时加载的图表数量
        this.maxConcurrentCharts = Math.max(2, this.maxConcurrentCharts - 1);
    }

    optimizeDataLoading() {
        // 启用数据压缩
        this.enableDataCompression = true;
        
        // 增加缓存时间
        this.dataCache.forEach(item => {
            item.ttl = Math.min(item.ttl * 1.5, 600000); // 最大10分钟
        });
    }

    optimizeRendering() {
        // 启用渲染节流
        this.enableRenderThrottling = true;
        
        // 减少动画复杂度
        this.reduceAnimationComplexity = true;
    }

    // 监控内存使用
    monitorMemoryUsage() {
        const usage = this.memoryManager.getMemoryUsage();
        if (!usage) return;

        const usagePercent = (usage.used / usage.limit) * 100;
        
        if (usagePercent > 80) {
            console.warn(`内存使用率过高: ${usagePercent.toFixed(1)}%`);
            this.memoryManager.cleanupExpiredCache();
            this.memoryManager.cleanupOldCharts();
        }

        // 记录内存使用情况
        this.recordMetric('memory-usage', usagePercent);
    }

    // 错误回退
    showErrorFallback(container) {
        container.innerHTML = `
            <div class="chart-error-fallback">
                <div class="error-icon">📊</div>
                <div class="error-title">图表暂时无法显示</div>
                <div class="error-message">请稍后重试或刷新页面</div>
                <button class="retry-button" onclick="window.performanceOptimizer.retryChart('${container.id}')">
                    重试加载
                </button>
            </div>
        `;
    }

    // 重试加载图表
    async retryChart(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // 清除缓存
        this.chartCache.delete(containerId);
        
        // 重新加载
        await this.loadChart(container);
    }

    // 获取性能报告
    getPerformanceReport() {
        const report = {
            timestamp: new Date().toISOString(),
            metrics: {},
            cacheStats: {
                chartCacheSize: this.chartCache.size,
                dataCacheSize: this.dataCache.size
            },
            memoryUsage: this.memoryManager.getMemoryUsage()
        };

        // 计算各项指标的统计信息
        Object.keys(this.performanceMetrics).forEach(type => {
            const metrics = this.performanceMetrics[type];
            if (metrics.length > 0) {
                const durations = metrics.map(m => m.duration);
                report.metrics[type] = {
                    count: metrics.length,
                    average: durations.reduce((a, b) => a + b, 0) / durations.length,
                    min: Math.min(...durations),
                    max: Math.max(...durations),
                    recent: durations.slice(-10)
                };
            }
        });

        return report;
    }

    // 导出性能数据
    exportPerformanceData() {
        const report = this.getPerformanceReport();
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance-report-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // 销毁优化器
    destroy() {
        // 清理观察器
        if (this.chartObserver) {
            this.chartObserver.disconnect();
        }
        
        if (this.performanceObserver) {
            this.performanceObserver.disconnect();
        }

        // 清理缓存
        this.chartCache.clear();
        this.dataCache.clear();

        // 清理定时器
        this.memoryManager.cleanupInterval && clearInterval(this.memoryManager.cleanupInterval);
    }
}

// 全局实例
window.performanceOptimizer = new PerformanceOptimizer();

// 添加样式
const style = document.createElement('style');
style.textContent = `
    .progressive-loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        padding: 2rem;
    }

    .loading-skeleton {
        width: 100%;
        max-width: 400px;
        margin-bottom: 2rem;
    }

    .skeleton-header {
        height: 20px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 4px;
        margin-bottom: 1rem;
    }

    .skeleton-chart {
        height: 200px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .skeleton-legend {
        height: 40px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 4px;
    }

    @keyframes loading {
        0% {
            background-position: 200% 0;
        }
        100% {
            background-position: -200% 0;
        }
    }

    .loading-progress {
        width: 100%;
        max-width: 300px;
        text-align: center;
    }

    .progress-bar {
        width: 100%;
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 1rem;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .progress-text {
        font-size: 0.875rem;
        color: #6b7280;
    }

    .chart-error-fallback {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        padding: 2rem;
        text-align: center;
    }

    .error-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .error-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
    }

    .error-message {
        color: #6b7280;
        margin-bottom: 2rem;
    }

    .retry-button {
        padding: 0.75rem 1.5rem;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 0.5rem;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.2s ease;
    }

    .retry-button:hover {
        background: #1d4ed8;
    }

    .error-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        padding: 2rem;
        text-align: center;
        border: 2px dashed #e5e7eb;
        border-radius: 1rem;
    }

    .error-state .error-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    .error-state .error-message {
        font-size: 1.125rem;
        font-weight: 600;
        color: #dc2626;
        margin-bottom: 0.5rem;
    }

    .error-state .error-details {
        font-size: 0.875rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }

    .error-state .retry-btn {
        padding: 0.5rem 1rem;
        background: #dc2626;
        color: white;
        border: none;
        border-radius: 0.375rem;
        cursor: pointer;
        font-size: 0.875rem;
        transition: background 0.2s ease;
    }

    .error-state .retry-btn:hover {
        background: #b91c1c;
    }
`;

document.head.appendChild(style);

// 导出为模块（如果支持）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}