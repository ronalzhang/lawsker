/**
 * Lawsker API 客户端 v1.5
 * 统一管理前端API调用
 * 更新时间: 2025-01-19
 * 改进: 移除演示模式，专注真实环境
 */

class ApiClient {
    constructor() {
        this.baseURL = 'https://156.236.74.200/api/v1';
        // 兼容多种token存储方式
        this.token = localStorage.getItem('authToken') || localStorage.getItem('accessToken');
        this.version = '1.5'; // API客户端版本号
    }

    /**
     * 刷新token
     */
    refreshToken() {
        this.token = localStorage.getItem('authToken') || localStorage.getItem('accessToken');
    }

    /**
     * 检查是否已认证
     */
    isAuthenticated() {
        this.refreshToken();
        return !!this.token;
    }

    /**
     * 通用请求方法
     */
    async request(endpoint, options = {}) {
        this.refreshToken();
        
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // 添加认证token（如果存在）
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        console.log(`🔗 API请求: ${config.method || 'GET'} ${url}`);

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Token过期或无效，清除并重定向到登录
                    localStorage.removeItem('authToken');
                    localStorage.removeItem('accessToken');
                    this.token = null;
                    
                    // 重定向到登录页面
                    window.location.href = '/auth';
                    return;
                }
                
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`✅ API成功: ${endpoint}`);
            return data;
            
        } catch (error) {
            console.error(`❌ API失败: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * GET请求
     */
    async get(endpoint, params = {}) {
        const url = new URL(endpoint, this.baseURL);
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
        return this.request(url.pathname + url.search);
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
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    /**
     * PATCH请求
     */
    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    // ========== 认证相关API ==========

    /**
     * 用户登录
     */
    async login(credentials) {
        return this.post('/auth/login', credentials);
    }

    /**
     * 用户注册
     */
    async register(userData) {
        return this.post('/auth/register', userData);
    }

    /**
     * 刷新认证token
     */
    async refreshAuthToken() {
        return this.post('/auth/refresh');
    }

    /**
     * 用户登出
     */
    async logout() {
        const result = await this.post('/auth/logout');
        localStorage.removeItem('authToken');
        localStorage.removeItem('accessToken');
        this.token = null;
        return result;
    }

    // ========== 用户相关API ==========

    /**
     * 获取当前用户信息
     */
    async getCurrentUserInfo() {
        return this.get('/user/profile');
    }

    /**
     * 更新用户信息
     */
    async updateUserProfile(profileData) {
        return this.put('/user/profile', profileData);
    }

    /**
     * 获取用户统计数据
     */
    async getUserStats() {
        return this.get('/user/stats');
    }

    /**
     * 获取仪表盘统计
     */
    async getDashboardStats() {
        return this.get('/dashboard/stats');
    }

    // ========== 任务相关API ==========

    /**
     * 获取可抢单任务列表
     */
    async getAvailableTasks(params = {}) {
        return this.get('/tasks/available', params);
    }

    /**
     * 获取我的任务列表
     */
    async getMyTasks(userType = 'user') {
        return this.get(`/tasks/my-tasks/${userType}`);
    }

    /**
     * 创建新任务
     */
    async createTask(taskData) {
        return this.post('/tasks', taskData);
    }

    /**
     * 抢单
     */
    async grabTask(taskId) {
        return this.post(`/tasks/${taskId}/grab`);
    }

    /**
     * 交换联系方式
     */
    async exchangeContact(taskId, contactData) {
        return this.post(`/tasks/${taskId}/exchange-contact`, contactData);
    }

    /**
     * 完成任务
     */
    async completeTask(taskId, completionData) {
        return this.post(`/tasks/${taskId}/complete`, completionData);
    }

    /**
     * 获取任务详情
     */
    async getTaskDetail(taskId) {
        return this.get(`/tasks/${taskId}`);
    }

    /**
     * 批量上传任务
     */
    async uploadTasks(formData) {
        return this.request('/tasks/upload', {
            method: 'POST',
            body: formData,
            headers: {
                // 移除Content-Type让浏览器自动设置multipart/form-data
                'Authorization': `Bearer ${this.token}`
            }
        });
    }

    // ========== 案件相关API ==========

    /**
     * 获取案件列表
     */
    async getCases(params = {}) {
        return this.get('/cases', params);
    }

    /**
     * 创建案件
     */
    async createCase(caseData) {
        return this.post('/cases', caseData);
    }

    /**
     * 更新案件
     */
    async updateCase(caseId, caseData) {
        return this.put(`/cases/${caseId}`, caseData);
    }

    // ========== 文件相关API ==========

    /**
     * 上传文件
     */
    async uploadFile(formData) {
        return this.request('/upload', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
    }

    // ========== 提现相关API ==========

    /**
     * 获取提现统计
     */
    async getWithdrawalStats() {
        return this.get('/finance/withdrawal/stats');
    }

    /**
     * 申请提现
     */
    async requestWithdrawal(withdrawalData) {
        return this.post('/finance/withdrawal/request', withdrawalData);
    }

    /**
     * 获取提现记录
     */
    async getWithdrawalHistory(params = {}) {
        return this.get('/finance/withdrawal/history', params);
    }

    // ========== 律师相关API ==========

    /**
     * 律师认证
     */
    async verifyLawyer(verificationData) {
        return this.post('/lawyer/verify', verificationData);
    }

    /**
     * 获取律师信息
     */
    async getLawyerInfo(lawyerId) {
        return this.get(`/lawyer/${lawyerId}`);
    }

    // ========== 管理员相关API ==========

    /**
     * 获取系统配置
     */
    async getSystemConfig() {
        return this.get('/admin/config');
    }

    /**
     * 更新系统配置
     */
    async updateSystemConfig(configData) {
        return this.put('/admin/config', configData);
    }

    /**
     * 获取管理员统计
     */
    async getAdminStats() {
        return this.get('/admin/stats');
    }

    // ========== AI相关API ==========

    /**
     * AI文书生成
     */
    async generateDocument(taskId, documentData) {
        return this.post(`/ai/generate-document`, {
            task_id: taskId,
            ...documentData
        });
    }

    /**
     * AI数据识别
     */
    async recognizeData(formData) {
        return this.request('/ai/recognize', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
    }
}

// 创建全局实例
window.apiClient = new ApiClient();

// 兼容性支持
window.ApiClient = ApiClient;