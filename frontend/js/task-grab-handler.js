/**
 * 统一的任务抢单处理器
 * 用于律师接单中心和律师工作台的抢单功能
 */

class TaskGrabHandler {
    constructor() {
        // 移除演示模式，专注真实环境
    }

    /**
     * 抢单主函数
     * @param {string} taskId - 任务ID
     * @param {Object} options - 选项
     * @param {HTMLElement} options.taskElement - 任务DOM元素
     * @param {HTMLElement} options.grabButton - 抢单按钮
     * @param {Function} options.onSuccess - 成功回调
     * @param {Function} options.onError - 失败回调
     */
    async grabTask(taskId, options = {}) {
        const { taskElement, grabButton, onSuccess, onError } = options;
        
        // 确认对话框
        if (!confirm('确定要抢这个任务吗？抢到后需要在规定时间内完成。')) {
            return;
        }

        // 更新按钮状态
        if (grabButton) {
            const originalText = grabButton.innerHTML;
            grabButton.disabled = true;
            grabButton.innerHTML = '🔄 抢单中...';
            if (grabButton.style) {
                grabButton.style.animation = 'none';
            }
        }

        try {
            // 检查用户是否已认证
            if (!window.apiClient || !window.apiClient.isAuthenticated()) {
                throw new Error('请先登录后再抢单');
            }

            // 真实API调用 - 使用统一的API客户端
            let result;
            try {
                result = await window.apiClient.grabTask(taskId);
            } catch (apiError) {
                // 如果API客户端失败，回退到直接fetch
                console.warn('API客户端抢单失败，尝试直接调用:', apiError);
                
                const response = await fetch(`${window.apiClient.baseURL}/tasks/grab/${taskId}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.message || '抢单失败');
                }
            }
            
            if (result.success) {
                const message = result.message || '抢单成功！任务已分配给您';
                
                // 抢单成功处理
                this.handleGrabSuccess(taskId, taskElement, message);
                
                // 执行成功回调
                if (onSuccess) {
                    onSuccess(taskId, message);
                }
            } else {
                throw new Error(result.message || '抢单失败');
            }

        } catch (error) {
            console.error('抢单失败:', error);
            
            // 恢复按钮状态
            if (grabButton) {
                const originalText = grabButton.getAttribute('data-original-text') || '⚡ 立即抢单';
                grabButton.disabled = false;
                grabButton.innerHTML = originalText;
                if (grabButton.style) {
                    grabButton.style.animation = 'pulse 2s infinite';
                }
            }
            
            // 显示错误消息
            const errorMessage = error.message || '抢单失败，请稍后重试';
            this.showNotification(errorMessage, 'error');
            
            // 执行失败回调
            if (onError) {
                onError(error);
            }
        }
    }

    /**
     * 处理抢单成功
     */
    handleGrabSuccess(taskId, taskElement, message) {
        // 更新任务元素样式（如果提供了元素）
        if (taskElement) {
            taskElement.classList.add('grabbed');
            if (taskElement.style) {
                taskElement.style.background = 'rgba(76, 175, 80, 0.1)';
                taskElement.style.border = '1px solid rgba(76, 175, 80, 0.3)';
            }
            
            // 更新操作按钮
            const actions = taskElement.querySelector('.task-actions');
            if (actions) {
                actions.innerHTML = '<span class="status-badge" style="padding: 6px 12px; border-radius: 6px; background: rgba(76, 175, 80, 0.2); color: #4caf50; font-size: 12px; font-weight: 500;">✅ 已抢到</span>';
            }
        }

        // 显示成功消息
        this.showNotification(message, 'success');

        // 延迟执行后续操作
        setTimeout(() => {
            // 如果在律师工作台，移动任务到我的任务列表
            if (typeof moveTaskToMyTasks === 'function' && taskElement) {
                try {
                    moveTaskToMyTasks(taskElement, taskId);
                } catch (error) {
                    console.error('移动任务到我的任务列表失败:', error);
                }
            }
            
            // 如果在接单中心，刷新列表
            if (typeof loadTasks === 'function') {
                try {
                    loadTasks();
                } catch (error) {
                    console.error('刷新接单中心任务列表失败:', error);
                }
            }
            if (typeof loadStats === 'function') {
                try {
                    loadStats();
                } catch (error) {
                    console.error('刷新统计数据失败:', error);
                }
            }
            
            // 刷新律师工作台的任务列表
            if (typeof loadAvailableTasks === 'function') {
                try {
                    loadAvailableTasks();
                } catch (error) {
                    console.error('刷新可抢单任务列表失败:', error);
                }
            }
            if (typeof loadMyTasks === 'function') {
                try {
                    loadMyTasks();
                } catch (error) {
                    console.error('刷新我的任务列表失败:', error);
                }
            }
        }, 1500);
    }

    /**
     * 显示通知消息
     */
    showNotification(message, type = 'info') {
        // 尝试使用已存在的通知函数
        if (typeof showNotification === 'function') {
            showNotification(message, type);
            return;
        }

        // 创建简单的通知
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            max-width: 350px;
            word-wrap: break-word;
            animation: slideIn 0.3s ease;
        `;

        // 根据类型设置颜色
        const colors = {
            success: '#4caf50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196f3'
        };
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;

        document.body.appendChild(notification);

        // 3秒后自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    /**
     * 获取可用任务列表
     * 统一的任务数据格式
     */
    async getAvailableTasks() {
        try {
            if (!window.apiClient || !window.apiClient.isAuthenticated()) {
                throw new Error('请先登录');
            }

            const result = await window.apiClient.getAvailableTasks();
            return result.tasks || result || [];
        } catch (error) {
            console.error('获取任务列表失败:', error);
            throw error;
        }
    }

}

// 创建全局实例
window.taskGrabHandler = new TaskGrabHandler();

// 导出统一的抢单函数供页面使用
window.grabTask = function(taskId, options = {}) {
    return window.taskGrabHandler.grabTask(taskId, options);
};