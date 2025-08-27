/**
 * Toast System - 现代化通知系统
 * 提供成功、错误、警告和信息提示
 */

class ToastSystem {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.init();
    }
    
    init() {
        // 创建toast容器
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        this.container.innerHTML = '';
        
        // 添加样式
        this.addStyles();
        
        // 添加到页面
        document.body.appendChild(this.container);
    }
    
    addStyles() {
        if (document.getElementById('toast-system-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'toast-system-styles';
        styles.textContent = `
            .toast-container {
                position: fixed;
                top: var(--space-4, 1rem);
                right: var(--space-4, 1rem);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: var(--space-2, 0.5rem);
                max-width: 400px;
                pointer-events: none;
            }
            
            .toast {
                background: var(--bg-primary, white);
                border-radius: var(--radius-lg, 0.5rem);
                box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1));
                padding: var(--space-4, 1rem);
                display: flex;
                align-items: flex-start;
                gap: var(--space-3, 0.75rem);
                min-width: 300px;
                max-width: 400px;
                pointer-events: auto;
                transform: translateX(100%);
                opacity: 0;
                transition: all 0.3s ease-out;
                border-left: 4px solid var(--gray-300, #d1d5db);
            }
            
            .toast.show {
                transform: translateX(0);
                opacity: 1;
            }
            
            .toast.success {
                border-left-color: var(--color-success, #10b981);
            }
            
            .toast.error {
                border-left-color: var(--color-error, #ef4444);
            }
            
            .toast.warning {
                border-left-color: var(--color-warning, #f59e0b);
            }
            
            .toast.info {
                border-left-color: var(--color-primary, #3b82f6);
            }
            
            .toast-icon {
                width: var(--space-5, 1.25rem);
                height: var(--space-5, 1.25rem);
                flex-shrink: 0;
                margin-top: var(--space-1, 0.25rem);
            }
            
            .toast-icon.success {
                color: var(--color-success, #10b981);
            }
            
            .toast-icon.error {
                color: var(--color-error, #ef4444);
            }
            
            .toast-icon.warning {
                color: var(--color-warning, #f59e0b);
            }
            
            .toast-icon.info {
                color: var(--color-primary, #3b82f6);
            }
            
            .toast-content {
                flex: 1;
                min-width: 0;
            }
            
            .toast-title {
                font-size: var(--text-sm, 0.875rem);
                font-weight: var(--font-medium, 500);
                color: var(--text-primary, #111827);
                margin-bottom: var(--space-1, 0.25rem);
                line-height: var(--leading-tight, 1.25);
            }
            
            .toast-message {
                font-size: var(--text-sm, 0.875rem);
                color: var(--text-secondary, #6b7280);
                line-height: var(--leading-relaxed, 1.625);
            }
            
            .toast-close {
                background: none;
                border: none;
                color: var(--text-tertiary, #9ca3af);
                cursor: pointer;
                padding: var(--space-1, 0.25rem);
                border-radius: var(--radius-sm, 0.25rem);
                transition: var(--transition-fast, all 0.15s ease-in-out);
                width: var(--space-5, 1.25rem);
                height: var(--space-5, 1.25rem);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .toast-close:hover {
                color: var(--text-secondary, #6b7280);
                background-color: var(--gray-100, #f3f4f6);
            }
            
            .toast-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 2px;
                background-color: var(--gray-300, #d1d5db);
                border-radius: 0 0 var(--radius-lg, 0.5rem) var(--radius-lg, 0.5rem);
                transform-origin: left;
                animation: toast-progress 5s linear forwards;
            }
            
            .toast.success .toast-progress {
                background-color: var(--color-success, #10b981);
            }
            
            .toast.error .toast-progress {
                background-color: var(--color-error, #ef4444);
            }
            
            .toast.warning .toast-progress {
                background-color: var(--color-warning, #f59e0b);
            }
            
            .toast.info .toast-progress {
                background-color: var(--color-primary, #3b82f6);
            }
            
            @keyframes toast-progress {
                from {
                    transform: scaleX(1);
                }
                to {
                    transform: scaleX(0);
                }
            }
            
            /* 响应式设计 */
            @media (max-width: 640px) {
                .toast-container {
                    top: var(--space-2, 0.5rem);
                    right: var(--space-2, 0.5rem);
                    left: var(--space-2, 0.5rem);
                    max-width: none;
                }
                
                .toast {
                    min-width: auto;
                    max-width: none;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    show(type = 'info', title = '', message = '', duration = 5000) {
        const toastId = this.generateId();
        const toast = this.createToast(toastId, type, title, message, duration);
        
        this.container.appendChild(toast);
        this.toasts.set(toastId, toast);
        
        // 触发显示动画
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toastId);
            }, duration);
        }
        
        return toastId;
    }
    
    createToast(id, type, title, message, duration) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.dataset.toastId = id;
        
        // 图标映射
        const iconMap = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'exclamation-triangle',
            info: 'information-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-icon ${type}" data-icon="${iconMap[type]}"></div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${this.escapeHtml(title)}</div>` : ''}
                ${message ? `<div class="toast-message">${this.escapeHtml(message)}</div>` : ''}
            </div>
            <button class="toast-close" data-icon="x-mark" aria-label="关闭"></button>
            ${duration > 0 ? '<div class="toast-progress"></div>' : ''}
        `;
        
        // 绑定关闭事件
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.remove(id);
        });
        
        // 替换图标（如果图标系统可用）
        if (window.IconSystem) {
            const icons = toast.querySelectorAll('[data-icon]');
            icons.forEach(icon => {
                const iconName = icon.getAttribute('data-icon');
                window.IconSystem.replaceWithIcon(icon, iconName, {
                    size: '20',
                    className: icon.className
                });
            });
        }
        
        return toast;
    }
    
    remove(toastId) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;
        
        // 移除动画
        toast.classList.remove('show');
        
        // 延迟移除DOM元素
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts.delete(toastId);
        }, 300);
    }
    
    clear() {
        this.toasts.forEach((toast, id) => {
            this.remove(id);
        });
    }
    
    success(title, message, duration = 5000) {
        return this.show('success', title, message, duration);
    }
    
    error(title, message, duration = 7000) {
        return this.show('error', title, message, duration);
    }
    
    warning(title, message, duration = 6000) {
        return this.show('warning', title, message, duration);
    }
    
    info(title, message, duration = 5000) {
        return this.show('info', title, message, duration);
    }
    
    generateId() {
        return 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 创建全局实例
window.ToastSystem = new ToastSystem();

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastSystem;
}