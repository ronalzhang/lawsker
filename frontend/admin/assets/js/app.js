/**
 * 律刻管理后台 - 主应用文件
 * 负责应用初始化、路由管理和模块加载
 */

class AdminApp {
    constructor() {
        this.currentModule = null;
        this.modules = new Map();
        this.isLoading = false;
        this.eventBus = new EventBus();
        
        // 绑定方法上下文
        this.handleNavigation = this.handleNavigation.bind(this);
        this.handleSidebarToggle = this.handleSidebarToggle.bind(this);
        this.handleResize = this.handleResize.bind(this);
    }

    /**
     * 初始化应用
     */
    async init() {
        try {
            console.log('🚀 正在初始化律刻管理后台...');
            
            // 检查认证状态
            await this.checkAuth();
            
            // 初始化UI组件
            this.initUI();
            
            // 注册事件监听器
            this.registerEventListeners();
            
            // 加载初始模块
            await this.loadInitialModule();
            
            // 隐藏加载屏幕
            this.hideLoadingScreen();
            
            console.log('✅ 应用初始化完成');
        } catch (error) {
            console.error('❌ 应用初始化失败:', error);
            this.showError('应用初始化失败，请刷新页面重试');
        }
    }

    /**
     * 检查认证状态
     */
    async checkAuth() {
        const isAuthenticated = sessionStorage.getItem('adminAuth') === 'true';
        if (!isAuthenticated) {
            console.warn('⚠️ 用户未认证，重定向到登录页面');
            // 这里可以添加重定向逻辑
            // window.location.href = '/admin/login';
        }
    }

    /**
     * 初始化UI组件
     */
    initUI() {
        // 更新时间显示
        this.updateLastUpdateTime();
        setInterval(() => this.updateLastUpdateTime(), 60000); // 每分钟更新

        // 初始化搜索功能
        this.initSearch();

        // 初始化用户菜单
        this.initUserMenu();
    }

