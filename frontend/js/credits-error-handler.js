/**
 * Enhanced Credits Error Handler
 * Provides user-friendly error messages and clear guidance
 */

class CreditsErrorHandler {
    constructor() {
        this.errorMessages = {
            // Network errors
            'network_error': {
                title: '网络连接问题',
                message: '无法连接到服务器，请检查网络连接',
                solutions: [
                    '检查网络连接是否正常',
                    '刷新页面重试',
                    '稍后再试'
                ],
                severity: 'warning'
            },
            
            // Credits insufficient
            'insufficient_credits': {
                title: 'Credits余额不足',
                message: '您的Credits不足以完成此操作',
                solutions: [
                    '购买更多Credits（50元/个）',
                    '等待每周一免费重置',
                    '使用单一任务上传（不消耗Credits）'
                ],
                severity: 'error'
            },
            
            // Invalid purchase quantity
            'invalid_quantity': {
                title: '购买数量无效',
                message: '请选择1-100之间的Credits数量',
                solutions: [
                    '选择1-100之间的数量',
                    '推荐购买5个享受10%折扣',
                    '推荐购买10个享受20%折扣'
                ],
                severity: 'warning'
            },
            
            // Payment failed
            'payment_failed': {
                title: '支付处理失败',
                message: '支付过程中出现问题，请重试',
                solutions: [
                    '检查支付方式是否正确',
                    '确认账户余额充足',
                    '联系客服获得帮助'
                ],
                severity: 'error'
            },
            
            // System error
            'system_error': {
                title: '系统暂时不可用',
                message: '系统正在处理您的请求，请稍后重试',
                solutions: [
                    '稍后重试操作',
                    '刷新页面',
                    '如问题持续，请联系技术支持'
                ],
                severity: 'error'
            }
        };
    }

    /**
     * Handle API error response
     */
    handleApiError(error, context = {}) {
        let errorInfo;
        
        if (error.response && error.response.data) {
            const data = error.response.data;
            errorInfo = this.parseApiError(data);
        } else if (error.message) {
            errorInfo = this.parseGenericError(error.message);
        } else {
            errorInfo = this.getDefaultError();
        }

        // Add context information
        errorInfo.context = context;
        
        // Show user-friendly error
        this.showUserFriendlyError(errorInfo);
        
        return errorInfo;
    }

    /**
     * Parse API error response
     */
    parseApiError(data) {
        const errorType = data.error || 'system_error';
        const template = this.errorMessages[errorType] || this.errorMessages['system_error'];
        
        return {
            type: errorType,
            title: template.title,
            message: data.user_message || data.message || template.message,
            solutions: data.suggestions || data.solutions || template.solutions,
            severity: template.severity,
            technical_detail: data.technical_detail,
            support_info: data.support_info
        };
    }

    /**
     * Parse generic error message
     */
    parseGenericError(message) {
        if (message.includes('network') || message.includes('fetch')) {
            return {
                ...this.errorMessages['network_error'],
                type: 'network_error'
            };
        } else {
            return {
                ...this.errorMessages['system_error'],
                type: 'system_error',
                message: message
            };
        }
    }

    /**
     * Get default error information
     */
    getDefaultError() {
        return {
            ...this.errorMessages['system_error'],
            type: 'system_error'
        };
    }

    /**
     * Show user-friendly error dialog
     */
    showUserFriendlyError(errorInfo) {
        // Create error modal
        const modal = this.createErrorModal(errorInfo);
        document.body.appendChild(modal);
        
        // Show modal with animation
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
        
        // Auto-hide for warnings after 8 seconds
        if (errorInfo.severity === 'warning') {
            setTimeout(() => {
                this.hideErrorModal(modal);
            }, 8000);
        }
    }

