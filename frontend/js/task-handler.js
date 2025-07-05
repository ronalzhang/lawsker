/**
 * 任务处理 JavaScript 模块
 * 支持验证码发送、任务提交、状态查询等功能
 */

class TaskHandler {
    constructor() {
        this.baseURL = '/api/v1';
        this.verificationTimeout = null;
        this.trackingInterval = null;
    }

    /**
     * 发送短信验证码
     */
    async sendVerificationCode(phone) {
        try {
            // 验证手机号格式
            if (!this.validatePhone(phone)) {
                throw new Error('手机号格式不正确');
            }

            const response = await fetch(`${this.baseURL}/tasks/send-verification-code`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ phone: phone })
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || '发送验证码失败');
            }

            return result;
        } catch (error) {
            console.error('发送验证码失败:', error);
            throw error;
        }
    }

    /**
     * 提交匿名任务
     */
    async submitAnonymousTask(taskData) {
        try {
            // 验证必填字段
            this.validateTaskData(taskData);

            const response = await fetch(`${this.baseURL}/tasks/anonymous/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskData)
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || '任务提交失败');
            }

            return result;
        } catch (error) {
            console.error('任务提交失败:', error);
            throw error;
        }
    }

    /**
     * 查询任务状态
     */
    async trackTask(taskNumber) {
        try {
            const response = await fetch(`${this.baseURL}/tasks/track/${taskNumber}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || '查询任务失败');
            }

            return result;
        } catch (error) {
            console.error('查询任务失败:', error);
            throw error;
        }
    }

    /**
     * 验证手机号格式
     */
    validatePhone(phone) {
        const phoneRegex = /^1[3-9]\d{9}$/;
        return phoneRegex.test(phone);
    }

    /**
     * 验证任务数据
     */
    validateTaskData(taskData) {
        const required = ['contact_name', 'contact_phone', 'service_type', 'case_title', 'case_description', 'verification_code'];
        
        for (const field of required) {
            if (!taskData[field]) {
                throw new Error(`${field} 是必填字段`);
            }
        }

        if (!this.validatePhone(taskData.contact_phone)) {
            throw new Error('手机号格式不正确');
        }
    }

    /**
     * 开始验证码倒计时
     */
    startVerificationCountdown(buttonElement, countdown = 60) {
        if (this.verificationTimeout) {
            clearInterval(this.verificationTimeout);
        }

        buttonElement.disabled = true;
        buttonElement.textContent = `${countdown}秒后重发`;

        this.verificationTimeout = setInterval(() => {
            countdown--;
            if (countdown <= 0) {
                clearInterval(this.verificationTimeout);
                buttonElement.disabled = false;
                buttonElement.textContent = '发送验证码';
                this.verificationTimeout = null;
            } else {
                buttonElement.textContent = `${countdown}秒后重发`;
            }
        }, 1000);
    }

    /**
     * 开始任务状态轮询
     */
    startTaskTracking(taskNumber, updateCallback, interval = 10000) {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
        }

        // 立即执行一次
        this.trackTask(taskNumber).then(updateCallback).catch(console.error);

        // 定期轮询
        this.trackingInterval = setInterval(() => {
            this.trackTask(taskNumber)
                .then(result => {
                    updateCallback(result);
                    // 如果任务完成，停止轮询
                    if (result.status === 'sent' || result.status === 'cancelled' || result.status === 'rejected') {
                        this.stopTaskTracking();
                    }
                })
                .catch(console.error);
        }, interval);
    }

    /**
     * 停止任务状态轮询
     */
    stopTaskTracking() {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
            this.trackingInterval = null;
        }
    }

    /**
     * 格式化任务状态显示
     */
    formatTaskStatus(task) {
        const statusMap = {
            'pending': { text: '等待处理', color: '#fbbf24', icon: '⏳' },
            'in_review': { text: '审核中', color: '#3b82f6', icon: '👨‍⚖️' },
            'modification_requested': { text: '修改中', color: '#f59e0b', icon: '✏️' },
            'approved': { text: '已审核', color: '#10b981', icon: '✅' },
            'authorized': { text: '已授权', color: '#8b5cf6', icon: '🔐' },
            'sent': { text: '已发送', color: '#059669', icon: '📧' },
            'rejected': { text: '已拒绝', color: '#ef4444', icon: '❌' },
            'cancelled': { text: '已取消', color: '#6b7280', icon: '🚫' }
        };

        const status = statusMap[task.status] || { text: '未知状态', color: '#6b7280', icon: '❓' };
        
        return {
            ...status,
            progress: task.progress,
            message: task.status_message
        };
    }

    /**
     * 显示通知消息
     */
    showNotification(message, type = 'info', duration = 3000) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;

        // 设置背景颜色
        const colors = {
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        notification.textContent = message;
        document.body.appendChild(notification);

        // 显示动画
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // 自动隐藏
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    /**
     * 更新进度条
     */
    updateProgressBar(progressElement, progress) {
        if (progressElement) {
            const progressBar = progressElement.querySelector('.progress-fill');
            const progressText = progressElement.querySelector('.progress-text');
            
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            
            if (progressText) {
                progressText.textContent = `${progress}%`;
            }
        }
    }

    /**
     * 清理资源
     */
    cleanup() {
        if (this.verificationTimeout) {
            clearInterval(this.verificationTimeout);
            this.verificationTimeout = null;
        }
        
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
            this.trackingInterval = null;
        }
    }
}

// 全局实例
window.taskHandler = new window.taskHandler || new TaskHandler();

// 页面卸载时清理资源
window.addEventListener('beforeunload', () => {
    if (window.taskHandler) {
        window.taskHandler.cleanup();
    }
});

// 导出模块（如果支持ES6模块）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TaskHandler;
} 