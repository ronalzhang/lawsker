/**
 * 系统设置模块
 * 系统配置、参数设置、基础数据管理
 */

import settingsAPI from '../api/SettingsAPI.js';

export class SettingsModule extends BaseModule {
    constructor(eventBus) {
        super(eventBus);
        this.currentTab = 'general';
        this.settings = {};
        this.settingsAPI = settingsAPI;
        this.isLoading = false;
        this.hasUnsavedChanges = false;
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
                    <div class="settings-nav-item active" data-tab="general">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                        </svg>
                        <span>基础设置</span>
                    </div>
                    <div class="settings-nav-item" data-tab="business">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                            <line x1="8" y1="21" x2="16" y2="21"></line>
                            <line x1="12" y1="17" x2="12" y2="21"></line>
                        </svg>
                        <span>业务配置</span>
                    </div>
                    <div class="settings-nav-item" data-tab="payment">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                            <line x1="1" y1="10" x2="23" y2="10"></line>
                        </svg>
                        <span>支付设置</span>
                    </div>
                    <div class="settings-nav-item" data-tab="ai">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m15.5-6.5L17 8.5m-10 7L3.5 19m15.5.5L17 15.5m-10-7L3.5 4.5"></path>
                        </svg>
                        <span>AI配置</span>
                    </div>
                    <div class="settings-nav-item" data-tab="email">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                            <polyline points="22,6 12,13 2,6"></polyline>
                        </svg>
                        <span>邮件配置</span>
                    </div>
                    <div class="settings-nav-item" data-tab="security">
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

                    <!-- AI配置 -->
                    <div class="settings-panel" id="ai-panel">
                        <div class="panel-header">
                            <h2>AI配置</h2>
                            <p>配置AI服务提供商和参数</p>
                        </div>
                        <div class="settings-form">
                            <!-- AI引擎配置 -->
                            <div class="form-section">
                                <h3>AI引擎配置</h3>
                                <div class="ai-engines-grid">
                                    <!-- OpenAI GPT -->
                                    <div class="ai-engine-card">
                                        <div class="engine-header">
                                            <div class="engine-info">
                                                <h4>OpenAI GPT</h4>
                                                <span class="status-indicator status-active" id="openai-status">运行中</span>
                                            </div>
                                            <label class="switch">
                                                <input type="checkbox" id="openai-enabled" checked>
                                                <span class="slider"></span>
                                            </label>
                                        </div>
                                        <div class="engine-config">
                                            <div class="form-group">
                                                <label class="form-label">API Key</label>
                                                <input type="password" class="form-input" id="openai-api-key" placeholder="sk-...">
                                            </div>
                                            <div class="form-group">
                                                <label class="form-label">模型</label>
                                                <select class="form-input" id="openai-model">
                                                    <option value="gpt-4" selected>GPT-4</option>
                                                    <option value="gpt-3.5-turbo">GPT-3.5-Turbo</option>
                                                </select>
                                            </div>
                                            <div class="form-group">
                                                <label class="form-label">Base URL</label>
                                                <input type="url" class="form-input" id="openai-base-url" value="https://api.openai.com/v1">
                                            </div>
                                        </div>
                                        <div class="engine-stats">
                                            <div class="stat-item">
                                                <span class="stat-label">今日调用</span>
                                                <span class="stat-value" id="openai-today">1,247</span>
                                            </div>
                                            <div class="stat-item">
                                                <span class="stat-label">月度调用</span>
                                                <span class="stat-value" id="openai-month">28,569</span>
                                            </div>
                                            <div class="stat-item">
                                                <span class="stat-label">账户余额</span>
                                                <span class="stat-value" id="openai-balance">$87.45</span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Deepseek -->
                                    <div class="ai-engine-card">
                                        <div class="engine-header">
                                            <div class="engine-info">
                                                <h4>Deepseek Chat</h4>
                                                <span class="status-indicator status-active" id="deepseek-status">运行中</span>
                                            </div>
                                            <label class="switch">
                                                <input type="checkbox" id="deepseek-enabled" checked>
                                                <span class="slider"></span>
                                            </label>
                                        </div>
                                        <div class="engine-config">
                                            <div class="form-group">
                                                <label class="form-label">API Key</label>
                                                <input type="password" class="form-input" id="deepseek-api-key" placeholder="sk-...">
                                            </div>
                                            <div class="form-group">
                                                <label class="form-label">模型</label>
                                                <select class="form-input" id="deepseek-model">
                                                    <option value="deepseek-chat" selected>deepseek-chat</option>
                                                </select>
                                            </div>
                                            <div class="form-group">
                                                <label class="form-label">Base URL</label>
                                                <input type="url" class="form-input" id="deepseek-base-url" value="https://api.deepseek.com/v1">
                                            </div>
                                        </div>
                                        <div class="engine-stats">
                                            <div class="stat-item">
                                                <span class="stat-label">今日调用</span>
                                                <span class="stat-value" id="deepseek-today">892</span>
                                            </div>
                                            <div class="stat-item">
                                                <span class="stat-label">月度调用</span>
                                                <span class="stat-value" id="deepseek-month">19,765</span>
                                            </div>
                                            <div class="stat-item">
                                                <span class="stat-label">账户余额</span>
                                                <span class="stat-value" id="deepseek-balance">¥156.80</span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Claude -->
                                    <div class="ai-engine-card">
                                        <div class="engine-header">
                                            <div class="engine-info">
                                                <h4>Claude 3.5</h4>
                                                <span class="status-indicator status-backup" id="claude-status">备用</span>
                                            </div>
                                            <label class="switch">
                                                <input type="checkbox" id="claude-enabled">
                                                <span class="slider"></span>
                                            </label>
                                        </div>
                                        <div class="engine-config">
                                            <div class="form-group">
                                                <label class="form-label">API Key</label>
                                                <input type="password" class="form-input" id="claude-api-key" placeholder="sk-ant-...">
                                            </div>
                                            <div class="form-group">
                                                <label class="form-label">模型</label>
                                                <select class="form-input" id="claude-model">
                                                    <option value="claude-3-5-sonnet-20241022" selected>Claude 3.5 Sonnet</option>
                                                    <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                                                </select>
                                            </div>
                                            <div class="form-group">
                                                <label class="form-label">Base URL</label>
                                                <input type="url" class="form-input" id="claude-base-url" value="https://api.anthropic.com">
                                            </div>
                                        </div>
                                        <div class="engine-stats">
                                            <div class="stat-item">
                                                <span class="stat-label">今日调用</span>
                                                <span class="stat-value" id="claude-today">0</span>
                                            </div>
                                            <div class="stat-item">
                                                <span class="stat-label">月度调用</span>
                                                <span class="stat-value" id="claude-month">0</span>
                                            </div>
                                            <div class="stat-item">
                                                <span class="stat-label">账户余额</span>
                                                <span class="stat-value" id="claude-balance">--</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 引擎策略配置 -->
                            <div class="form-section">
                                <h3>引擎策略</h3>
                                <div class="strategy-grid">
                                    <div class="form-group">
                                        <label class="form-label">主引擎</label>
                                        <select class="form-input" id="primary-engine">
                                            <option value="openai" selected>OpenAI GPT-4</option>
                                            <option value="deepseek">Deepseek Chat</option>
                                            <option value="claude">Claude 3.5</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">备用引擎</label>
                                        <select class="form-input" id="backup-engine">
                                            <option value="deepseek" selected>Deepseek Chat</option>
                                            <option value="openai">OpenAI GPT-4</option>
                                            <option value="claude">Claude 3.5</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">超时时间(秒)</label>
                                        <input type="number" class="form-input" id="ai-timeout" value="60" min="10" max="300">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">重试次数</label>
                                        <input type="number" class="form-input" id="ai-retry" value="3" min="1" max="5">
                                    </div>
                                </div>
                            </div>

                            <!-- Prompt模板管理 -->
                            <div class="form-section">
                                <h3>Prompt模板管理</h3>
                                <div class="prompt-templates">
                                    <div class="template-selector">
                                        <label class="form-label">选择模板类型</label>
                                        <select class="form-input" id="template-type">
                                            <option value="lawyer_letter">律师函</option>
                                            <option value="debt_collection">债务催收函</option>
                                            <option value="contract_review">合同审查</option>
                                            <option value="legal_consultation">法律咨询</option>
                                            <option value="legal_document">通用法律文书</option>
                                        </select>
                                    </div>
                                    <div class="template-editor">
                                        <label class="form-label">Prompt模板内容</label>
                                        <textarea class="form-input prompt-textarea" id="prompt-content" rows="12" placeholder="请输入Prompt模板内容...">你是一位专业的律师，请根据以下信息生成一份正式的律师函：
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
6. 法律后果警告</textarea>
                                    </div>
                                    <div class="template-variables">
                                        <label class="form-label">可用变量</label>
                                        <div class="variables-list">
                                            <span class="variable-tag">{case_type}</span>
                                            <span class="variable-tag">{client_name}</span>
                                            <span class="variable-tag">{target_name}</span>
                                            <span class="variable-tag">{amount}</span>
                                            <span class="variable-tag">{description}</span>
                                            <span class="variable-tag">{legal_basis}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="form-actions">
                                <button class="btn btn-primary" id="save-ai">保存设置</button>
                                <button class="btn btn-secondary" id="test-ai">测试连接</button>
                                <button class="btn btn-secondary" id="reset-ai">重置</button>
                            </div>
                        </div>
                    </div>

                    <!-- 邮件配置 -->
                    <div class="settings-panel" id="email-panel">
                        <div class="panel-header">
                            <h2>邮件配置</h2>
                            <p>配置SMTP邮件服务</p>
                        </div>
                        <div class="settings-form">
                            <div class="form-section">
                                <h3>SMTP设置</h3>
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">SMTP服务器</label>
                                        <input type="text" class="form-input" id="smtp-host" placeholder="smtp.exmail.qq.com">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">端口</label>
                                        <input type="number" class="form-input" id="smtp-port" value="465">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">用户名</label>
                                        <input type="text" class="form-input" id="smtp-user" placeholder="noreply@lawsker.com">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">密码</label>
                                        <input type="password" class="form-input" id="smtp-password" placeholder="邮箱密码或授权码">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">发件人邮箱</label>
                                        <input type="email" class="form-input" id="from-email" placeholder="noreply@lawsker.com">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">发件人名称</label>
                                        <input type="text" class="form-input" id="from-name" placeholder="律刻法律服务平台">
                                    </div>
                                </div>
                            </div>
                            <div class="form-section">
                                <div class="checkbox-group">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="smtp-secure" checked>
                                        <span>启用SSL/TLS加密</span>
                                    </label>
                                </div>
                            </div>
                            <div class="form-actions">
                                <button class="btn btn-primary" id="save-email">保存设置</button>
                                <button class="btn btn-secondary" id="test-email">测试连接</button>
                                <button class="btn btn-secondary" id="reset-email">重置</button>
                            </div>
                        </div>
                    </div>

                    <!-- 安全设置 -->
                    <div class="settings-panel" id="security-panel">
                        <div class="panel-header">
                            <h2>安全设置</h2>
                            <p>配置系统安全策略</p>
                        </div>
                        <div class="settings-form">
                            <div class="form-section">
                                <h3>密码策略</h3>
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">最小密码长度</label>
                                        <input type="number" class="form-input" id="password-min-length" value="8" min="6" max="32">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">最大登录尝试次数</label>
                                        <input type="number" class="form-input" id="max-login-attempts" value="5" min="3" max="10">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">锁定时长(分钟)</label>
                                        <input type="number" class="form-input" id="lockout-duration" value="5" min="1" max="60">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">会话超时(小时)</label>
                                        <input type="number" class="form-input" id="session-max-age" value="2" min="1" max="24">
                                    </div>
                                </div>
                            </div>
                            <div class="form-section">
                                <h3>密码要求</h3>
                                <div class="checkbox-list">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="require-uppercase" checked>
                                        <span>要求包含大写字母</span>
                                    </label>
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="require-numbers" checked>
                                        <span>要求包含数字</span>
                                    </label>
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="require-symbols">
                                        <span>要求包含特殊字符</span>
                                    </label>
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="enable-two-factor">
                                        <span>启用双因素认证</span>
                                    </label>
                                </div>
                            </div>
                            <div class="form-actions">
                                <button class="btn btn-primary" id="save-security">保存设置</button>
                                <button class="btn btn-secondary" id="reset-security">重置</button>
                            </div>
                        </div>
                    </div>
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
            }

