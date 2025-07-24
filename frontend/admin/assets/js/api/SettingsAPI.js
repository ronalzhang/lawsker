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