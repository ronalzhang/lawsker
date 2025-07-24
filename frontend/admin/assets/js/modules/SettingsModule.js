/**
 * 系统设置模块
 * 系统配置、参数设置、基础数据管理
 */

export class SettingsModule extends BaseModule {
    constructor(eventBus) {
        super(eventBus);
        this.currentTab = 'general';
        this.settings = {};
    }

    async render() {
        this.container.innerHTML = `
            <div class="settings-container">
                <!-- 页面标题 -->
                <div class="page-header">
                    <h1 class="page-title">系统设置</h1>
                    <p class="page-description">配置系统参数和基础设置</p>
                </div>

                <!-- 设置导航 -->
                <div class="settings-navigation">
                    <div class="nav-item active" data-tab="general">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                        </svg>
                        <span>基础设置</span>
                    </div>
                    <div class="nav-item" data-tab="business">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                            <line x1="8" y1="21" x2="16" y2="21"></line>
                            <line x1="12" y1="17" x2="12" y2="21"></line>
                        </svg>
                        <span>业务配置</span>
                    </div>
                    <div class="nav-item" data-tab="payment">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                            <line x1="1" y1="10" x2="23" y2="10"></line>
                        </svg>
                        <span>支付设置</span>
                    </div>
                    <div class="nav-item" data-tab="email">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                            <polyline points="22,6 12,13 2,6"></polyline>
                        </svg>
                        <span>邮件配置</span>
                    </div>
                    <div class="nav-item" data-tab="security">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        </svg>
                        <span>安全设置</span>
                    </div>
                </div>

                <!-- 设置内容 -->
                <div class="settings-content">
                    <!-- 基础设置 -->
                    <div class="settings-panel active" id="general-panel">
                        <div class="panel-header">
                            <h2>基础设置</h2>
                            <p>配置系统的基本信息和参数</p>
                        </div>
                        <div class="settings-form">
                            <div class="form-section">
                                <h3>网站信息</h3>
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">网站名称</label>
                                        <input type="text" class="form-input" id="site-name" value="律刻法律服务平台">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">网站描述</label>
                                        <textarea class="form-input" id="site-description" rows="3">专业的法律服务平台，连接用户与律师</textarea>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">联系邮箱</label>
                                        <input type="email" class="form-input" id="contact-email" value="contact@lawsker.com">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">客服电话</label>
                                        <input type="tel" class="form-input" id="contact-phone" value="400-123-4567">
                                    </div>
                                </div>
                            </div>

                            <div class="form-section">
                                <h3>系统参数</h3>
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">每页显示数量</label>
                                        <select class="form-input" id="page-size">
                                            <option value="10">10</option>
                                            <option value="20" selected>20</option>
                                            <option value="50">50</option>
                                            <option value="100">100</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">会话超时时间(分钟)</label>
                                        <input type="number" class="form-input" id="session-timeout" value="30">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">时区设置</label>
                                        <select class="form-input" id="timezone">
                                            <option value="Asia/Shanghai" selected>中国标准时间 (UTC+8)</option>
                                            <option value="UTC">协调世界时 (UTC)</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">语言设置</label>
                                        <select class="form-input" id="language">
                                            <option value="zh-CN" selected>简体中文</option>
                                            <option value="zh-TW">繁体中文</option>
                                            <option value="en-US">English</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div class="form-actions">
                                <button class="btn btn-primary" id="save-general">保存设置</button>
                                <button class="btn btn-secondary" id="reset-general">重置</button>
                            </div>
                        </div>
                    </div>

                    <!-- 业务配置 -->
                    <div class="settings-panel" id="business-panel">
                        <div class="panel-header">
                            <h2>业务配置</h2>
                            <p>配置业务相关的参数和规则</p>
                        </div>
                        <div class="settings-form">
                            <div class="form-section">
                                <h3>服务定价</h3>
                                <div class="pricing-grid">
                                    <div class="pricing-item">
                                        <label class="form-label">咨询服务费率</label>
                                        <div class="input-group">
                                            <input type="number" class="form-input" value="20" step="0.01">
                                            <span class="input-suffix">%</span>
                                        </div>
                                    </div>
                                    <div class="pricing-item">
                                        <label class="form-label">文书生成费用</label>
                                        <div class="input-group">
                                            <span class="input-prefix">¥</span>
                                            <input type="number" class="form-input" value="100" step="1">
                                        </div>
                                    </div>
                                    <div class="pricing-item">
                                        <label class="form-label">最低服务费</label>
                                        <div class="input-group">
                                            <span class="input-prefix">¥</span>
                                            <input type="number" class="form-input" value="50" step="1">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="form-section">
                                <h3>业务规则</h3>
                                <div class="rules-list">
                                    <div class="rule-item">
                                        <label class="checkbox-label">
                                            <input type="checkbox" checked>
                                            <span>启用实名认证</span>
                                        </label>
                                        <p class="rule-desc">用户必须完成实名认证才能发布任务</p>
                                    </div>
                                    <div class="rule-item">
                                        <label class="checkbox-label">
                                            <input type="checkbox" checked>
                                            <span>律师资质审核</span>
                                        </label>
                                        <p class="rule-desc">律师需要通过资质审核才能接单</p>
                                    </div>
                                    <div class="rule-item">
                                        <label class="checkbox-label">
                                            <input type="checkbox">
                                            <span>自动分配任务</span>
                                        </label>
                                        <p class="rule-desc">系统自动将任务分配给合适的律师</p>
                                    </div>
                                </div>
                            </div>

                            <div class="form-actions">
                                <button class="btn btn-primary" id="save-business">保存设置</button>
                                <button class="btn btn-secondary" id="reset-business">重置</button>
                            </div>
                        </div>
                    </div>

                    <!-- 支付设置 -->
                    <div class="settings-panel" id="payment-panel">
                        <div class="panel-header">
                            <h2>支付设置</h2>
                            <p>配置支付方式和相关参数</p>
                        </div>
                        <div class="settings-form">
                            <div class="payment-methods">
                                <div class="method-card">
                                    <div class="method-header">
                                        <h4>微信支付</h4>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider"></span>
                                        </label>
                                    </div>
                                    <div class="method-config">
                                        <div class="form-group">
                                            <label class="form-label">商户号</label>
                                            <input type="text" class="form-input" placeholder="请输入微信支付商户号">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">API密钥</label>
                                            <input type="password" class="form-input" placeholder="请输入API密钥">
                                        </div>
                                    </div>
                                </div>

                                <div class="method-card">
                                    <div class="method-header">
                                        <h4>支付宝</h4>
                                        <label class="switch">
                                            <input type="checkbox" checked>
                                            <span class="slider"></span>
                                        </label>
                                    </div>
                                    <div class="method-config">
                                        <div class="form-group">
                                            <label class="form-label">应用ID</label>
                                            <input type="text" class="form-input" placeholder="请输入支付宝应用ID">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">私钥</label>
                                            <textarea class="form-input" rows="3" placeholder="请输入应用私钥"></textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="form-actions">
                                <button class="btn btn-primary" id="save-payment">保存设置</button>
                                <button class="btn btn-secondary" id="test-payment">测试连接</button>
                            </div>
                        </div>
                    </div>

                    <!-- 其他面板... -->
                </div>
            </div>
        `;

        await this.loadStyles();
        await this.loadData();
    }