            .settings-navigation {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 8px;
                margin-bottom: 32px;
                display: flex;
                gap: 4px;
                overflow-x: auto;
            }

            .settings-nav-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 20px;
                border-radius: var(--radius-md);
                cursor: pointer;
                transition: all var(--transition-fast);
                color: var(--text-secondary);
                white-space: nowrap;
                font-size: 14px;
                font-weight: 500;
                min-width: 140px;
                justify-content: center;
            }

            .settings-nav-item:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .settings-nav-item.active {
                background: var(--primary);
                color: white;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            }

            .settings-nav-item svg {
                flex-shrink: 0;
                width: 16px;
                height: 16px;
            }

            .settings-content {
                position: relative;
            }

            .settings-panel {
                display: none;
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 32px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }

            .settings-panel.active {
                display: block;
                animation: fadeIn 0.3s ease-in-out;
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

            @keyframes fadeIn {
                from { 
                    opacity: 0; 
                    transform: translateY(10px); 
                }
                to { 
                    opacity: 1; 
                    transform: translateY(0); 
                }
            }

            .checkbox-group {
                margin-bottom: 16px;
            }

            .checkbox-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .checkbox-list .checkbox-label {
                margin-bottom: 0;
            }

            /* AI配置样式 */
            .ai-engines-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 24px;
                margin-bottom: 32px;
            }

            .ai-engine-card {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 20px;
                transition: all var(--transition-fast);
            }

            .ai-engine-card:hover {
                border-color: var(--border-accent);
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }

            .engine-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
                padding-bottom: 16px;
                border-bottom: 1px solid var(--border-secondary);
            }

            .engine-info h4 {
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 4px 0;
            }

            .status-indicator {
                padding: 2px 8px;
                border-radius: var(--radius-sm);
                font-size: 12px;
                font-weight: 500;
            }

            .status-active {
                background: rgba(16, 185, 129, 0.1);
                color: var(--success);
            }

            .status-backup {
                background: rgba(251, 191, 36, 0.1);
                color: var(--warning);
            }

            .status-inactive {
                background: rgba(156, 163, 175, 0.1);
                color: var(--text-muted);
            }

            .engine-config {
                margin-bottom: 16px;
            }

            .engine-config .form-group {
                margin-bottom: 12px;
            }

            .engine-stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                padding-top: 16px;
                border-top: 1px solid var(--border-secondary);
            }

            .stat-item {
                text-align: center;
            }

            .stat-label {
                display: block;
                color: var(--text-secondary);
                font-size: 12px;
                margin-bottom: 4px;
            }

            .stat-value {
                display: block;
                color: var(--text-primary);
                font-size: 14px;
                font-weight: 600;
            }

            .strategy-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }

            .prompt-templates {
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            .template-selector {
                max-width: 300px;
            }

            .template-editor {
                flex: 1;
            }

            .prompt-textarea {
                min-height: 200px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 13px;
                line-height: 1.4;
                resize: vertical;
            }

            .template-variables {
                margin-top: 12px;
            }

            .variables-list {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 8px;
            }

            .variable-tag {
                background: rgba(16, 185, 129, 0.1);
                color: var(--success);
                font-size: 12px;
                padding: 4px 8px;
                border-radius: var(--radius-sm);
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .variable-tag:hover {
                background: rgba(16, 185, 129, 0.2);
                transform: scale(1.05);
            }

            @media (max-width: 768px) {
                .settings-navigation {
                    flex-wrap: wrap;
                    justify-content: center;
                }

                .settings-nav-item {
                    min-width: 120px;
                    flex-direction: column;
                    gap: 4px;
                    padding: 8px 12px;
                }

                .settings-nav-item span {
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
        document.querySelectorAll('.settings-nav-item').forEach(item => {
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

        document.getElementById('save-email')?.addEventListener('click', () => {
            this.saveEmailSettings();
        });

        document.getElementById('save-security')?.addEventListener('click', () => {
            this.saveSecuritySettings();
        });

        document.getElementById('save-ai')?.addEventListener('click', () => {
            this.saveAISettings();
        });

        // 重置按钮
        document.getElementById('reset-general')?.addEventListener('click', () => {
            this.resetSettings('general');
        });

        document.getElementById('reset-business')?.addEventListener('click', () => {
            this.resetSettings('business');
        });

        document.getElementById('reset-email')?.addEventListener('click', () => {
            this.resetSettings('email');
        });

        document.getElementById('reset-security')?.addEventListener('click', () => {
            this.resetSettings('security');
        });

        document.getElementById('reset-ai')?.addEventListener('click', () => {
            this.resetSettings('ai');
        });

        // 测试连接按钮
        document.getElementById('test-payment')?.addEventListener('click', () => {
            this.testPaymentConnection();
        });

        document.getElementById('test-email')?.addEventListener('click', () => {
            this.testEmailConnection();
        });

        document.getElementById('test-ai')?.addEventListener('click', () => {
            this.testAIConnection();
        });

        // Prompt模板切换
        document.getElementById('template-type')?.addEventListener('change', (e) => {
            this.loadPromptTemplate(e.target.value);
        });

        // 监听表单变化以标记未保存状态
        this.bindFormChangeEvents();
    }

    async loadData() {
        try {
            this.showLoading();
            this.settings = await this.settingsAPI.loadSettings();
            this.populateFormFields();
            this.hideLoading();
        } catch (error) {
            console.error('加载设置失败:', error);
            this.showError('加载设置失败，请刷新页面重试');
        }
    }

    showLoading() {
        this.isLoading = true;
        const panels = document.querySelectorAll('.settings-panel');
        panels.forEach(panel => {
            panel.style.opacity = '0.6';
            panel.style.pointerEvents = 'none';
        });
    }

    hideLoading() {
        this.isLoading = false;
        const panels = document.querySelectorAll('.settings-panel');
        panels.forEach(panel => {
            panel.style.opacity = '1';
            panel.style.pointerEvents = 'auto';
        });
    }

    populateFormFields() {
        // 填充基础设置表单
        if (this.settings.general) {
            const general = this.settings.general;
            const fields = {
                'site-name': general.siteName,
                'site-description': general.siteDescription,
                'contact-email': general.contactEmail,
                'contact-phone': general.contactPhone,
                'page-size': general.pageSize,
                'session-timeout': general.sessionTimeout,
                'timezone': general.timezone,
                'language': general.language
            };

            Object.entries(fields).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element && value !== undefined) {
                    element.value = value;
                }
            });
        }

        // 填充业务设置表单
        if (this.settings.business) {
            this.populateBusinessFields();
        }

        // 填充支付设置表单
        if (this.settings.payment) {
            this.populatePaymentFields();
        }

        // 填充邮件设置表单
        if (this.settings.email) {
            this.populateEmailFields();
        }

        // 填充安全设置表单
        if (this.settings.security) {
            this.populateSecurityFields();
        }

        // 填充AI设置表单
        if (this.settings.ai) {
            this.populateAIFields();
        }
    }

    populateBusinessFields() {
        const business = this.settings.business;
        
        // 更新业务规则复选框
        const ruleElements = document.querySelectorAll('.rule-item input[type="checkbox"]');
        ruleElements.forEach((checkbox, index) => {
            switch (index) {
                case 0:
                    checkbox.checked = business.requireRealName;
                    break;
                case 1:
                    checkbox.checked = business.requireLawyerVerification;
                    break;
                case 2:
                    checkbox.checked = business.autoAssignTasks;
                    break;
            }
        });
    }

    populatePaymentFields() {
        const payment = this.settings.payment;
        
        // 更新支付方式开关
        const paymentSwitches = document.querySelectorAll('.method-card .switch input');
        paymentSwitches.forEach((switchInput, index) => {
            switch (index) {
                case 0:
                    switchInput.checked = payment.wechatEnabled;
                    break;
                case 1:
                    switchInput.checked = payment.alipayEnabled;
                    break;
            }
        });
    }

    switchPanel(tab) {
        this.currentTab = tab;

        // 更新导航状态
        document.querySelectorAll('.settings-nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.tab === tab);
        });

        // 更新面板显示
        document.querySelectorAll('.settings-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `${tab}-panel`);
        });
    }

    async saveGeneralSettings() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
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

            const result = await this.settingsAPI.saveSettings('general', formData);
            
            if (result.success) {
                this.settings.general = { ...this.settings.general, ...formData };
                this.hasUnsavedChanges = false;
                this.showNotification(
                    result.fromLocal ? '基础设置已保存到本地' : '基础设置保存成功', 
                    'success'
                );
            } else {
                this.showNotification(result.error || '保存失败', 'error');
            }
        } catch (error) {
            console.error('保存基础设置失败:', error);
            this.showNotification('保存失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async saveBusinessSettings() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            // 收集业务配置数据
            const ruleElements = document.querySelectorAll('.rule-item input[type="checkbox"]');
            const businessData = {
                consultingFeeRate: parseFloat(document.querySelector('.pricing-item input[step="0.01"]')?.value) || 20,
                documentFee: parseFloat(document.querySelector('.pricing-item input[step="1"]')?.value) || 100,
                minimumFee: parseFloat(document.querySelectorAll('.pricing-item input[step="1"]')[1]?.value) || 50,
                requireRealName: ruleElements[0]?.checked || false,
                requireLawyerVerification: ruleElements[1]?.checked || false,
                autoAssignTasks: ruleElements[2]?.checked || false,
                maxTasksPerLawyer: 10,
                taskTimeoutHours: 72
            };

            const result = await this.settingsAPI.saveSettings('business', businessData);
            
            if (result.success) {
                this.settings.business = { ...this.settings.business, ...businessData };
                this.hasUnsavedChanges = false;
                this.showNotification(
                    result.fromLocal ? '业务设置已保存到本地' : '业务设置保存成功', 
                    'success'
                );
            } else {
                this.showNotification(result.error || '保存失败', 'error');
            }
        } catch (error) {
            console.error('保存业务设置失败:', error);
            this.showNotification('保存失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async savePaymentSettings() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            // 收集支付配置数据
            const paymentSwitches = document.querySelectorAll('.method-card .switch input');
            const paymentInputs = document.querySelectorAll('.method-config .form-input');
            
            const paymentData = {
                wechatEnabled: paymentSwitches[0]?.checked || false,
                alipayEnabled: paymentSwitches[1]?.checked || false,
                wechatMerchantId: paymentInputs[0]?.value || '',
                wechatApiKey: paymentInputs[1]?.value || '',
                alipayAppId: paymentInputs[2]?.value || '',
                alipayPrivateKey: paymentInputs[3]?.value || '',
                paymentTimeout: 30
            };

            const result = await this.settingsAPI.saveSettings('payment', paymentData);
            
            if (result.success) {
                this.settings.payment = { ...this.settings.payment, ...paymentData };
                this.hasUnsavedChanges = false;
                this.showNotification(
                    result.fromLocal ? '支付设置已保存到本地' : '支付设置保存成功', 
                    'success'
                );
            } else {
                this.showNotification(result.error || '保存失败', 'error');
            }
        } catch (error) {
            console.error('保存支付设置失败:', error);
            this.showNotification('保存失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async testPaymentConnection() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const paymentSwitches = document.querySelectorAll('.method-card .switch input');
            const paymentInputs = document.querySelectorAll('.method-config .form-input');
            
            const paymentData = {
                wechatEnabled: paymentSwitches[0]?.checked || false,
                alipayEnabled: paymentSwitches[1]?.checked || false,
                wechatMerchantId: paymentInputs[0]?.value || '',
                wechatApiKey: paymentInputs[1]?.value || '',
                alipayAppId: paymentInputs[2]?.value || '',
                alipayPrivateKey: paymentInputs[3]?.value || ''
            };

            const result = await this.settingsAPI.testPaymentConfig(paymentData);
            
            if (result.success) {
                this.showNotification('支付服务连接测试成功', 'success');
            } else {
                this.showNotification(result.error || '支付服务连接测试失败', 'error');
            }
        } catch (error) {
            console.error('测试支付连接失败:', error);
            this.showNotification('测试失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async resetSettings(category) {
        if (this.isLoading) return;

        const categoryNames = {
            general: '基础设置',
            business: '业务设置',
            payment: '支付设置',
            email: '邮件设置',
            security: '安全设置',
            ai: 'AI配置'
        };

        if (!confirm(`确定要重置${categoryNames[category] || category}为默认值吗？此操作不可撤销。`)) {
            return;
        }

        try {
            this.showLoading();
            
            const result = await this.settingsAPI.resetSettings(category);
            
            if (result.success) {
                await this.loadData(); // 重新加载数据
                this.showNotification(`${categoryNames[category]}已重置为默认值`, 'success');
            } else {
                this.showNotification(result.error || '重置失败', 'error');
            }
        } catch (error) {
            console.error('重置设置失败:', error);
            this.showNotification('重置失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    bindFormChangeEvents() {
        const formInputs = document.querySelectorAll('.settings-form input, .settings-form select, .settings-form textarea');
        formInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.hasUnsavedChanges = true;
            });
        });
    }

    showNotification(message, type) {
        if (this.eventBus) {
            this.eventBus.emit('notification', { message, type });
        }
    }

    populateAIFields() {
        const ai = this.settings.ai;
        
        // 填充AI引擎配置
        Object.entries(ai.engines).forEach(([engine, config]) => {
            const enabledElement = document.getElementById(`${engine}-enabled`);
            const apiKeyElement = document.getElementById(`${engine}-api-key`);
            const modelElement = document.getElementById(`${engine}-model`);
            const baseUrlElement = document.getElementById(`${engine}-base-url`);
            const statusElement = document.getElementById(`${engine}-status`);

            if (enabledElement) enabledElement.checked = config.enabled;
            if (apiKeyElement) apiKeyElement.value = config.apiKey;
            if (modelElement) modelElement.value = config.model;
            if (baseUrlElement) baseUrlElement.value = config.baseUrl;
            if (statusElement) {
                statusElement.textContent = config.status === 'active' ? '运行中' : 
                                          config.status === 'backup' ? '备用' : '停用';
                statusElement.className = `status-indicator status-${config.status}`;
            }
        });

        // 填充引擎策略
        const primaryEngine = document.getElementById('primary-engine');
        const backupEngine = document.getElementById('backup-engine');
        const aiTimeout = document.getElementById('ai-timeout');
        const aiRetry = document.getElementById('ai-retry');

        if (primaryEngine) primaryEngine.value = ai.strategy.primaryEngine;
        if (backupEngine) backupEngine.value = ai.strategy.backupEngine;
        if (aiTimeout) aiTimeout.value = ai.strategy.timeout;
        if (aiRetry) aiRetry.value = ai.strategy.retryAttempts;

        // 填充统计数据
        Object.entries(ai.stats).forEach(([engine, stats]) => {
            const todayElement = document.getElementById(`${engine}-today`);
            const monthElement = document.getElementById(`${engine}-month`);
            const balanceElement = document.getElementById(`${engine}-balance`);

            if (todayElement) todayElement.textContent = stats.todayCalls.toLocaleString();
            if (monthElement) monthElement.textContent = stats.monthCalls.toLocaleString();
            if (balanceElement) balanceElement.textContent = stats.balance;
        });

        // 加载默认Prompt模板
        this.loadPromptTemplate('lawyer_letter');
    }

    loadPromptTemplate(templateType) {
        const ai = this.settings.ai;
        const promptContent = document.getElementById('prompt-content');
        const variablesList = document.querySelector('.variables-list');

        if (promptContent && ai.prompts[templateType]) {
            promptContent.value = ai.prompts[templateType];
        }

        // 更新可用变量列表
        const variableMap = {
            lawyer_letter: ['{case_type}', '{client_name}', '{target_name}', '{amount}', '{description}', '{legal_basis}'],
            debt_collection: ['{debtor_name}', '{creditor_name}', '{debt_amount}', '{overdue_days}', '{contract_number}'],
            contract_review: ['{contract_type}', '{contract_name}', '{parties}', '{contract_amount}', '{performance_deadline}', '{special_clauses}'],
            legal_consultation: ['{consultation_category}', '{problem_description}', '{background_info}', '{expected_outcome}'],
            legal_document: ['{document_type}', '{case_title}', '{basic_facts}', '{legal_basis}', '{processing_requirements}']
        };

        if (variablesList && variableMap[templateType]) {
            variablesList.innerHTML = variableMap[templateType]
                .map(variable => `<span class="variable-tag">${variable}</span>`)
                .join('');
        }
    }

    async saveAISettings() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            // 收集AI引擎配置
            const engines = {};
            ['openai', 'deepseek', 'claude'].forEach(engine => {
                engines[engine] = {
                    enabled: document.getElementById(`${engine}-enabled`)?.checked || false,
                    apiKey: document.getElementById(`${engine}-api-key`)?.value || '',
                    model: document.getElementById(`${engine}-model`)?.value || '',
                    baseUrl: document.getElementById(`${engine}-base-url`)?.value || '',
                    status: document.getElementById(`${engine}-enabled`)?.checked ? 'active' : 'inactive'
                };
            });

            // 收集引擎策略
            const strategy = {
                primaryEngine: document.getElementById('primary-engine')?.value || 'openai',
                backupEngine: document.getElementById('backup-engine')?.value || 'deepseek',
                timeout: parseInt(document.getElementById('ai-timeout')?.value) || 60,
                retryAttempts: parseInt(document.getElementById('ai-retry')?.value) || 3
            };

            // 收集Prompt模板
            const templateType = document.getElementById('template-type')?.value || 'lawyer_letter';
            const promptContent = document.getElementById('prompt-content')?.value || '';
            const prompts = { ...this.settings.ai.prompts };
            prompts[templateType] = promptContent;

            const aiData = {
                engines,
                strategy,
                prompts,
                stats: this.settings.ai.stats // 保持统计数据
            };

            const result = await this.settingsAPI.saveSettings('ai', aiData);
            
            if (result.success) {
                this.settings.ai = { ...this.settings.ai, ...aiData };
                this.hasUnsavedChanges = false;
                this.showNotification(
                    result.fromLocal ? 'AI配置已保存到本地' : 'AI配置保存成功', 
                    'success'
                );
            } else {
                this.showNotification(result.error || '保存失败', 'error');
            }
        } catch (error) {
            console.error('保存AI设置失败:', error);
            this.showNotification('保存失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async testAIConnection() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            // 收集启用的AI引擎配置进行测试
            const enabledEngines = {};
            ['openai', 'deepseek', 'claude'].forEach(engine => {
                const enabled = document.getElementById(`${engine}-enabled`)?.checked;
                if (enabled) {
                    enabledEngines[engine] = {
                        apiKey: document.getElementById(`${engine}-api-key`)?.value || '',
                        model: document.getElementById(`${engine}-model`)?.value || '',
                        baseUrl: document.getElementById(`${engine}-base-url`)?.value || ''
                    };
                }
            });

            if (Object.keys(enabledEngines).length === 0) {
                this.showNotification('请至少启用一个AI引擎进行测试', 'warning');
                return;
            }

            const result = await this.settingsAPI.testAIConfig(enabledEngines);
            
            if (result.success) {
                this.showNotification('AI服务连接测试成功', 'success');
            } else {
                this.showNotification(result.error || 'AI服务连接测试失败', 'error');
            }
        } catch (error) {
            console.error('测试AI连接失败:', error);
            this.showNotification('测试失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }
}