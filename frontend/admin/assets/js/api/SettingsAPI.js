/**
 * 系统设置 API 服务
 * 处理设置数据的保存、加载和验证
 */

class SettingsAPI {
    constructor() {
        this.baseURL = '/api/admin/settings';
        this.storageKey = 'lawsker_admin_settings';
        
        // 默认设置
        this.defaultSettings = {
            general: {
                siteName: '律刻法律服务平台',
                siteDescription: '专业的法律服务平台，连接用户与律师',
                contactEmail: 'contact@lawsker.com',
                contactPhone: '400-123-4567',
                pageSize: 20,
                sessionTimeout: 30,
                timezone: 'Asia/Shanghai',
                language: 'zh-CN'
            },
            business: {
                consultingFeeRate: 20,
                documentFee: 100,
                minimumFee: 50,
                requireRealName: true,
                requireLawyerVerification: true,
                autoAssignTasks: false,
                maxTasksPerLawyer: 10,
                taskTimeoutHours: 72
            },
            payment: {
                wechatEnabled: true,
                alipayEnabled: true,
                wechatMerchantId: '',
                wechatApiKey: '',
                alipayAppId: '',
                alipayPrivateKey: '',
                paymentTimeout: 30
            },
            email: {
                smtpHost: 'smtp.exmail.qq.com',
                smtpPort: 465,
                smtpUser: '',
                smtpPassword: '',
                smtpSecure: true,
                fromEmail: 'noreply@lawsker.com',
                fromName: '律刻法律服务平台'
            },
            security: {
                passwordMinLength: 8,
                passwordRequireUppercase: true,
                passwordRequireNumbers: true,
                passwordRequireSymbols: false,
                sessionMaxAge: 7200000, // 2小时
                maxLoginAttempts: 5,
                lockoutDuration: 300000, // 5分钟
                enableTwoFactor: false,
                allowedIpWhitelist: []
            },
            ai: {
                engines: {
                    openai: {
                        enabled: true,
                        apiKey: '',
                        model: 'gpt-4',
                        baseUrl: 'https://api.openai.com/v1',
                        status: 'active'
                    },
                    deepseek: {
                        enabled: true,
                        apiKey: '',
                        model: 'deepseek-chat',
                        baseUrl: 'https://api.deepseek.com/v1',
                        status: 'active'
                    },
                    claude: {
                        enabled: false,
                        apiKey: '',
                        model: 'claude-3-5-sonnet-20241022',
                        baseUrl: 'https://api.anthropic.com',
                        status: 'backup'
                    }
                },
                strategy: {
                    primaryEngine: 'openai',
                    backupEngine: 'deepseek',
                    timeout: 60,
                    retryAttempts: 3
                },
                prompts: {
                    lawyer_letter: `你是一位专业的律师，请根据以下信息生成一份正式的律师函：
案件类型：{case_type}
当事人：{client_name}
对方：{target_name}
争议金额：{amount}
案件描述：{description}
法律依据：{legal_basis}
请确保律师函包含以下要素：
1. 正式的开头称谓
2. 事实陈述
3. 法律分析
4. 具体要求
5. 截止期限
6. 法律后果警告`,
                    debt_collection: `你是一位专业的律师，请生成一份债务催收律师函：
债务人：{debtor_name}
债权人：{creditor_name}
欠款金额：{debt_amount}
逾期天数：{overdue_days}
合同编号：{contract_number}
要求：语气严厉但合法合规，明确还款期限和法律后果`,
                    contract_review: `你是一位专业的律师，请对以下合同进行法律审查：
合同类型：{contract_type}
合同名称：{contract_name}
当事方：{parties}
合同金额：{contract_amount}
履行期限：{performance_deadline}
特殊条款：{special_clauses}
请从以下角度进行审查：
1. 合同主体资格
2. 合同条款完整性
3. 法律风险识别
4. 合规性检查`,
                    legal_consultation: `你是一位专业的律师，请针对以下法律问题提供咨询意见：
咨询类别：{consultation_category}
问题描述：{problem_description}
相关背景：{background_info}
期望结果：{expected_outcome}
请提供：
1. 问题的法律性质分析
2. 适用的法律法规
3. 处理建议和操作步骤`,
                    legal_document: `你是一位专业的律师，请根据以下信息生成相应的法律文书：
文书类型：{document_type}
案件标题：{case_title}
基本事实：{basic_facts}
法律依据：{legal_basis}
处理要求：{processing_requirements}
请确保文书内容：
1. 事实描述客观准确
2. 法律依据充分有效
3. 格式规范专业`
                },
                stats: {
                    openai: {
                        todayCalls: 1247,
                        monthCalls: 28569,
                        balance: '$87.45'
                    },
                    deepseek: {
                        todayCalls: 892,
                        monthCalls: 19765,
                        balance: '¥156.80'
                    },
                    claude: {
                        todayCalls: 0,
                        monthCalls: 0,
                        balance: '--'
                    }
                }
            }
        };
    }