    async loadStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .settings-container {
                max-width: 1200px;
                margin: 0 auto;
                display: grid;
                grid-template-columns: 250px 1fr;
                gap: 32px;
            }

            .settings-navigation {
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 16px;
                height: fit-content;
                position: sticky;
                top: 96px;
            }

            .nav-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px;
                border-radius: var(--radius-md);
                cursor: pointer;
                transition: all var(--transition-fast);
                margin-bottom: 4px;
                color: var(--text-secondary);
            }

            .nav-item:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .nav-item.active {
                background: rgba(59, 130, 246, 0.1);
                color: var(--primary);
            }

            .nav-item svg {
                flex-shrink: 0;
            }

            .settings-content {
                position: relative;
            }

            .settings-panel {
                display: none;
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 32px;
            }

            .settings-panel.active {
                display: block;
            }

            .panel-header {
                margin-bottom: 32px;
            }

            .panel-header h2 {
                color: var(--text-primary);
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 8px;
            }

            .panel-header p {
                color: var(--text-secondary);
                font-size: 16px;
            }

            .form-section {
                margin-bottom: 32px;
                padding-bottom: 32px;
                border-bottom: 1px solid var(--border-secondary);
            }

            .form-section:last-child {
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }

            .form-section h3 {
                color: var(--text-primary);
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 20px;
            }

            .form-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }

            .form-group {
                display: flex;
                flex-direction: column;
            }

            .form-label {
                color: var(--text-primary);
                font-weight: 500;
                margin-bottom: 8px;
                font-size: 14px;
            }

            .form-input {
                padding: 12px 16px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                font-size: 14px;
                transition: all var(--transition-fast);
            }

            .form-input:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }

            .pricing-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }

            .pricing-item {
                display: flex;
                flex-direction: column;
            }

            .input-group {
                position: relative;
                display: flex;
                align-items: center;
            }

            .input-prefix,
            .input-suffix {
                position: absolute;
                color: var(--text-secondary);
                font-size: 14px;
                z-index: 1;
            }

            .input-prefix {
                left: 12px;
            }

            .input-suffix {
                right: 12px;
            }

            .input-group .form-input {
                padding-left: 32px;
            }

            .input-group .form-input:has(+ .input-suffix) {
                padding-right: 32px;
            }

            .rules-list {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }

            .rule-item {
                padding: 16px;
                background: var(--bg-tertiary);
                border-radius: var(--radius-md);
                border: 1px solid var(--border-secondary);
            }

            .checkbox-label {
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--text-primary);
                font-weight: 500;
                margin-bottom: 8px;
                cursor: pointer;
            }

            .checkbox-label input[type="checkbox"] {
                width: 16px;
                height: 16px;
                accent-color: var(--primary);
            }

            .rule-desc {
                color: var(--text-secondary);
                font-size: 13px;
                margin: 0;
                margin-left: 24px;
            }

            .payment-methods {
                display: flex;
                flex-direction: column;
                gap: 24px;
            }

            .method-card {
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 20px;
                background: var(--bg-tertiary);
            }

            .method-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
            }

            .method-header h4 {
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
                margin: 0;
            }

            .switch {
                position: relative;
                display: inline-block;
                width: 48px;
                height: 24px;
            }

            .switch input {
                opacity: 0;
                width: 0;
                height: 0;
            }

            .slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: var(--gray-300);
                transition: var(--transition-fast);
                border-radius: 24px;
            }

            .slider:before {
                position: absolute;
                content: "";
                height: 20px;
                width: 20px;
                left: 2px;
                bottom: 2px;
                background-color: white;
                transition: var(--transition-fast);
                border-radius: 50%;
            }

            input:checked + .slider {
                background-color: var(--primary);
            }

            input:checked + .slider:before {
                transform: translateX(24px);
            }

            .method-config {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 16px;
            }

            .form-actions {
                display: flex;
                gap: 12px;
                padding-top: 32px;
                border-top: 1px solid var(--border-secondary);
                margin-top: 32px;
            }

            .btn {
                padding: 12px 24px;
                border: none;
                border-radius: var(--radius-md);
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .btn-primary {
                background: var(--primary);
                color: white;
            }

            .btn-primary:hover {
                background: var(--primary-hover);
            }

            .btn-secondary {
                background: var(--bg-tertiary);
                color: var(--text-primary);
                border: 1px solid var(--border-primary);
            }

            .btn-secondary:hover {
                background: var(--bg-hover);
            }

            @media (max-width: 768px) {
                .settings-container {
                    grid-template-columns: 1fr;
                    gap: 20px;
                }

                .settings-navigation {
                    position: static;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 8px;
                }

                .nav-item {
                    flex-direction: column;
                    text-align: center;
                    padding: 12px 8px;
                }

                .nav-item span {
                    font-size: 12px;
                }

                .settings-panel {
                    padding: 20px;
                }

                .form-grid {
                    grid-template-columns: 1fr;
                }

                .pricing-grid {
                    grid-template-columns: 1fr;
                }

                .method-config {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        // 导航切换
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchPanel(tab);
            });
        });

        // 保存按钮
        document.getElementById('save-general')?.addEventListener('click', () => {
            this.saveGeneralSettings();
        });

        document.getElementById('save-business')?.addEventListener('click', () => {
            this.saveBusinessSettings();
        });

        document.getElementById('save-payment')?.addEventListener('click', () => {
            this.savePaymentSettings();
        });
    }

    async loadData() {
        // 模拟加载配置数据
        this.settings = {
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
                consultingFee: 20,
                documentFee: 100,
                minimumFee: 50,
                requireRealName: true,
                requireLawyerVerification: true,
                autoAssignTasks: false
            },
            payment: {
                wechatEnabled: true,
                alipayEnabled: true
            }
        };
    }

    switchPanel(tab) {
        this.currentTab = tab;

        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.tab === tab);
        });

        // 更新面板显示
        document.querySelectorAll('.settings-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `${tab}-panel`);
        });
    }

    saveGeneralSettings() {
        const formData = {
            siteName: document.getElementById('site-name').value,
            siteDescription: document.getElementById('site-description').value,
            contactEmail: document.getElementById('contact-email').value,
            contactPhone: document.getElementById('contact-phone').value,
            pageSize: parseInt(document.getElementById('page-size').value),
            sessionTimeout: parseInt(document.getElementById('session-timeout').value),
            timezone: document.getElementById('timezone').value,
            language: document.getElementById('language').value
        };

        // 模拟保存
        console.log('保存基础设置:', formData);
        this.showNotification('基础设置保存成功', 'success');

        // 更新本地设置
        this.settings.general = { ...this.settings.general, ...formData };
    }

    saveBusinessSettings() {
        // 收集业务配置数据
        const businessData = {
            // 这里可以收集业务配置表单数据
        };

        console.log('保存业务设置:', businessData);
        this.showNotification('业务设置保存成功', 'success');
    }

    savePaymentSettings() {
        // 收集支付配置数据
        const paymentData = {
            // 这里可以收集支付配置表单数据
        };

        console.log('保存支付设置:', paymentData);
        this.showNotification('支付设置保存成功', 'success');
    }

    showNotification(message, type) {
        if (this.eventBus) {
            this.eventBus.emit('notification', { message, type });
        }
    }
}