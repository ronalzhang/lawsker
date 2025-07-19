/**
 * 统一的任务抢单处理器
 * 用于律师接单中心和律师工作台的抢单功能
 */

class TaskGrabHandler {
    constructor() {
        this.isDemoMode = !window.apiClient || !window.apiClient.isAuthenticated();
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
            let success = false;
            let message = '';

            // 检查是否为演示任务
            const isDemoTask = taskId.startsWith('demo-task-') || this.isDemoMode;
            
            if (!isDemoTask && window.apiClient && window.apiClient.isAuthenticated()) {
                // 真实API调用
                const response = await fetch(`/api/v1/tasks/grab/${taskId}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    success = true;
                    message = '抢单成功！任务已分配给您';
                } else {
                    throw new Error(result.message || '抢单失败');
                }
            } else {
                // 演示模式 - 模拟抢单
                console.log('演示模式抢单:', taskId);
                await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
                
                const successRate = Math.random();
                if (successRate > 0.2) { // 80%成功率
                    success = true;
                    message = '🎉 恭喜！您已成功抢到这个任务！（演示模式）';
                } else {
                    throw new Error('很遗憾，其他律师抢先一步，请尝试其他任务。');
                }
            }

            if (success) {
                // 抢单成功处理
                this.handleGrabSuccess(taskId, taskElement, message);
                
                // 执行成功回调
                if (onSuccess) {
                    onSuccess(taskId, message);
                }
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
            if (typeof moveTaskToMyTasks === 'function') {
                moveTaskToMyTasks(taskElement, taskId);
            }
            
            // 如果在接单中心，刷新列表
            if (typeof loadTasks === 'function') {
                loadTasks();
            }
            if (typeof loadStats === 'function') {
                loadStats();
            }
            
            // 刷新律师工作台的任务列表
            if (typeof loadAvailableTasks === 'function') {
                loadAvailableTasks();
            }
            if (typeof loadMyTasks === 'function') {
                loadMyTasks();
            }
        }, 2000);
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
            if (this.isDemoMode) {
                return this.getDemoTasks();
            }

            const response = await fetch('/api/v1/tasks/available', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.ok) {
                const result = await response.json();
                return result.tasks || [];
            }

            throw new Error('获取任务列表失败');
        } catch (error) {
            console.error('获取任务列表失败:', error);
            return this.getDemoTasks();
        }
    }

    /**
     * 获取演示任务数据
     */
    getDemoTasks() {
        return [
            {
                task_id: 'demo-task-001',
                task_type: 'lawyer_letter',
                title: '债权催收律师函 #001',
                description: '需要向欠款人发送正式的债权催收律师函，督促其履行还款义务。案件编号: CASE-2024-0001',
                budget: 650,
                urgency: 'normal',
                created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                publisher_name: '张***',
                is_demo: true
            },
            {
                task_id: 'demo-task-002',
                task_type: 'debt_collection',
                title: '企业欠款催收 #002',
                description: '企业间的货款纠纷，需要专业律师进行催收处理。案件编号: CASE-2024-0002',
                budget: 3500,
                urgency: 'urgent',
                created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
                publisher_name: '李***',
                is_demo: true
            },
            {
                task_id: 'demo-task-003',
                task_type: 'contract_review',
                title: '商务合同审查 #003',
                description: '需要律师审查商务合作合同的条款和风险点。案件编号: CASE-2024-0003',
                budget: 1200,
                urgency: 'normal',
                created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
                publisher_name: '王***',
                is_demo: true
            },
            {
                task_id: 'demo-task-004',
                task_type: 'legal_consultation',
                title: '法律咨询服务 #004',
                description: '关于公司经营中的法律问题咨询和建议。案件编号: CASE-2024-0004',
                budget: 800,
                urgency: 'low',
                created_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
                publisher_name: '陈***',
                is_demo: true
            },
            {
                task_id: 'demo-task-005',
                task_type: 'lawyer_letter',
                title: '违约责任追究函 #005',
                description: '合同违约后需要发送法律函件追究违约责任。案件编号: CASE-2024-0005',
                budget: 950,
                urgency: 'urgent',
                created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
                publisher_name: '刘***',
                is_demo: true
            }
        ];
    }
}

// 创建全局实例
window.taskGrabHandler = new TaskGrabHandler();

// 导出统一的抢单函数供页面使用
window.grabTask = function(taskId, options = {}) {
    return window.taskGrabHandler.grabTask(taskId, options);
};