/**
 * API客户端 - 支持个人化数据加载
 * 确保所有数据请求都基于当前用户ID进行过滤
 */

class ApiClient {
    constructor() {
        this.baseUrl = 'http://156.236.74.200/api/v1';
        this.authToken = localStorage.getItem('authToken');
        this.currentUser = this.getCurrentUser();
    }

    // 获取当前用户信息
    getCurrentUser() {
        try {
            const userInfo = localStorage.getItem('userInfo');
            return userInfo ? JSON.parse(userInfo) : null;
        } catch (e) {
            console.error('解析用户信息失败:', e);
            return null;
        }
    }

    // 检查是否已认证
    isAuthenticated() {
        return !!this.authToken && !!this.currentUser;
    }

    // 获取当前用户ID
    getCurrentUserId() {
        return this.currentUser?.id || this.currentUser?.user_id;
    }

    // 获取当前用户角色
    getCurrentUserRole() {
        return this.currentUser?.role || 'user';
    }

    // 构建请求头
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }
        
        return headers;
    }

    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API请求失败 ${endpoint}:`, error);
            throw error;
        }
    }

    // GET请求便捷方法
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullEndpoint = queryString ? `${endpoint}?${queryString}` : endpoint;
        return await this.request(fullEndpoint);
    }

    // 获取案件列表
    async getCases(params = {}) {
        return await this.request(`/cases/?${new URLSearchParams(params).toString()}`);
    }

    // 获取用户个人统计数据
    async getUserStats() {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/statistics/user-stats`);
    }

    // 获取律师个人统计数据
    async getLawyerStats() {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/statistics/lawyer-stats`);
    }

    // 获取用户个人案件列表
    async getUserCases(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        // 根据用户角色获取不同的案件数据
        const userRole = this.getCurrentUserRole();
        
        if (userRole === 'lawyer') {
            // 律师：获取分配给自己的案件
            return await this.request(`/cases/?assigned_to=${currentUserId}&page_size=50`);
        } else {
            // 用户：获取自己创建的案件
            return await this.request(`/cases/?client_id=${currentUserId}&page_size=50`);
        }
    }

    // 获取律师个人案件列表
    async getLawyerCases(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/cases/?assigned_to=${currentUserId}&page_size=50`);
    }

    // 获取用户个人任务列表
    async getUserTasks(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/tasks/my-tasks/user?limit=50`);
    }

    // 获取律师个人任务列表
    async getLawyerTasks(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/tasks/my-tasks/lawyer?limit=50`);
    }

    // 获取用户个人提现记录
    async getUserWithdrawalHistory(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/finance/withdrawals/user/${currentUserId}`);
    }

    // 获取律师个人提现记录
    async getLawyerWithdrawalHistory(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/finance/withdrawals/lawyer/${currentUserId}`);
    }

    // 获取用户个人收入统计
    async getUserEarnings(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/finance/earnings/user/${currentUserId}`);
    }

    // 获取律师个人收入统计
    async getLawyerEarnings(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/finance/earnings/lawyer/${currentUserId}`);
    }

    // 获取用户个人配置
    async getUserConfig(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/users/${currentUserId}/config`);
    }

    // 更新用户个人配置
    async updateUserConfig(config, userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/users/${currentUserId}/config`, {
            method: 'PUT',
            body: JSON.stringify(config)
        });
    }

    // 获取用户个人活动记录
    async getUserActivityLog(userId = null, limit = 20) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/users/${currentUserId}/activity?limit=${limit}`);
    }

    // 获取律师个人活动记录
    async getLawyerActivityLog(userId = null, limit = 20) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/lawyers/${currentUserId}/activity?limit=${limit}`);
    }

    // 获取用户个人文档库
    async getUserDocuments(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/document-library/user/${currentUserId}`);
    }

    // 获取律师个人文档库
    async getLawyerDocuments(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/document-library/lawyer/${currentUserId}`);
    }

    // 获取用户个人发送记录
    async getUserSendRecords(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/document-send/records/user/${currentUserId}`);
    }

    // 获取律师个人发送记录
    async getLawyerSendRecords(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/document-send/records/lawyer/${currentUserId}`);
    }

    // 获取仪表盘统计数据（根据用户角色）
    async getDashboardStats() {
        const userRole = this.getCurrentUserRole();
        
        if (userRole === 'lawyer') {
            return await this.getLawyerStats();
        } else if (userRole === 'admin') {
            return await this.request('/statistics/admin-stats');
        } else {
            return await this.getUserStats();
        }
    }

    // 获取当前用户信息
    async getCurrentUserInfo() {
        return await this.request('/auth/me');
    }

    // 更新用户信息
    async updateUserProfile(profileData) {
        return await this.request('/users/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    // 获取可抢单任务（律师专用）
    async getAvailableTasks() {
        const userRole = this.getCurrentUserRole();
        if (userRole !== 'lawyer') {
            throw new Error('只有律师可以获取可抢单任务');
        }

        return await this.request('/tasks/available');
    }

    // 抢单（律师专用）
    async grabTask(taskId) {
        const userRole = this.getCurrentUserRole();
        if (userRole !== 'lawyer') {
            throw new Error('只有律师可以抢单');
        }

        const userId = this.getCurrentUserId();
        return await this.request(`/tasks/${taskId}/grab`, {
            method: 'POST',
            body: JSON.stringify({ lawyer_id: userId })
        });
    }

    // 发布任务（用户专用）
    async publishTask(taskData) {
        const userRole = this.getCurrentUserRole();
        if (userRole !== 'user' && userRole !== 'sales') {
            throw new Error('只有用户和销售可以发布任务');
        }

        const userId = this.getCurrentUserId();
        return await this.request('/tasks/publish', {
            method: 'POST',
            body: JSON.stringify({
                ...taskData,
                user_id: userId
            })
        });
    }

    // 获取提现统计
    async getWithdrawalStats() {
        const userRole = this.getCurrentUserRole();
        
        if (userRole === 'lawyer') {
            return await this.request('/finance/withdrawal-stats/lawyer');
        } else {
            return await this.request('/finance/withdrawal-stats/user');
        }
    }

    // 申请提现
    async requestWithdrawal(withdrawalData) {
        const userId = this.getCurrentUserId();
        return await this.request('/finance/withdrawals', {
            method: 'POST',
            body: JSON.stringify({
                ...withdrawalData,
                user_id: userId
            })
        });
    }

    // 获取个人通知
    async getPersonalNotifications(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/notifications/user/${currentUserId}`);
    }

    // 标记通知为已读
    async markNotificationAsRead(notificationId) {
        return await this.request(`/notifications/${notificationId}/read`, {
            method: 'PUT'
        });
    }

    // 获取个人消息
    async getPersonalMessages(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/messages/user/${currentUserId}`);
    }

    // 发送个人消息
    async sendPersonalMessage(messageData) {
        const userId = this.getCurrentUserId();
        return await this.request('/messages', {
            method: 'POST',
            body: JSON.stringify({
                ...messageData,
                sender_id: userId
            })
        });
    }

    // 获取个人设置
    async getPersonalSettings(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/users/${currentUserId}/settings`);
    }

    // 更新个人设置
    async updatePersonalSettings(settings, userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/users/${currentUserId}/settings`, {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
    }

    // 获取个人文件
    async getPersonalFiles(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/files/user/${currentUserId}`);
    }

    // 上传个人文件
    async uploadPersonalFile(fileData) {
        const userId = this.getCurrentUserId();
        const formData = new FormData();
        formData.append('file', fileData);
        formData.append('user_id', userId);

        return await fetch(`${this.baseUrl}/files/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            },
            body: formData
        });
    }

    // 删除个人文件
    async deletePersonalFile(fileId) {
        return await this.request(`/files/${fileId}`, {
            method: 'DELETE'
        });
    }

    // 获取个人日历事件
    async getPersonalCalendarEvents(userId = null, startDate = null, endDate = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        let endpoint = `/calendar/user/${currentUserId}`;
        if (startDate && endDate) {
            endpoint += `?start_date=${startDate}&end_date=${endDate}`;
        }

        return await this.request(endpoint);
    }

    // 创建个人日历事件
    async createPersonalCalendarEvent(eventData) {
        const userId = this.getCurrentUserId();
        return await this.request('/calendar/events', {
            method: 'POST',
            body: JSON.stringify({
                ...eventData,
                user_id: userId
            })
        });
    }

    // 更新个人日历事件
    async updatePersonalCalendarEvent(eventId, eventData) {
        return await this.request(`/calendar/events/${eventId}`, {
            method: 'PUT',
            body: JSON.stringify(eventData)
        });
    }

    // 删除个人日历事件
    async deletePersonalCalendarEvent(eventId) {
        return await this.request(`/calendar/events/${eventId}`, {
            method: 'DELETE'
        });
    }

    // 获取个人报告
    async getPersonalReports(userId = null, reportType = 'monthly') {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/reports/user/${currentUserId}?type=${reportType}`);
    }

    // 生成个人报告
    async generatePersonalReport(reportData) {
        const userId = this.getCurrentUserId();
        return await this.request('/reports/generate', {
            method: 'POST',
            body: JSON.stringify({
                ...reportData,
                user_id: userId
            })
        });
    }

    // 获取个人分析数据
    async getPersonalAnalytics(userId = null, period = '30d') {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/analytics/user/${currentUserId}?period=${period}`);
    }

    // 获取个人排行榜数据
    async getPersonalRankings(userId = null, category = 'earnings') {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/rankings/user/${currentUserId}?category=${category}`);
    }

    // 获取个人成就
    async getPersonalAchievements(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/achievements/user/${currentUserId}`);
    }

    // 解锁个人成就
    async unlockPersonalAchievement(achievementId) {
        const userId = this.getCurrentUserId();
        return await this.request(`/achievements/${achievementId}/unlock`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    // 获取个人积分
    async getPersonalPoints(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/points/user/${currentUserId}`);
    }

    // 兑换积分
    async redeemPoints(rewardId, points) {
        const userId = this.getCurrentUserId();
        return await this.request('/points/redeem', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                reward_id: rewardId,
                points: points
            })
        });
    }

    // 获取个人优惠券
    async getPersonalCoupons(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/coupons/user/${currentUserId}`);
    }

    // 使用个人优惠券
    async usePersonalCoupon(couponId) {
        const userId = this.getCurrentUserId();
        return await this.request(`/coupons/${couponId}/use`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    // 获取个人订阅
    async getPersonalSubscriptions(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/subscriptions/user/${currentUserId}`);
    }

    // 订阅服务
    async subscribeToService(serviceId, planId) {
        const userId = this.getCurrentUserId();
        return await this.request('/subscriptions', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                service_id: serviceId,
                plan_id: planId
            })
        });
    }

    // 取消订阅
    async cancelSubscription(subscriptionId) {
        return await this.request(`/subscriptions/${subscriptionId}/cancel`, {
            method: 'PUT'
        });
    }

    // 获取个人API密钥
    async getPersonalApiKeys(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/api-keys/user/${currentUserId}`);
    }

    // 生成个人API密钥
    async generatePersonalApiKey(keyName) {
        const userId = this.getCurrentUserId();
        return await this.request('/api-keys', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                name: keyName
            })
        });
    }

    // 删除个人API密钥
    async deletePersonalApiKey(keyId) {
        return await this.request(`/api-keys/${keyId}`, {
            method: 'DELETE'
        });
    }

    // 获取个人Webhook
    async getPersonalWebhooks(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/webhooks/user/${currentUserId}`);
    }

    // 创建个人Webhook
    async createPersonalWebhook(webhookData) {
        const userId = this.getCurrentUserId();
        return await this.request('/webhooks', {
            method: 'POST',
            body: JSON.stringify({
                ...webhookData,
                user_id: userId
            })
        });
    }

    // 删除个人Webhook
    async deletePersonalWebhook(webhookId) {
        return await this.request(`/webhooks/${webhookId}`, {
            method: 'DELETE'
        });
    }

    // 获取个人日志
    async getPersonalLogs(userId = null, level = 'info', limit = 100) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/logs/user/${currentUserId}?level=${level}&limit=${limit}`);
    }

    // 获取个人错误报告
    async getPersonalErrorReports(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/errors/user/${currentUserId}`);
    }

    // 提交个人错误报告
    async submitPersonalErrorReport(errorData) {
        const userId = this.getCurrentUserId();
        return await this.request('/errors', {
            method: 'POST',
            body: JSON.stringify({
                ...errorData,
                user_id: userId
            })
        });
    }

    // 获取个人备份
    async getPersonalBackups(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/backups/user/${currentUserId}`);
    }

    // 创建个人备份
    async createPersonalBackup(backupData) {
        const userId = this.getCurrentUserId();
        return await this.request('/backups', {
            method: 'POST',
            body: JSON.stringify({
                ...backupData,
                user_id: userId
            })
        });
    }

    // 恢复个人备份
    async restorePersonalBackup(backupId) {
        const userId = this.getCurrentUserId();
        return await this.request(`/backups/${backupId}/restore`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    // 删除个人备份
    async deletePersonalBackup(backupId) {
        return await this.request(`/backups/${backupId}`, {
            method: 'DELETE'
        });
    }

    // 获取个人数据导出
    async getPersonalDataExport(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/exports/user/${currentUserId}`);
    }

    // 请求个人数据导出
    async requestPersonalDataExport(exportData) {
        const userId = this.getCurrentUserId();
        return await this.request('/exports', {
            method: 'POST',
            body: JSON.stringify({
                ...exportData,
                user_id: userId
            })
        });
    }

    // 下载个人数据导出
    async downloadPersonalDataExport(exportId) {
        return await this.request(`/exports/${exportId}/download`);
    }

    // 删除个人数据导出
    async deletePersonalDataExport(exportId) {
        return await this.request(`/exports/${exportId}`, {
            method: 'DELETE'
        });
    }

    // 获取个人数据使用情况
    async getPersonalDataUsage(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/usage/user/${currentUserId}`);
    }

    // 获取个人数据限制
    async getPersonalDataLimits(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/limits/user/${currentUserId}`);
    }

    // 获取个人数据配额
    async getPersonalDataQuota(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/quota/user/${currentUserId}`);
    }

    // 获取个人数据统计
    async getPersonalDataStats(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/stats/user/${currentUserId}`);
    }

    // 获取个人数据趋势
    async getPersonalDataTrends(userId = null, period = '30d') {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/trends/user/${currentUserId}?period=${period}`);
    }

    // 获取个人数据预测
    async getPersonalDataPredictions(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/predictions/user/${currentUserId}`);
    }

    // 获取个人数据建议
    async getPersonalDataRecommendations(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/recommendations/user/${currentUserId}`);
    }

    // 获取个人数据洞察
    async getPersonalDataInsights(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/insights/user/${currentUserId}`);
    }

    // 获取个人数据报告
    async getPersonalDataReports(userId = null, reportType = 'comprehensive') {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/reports/user/${currentUserId}?type=${reportType}`);
    }

    // 生成个人数据报告
    async generatePersonalDataReport(reportData) {
        const userId = this.getCurrentUserId();
        return await this.request('/reports/generate', {
            method: 'POST',
            body: JSON.stringify({
                ...reportData,
                user_id: userId
            })
        });
    }

    // 获取个人数据摘要
    async getPersonalDataSummary(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/summary/user/${currentUserId}`);
    }

    // 获取个人数据概览
    async getPersonalDataOverview(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/overview/user/${currentUserId}`);
    }

    // 获取个人数据仪表板
    async getPersonalDataDashboard(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/dashboard/user/${currentUserId}`);
    }

    // 获取个人数据概览
    async getPersonalDataOverview(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/overview/user/${currentUserId}`);
    }

    // 获取个人数据仪表板
    async getPersonalDataDashboard(userId = null) {
        const currentUserId = userId || this.getCurrentUserId();
        if (!currentUserId) {
            throw new Error('未获取到用户ID');
        }

        return await this.request(`/dashboard/user/${currentUserId}`);
    }
}

// 创建全局API客户端实例
window.apiClient = new ApiClient();