/**
 * Lawsker API 客户端
 * 统一管理前端API调用
 */

class ApiClient {
    constructor() {
        this.baseURL = window.location.origin + '/api/v1';
        this.token = localStorage.getItem('authToken');
    }

    /**
     * 通用请求方法
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // 添加认证token
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    /**
     * GET请求
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST请求
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT请求
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE请求
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * 获取仪表盘统计数据
     */
    async getDashboardStats() {
        return this.get('/statistics/dashboard');
    }

    /**
     * 获取演示数据（无需认证）
     */
    async getDemoData() {
        return this.get('/statistics/demo-data');
    }

    /**
     * 获取最近活动
     */
    async getRecentActivities() {
        return this.get('/statistics/recent-activities');
    }

    /**
     * 记录用户活动
     */
    async logActivity(activity) {
        return this.post('/statistics/log-activity', activity);
    }

    /**
     * 获取用户信息
     */
    async getUserInfo() {
        return this.get('/auth/me');
    }

    /**
     * 获取当前用户信息（别名方法）
     */
    async getCurrentUserInfo() {
        return this.getUserInfo();
    }

    /**
     * 获取案件列表
     */
    async getCases(params = {}) {
        return this.get('/cases', params);
    }

    /**
     * 获取任务列表
     */
    async getTasks(params = {}) {
        return this.get('/tasks', params);
    }

    /**
     * 发布任务
     */
    async publishTask(taskData) {
        return this.post('/tasks', taskData);
    }

    /**
     * 上传数据
     */
    async uploadData(formData) {
        return this.request('/tasks/upload', {
            method: 'POST',
            body: formData,
            headers: {} // 不设置Content-Type，让浏览器自动设置
        });
    }

    /**
     * 获取财务统计
     */
    async getFinanceStats() {
        return this.get('/finance/stats');
    }

    /**
     * 获取提现记录
     */
    async getWithdrawals() {
        return this.get('/finance/withdrawals');
    }

    /**
     * 获取提现统计数据
     */
    async getWithdrawalStats() {
        return this.get('/finance/withdrawal-stats');
    }

    /**
     * 申请提现
     */
    async requestWithdrawal(withdrawalData) {
        return this.post('/finance/withdrawals', withdrawalData);
    }

    /**
     * 登录
     */
    async login(credentials) {
        const response = await this.post('/auth/login', credentials);
        if (response.access_token) {
            this.token = response.access_token;
            localStorage.setItem('authToken', this.token);
        }
        return response;
    }

    /**
     * 登出
     */
    logout() {
        this.token = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
    }

    /**
     * 检查认证状态
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * 获取用户角色
     */
    getUserRole() {
        const userInfo = localStorage.getItem('userInfo');
        if (userInfo) {
            return JSON.parse(userInfo).role;
        }
        return null;
    }

    /**
     * 设置用户信息
     */
    setUserInfo(userInfo) {
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
    }

    /**
     * 获取用户信息
     */
    getUserInfo() {
        const userInfo = localStorage.getItem('userInfo');
        return userInfo ? JSON.parse(userInfo) : null;
    }
}

// 创建全局API客户端实例
window.apiClient = new ApiClient();

// 导出API客户端类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
} 