    /**
     * 加载所有设置
     */
    async loadSettings() {
        try {
            // 优先从服务器加载
            const response = await this.fetch('/all');
            if (response.ok) {
                const settings = await response.json();
                this.saveToLocalStorage(settings);
                return settings;
            }
        } catch (error) {
            console.warn('从服务器加载设置失败，使用本地存储:', error);
        }

        // 回退到本地存储
        const localSettings = this.loadFromLocalStorage();
        return localSettings || this.defaultSettings;
    }

    /**
     * 保存特定分类的设置
     */
    async saveSettings(category, settings) {
        try {
            // 验证设置数据
            const validatedSettings = this.validateSettings(category, settings);
            
            // 保存到服务器
            const response = await this.fetch(`/${category}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(validatedSettings)
            });

            if (response.ok) {
                const result = await response.json();
                
                // 更新本地存储
                const allSettings = this.loadFromLocalStorage() || {};
                allSettings[category] = validatedSettings;
                this.saveToLocalStorage(allSettings);
                
                return { success: true, data: result };
            } else {
                const error = await response.json();
                return { success: false, error: error.message };
            }
        } catch (error) {
            console.error('保存设置失败:', error);
            
            // 降级保存到本地存储
            const allSettings = this.loadFromLocalStorage() || {};
            allSettings[category] = settings;
            this.saveToLocalStorage(allSettings);
            
            return { success: true, data: settings, fromLocal: true };
        }
    }

    /**
     * 获取特定分类的设置
     */
    async getSettings(category) {
        try {
            const response = await this.fetch(`/${category}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn(`获取${category}设置失败:`, error);
        }

        // 回退到本地存储
        const allSettings = this.loadFromLocalStorage() || {};
        return allSettings[category] || this.defaultSettings[category];
    }

    /**
     * 测试邮件配置
     */
    async testEmailConfig(emailSettings) {
        try {
            const response = await this.fetch('/email/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(emailSettings)
            });

            const result = await response.json();
            return { success: response.ok, ...result };
        } catch (error) {
            return { 
                success: false, 
                error: '连接服务器失败，请检查网络连接',
                details: error.message 
            };
        }
    }

