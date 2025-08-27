/**
 * 演示账户访问小组件
 * 可以嵌入到任何页面中，提供快速演示账户访问
 */

class DemoAccessWidget {
    constructor(options = {}) {
        this.options = {
            position: 'bottom-right', // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
            showOnPages: ['/', '/index.html', '/unified-auth.html'], // 显示在哪些页面
            autoShow: true, // 是否自动显示
            showDelay: 3000, // 延迟显示时间（毫秒）
            ...options
        };
        
        this.isVisible = false;
        this.widget = null;
        
        this.init();
    }
    
    init() {
        // 检查是否应该在当前页面显示
        if (!this.shouldShowOnCurrentPage()) {
            return;
        }
        
        // 创建小组件
        this.createWidget();
        
        // 自动显示
        if (this.options.autoShow) {
            setTimeout(() => {
                this.show();
            }, this.options.showDelay);
        }
    }
    
    shouldShowOnCurrentPage() {
        const currentPath = window.location.pathname;
        return this.options.showOnPages.some(page => 
            currentPath === page || currentPath.endsWith(page)
        );
    }
    
    createWidget() {
        // 创建小组件容器
        this.widget = document.createElement('div');
        this.widget.className = `demo-access-widget demo-widget-${this.options.position}`;
        this.widget.innerHTML = `
            <div class="demo-widget-content">
                <div class="demo-widget-header">
                    <span class="demo-widget-title">
                        <i class="fas fa-eye"></i>
                        免费体验
                    </span>
                    <button class="demo-widget-close" onclick="demoWidget.hide()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="demo-widget-body">
                    <p class="demo-widget-text">无需注册，立即体验平台功能</p>
                    <div class="demo-widget-buttons">
                        <button class="demo-widget-btn demo-btn-lawyer" onclick="demoWidget.enterDemo('lawyer')">
                            <i class="fas fa-balance-scale"></i>
                            律师演示
                        </button>
                        <button class="demo-widget-btn demo-btn-user" onclick="demoWidget.enterDemo('user')">
                            <i class="fas fa-building"></i>
                            用户演示
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // 添加样式
        this.addStyles();
        
        // 添加到页面
        document.body.appendChild(this.widget);
        
        // 初始隐藏
        this.widget.style.display = 'none';
    }
    
    addStyles() {
        if (document.getElementById('demo-widget-styles')) {
            return;
        }
        
        const styles = document.createElement('style');
        styles.id = 'demo-widget-styles';
        styles.textContent = `
            .demo-access-widget {
                position: fixed;
                z-index: 9999;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
                border: 1px solid #e5e7eb;
                width: 280px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                animation: slideIn 0.3s ease-out;
            }
            
            .demo-widget-bottom-right {
                bottom: 20px;
                right: 20px;
            }
            
            .demo-widget-bottom-left {
                bottom: 20px;
                left: 20px;
            }
            
            .demo-widget-top-right {
                top: 80px;
                right: 20px;
            }
            
            .demo-widget-top-left {
                top: 80px;
                left: 20px;
            }
            
            .demo-widget-content {
                padding: 0;
            }
            
            .demo-widget-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 16px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 12px 12px 0 0;
            }
            
            .demo-widget-title {
                font-weight: 600;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            
            .demo-widget-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                transition: background-color 0.2s;
            }
            
            .demo-widget-close:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            
            .demo-widget-body {
                padding: 16px;
            }
            
            .demo-widget-text {
                color: #6b7280;
                font-size: 13px;
                margin: 0 0 12px 0;
                line-height: 1.4;
            }
            
            .demo-widget-buttons {
                display: flex;
                gap: 8px;
            }
            
            .demo-widget-btn {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background: white;
                color: #374151;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
            }
            
            .demo-btn-lawyer:hover {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            
            .demo-btn-user:hover {
                background: #10b981;
                color: white;
                border-color: #10b981;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes slideOut {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(20px);
                }
            }
            
