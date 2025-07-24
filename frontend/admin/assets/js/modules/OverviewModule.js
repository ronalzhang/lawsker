/**
 * 系统概览模块
 * 显示系统状态、统计数据和快速操作
 */

export class OverviewModule extends BaseModule {
    constructor(eventBus) {
        super(eventBus);
        this.refreshInterval = null;
        this.charts = new Map();
    }

    async render() {
        this.container.innerHTML = `
            <div class="overview-container">
                <!-- 页面标题 -->
                <div class="page-header">
                    <h1 class="page-title">系统概览</h1>
                    <p class="page-description">查看系统运行状态、数据统计和快速操作</p>
                </div>

                <!-- 统计卡片 -->
                <div class="stats-grid">
                    <div class="stat-card" data-stat="users">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                <circle cx="9" cy="7" r="4"></circle>
                                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="users-count">--</div>
                            <div class="stat-label">注册用户</div>
                            <div class="stat-change positive" id="users-change">+12.5%</div>
                        </div>
                    </div>

                    <div class="stat-card" data-stat="lawyers">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="lawyers-count">--</div>
                            <div class="stat-label">认证律师</div>
                            <div class="stat-change positive" id="lawyers-change">+8.3%</div>
                        </div>
                    </div>

                    <div class="stat-card" data-stat="tasks">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14,2 14,8 20,8"></polyline>
                                <line x1="16" y1="13" x2="8" y2="13"></line>
                                <line x1="16" y1="17" x2="8" y2="17"></line>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="tasks-count">--</div>
                            <div class="stat-label">活跃任务</div>
                            <div class="stat-change negative" id="tasks-change">-2.1%</div>
                        </div>
                    </div>

                    <div class="stat-card" data-stat="revenue">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="1" x2="12" y2="23"></line>
                                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="revenue-count">--</div>
                            <div class="stat-label">本月收入</div>
                            <div class="stat-change positive" id="revenue-change">+15.7%</div>
                        </div>
                    </div>
                </div>

                <!-- 图表区域 -->
                <div class="charts-section">
                    <div class="chart-container">
                        <div class="chart-header">
                            <h3>访问趋势</h3>
                            <div class="chart-controls">
                                <select id="chart-period">
                                    <option value="7days">近7天</option>
                                    <option value="30days" selected>近30天</option>
                                    <option value="90days">近90天</option>
                                </select>
                            </div>
                        </div>
                        <div class="chart-body">
                            <canvas id="visits-chart" width="400" height="200"></canvas>
                        </div>
                    </div>

                    <div class="chart-container">
                        <div class="chart-header">
                            <h3>收入分析</h3>
                            <div class="chart-controls">
                                <button class="chart-btn active" data-type="revenue">收入</button>
                                <button class="chart-btn" data-type="profit">利润</button>
                            </div>
                        </div>
                        <div class="chart-body">
                            <canvas id="revenue-chart" width="400" height="200"></canvas>
                        </div>
                    </div>
                </div>

                <!-- 快速操作 -->
                <div class="quick-actions-section">
                    <h3>快速操作</h3>
                    <div class="quick-actions-grid">
                        <button class="quick-action-card" data-action="add-user">
                            <div class="action-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="9" cy="7" r="4"></circle>
                                    <line x1="19" y1="8" x2="19" y2="14"></line>
                                    <line x1="22" y1="11" x2="16" y2="11"></line>
                                </svg>
                            </div>
                            <div class="action-content">
                                <div class="action-title">添加用户</div>
                                <div class="action-desc">创建新的用户账户</div>
                            </div>
                        </button>

                        <button class="quick-action-card" data-action="verify-lawyer">
                            <div class="action-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 12l2 2 4-4"></path>
                                    <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"></path>
                                    <path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3"></path>
                                    <path d="M12 3c0 1-1 3-3 3s-3-2-3-3 1-3 3-3 3 2 3 3"></path>
                                    <path d="M12 21c0-1 1-3 3-3s3 2 3 3-1 3-3 3-3-2-3-3"></path>
                                </svg>
                            </div>
                            <div class="action-content">
                                <div class="action-title">审核律师</div>
                                <div class="action-desc">审核律师认证申请</div>
                            </div>
                        </button>

                        <button class="quick-action-card" data-action="system-backup">
                            <div class="action-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="7,10 12,15 17,10"></polyline>
                                    <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                            </div>
                            <div class="action-content">
                                <div class="action-title">系统备份</div>
                                <div class="action-desc">创建系统数据备份</div>
                            </div>
                        </button>

                        <button class="quick-action-card" data-action="view-logs">
                            <div class="action-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <polyline points="14,2 14,8 20,8"></polyline>
                                    <line x1="16" y1="13" x2="8" y2="13"></line>
                                    <line x1="16" y1="17" x2="8" y2="17"></line>
                                </svg>
                            </div>
                            <div class="action-content">
                                <div class="action-title">查看日志</div>
                                <div class="action-desc">检查系统运行日志</div>
                            </div>
                        </button>
                    </div>
                </div>

                <!-- 系统状态 -->
                <div class="system-status-section">
                    <h3>系统状态</h3>
                    <div class="status-grid">
                        <div class="status-item">
                            <div class="status-indicator">
                                <div class="status-dot status-healthy"></div>
                                <span>数据库</span>
                            </div>
                            <div class="status-value">正常</div>
                        </div>

                        <div class="status-item">
                            <div class="status-indicator">
                                <div class="status-dot status-healthy"></div>
                                <span>API服务</span>
                            </div>
                            <div class="status-value">正常</div>
                        </div>

                        <div class="status-item">
                            <div class="status-indicator">
                                <div class="status-dot status-warning"></div>
                                <span>存储空间</span>
                            </div>
                            <div class="status-value">75%</div>
                        </div>

                        <div class="status-item">
                            <div class="status-indicator">
                                <div class="status-dot status-healthy"></div>
                                <span>网络</span>
                            </div>
                            <div class="status-value">良好</div>
                        </div>
                    </div>
                </div>

                <!-- 最近活动 -->
                <div class="recent-activities-section">
                    <h3>最近活动</h3>
                    <div class="activities-list" id="activities-list">
                        <!-- 活动项将通过JavaScript动态加载 -->
                    </div>
                </div>
            </div>
        `;

        // 加载样式
        await this.loadStyles();
        
        // 加载数据
        await this.loadData();
        
        // 初始化图表
        this.initCharts();
    }