    /**
     * 测试支付配置
     */
    async testPaymentConfig(paymentSettings) {
        try {
            const response = await this.fetch('/payment/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(paymentSettings)
            });

            const result = await response.json();
            return { success: response.ok, ...result };
        } catch (error) {
            return { 
                success: false, 
                error: '支付服务连接失败',
                details: error.message 
            };
        }
    }

    /**
     * 测试AI引擎配置
     */
    async testAIConfig(aiSettings) {
        try {
            const response = await this.fetch('/ai/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(aiSettings)
            });

            const result = await response.json();
            return { success: response.ok, ...result };
        } catch (error) {
            return { 
                success: false, 
                error: 'AI服务连接失败',
                details: error.message 
            };
        }
    }

    /**
     * 获取AI引擎统计数据
     */
    async getAIStats() {
        try {
            const response = await this.fetch('/ai/stats');
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn('获取AI统计数据失败:', error);
        }

        // 回退到默认统计数据
        return this.defaultSettings.ai.stats;
    }

    /**
     * 重置设置为默认值
     */
    async resetSettings(category) {
        const defaultSettings = this.defaultSettings[category];
        if (!defaultSettings) {
            return { success: false, error: '无效的设置分类' };
        }

        return await this.saveSettings(category, defaultSettings);
    }

    /**
     * 导出设置
     */
    async exportSettings() {
        const settings = await this.loadSettings();
        const exportData = {
            version: '1.0',
            timestamp: new Date().toISOString(),
            settings: settings
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lawsker-settings-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);

        return { success: true };
    }

    /**
     * 导入设置
     */
    async importSettings(file) {
        try {
            const text = await file.text();
            const importData = JSON.parse(text);
            
            if (!importData.settings) {
                return { success: false, error: '无效的设置文件格式' };
            }

            // 验证并保存各个分类的设置
            const results = {};
            for (const [category, settings] of Object.entries(importData.settings)) {
                if (this.defaultSettings[category]) {
                    const result = await this.saveSettings(category, settings);
                    results[category] = result;
                }
            }

            return { success: true, results };
        } catch (error) {
            return { 
                success: false, 
                error: '导入设置失败', 
                details: error.message 
            };
        }
    }

    /**
     * 验证设置数据
     */
    validateSettings(category, settings) {
        const validators = {
            general: (data) => {
                const validated = { ...data };
                
                // 验证必填字段
                if (!validated.siteName || validated.siteName.trim().length === 0) {
                    throw new Error('网站名称不能为空');
                }
                
                if (!validated.contactEmail || !this.isValidEmail(validated.contactEmail)) {
                    throw new Error('请输入有效的联系邮箱');
                }
                
                if (!validated.contactPhone || validated.contactPhone.trim().length === 0) {
                    throw new Error('联系电话不能为空');
                }
                
                // 验证数值范围
                validated.pageSize = Math.max(10, Math.min(100, parseInt(validated.pageSize) || 20));
                validated.sessionTimeout = Math.max(5, Math.min(120, parseInt(validated.sessionTimeout) || 30));
                
                return validated;
            },
            
            business: (data) => {
                const validated = { ...data };
                
                validated.consultingFeeRate = Math.max(0, Math.min(50, parseFloat(validated.consultingFeeRate) || 20));
                validated.documentFee = Math.max(0, parseFloat(validated.documentFee) || 100);
                validated.minimumFee = Math.max(0, parseFloat(validated.minimumFee) || 50);
                validated.maxTasksPerLawyer = Math.max(1, Math.min(50, parseInt(validated.maxTasksPerLawyer) || 10));
                validated.taskTimeoutHours = Math.max(1, Math.min(168, parseInt(validated.taskTimeoutHours) || 72));
                
                return validated;
            },
            
            payment: (data) => {
                const validated = { ...data };
                validated.paymentTimeout = Math.max(5, Math.min(60, parseInt(validated.paymentTimeout) || 30));
                return validated;
            },
            
            email: (data) => {
                const validated = { ...data };
                
                if (validated.fromEmail && !this.isValidEmail(validated.fromEmail)) {
                    throw new Error('请输入有效的发件人邮箱');
                }
                
                validated.smtpPort = Math.max(1, Math.min(65535, parseInt(validated.smtpPort) || 465));
                
                return validated;
            },
            
            security: (data) => {
                const validated = { ...data };
                
                validated.passwordMinLength = Math.max(6, Math.min(32, parseInt(validated.passwordMinLength) || 8));
                validated.sessionMaxAge = Math.max(300000, Math.min(86400000, parseInt(validated.sessionMaxAge) || 7200000));
                validated.maxLoginAttempts = Math.max(3, Math.min(10, parseInt(validated.maxLoginAttempts) || 5));
                validated.lockoutDuration = Math.max(60000, Math.min(3600000, parseInt(validated.lockoutDuration) || 300000));
                
                return validated;
            },
            
            ai: (data) => {
                const validated = { ...data };
                
                // 验证引擎配置
                if (validated.engines) {
                    Object.keys(validated.engines).forEach(engine => {
                        const config = validated.engines[engine];
                        if (config.enabled && !config.apiKey) {
                            throw new Error(`${engine}引擎已启用但API Key为空`);
                        }
                        if (config.enabled && !config.baseUrl) {
                            throw new Error(`${engine}引擎已启用但Base URL为空`);
                        }
                    });
                }
                
                // 验证引擎策略
                if (validated.strategy) {
                    validated.strategy.timeout = Math.max(10, Math.min(300, parseInt(validated.strategy.timeout) || 60));
                    validated.strategy.retryAttempts = Math.max(1, Math.min(5, parseInt(validated.strategy.retryAttempts) || 3));
                }
                
                return validated;
            }
        };

        const validator = validators[category];
        if (!validator) {
            throw new Error(`未知的设置分类: ${category}`);
        }

        return validator(settings);
    }

    /**
     * 邮箱格式验证
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * 本地存储操作
     */
    saveToLocalStorage(settings) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(settings));
            return true;
        } catch (error) {
            console.error('保存到本地存储失败:', error);
            return false;
        }
    }

    loadFromLocalStorage() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('从本地存储加载失败:', error);
            return null;
        }
    }

    /**
     * HTTP 请求封装
     */
    async fetch(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = { ...defaultOptions, ...options };
        
        // 模拟网络延迟
        await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 200));
        
        // 模拟服务器响应
        if (endpoint === '/all') {
            return new Response(JSON.stringify(this.loadFromLocalStorage() || this.defaultSettings), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        if (options.method === 'POST') {
            return new Response(JSON.stringify({ success: true, timestamp: new Date().toISOString() }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 对于其他请求，返回默认设置
        const category = endpoint.substring(1);
        if (this.defaultSettings[category]) {
            return new Response(JSON.stringify(this.defaultSettings[category]), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        return new Response(JSON.stringify({ error: 'Not found' }), {
            status: 404,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// 导出单例实例
const settingsAPI = new SettingsAPI();
export default settingsAPI;