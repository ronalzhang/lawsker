/**
 * 自动重定向管理器
 * 处理登录后的自动重定向逻辑，减少用户困惑
 */

class AutoRedirectManager {
    constructor() {
        this.redirectDelay = 1500; // 重定向延迟时间（毫秒）
        this.showRedirectMessage = true; // 是否显示重定向消息
    }

    /**
     * 处理登录成功后的自动重定向
     * @param {Object} loginResult - 登录结果
     * @param {string} loginResult.redirect_url - 重定向URL
     * @param {string} loginResult.message - 显示消息
     * @param {boolean} loginResult.auto_redirect - 是否自动重定向
     * @param {string} loginResult.account_type - 账户类型
     */
    async handleLoginRedirect(loginResult) {
        if (!loginResult.auto_redirect || !loginResult.redirect_url) {
            console.warn('登录结果中缺少重定向信息');
            return;
        }

        // 显示重定向消息
        if (this.showRedirectMessage && loginResult.message) {
            this.showRedirectingMessage(loginResult.message, loginResult.account_type);
        }

        // 保存用户信息到本地存储
        this.saveUserInfo(loginResult);

        // 延迟重定向，让用户看到成功消息
        setTimeout(() => {
            this.performRedirect(loginResult.redirect_url);
        }, this.redirectDelay);
    }

    /**
     * 检查当前用户登录状态并自动重定向
     * 用于页面刷新或直接访问认证页面时
     */
    async checkAndRedirectIfLoggedIn() {
        try {
            const token = this.getStoredToken();
            if (!token) {
                return false; // 未登录
            }

            const response = await fetch('/api/v1/unified-auth/check-login-status', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                
                if (result.logged_in && result.redirect_url) {
                    // 用户已登录，执行重定向
                    this.showRedirectingMessage(
                        result.message || '检测到您已登录，正在跳转...',
                        result.account_type
                    );
                    
                    setTimeout(() => {
                        this.performRedirect(result.redirect_url);
                    }, 1000);
                    
                    return true;
                }
            }
        } catch (error) {
            console.error('检查登录状态失败:', error);
        }
        
        return false;
    }