    async loadStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .overview-container {
                max-width: 1200px;
                margin: 0 auto;
            }

            .page-header {
                margin-bottom: 32px;
            }

            .page-title {
                font-size: 28px;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 8px;
            }

            .page-description {
                color: var(--text-secondary);
                font-size: 16px;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 24px;
                margin-bottom: 40px;
            }

            .stat-card {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 24px;
                display: flex;
                align-items: center;
                gap: 16px;
                transition: all var(--transition-fast);
                cursor: pointer;
            }

            .stat-card:hover {
                border-color: var(--border-accent);
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }

            .stat-icon {
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                border-radius: var(--radius-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            }

            .stat-content {
                flex: 1;
            }

            .stat-value {
                font-size: 24px;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 4px;
            }

            .stat-label {
                color: var(--text-secondary);
                font-size: 14px;
                margin-bottom: 8px;
            }

            .stat-change {
                font-size: 12px;
                font-weight: 600;
                padding: 2px 6px;
                border-radius: var(--radius-sm);
            }

            .stat-change.positive {
                background: rgba(16, 185, 129, 0.1);
                color: var(--success);
            }

            .stat-change.negative {
                background: rgba(239, 68, 68, 0.1);
                color: var(--danger);
            }

            .charts-section {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 24px;
                margin-bottom: 40px;
            }

            .chart-container {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 24px;
            }

            .chart-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }

            .chart-header h3 {
                color: var(--text-primary);
                font-size: 18px;
                font-weight: 600;
            }

            .chart-controls select {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                padding: 6px 12px;
                font-size: 14px;
            }

            .chart-btn {
                background: transparent;
                border: 1px solid var(--border-primary);
                color: var(--text-secondary);
                padding: 6px 12px;
                border-radius: var(--radius-md);
                font-size: 14px;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .chart-btn.active {
                background: var(--primary);
                color: white;
                border-color: var(--primary);
            }

            .chart-body {
                position: relative;
                height: 200px;
            }

            .quick-actions-section h3,
            .system-status-section h3,
            .recent-activities-section h3 {
                color: var(--text-primary);
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
            }

            .quick-actions-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 40px;
            }

