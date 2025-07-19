/**
 * Lawsker API 客户端 v1.4
 * 统一管理前端API调用
 * 更新时间: 2024-01-16
 * 改进: 演示模式优化，减少无效API调用
 */

class ApiClient {
    constructor() {
        this.baseURL = 'https://156.236.74.200/api/v1';
        // 兼容多种token存储方式
        this.token = localStorage.getItem('authToken') || localStorage.getItem('accessToken');
        this.version = '1.4'; // API客户端版本号
        
        // 检测是否为演示模式
        this.isDemoMode = this._checkDemoMode();
        if (this.isDemoMode) {
            console.log('🎭 演示模式已启用，将使用本地数据');
        }
    }

    /**
     * 检测是否为演示模式
     */
    _checkDemoMode() {
        const path = window.location.pathname;
        // 演示页面路径：/legal, /user (不带数字/ID)
        return path === '/legal' || path === '/user' || path === '/institution' ||
               path === '/legal/' || path === '/user/' || path === '/institution/';
    }

    /**
     * 检测是否为个人工作台模式
     */
    _isPersonalWorkspace() {
        const path = window.location.pathname;
        // 个人工作台模式：包含用户ID的路径
        return path.includes('/workspace/') || 
               /\/(user|legal|institution)\/[^\/]+$/.test(path);
    }

    /**
     * 刷新token
     */
    refreshToken() {
        this.token = localStorage.getItem('authToken') || localStorage.getItem('accessToken');
    }

    /**
     * 通用请求方法
     */
    async request(endpoint, options = {}) {
        // 演示模式下，如果没有token直接使用fallback数据
        if (this.isDemoMode) {
            this.refreshToken();
            if (!this.token) {
                console.log(`🎭 演示模式: 无Token，直接使用本地数据 for ${endpoint}`);
                // 模拟网络延迟，提供真实感
                await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200));
                return this._getFallbackData(endpoint);
            }
            