    /**
     * 显示重定向消息
     * @param {string} message - 消息内容
     * @param {string} accountType - 账户类型
     */
    showRedirectingMessage(message, accountType) {
        // 创建消息容器
        const messageContainer = document.getElementById('redirect-message-container') || 
                                this.createMessageContainer();

        // 获取账户类型对应的图标
        const icon = this.getAccountTypeIcon(accountType);
        
        messageContainer.innerHTML = `
            <div class="redirect-message success">
                <div class="redirect-icon">
                    ${icon}
                </div>
                <div class="redirect-content">
                    <div class="redirect-text">${message}</div>
                    <div class="redirect-progress">
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 添加样式
        this.addRedirectStyles();
        
        // 启动进度条动画
        setTimeout(() => {
            const progressFill = messageContainer.querySelector('.progress-fill');
            if (progressFill) {
                progressFill.style.width = '100%';
            }
        }, 100);
    }

    /**
     * 创建消息容器
     */
    createMessageContainer() {
        let container = document.getElementById('redirect-message-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'redirect-message-container';
            container.className = 'redirect-message-container';
            
            // 插入到页面顶部
            const body = document.body;
            body.insertBefore(container, body.firstChild);
        }
        return container;
    }

    /**
     * 获取账户类型对应的图标
     * @param {string} accountType - 账户类型
     */
    getAccountTypeIcon(accountType) {
        const icons = {
            'lawyer': `
                <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"/>
                </svg>
            `,
            'admin': `
                <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
            `,
            'user': `
                <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
            `
        };
        
        return icons[accountType] || icons['user'];
    }

    /**
     * 添加重定向相关样式
     */
    addRedirectStyles() {
        if (document.getElementById('redirect-styles')) {
            return; // 样式已存在
        }

        const style = document.createElement('style');
        style.id = 'redirect-styles';
        style.textContent = `
            .redirect-message-container {
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 10000;
                width: 90%;
                max-width: 400px;
            }

            .redirect-message {
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
                padding: 1.5rem;
                display: flex;
                align-items: center;
                gap: 1rem;
                border-left: 4px solid #10b981;
                animation: slideInDown 0.3s ease-out;
            }

            .redirect-icon {
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #10b981, #059669);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                flex-shrink: 0;
            }

            .redirect-icon .icon {
                width: 20px;
                height: 20px;
            }

            .redirect-content {
                flex: 1;
            }

            .redirect-text {
                color: #1f2937;
                font-weight: 500;
                margin-bottom: 0.5rem;
                font-size: 0.875rem;
            }

            .redirect-progress {
                width: 100%;
            }

            .progress-bar {
                width: 100%;
                height: 4px;
                background: #e5e7eb;
                border-radius: 2px;
                overflow: hidden;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #10b981, #059669);
                width: 0%;
                transition: width ${this.redirectDelay}ms ease-out;
                border-radius: 2px;
            }

            @keyframes slideInDown {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @media (max-width: 640px) {
                .redirect-message-container {
                    top: 10px;
                    width: 95%;
                }
                
                .redirect-message {
                    padding: 1rem;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    /**
     * 保存用户信息到本地存储
     * @param {Object} loginResult - 登录结果
     */
    saveUserInfo(loginResult) {
        try {
            const userInfo = {
                workspace_id: loginResult.workspace_id,
                account_type: loginResult.account_type,
                redirect_url: loginResult.redirect_url,
                login_time: new Date().toISOString()
            };
            
            localStorage.setItem('user_info', JSON.stringify(userInfo));
            
            // 保存token（如果存在）
            if (loginResult.access_token) {
                localStorage.setItem('access_token', loginResult.access_token);
            }
        } catch (error) {
            console.error('保存用户信息失败:', error);
        }
    }

    /**
     * 获取存储的token
     */
    getStoredToken() {
        return localStorage.getItem('access_token');
    }

    /**
     * 执行重定向
     * @param {string} url - 重定向URL
     */
    performRedirect(url) {
        try {
            // 记录重定向日志
            console.log('执行自动重定向:', url);
            
            // 执行重定向
            window.location.href = url;
        } catch (error) {
            console.error('重定向失败:', error);
            
            // 重定向失败时的后备方案
            this.showRedirectError('重定向失败，请手动刷新页面');
        }
    }

    /**
     * 显示重定向错误
     * @param {string} message - 错误消息
     */
    showRedirectError(message) {
        const messageContainer = this.createMessageContainer();
        
        messageContainer.innerHTML = `
            <div class="redirect-message error">
                <div class="redirect-icon error">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <div class="redirect-content">
                    <div class="redirect-text">${message}</div>
                </div>
            </div>
        `;

        // 添加错误样式
        const style = document.createElement('style');
        style.textContent = `
            .redirect-message.error {
                border-left-color: #ef4444;
            }
            .redirect-icon.error {
                background: linear-gradient(135deg, #ef4444, #dc2626);
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * 清除重定向消息
     */
    clearRedirectMessage() {
        const container = document.getElementById('redirect-message-container');
        if (container) {
            container.innerHTML = '';
        }
    }

    /**
     * 设置重定向延迟时间
     * @param {number} delay - 延迟时间（毫秒）
     */
    setRedirectDelay(delay) {
        this.redirectDelay = delay;
    }

    /**
     * 设置是否显示重定向消息
     * @param {boolean} show - 是否显示
     */
    setShowRedirectMessage(show) {
        this.showRedirectMessage = show;
    }
}

// 创建全局实例
window.AutoRedirectManager = new AutoRedirectManager();

// 页面加载完成后检查登录状态
document.addEventListener('DOMContentLoaded', () => {
    // 只在认证相关页面检查登录状态
    const authPages = ['/auth', '/login', '/register', '/unified-auth'];
    const currentPath = window.location.pathname;
    
    if (authPages.some(page => currentPath.includes(page))) {
        window.AutoRedirectManager.checkAndRedirectIfLoggedIn();
    }
});

// 导出模块（如果支持ES6模块）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutoRedirectManager;
}