    /**
     * 注册事件监听器
     */
    registerEventListeners() {
        // 导航链接点击事件
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('.nav-link');
            if (navLink && navLink.dataset.module) {
                e.preventDefault();
                this.handleNavigation(navLink.dataset.module);
            }
        });

        // 侧边栏切换按钮
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', this.handleSidebarToggle);
        }

        // 窗口大小变化
        window.addEventListener('resize', this.handleResize);

        // 全局搜索
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => {
                this.handleGlobalSearch(e.target.value);
            });
        }

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    /**
     * 处理导航
     */
    async handleNavigation(moduleName) {
        if (this.isLoading || this.currentModule === moduleName) {
            return;
        }

        console.log(`📍 导航到模块: ${moduleName}`);

        try {
            this.isLoading = true;
            this.showContentLoading();

            // 更新导航状态
            this.updateNavState(moduleName);

            // 卸载当前模块
            if (this.currentModule && this.modules.has(this.currentModule)) {
                await this.modules.get(this.currentModule).destroy();
            }

            // 加载新模块
            const module = await this.loadModule(moduleName);
            await module.init();

            this.currentModule = moduleName;
            this.hideContentLoading();

            // 更新页面标题
            this.updatePageTitle(moduleName);

            // 触发导航事件
            this.eventBus.emit('navigation', { module: moduleName });

        } catch (error) {
            console.error(`❌ 加载模块失败: ${moduleName}`, error);
            this.showError(`加载 ${moduleName} 模块失败`);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 加载模块
     */
    async loadModule(moduleName) {
        if (this.modules.has(moduleName)) {
            return this.modules.get(moduleName);
        }

        console.log(`📦 正在加载模块: ${moduleName}`);

        try {
            // 动态导入模块
            const moduleClass = await this.importModule(moduleName);
            const module = new moduleClass(this.eventBus);
            
            this.modules.set(moduleName, module);
            return module;
        } catch (error) {
            console.error(`❌ 导入模块失败: ${moduleName}`, error);
            throw new Error(`无法加载模块: ${moduleName}`);
        }
    }

    /**
     * 动态导入模块
     */
    async importModule(moduleName) {
        const moduleMap = {
            'overview': () => import('./modules/OverviewModule.js').then(m => m.OverviewModule),
            'operations': () => import('./modules/OperationsModule.js').then(m => m.OperationsModule),
            'documents': () => import('./modules/DocumentsModule.js').then(m => m.DocumentsModule),
            'users': () => import('./modules/UsersModule.js').then(m => m.UsersModule),
            'settings': () => import('./modules/SettingsModule.js').then(m => m.SettingsModule)
        };

        if (!moduleMap[moduleName]) {
            throw new Error(`未知模块: ${moduleName}`);
        }

        return await moduleMap[moduleName]();
    }

    /**
     * 更新导航状态
     */
    updateNavState(activeModule) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`[data-module="${activeModule}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    /**
     * 更新页面标题
     */
    updatePageTitle(moduleName) {
        const titles = {
            'overview': '系统概览',
            'operations': '运维中心',
            'documents': '文书管理',
            'users': '用户管理',
            'settings': '系统设置'
        };

        const title = titles[moduleName] || '管理后台';
        document.title = `${title} - 律刻管理后台`;
    }

    /**
     * 显示内容加载状态
     */
    showContentLoading() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="content-placeholder">
                    <div class="placeholder-spinner"></div>
                    <p>正在加载内容...</p>
                </div>
            `;
        }
    }

    /**
     * 隐藏内容加载状态
     */
    hideContentLoading() {
        // 内容将由模块自己渲染
    }

    /**
     * 加载初始模块
     */
    async loadInitialModule() {
        const hash = window.location.hash.slice(1);
        const initialModule = hash || 'overview';
        await this.handleNavigation(initialModule);
    }

    /**
     * 隐藏加载屏幕
     */
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        const app = document.getElementById('app');

        if (loadingScreen && app) {
            setTimeout(() => {
                loadingScreen.style.opacity = '0';
                app.style.display = 'flex';
                
                setTimeout(() => {
                    loadingScreen.remove();
                }, 300);
            }, 500); // 最少显示500ms
        }
    }

    /**
     * 处理侧边栏切换
     */
    handleSidebarToggle() {
        const sidebar = document.getElementById('app-sidebar');
        if (sidebar) {
            sidebar.classList.toggle('open');
        }
    }

    /**
     * 处理窗口大小变化
     */
    handleResize() {
        // 在小屏幕上自动关闭侧边栏
        if (window.innerWidth > 768) {
            const sidebar = document.getElementById('app-sidebar');
            if (sidebar) {
                sidebar.classList.remove('open');
            }
        }
    }

    /**
     * 初始化搜索功能
     */
    initSearch() {
        // 搜索功能可以在这里实现
        console.log('🔍 搜索功能已初始化');
    }

    /**
     * 处理全局搜索
     */
    handleGlobalSearch(query) {
        if (query.length < 2) return;
        
        console.log(`🔍 搜索: ${query}`);
        // 这里可以实现搜索逻辑
    }

    /**
     * 初始化用户菜单
     */
    initUserMenu() {
        console.log('👤 用户菜单已初始化');
    }

    /**
     * 处理键盘快捷键
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K 打开搜索
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('global-search');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // ESC 关闭侧边栏（移动端）
        if (e.key === 'Escape') {
            const sidebar = document.getElementById('app-sidebar');
            if (sidebar && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        }
    }

    /**
     * 更新最后更新时间
     */
    updateLastUpdateTime() {
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            lastUpdateEl.textContent = timeString;
        }
    }

    /**
     * 显示错误消息
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <p>${message}</p>
            </div>
        `;

        container.appendChild(notification);

        // 显示动画
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // 自动移除
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
}

/**
 * 简单的事件总线
 */
class EventBus {
    constructor() {
        this.events = {};
    }

    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }

    off(event, callback) {
        if (this.events[event]) {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('事件处理器错误:', error);
                }
            });
        }
    }
}

/**
 * 基础模块类
 */
class BaseModule {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.container = document.getElementById('main-content');
        this.isInitialized = false;
    }

    async init() {
        if (this.isInitialized) return;
        
        console.log(`🔧 初始化模块: ${this.constructor.name}`);
        
        await this.render();
        this.bindEvents();
        this.isInitialized = true;
    }

    async render() {
        throw new Error('子类必须实现 render 方法');
    }

    bindEvents() {
        // 子类可以重写此方法
    }

    async destroy() {
        if (!this.isInitialized) return;
        
        console.log(`🗑️ 销毁模块: ${this.constructor.name}`);
        
        this.unbindEvents();
        this.isInitialized = false;
    }

    unbindEvents() {
        // 子类可以重写此方法
    }

    showLoading() {
        if (this.container) {
            this.container.innerHTML = `
                <div class="content-placeholder">
                    <div class="placeholder-spinner"></div>
                    <p>正在加载...</p>
                </div>
            `;
        }
    }

    showError(message) {
        if (this.container) {
            this.container.innerHTML = `
                <div class="error-message">
                    <h3>加载失败</h3>
                    <p>${message}</p>
                    <button onclick="location.reload()" class="retry-btn">重试</button>
                </div>
            `;
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', async () => {
    window.adminApp = new AdminApp();
    await window.adminApp.init();
});

// 导出类供其他模块使用
window.BaseModule = BaseModule;
window.EventBus = EventBus;