            console.log(`🎭 演示模式: 有Token，先尝试真实API，失败后使用本地数据 for ${endpoint}`);
            // 尝试真实API调用
            try {
                const url = `${this.baseURL}${endpoint}`;
                const config = {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                };

                // 添加token到请求头
                config.headers['Authorization'] = `Bearer ${this.token}`;
                console.log(`🔗 演示模式API尝试: ${config.method || 'GET'} ${url} (有Token)`);

                const response = await fetch(url, config);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log(`✅ 演示模式获取到真实数据: ${endpoint}`);
                    return data;
                } else {
                    console.log(`⚠️ 演示模式API失败(${response.status})，使用fallback数据: ${endpoint}`);
                    // 如果是401错误，清除无效token避免后续重复请求
                    if (response.status === 401) {
                        localStorage.removeItem('authToken');
                        localStorage.removeItem('accessToken');
                        this.token = null;
                    }
                    // 模拟网络延迟，提供真实感
                    await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200));
                    return this._getFallbackData(endpoint);
                }
            } catch (error) {
                console.log(`⚠️ 演示模式API异常，使用fallback数据: ${endpoint}`, error);
                // 模拟网络延迟，提供真实感
                await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200));
                return this._getFallbackData(endpoint);
            }
        }

        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // 刷新token并添加认证
        this.refreshToken();
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
            console.log(`🔗 API请求 v${this.version}: ${config.method || 'GET'} ${url} (Token: ${this.token.substring(0, 20)}...)`);
        } else {
            console.log(`🔗 API请求 v${this.version}: ${config.method || 'GET'} ${url} (无Token)`);
        }

        // 检查是否为个人工作台模式
        const isPersonalWorkspace = this._isPersonalWorkspace();

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                console.error(`❌ API请求失败: ${response.status} ${response.statusText} for ${endpoint}`);
                
                // 个人工作台模式：绝不使用降级数据，直接抛出错误
                if (isPersonalWorkspace) {
                    console.error(`🚫 个人工作台模式: API失败不允许降级 ${endpoint}`);
                    throw new Error(`个人工作台API请求失败: ${response.status} ${response.statusText}`);
                }
                
                // 非个人工作台：对于统计和财务数据，可以使用演示数据
                if (endpoint.includes('/statistics/') || endpoint.includes('/finance/') || 
                    endpoint.includes('/cases') || endpoint.includes('/tasks')) {
                    
                    if (response.status === 403 || response.status === 401) {
                        console.warn(`⚠️ 认证失败(${response.status})，使用演示数据 for ${endpoint}`);
                    } else if (response.status === 404) {
                        console.warn(`⚠️ API端点不存在(${response.status})，使用演示数据 for ${endpoint}`);
                    }
                    
                    return this._getFallbackData(endpoint);
                }
                
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`💥 API请求异常 for ${endpoint}:`, error);
            
            // 个人工作台模式：绝不使用降级数据
            if (isPersonalWorkspace) {
                console.error(`🚫 个人工作台模式: API异常不允许降级 ${endpoint}`);
                throw error;
            }
            
            // 非个人工作台：对于关键数据请求失败，使用fallback
            if (endpoint.includes('/statistics/') || endpoint.includes('/finance/') || 
                endpoint.includes('/cases') || endpoint.includes('/tasks')) {
                console.warn(`⚠️ 使用fallback数据 for ${endpoint}`);
                return this._getFallbackData(endpoint);
            }
            
            throw error;
        }
    }

    /**
     * 获取后备数据
     */
    _getFallbackData(endpoint) {
        // 演示数据版本标识
        const demoTimestamp = new Date().toISOString();
        
        // 根据不同的endpoint返回相应的fallback数据
        if (endpoint.includes('/cases')) {
            return {
                items: [
                    {
                        id: "demo-case-1",
                        case_number: "LAW-2024-001",
                        debtor_name: "张三",
                        debt_amount: 50000,
                        status: "进行中",
                        progress: 65,
                        created_at: "2024-01-15T10:30:00Z",
                        assigned_to: "李律师",
                        last_contact: "2024-01-16T14:20:00Z"
                    },
                    {
                        id: "demo-case-2", 
                        case_number: "LAW-2024-002",
                        debtor_name: "王五",
                        debt_amount: 35000,
                        status: "已完成",
                        progress: 100,
                        created_at: "2024-01-14T09:20:00Z",
                        assigned_to: "张律师",
                        completed_at: "2024-01-16T11:30:00Z"
                    },
                    {
                        id: "demo-case-3",
                        case_number: "LAW-2024-003", 
                        debtor_name: "赵六",
                        debt_amount: 28000,
                        status: "待处理",
                        progress: 10,
                        created_at: "2024-01-16T08:45:00Z",
                        assigned_to: "王律师"
                    }
                ],
                total: 67,
                active_cases: 8,
                completed_cases: 56,
                pending_cases: 3,
                page: 1,
                pages: 4
            };
        }
        
        if (endpoint.includes('/tasks')) {
            return {
                items: [
                    {
                        id: "demo-task-1",
                        title: "债务催收任务",
                        description: "客户逾期账款催收，金额较大需要专业处理",
                        amount: 25000,
                        commission: 5000,
                        status: "可接单",
                        urgency: "高",
                        created_at: "2024-01-16T08:30:00Z",
                        deadline: "2024-01-20T18:00:00Z",
                        publisher: "某金融公司",
                        requirements: ["执业律师资质", "债务催收经验", "沟通能力强"]
                    },
                    {
                        id: "demo-task-2",
                        title: "合同纠纷处理", 
                        description: "商业合同违约处理，涉及技术服务合同",
                        amount: 18000,
                        commission: 3600,
                        status: "进行中",
                        urgency: "中",
                        created_at: "2024-01-15T14:20:00Z",
                        deadline: "2024-01-25T18:00:00Z",
                        publisher: "某科技公司",
                        grabbed_by: "我",
                        requirements: ["商事法律经验", "合同法专业"]
                    },
                    {
                        id: "demo-task-3",
                        title: "投资纠纷调解",
                        description: "投资理财产品纠纷，需要协助客户维权",
                        amount: 35000,
                        commission: 7000,
                        status: "可接单",
                        urgency: "高",
                        created_at: "2024-01-16T10:15:00Z",
                        deadline: "2024-01-18T18:00:00Z",
                        publisher: "某投资咨询公司",
                        requirements: ["金融法律经验", "投资纠纷处理"]
                    }
                ],
                total: 15,
                available: 8,
                grabbed: 4,
                completed: 3,
                page: 1,
                pages: 2
            };
        }
        
        if (endpoint.includes('/withdrawal') || endpoint.includes('/finance/')) {
            return {
                items: [
                    {
                        id: "demo-withdrawal-1",
                        request_number: "WD-2024-001",
                        amount: 5000,
                        fee: 0,
                        net_amount: 5000,
                        status: "已完成",
                        method: "支付宝",
                        account: "138****8888",
                        created_at: "2024-01-10T10:30:00Z",
                        processed_at: "2024-01-10T15:20:00Z",
                        bank_name: "支付宝"
                    },
                    {
                        id: "demo-withdrawal-2",
                        request_number: "WD-2024-002", 
                        amount: 3000,
                        fee: 0,
                        net_amount: 3000,
                        status: "处理中",
                        method: "银行卡",
                        account: "****1234",
                        created_at: "2024-01-15T16:45:00Z",
                        bank_name: "工商银行"
                    },
                    {
                        id: "demo-withdrawal-3",
                        request_number: "WD-2024-003",
                        amount: 8000,
                        fee: 0,
                        net_amount: 8000,
                        status: "已完成",
                        method: "微信",
                        account: "189****6666",
                        created_at: "2024-01-08T09:20:00Z",
                        processed_at: "2024-01-08T14:30:00Z",
                        bank_name: "微信钱包"
                    }
                ],
                // 提现统计数据
                total_withdrawn: 25000,
                withdrawal_count: 12,
                monthly_withdrawn: 8000,
                monthly_count: 3,
                average_amount: 2083.33,
                pending_amount: 3000,
                pending_count: 1,
                completed_amount: 22000,
                completed_count: 11,
                largest_withdrawal: 8000,
                success_rate: 95.8
            };
        }
        
        if (endpoint.includes('/auth/me') || endpoint.includes('/user')) {
            return {
                id: "demo-user-001",
                username: "演示用户",
                email: "demo@lawsker.com",
                phone: "138****8888",
                role: this.isDemoMode && window.location.pathname.includes('/legal') ? 'lawyer' : 'sales',
                status: "active",
                avatar: "/images/default-avatar.png",
                created_at: "2024-01-01T08:00:00Z",
                last_login: demoTimestamp,
                profile: {
                    real_name: "张三",
                    license_number: this.isDemoMode && window.location.pathname.includes('/legal') ? "11010120220001" : null,
                    law_firm: this.isDemoMode && window.location.pathname.includes('/legal') ? "北京某某律师事务所" : null,
                    specialties: this.isDemoMode && window.location.pathname.includes('/legal') ? ["债务催收", "合同纠纷"] : null
                }
            };
        }
        
        // 通用统计数据
        const fallbackData = {
            // 基础统计数据
            total_tasks: 128,
            completed_tasks: 95,
            active_users: 42,
            total_revenue: 285600,
            monthly_revenue: 68400,
            completion_rate: 89.5,
            growth_rate: 12.3,
            
            // 用户统计 (律客用户)
            published_tasks: 15,
            uploaded_data: 8,
            total_earnings: 12580,
            monthly_earnings: 3200,
            upload_records: 23,
            task_completion_rate: 92.5,
            average_task_value: 1680,
            
            // 律师统计
            my_cases: 67,
            monthly_income: 18500,
            pending_cases: 3,
            active_cases: 8,
            completed_cases: 56,
            total_earnings: 145000,
            pending_earnings: 15600,
            this_month_earnings: 18500,
            review_tasks: 12,
            pending_reviews: 3,
            case_success_rate: 94.2,
            client_satisfaction: 4.8,
            response_time: 2.5, // 小时
            
            // 提现统计
            total_withdrawn: 25000,
            withdrawal_count: 12,
            monthly_withdrawn: 8000,
            monthly_count: 3,
            average_amount: 2083.33,
            pending_amount: 3000,
            pending_count: 1,
            completed_amount: 22000,
            completed_count: 11,
            
            // 用户等级
            current_level: 3,
            level_name: "律客达人",
            level_progress: 56,
            next_level_threshold: 5000,
            level_benefits: ["专属客服", "优先推荐", "更高佣金"],
            
            // 钱包信息
            user_id: "demo-user-001",
            balance: 8500,
            withdrawable_balance: 8500,
            frozen_balance: 0,
            total_earned: 25000,
            commission_count: 15,
            pending_commission: 2500,
            
            // 业务指标
            today_income: 1500,
            week_income: 8500,
            month_target: 20000,
            completion_percentage: 75.5,
            
            user_type: "demo",
            data_source: "fallback",
            generated_at: demoTimestamp,
            
            // 最近活动
            recent_activities: [
                {
                    id: "demo-activity-1",
                    action: "任务完成",
                    resource_type: "task",
                    details: { task_title: "债务催收协助", amount: 1500, commission: 300 },
                    created_at: "2024-01-16T14:30:00Z"
                },
                {
                    id: "demo-activity-2", 
                    action: "提现申请",
                    resource_type: "withdrawal",
                    details: { amount: 5000, status: "已完成", method: "支付宝" },
                    created_at: "2024-01-15T10:20:00Z"
                },
                {
                    id: "demo-activity-3",
                    action: this.isDemoMode && window.location.pathname.includes('/legal') ? "案件分配" : "任务发布",
                    resource_type: this.isDemoMode && window.location.pathname.includes('/legal') ? "case" : "task",
                    details: this.isDemoMode && window.location.pathname.includes('/legal') ? 
                        { case_number: "LAW-2024-003", debtor: "赵六", amount: 28000 } :
                        { task_title: "合同审查", budget: 3000, deadline: "2024-01-20" },
                    created_at: "2024-01-14T09:15:00Z"
                },
                {
                    id: "demo-activity-4",
                    action: "系统登录",
                    resource_type: "auth",
                    details: { login_method: "密码登录", ip: "192.168.1.100" },
                    created_at: "2024-01-16T08:00:00Z"
                }
            ]
        };
        
        return fallbackData;
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
        return this.get('/finance/withdrawal/list');
    }

    /**
     * 获取用户统计数据
     */
    async getUserStats() {
        return this.get('/statistics/user-stats');
    }

    /**
     * 获取律师统计数据
     */
    async getLawyerStats() {
        return this.get('/statistics/lawyer-stats');
    }

    /**
     * 获取销售统计数据
     */
    async getSalesStats() {
        return this.get('/statistics/sales-stats');
    }

    /**
     * 获取用户等级信息
     */
    async getUserLevel() {
        return this.get('/statistics/user-level');
    }

    /**
     * 获取提现统计数据（修正路径）
     */
    async getWithdrawalStats() {
        return this.get('/finance/withdrawal/stats');
    }

    /**
     * 获取销售提现统计数据
     */
    async getSalesWithdrawalStats() {
        return this.get('/finance/withdrawal/stats');
    }

    /**
     * 获取钱包信息
     */
    async getWalletInfo() {
        return this.get('/finance/wallet');
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
     * 获取我的任务
     */
    async getMyTasks() {
        return this.get('/tasks/my-tasks');
    }

    /**
     * 获取可用任务
     */
    async getAvailableTasks() {
        return this.get('/tasks/available');
    }

    /**
     * 获取任务详情
     */
    async getTaskDetail(taskId) {
        return this.get(`/tasks/${taskId}`);
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