            .quick-action-card {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .quick-action-card:hover {
                border-color: var(--border-accent);
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }

            .action-icon {
                width: 40px;
                height: 40px;
                background: rgba(59, 130, 246, 0.1);
                border-radius: var(--radius-md);
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--primary);
            }

            .action-title {
                color: var(--text-primary);
                font-weight: 500;
                margin-bottom: 2px;
            }

            .action-desc {
                color: var(--text-secondary);
                font-size: 12px;
            }

            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 40px;
            }

            .status-item {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--text-secondary);
                font-size: 14px;
            }

            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
            }

            .status-healthy {
                background: var(--success);
            }

            .status-warning {
                background: var(--warning);
            }

            .status-error {
                background: var(--danger);
            }

            .status-value {
                color: var(--text-primary);
                font-weight: 500;
            }

            .activities-list {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                max-height: 300px;
                overflow-y: auto;
            }

            .activity-item {
                padding: 16px;
                border-bottom: 1px solid var(--border-secondary);
                display: flex;
                gap: 12px;
            }

            .activity-item:last-child {
                border-bottom: none;
            }

            .activity-avatar {
                width: 32px;
                height: 32px;
                background: var(--primary);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 600;
            }

            .activity-content {
                flex: 1;
            }

            .activity-text {
                color: var(--text-primary);
                font-size: 14px;
                margin-bottom: 4px;
            }

            .activity-time {
                color: var(--text-muted);
                font-size: 12px;
            }

            @media (max-width: 768px) {
                .stats-grid {
                    grid-template-columns: 1fr;
                }

                .charts-section {
                    grid-template-columns: 1fr;
                }

                .quick-actions-grid {
                    grid-template-columns: 1fr;
                }

                .status-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        // 快速操作点击事件
        this.container.addEventListener('click', (e) => {
            const actionCard = e.target.closest('.quick-action-card');
            if (actionCard) {
                const action = actionCard.dataset.action;
                this.handleQuickAction(action);
            }

            const statCard = e.target.closest('.stat-card');
            if (statCard) {
                const stat = statCard.dataset.stat;
                this.handleStatClick(stat);
            }
        });

        // 图表控制事件
        const chartPeriod = document.getElementById('chart-period');
        if (chartPeriod) {
            chartPeriod.addEventListener('change', (e) => {
                this.updateChart('visits', e.target.value);
            });
        }

        // 启动数据刷新
        this.startDataRefresh();
    }

    async loadData() {
        try {
            // 模拟API调用
            const data = await this.fetchOverviewData();
            this.updateStats(data.stats);
            this.updateActivities(data.activities);
        } catch (error) {
            console.error('加载概览数据失败:', error);
        }
    }

    async fetchOverviewData() {
        // 模拟数据
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    stats: {
                        users: { count: 2847, change: 12.5 },
                        lawyers: { count: 156, change: 8.3 },
                        tasks: { count: 89, change: -2.1 },
                        revenue: { count: '¥52,340', change: 15.7 }
                    },
                    activities: [
                        { user: '张律师', action: '完成了用户咨询任务', time: '2分钟前' },
                        { user: '李用户', action: '提交了新的法律咨询', time: '5分钟前' },
                        { user: '王律师', action: '更新了个人资料', time: '10分钟前' },
                        { user: '管理员', action: '执行了系统备份', time: '1小时前' },
                        { user: '赵用户', action: '完成了实名认证', time: '2小时前' }
                    ]
                });
            }, 300);
        });
    }

    updateStats(stats) {
        Object.entries(stats).forEach(([key, data]) => {
            const countEl = document.getElementById(`${key}-count`);
            const changeEl = document.getElementById(`${key}-change`);
            
            if (countEl) {
                countEl.textContent = data.count;
            }
            
            if (changeEl) {
                const isPositive = data.change > 0;
                changeEl.textContent = `${isPositive ? '+' : ''}${data.change}%`;
                changeEl.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
            }
        });
    }

    updateActivities(activities) {
        const activitiesList = document.getElementById('activities-list');
        if (!activitiesList) return;

        activitiesList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-avatar">
                    ${activity.user.charAt(0)}
                </div>
                <div class="activity-content">
                    <div class="activity-text">
                        <strong>${activity.user}</strong> ${activity.action}
                    </div>
                    <div class="activity-time">${activity.time}</div>
                </div>
            </div>
        `).join('');
    }

    initCharts() {
        this.initVisitsChart();
        this.initRevenueChart();
    }

    initVisitsChart() {
        const canvas = document.getElementById('visits-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = [120, 150, 180, 200, 170, 190, 220, 180, 160, 210, 240, 190, 170, 200, 230, 250, 220, 180, 190, 210, 240, 220, 200, 180, 160, 190, 220, 250, 230, 210];
        
        this.drawLineChart(ctx, data, '#3b82f6');
    }

    initRevenueChart() {
        const canvas = document.getElementById('revenue-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = [3200, 3800, 4200, 3900, 4500, 4800, 5200, 4900, 4600, 5100, 5400, 5000, 4700, 5200, 5600, 5900, 5500, 5200, 5400, 5700, 6000, 5800, 5500, 5200, 4900, 5300, 5700, 6100, 5900, 5600];
        
        this.drawLineChart(ctx, data, '#10b981');
    }

    drawLineChart(ctx, data, color) {
        const canvas = ctx.canvas;
        const width = canvas.width;
        const height = canvas.height;
        const padding = 40;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        
        const maxVal = Math.max(...data);
        const minVal = Math.min(...data);
        const range = maxVal - minVal || 1;
        
        // 清空画布
        ctx.clearRect(0, 0, width, height);
        
        // 绘制背景网格
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.1)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 5; i++) {
            const y = padding + (i / 5) * chartHeight;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(padding + chartWidth, y);
            ctx.stroke();
        }
        
        // 绘制数据线
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        data.forEach((val, i) => {
            const x = padding + (i / (data.length - 1)) * chartWidth;
            const y = padding + (1 - (val - minVal) / range) * chartHeight;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // 绘制数据点
        ctx.fillStyle = color;
        data.forEach((val, i) => {
            const x = padding + (i / (data.length - 1)) * chartWidth;
            const y = padding + (1 - (val - minVal) / range) * chartHeight;
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    handleQuickAction(action) {
        console.log(`执行快速操作: ${action}`);
        
        const actions = {
            'add-user': '添加用户',
            'verify-lawyer': '审核律师',
            'system-backup': '系统备份',
            'view-logs': '查看日志'
        };
        
        const actionName = actions[action] || action;
        
        // 显示通知
        if (this.eventBus) {
            this.eventBus.emit('notification', {
                message: `正在执行: ${actionName}`,
                type: 'info'
            });
        }
        
        // 这里可以添加具体的操作逻辑
        switch (action) {
            case 'add-user':
                // 跳转到用户管理页面
                this.eventBus.emit('navigate', { module: 'users', action: 'add' });
                break;
            case 'verify-lawyer':
                // 跳转到律师审核页面
                this.eventBus.emit('navigate', { module: 'users', action: 'verify-lawyers' });
                break;
            case 'system-backup':
                // 跳转到运维页面
                this.eventBus.emit('navigate', { module: 'operations', action: 'backup' });
                break;
            case 'view-logs':
                // 跳转到日志页面
                this.eventBus.emit('navigate', { module: 'operations', action: 'logs' });
                break;
        }
    }

    handleStatClick(stat) {
        console.log(`点击统计项: ${stat}`);
        
        // 根据点击的统计项跳转到相应的详细页面
        const targetModules = {
            'users': 'users',
            'lawyers': 'users',
            'tasks': 'operations',
            'revenue': 'operations'
        };
        
        const targetModule = targetModules[stat];
        if (targetModule && this.eventBus) {
            this.eventBus.emit('navigate', { module: targetModule, filter: stat });
        }
    }

    updateChart(chartType, period) {
        console.log(`更新图表: ${chartType}, 周期: ${period}`);
        // 这里可以根据新的时间周期重新加载图表数据
    }

    startDataRefresh() {
        // 每30秒刷新一次数据
        this.refreshInterval = setInterval(() => {
            this.loadData();
        }, 30000);
    }

    async destroy() {
        // 清理定时器
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        // 清理图表
        this.charts.clear();
        
        await super.destroy();
    }
}