            .demo-access-widget.hiding {
                animation: slideOut 0.3s ease-out forwards;
            }
            
            /* 移动端适配 */
            @media (max-width: 768px) {
                .demo-access-widget {
                    width: calc(100vw - 40px);
                    max-width: 280px;
                }
                
                .demo-widget-bottom-right,
                .demo-widget-bottom-left {
                    left: 20px;
                    right: 20px;
                    width: auto;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    show() {
        if (this.widget && !this.isVisible) {
            this.widget.style.display = 'block';
            this.isVisible = true;
            
            // 记录显示事件
            this.trackEvent('demo_widget_shown');
        }
    }
    
    hide() {
        if (this.widget && this.isVisible) {
            this.widget.classList.add('hiding');
            setTimeout(() => {
                this.widget.style.display = 'none';
                this.widget.classList.remove('hiding');
                this.isVisible = false;
            }, 300);
            
            // 记录隐藏事件
            this.trackEvent('demo_widget_hidden');
        }
    }
    
    async enterDemo(demoType) {
        try {
            // 显示加载状态
            this.showLoading();
            
            // 记录点击事件
            this.trackEvent('demo_widget_click', { demo_type: demoType });
            
            // 请求演示账户
            const response = await fetch(`/api/v1/demo/demo/${demoType}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 重定向到演示工作台
                window.location.href = result.data.redirect_url;
            } else {
                throw new Error(result.message || '获取演示账户失败');
            }
        } catch (error) {
            console.error('进入演示模式失败:', error);
            this.showError('演示环境暂时不可用，请稍后重试');
        } finally {
            this.hideLoading();
        }
    }
    
    showLoading() {
        const buttons = this.widget.querySelectorAll('.demo-widget-btn');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 加载中...';
        });
    }
    
    hideLoading() {
        const buttons = this.widget.querySelectorAll('.demo-widget-btn');
        buttons[0].disabled = false;
        buttons[0].innerHTML = '<i class="fas fa-balance-scale"></i> 律师演示';
        buttons[1].disabled = false;
        buttons[1].innerHTML = '<i class="fas fa-building"></i> 用户演示';
    }
    
    showError(message) {
        const body = this.widget.querySelector('.demo-widget-body');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'demo-widget-error';
        errorDiv.style.cssText = `
            background: #fef2f2;
            color: #dc2626;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            margin-top: 8px;
            border: 1px solid #fecaca;
        `;
        errorDiv.textContent = message;
        
        body.appendChild(errorDiv);
        
        // 3秒后移除错误信息
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 3000);
    }
    
    trackEvent(eventName, data = {}) {
        try {
            // 发送到分析系统
            if (window.gtag) {
                window.gtag('event', eventName, {
                    event_category: 'demo_widget',
                    ...data
                });
            }
            
            // 发送到内部分析
            if (window.analytics && window.analytics.track) {
                window.analytics.track(eventName, {
                    source: 'demo_widget',
                    ...data
                });
            }
            
            console.log('Demo widget event:', eventName, data);
        } catch (error) {
            console.error('Failed to track demo widget event:', error);
        }
    }
    
    destroy() {
        if (this.widget) {
            this.widget.remove();
            this.widget = null;
            this.isVisible = false;
        }
    }
}

// 全局实例
let demoWidget = null;

// 自动初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否应该显示演示小组件
    const shouldShow = !window.location.pathname.includes('/demo-account.html') && 
                      !window.location.pathname.includes('/lawyer/') && 
                      !window.location.pathname.includes('/user/');
    
    if (shouldShow) {
        demoWidget = new DemoAccessWidget({
            position: 'bottom-right',
            showOnPages: ['/', '/index.html', '/unified-auth.html'],
            autoShow: true,
            showDelay: 5000 // 5秒后显示
        });
    }
});

// 导出供外部使用
window.DemoAccessWidget = DemoAccessWidget;