    /**
     * Create error modal HTML
     */
    createErrorModal(errorInfo) {
        const modal = document.createElement('div');
        modal.className = `credits-error-modal ${errorInfo.severity}`;
        
        const iconMap = {
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        modal.innerHTML = `
            <div class="error-modal-overlay" onclick="this.parentElement.remove()">
                <div class="error-modal-content" onclick="event.stopPropagation()">
                    <div class="error-modal-header">
                        <div class="error-icon">${iconMap[errorInfo.severity] || '❌'}</div>
                        <h3>${errorInfo.title}</h3>
                        <button class="error-modal-close" onclick="this.closest('.credits-error-modal').remove()">×</button>
                    </div>
                    
                    <div class="error-modal-body">
                        <p class="error-message">${errorInfo.message}</p>
                        
                        ${errorInfo.solutions && errorInfo.solutions.length > 0 ? `
                            <div class="error-solutions">
                                <h4>解决方案：</h4>
                                <ul>
                                    ${errorInfo.solutions.map(solution => `<li>${solution}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        
                        ${errorInfo.support_info ? `
                            <div class="error-support">
                                <h4>需要帮助？</h4>
                                <p>联系方式：${errorInfo.support_info.contact}</p>
                                <p>工作时间：${errorInfo.support_info.hours}</p>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="error-modal-footer">
                        <button class="btn-secondary" onclick="this.closest('.credits-error-modal').remove()">
                            知道了
                        </button>
                        ${this.getActionButton(errorInfo)}
                    </div>
                </div>
            </div>
        `;
        
        return modal;
    }

    /**
     * Get action button based on error type
     */
    getActionButton(errorInfo) {
        switch (errorInfo.type) {
            case 'insufficient_credits':
                return `<button class="btn-primary" onclick="showPurchaseModal(); this.closest('.credits-error-modal').remove();">
                    购买Credits
                </button>`;
            
            case 'invalid_quantity':
                return `<button class="btn-primary" onclick="this.closest('.credits-error-modal').remove(); selectPurchase(5, 225);">
                    购买5个Credits
                </button>`;
            
            case 'network_error':
                return `<button class="btn-primary" onclick="location.reload();">
                    刷新页面
                </button>`;
            
            default:
                return '';
        }
    }

    /**
     * Hide error modal
     */
    hideErrorModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            if (modal.parentElement) {
                modal.remove();
            }
        }, 300);
    }

    /**
     * Show success message
     */
    showSuccess(title, message, duration = 4000) {
        const toast = document.createElement('div');
        toast.className = 'credits-success-toast';
        toast.innerHTML = `
            <div class="success-toast-content">
                <div class="success-icon">✅</div>
                <div class="success-text">
                    <h4>${title}</h4>
                    <p>${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    }

    /**
     * Show informational message
     */
    showInfo(title, message, actions = []) {
        const modal = this.createInfoModal(title, message, actions);
        document.body.appendChild(modal);
        
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    /**
     * Create info modal
     */
    createInfoModal(title, message, actions) {
        const modal = document.createElement('div');
        modal.className = 'credits-info-modal';
        
        modal.innerHTML = `
            <div class="info-modal-overlay" onclick="this.parentElement.remove()">
                <div class="info-modal-content" onclick="event.stopPropagation()">
                    <div class="info-modal-header">
                        <div class="info-icon">ℹ️</div>
                        <h3>${title}</h3>
                        <button class="info-modal-close" onclick="this.closest('.credits-info-modal').remove()">×</button>
                    </div>
                    
                    <div class="info-modal-body">
                        <p>${message}</p>
                    </div>
                    
                    <div class="info-modal-footer">
                        <button class="btn-secondary" onclick="this.closest('.credits-info-modal').remove()">
                            关闭
                        </button>
                        ${actions.map(action => `
                            <button class="btn-primary" onclick="${action.onclick}; this.closest('.credits-info-modal').remove();">
                                ${action.text}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        return modal;
    }
}

// CSS styles for error handling
const errorHandlerStyles = `
<style>
.credits-error-modal, .credits-info-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 2000;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.credits-error-modal.show, .credits-info-modal.show {
    opacity: 1;
}

.error-modal-overlay, .info-modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
}

.error-modal-content, .info-modal-content {
    background: white;
    border-radius: 1rem;
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    transform: scale(0.9);
    transition: transform 0.3s ease;
}

.credits-error-modal.show .error-modal-content,
.credits-info-modal.show .info-modal-content {
    transform: scale(1);
}

.error-modal-header, .info-modal-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
}

.error-icon, .info-icon {
    font-size: 1.5rem;
}

.error-modal-header h3, .info-modal-header h3 {
    flex: 1;
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
}

.error-modal-close, .info-modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6b7280;
    padding: 0.25rem;
    border-radius: 0.25rem;
}

.error-modal-close:hover, .info-modal-close:hover {
    background: #f3f4f6;
}

.error-modal-body, .info-modal-body {
    padding: 1.5rem;
}

.error-message {
    font-size: 1rem;
    color: #374151;
    margin-bottom: 1rem;
    line-height: 1.6;
}

.error-solutions {
    margin-bottom: 1rem;
}

.error-solutions h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
}

.error-solutions ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.error-solutions li {
    padding: 0.5rem 0;
    color: #6b7280;
    position: relative;
    padding-left: 1.5rem;
}

.error-solutions li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: #3b82f6;
    font-weight: bold;
}

.error-support {
    background: #f8fafc;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-top: 1rem;
}

.error-support h4 {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
}

.error-support p {
    font-size: 0.875rem;
    color: #6b7280;
    margin: 0.25rem 0;
}

.error-modal-footer, .info-modal-footer {
    display: flex;
    gap: 1rem;
    padding: 1.5rem;
    border-top: 1px solid #e5e7eb;
    justify-content: flex-end;
}

.credits-success-toast {
    position: fixed;
    top: 2rem;
    right: 2rem;
    z-index: 2001;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
}

.credits-success-toast.show {
    opacity: 1;
    transform: translateX(0);
}

.success-toast-content {
    background: white;
    border-radius: 0.75rem;
    padding: 1rem 1.5rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #10b981;
    display: flex;
    align-items: center;
    gap: 1rem;
    min-width: 300px;
}

.success-icon {
    font-size: 1.25rem;
}

.success-text h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
}

.success-text p {
    margin: 0;
    font-size: 0.875rem;
    color: #6b7280;
}

.success-toast-content button {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    color: #6b7280;
    padding: 0.25rem;
    border-radius: 0.25rem;
}

.success-toast-content button:hover {
    background: #f3f4f6;
}

/* Error severity styles */
.credits-error-modal.error .error-modal-header {
    border-left: 4px solid #ef4444;
}

.credits-error-modal.warning .error-modal-header {
    border-left: 4px solid #f59e0b;
}

.credits-error-modal.info .error-modal-header {
    border-left: 4px solid #3b82f6;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', errorHandlerStyles);

// Initialize global error handler
window.creditsErrorHandler = new CreditsErrorHandler();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CreditsErrorHandler;
}