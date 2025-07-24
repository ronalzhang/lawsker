/**
 * 运维中心模块
 * 系统监控、日志查看、维护工具
 */

export class OperationsModule extends BaseModule {
    constructor(eventBus) {
        super(eventBus);
        this.monitoringInterval = null;
        this.logUpdateInterval = null;
    }

    async render() {
        this.container.innerHTML = `
            <div class="operations-container">
                <!-- 页面标题 -->
                <div class="page-header">
                    <h1 class="page-title">运维中心</h1>
                    <p class="page-description">系统监控、性能分析和维护工具</p>
                </div>

                <!-- 系统监控面板 -->
                <div class="monitoring-section">
                    <h2 class="section-title">系统监控</h2>
                    <div class="monitoring-grid">
                        <div class="monitor-card">
                            <div class="monitor-header">
                                <h3>服务器状态</h3>
                                <div class="status-indicator status-healthy"></div>
                            </div>
                            <div class="monitor-stats">
                                <div class="stat-item">
                                    <span class="stat-label">CPU使用率</span>
                                    <span class="stat-value" id="cpu-usage">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">内存使用率</span>
                                    <span class="stat-value" id="memory-usage">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">磁盘使用率</span>
                                    <span class="stat-value" id="disk-usage">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">网络流量</span>
                                    <span class="stat-value" id="network-traffic">--</span>
                                </div>
                            </div>
                        </div>

                        <div class="monitor-card">
                            <div class="monitor-header">
                                <h3>数据库状态</h3>
                                <div class="status-indicator status-healthy"></div>
                            </div>
                            <div class="monitor-stats">
                                <div class="stat-item">
                                    <span class="stat-label">连接数</span>
                                    <span class="stat-value" id="db-connections">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">查询耗时</span>
                                    <span class="stat-value" id="db-query-time">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">缓存命中率</span>
                                    <span class="stat-value" id="db-cache-hit">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">数据库大小</span>
                                    <span class="stat-value" id="db-size">--</span>
                                </div>
                            </div>
                        </div>

                        <div class="monitor-card">
                            <div class="monitor-header">
                                <h3>应用性能</h3>
                                <div class="status-indicator status-healthy"></div>
                            </div>
                            <div class="monitor-stats">
                                <div class="stat-item">
                                    <span class="stat-label">响应时间</span>
                                    <span class="stat-value" id="response-time">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">QPS</span>
                                    <span class="stat-value" id="qps">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">错误率</span>
                                    <span class="stat-value" id="error-rate">--</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">在线用户</span>
                                    <span class="stat-value" id="online-users">--</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 日志管理 -->
                <div class="logs-section">
                    <h2 class="section-title">系统日志</h2>
                    <div class="logs-container">
                        <div class="logs-controls">
                            <div class="controls-left">
                                <select id="log-level">
                                    <option value="all">所有级别</option>
                                    <option value="error">错误</option>
                                    <option value="warning">警告</option>
                                    <option value="info">信息</option>
                                    <option value="debug">调试</option>
                                </select>
                                <select id="log-source">
                                    <option value="all">所有来源</option>
                                    <option value="api">API服务</option>
                                    <option value="database">数据库</option>
                                    <option value="auth">认证系统</option>
                                    <option value="scheduler">定时任务</option>
                                </select>
                                <input type="text" id="log-search" placeholder="搜索日志内容...">
                            </div>
                            <div class="controls-right">
                                <button class="btn btn-secondary" id="clear-logs">清空日志</button>
                                <button class="btn btn-primary" id="export-logs">导出日志</button>
                                <button class="btn btn-primary" id="refresh-logs">刷新</button>
                            </div>
                        </div>
                        <div class="logs-content" id="logs-content">
                            <!-- 日志内容将动态加载 -->
                        </div>
                    </div>
                </div>

                <!-- 维护工具 -->
                <div class="maintenance-section">
                    <h2 class="section-title">维护工具</h2>
                    <div class="maintenance-grid">
                        <div class="maintenance-card">
                            <div class="maintenance-header">
                                <h3>数据库备份</h3>
                                <button class="btn btn-primary" id="create-backup">创建备份</button>
                            </div>
                            <div class="maintenance-content">
                                <div class="backup-list" id="backup-list">
                                    <!-- 备份列表将动态加载 -->
                                </div>
                            </div>
                        </div>

                        <div class="maintenance-card">
                            <div class="maintenance-header">
                                <h3>缓存管理</h3>
                                <button class="btn btn-warning" id="clear-cache">清空缓存</button>
                            </div>
                            <div class="maintenance-content">
                                <div class="cache-stats">
                                    <div class="cache-item">
                                        <span>应用缓存</span>
                                        <span id="app-cache-size">--</span>
                                    </div>
                                    <div class="cache-item">
                                        <span>数据库缓存</span>
                                        <span id="db-cache-size">--</span>
                                    </div>
                                    <div class="cache-item">
                                        <span>静态文件缓存</span>
                                        <span id="static-cache-size">--</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="maintenance-card">
                            <div class="maintenance-header">
                                <h3>系统清理</h3>
                                <button class="btn btn-warning" id="system-cleanup">开始清理</button>
                            </div>
                            <div class="maintenance-content">
                                <div class="cleanup-options">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="cleanup-temp" checked>
                                        <span>临时文件</span>
                                    </label>
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="cleanup-logs">
                                        <span>过期日志</span>
                                    </label>
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="cleanup-sessions">
                                        <span>过期会话</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="maintenance-card">
                            <div class="maintenance-header">
                                <h3>服务管理</h3>
                                <div class="service-status">
                                    <span class="status-dot status-healthy"></span>
                                    <span>所有服务正常</span>
                                </div>
                            </div>
                            <div class="maintenance-content">
                                <div class="service-list">
                                    <div class="service-item">
                                        <span>API服务</span>
                                        <button class="btn btn-sm" id="restart-api">重启</button>
                                    </div>
                                    <div class="service-item">
                                        <span>定时任务</span>
                                        <button class="btn btn-sm" id="restart-scheduler">重启</button>
                                    </div>
                                    <div class="service-item">
                                        <span>邮件服务</span>
                                        <button class="btn btn-sm" id="restart-mail">重启</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 性能图表 -->
                <div class="performance-section">
                    <h2 class="section-title">性能分析</h2>
                    <div class="performance-charts">
                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>系统负载</h3>
                                <select id="load-timeframe">
                                    <option value="1h">近1小时</option>
                                    <option value="6h">近6小时</option>
                                    <option value="24h" selected>近24小时</option>
                                    <option value="7d">近7天</option>
                                </select>
                            </div>
                            <div class="chart-body">
                                <canvas id="load-chart" width="400" height="200"></canvas>
                            </div>
                        </div>

                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>响应时间</h3>
                                <select id="response-timeframe">
                                    <option value="1h">近1小时</option>
                                    <option value="6h">近6小时</option>
                                    <option value="24h" selected>近24小时</option>
                                    <option value="7d">近7天</option>
                                </select>
                            </div>
                            <div class="chart-body">
                                <canvas id="response-chart" width="400" height="200"></canvas>
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
            .operations-container {
                max-width: 1200px;
                margin: 0 auto;
            }

            .section-title {
                color: var(--text-primary);
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .section-title::before {
                content: '';
                width: 4px;
                height: 20px;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                border-radius: 2px;
            }

            .monitoring-section {
                margin-bottom: 40px;
            }

            .monitoring-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 24px;
            }

            .monitor-card {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 24px;
            }

            .monitor-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }

            .monitor-header h3 {
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
                margin: 0;
            }

            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                animation: pulse 2s infinite;
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

            .monitor-stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }

            .stat-item {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .stat-label {
                color: var(--text-secondary);
                font-size: 12px;
            }

            .stat-value {
                color: var(--text-primary);
                font-size: 18px;
                font-weight: 600;
            }

            .logs-section {
                margin-bottom: 40px;
            }

            .logs-container {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                overflow: hidden;
            }

            .logs-controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 24px;
                border-bottom: 1px solid var(--border-secondary);
                gap: 16px;
            }

            .controls-left {
                display: flex;
                gap: 12px;
                flex: 1;
            }

            .controls-right {
                display: flex;
                gap: 8px;
            }

            .logs-controls select,
            .logs-controls input {
                padding: 6px 12px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                font-size: 14px;
            }

            .logs-controls input {
                min-width: 200px;
            }

            .btn {
                padding: 6px 16px;
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
                color: var(--text-secondary);
                border: 1px solid var(--border-primary);
            }

            .btn-secondary:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .btn-warning {
                background: var(--warning);
                color: white;
            }

            .btn-sm {
                padding: 4px 8px;
                font-size: 12px;
            }

            .logs-content {
                max-height: 400px;
                overflow-y: auto;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 13px;
                line-height: 1.4;
            }

            .log-entry {
                display: flex;
                padding: 8px 24px;
                border-bottom: 1px solid var(--border-secondary);
                transition: background var(--transition-fast);
            }

            .log-entry:hover {
                background: var(--bg-hover);
            }

            .log-time {
                width: 140px;
                color: var(--text-muted);
                flex-shrink: 0;
            }

            .log-level {
                width: 60px;
                font-weight: 600;
                flex-shrink: 0;
            }

            .log-level.error {
                color: var(--danger);
            }

            .log-level.warning {
                color: var(--warning);
            }

            .log-level.info {
                color: var(--info);
            }

            .log-level.debug {
                color: var(--text-muted);
            }

            .log-source {
                width: 80px;
                color: var(--text-secondary);
                flex-shrink: 0;
            }

            .log-message {
                color: var(--text-primary);
                flex: 1;
                word-break: break-word;
            }

            .maintenance-section {
                margin-bottom: 40px;
            }

            .maintenance-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 24px;
            }

            .maintenance-card {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 24px;
            }

            .maintenance-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }

            .maintenance-header h3 {
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
                margin: 0;
            }

            .backup-list,
            .cache-stats,
            .service-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .backup-item,
            .cache-item,
            .service-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                background: var(--bg-tertiary);
                border-radius: var(--radius-md);
                font-size: 14px;
            }

            .backup-item span:first-child,
            .cache-item span:first-child,
            .service-item span:first-child {
                color: var(--text-primary);
            }

            .backup-item span:last-child,
            .cache-item span:last-child {
                color: var(--text-secondary);
                font-size: 12px;
            }

            .cleanup-options {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .checkbox-label {
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--text-primary);
                cursor: pointer;
                font-size: 14px;
            }

            .checkbox-label input[type="checkbox"] {
                width: 16px;
                height: 16px;
                accent-color: var(--primary);
            }

            .service-status {
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--text-secondary);
                font-size: 14px;
            }

            .performance-charts {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 24px;
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
                font-size: 16px;
                font-weight: 600;
                margin: 0;
            }

            .chart-body {
                position: relative;
                height: 200px;
            }

            @media (max-width: 768px) {
                .monitoring-grid {
                    grid-template-columns: 1fr;
                }

                .maintenance-grid {
                    grid-template-columns: 1fr;
                }

                .performance-charts {
                    grid-template-columns: 1fr;
                }

                .logs-controls {
                    flex-direction: column;
                    align-items: stretch;
                }

                .controls-left {
                    order: 2;
                    margin-top: 12px;
                }

                .controls-right {
                    order: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        // 日志控制事件
        document.getElementById('refresh-logs')?.addEventListener('click', () => {
            this.loadLogs();
        });

        document.getElementById('clear-logs')?.addEventListener('click', () => {
            this.clearLogs();
        });

        document.getElementById('export-logs')?.addEventListener('click', () => {
            this.exportLogs();
        });

        // 维护工具事件
        document.getElementById('create-backup')?.addEventListener('click', () => {
            this.createBackup();
        });

        document.getElementById('clear-cache')?.addEventListener('click', () => {
            this.clearCache();
        });

        document.getElementById('system-cleanup')?.addEventListener('click', () => {
            this.systemCleanup();
        });

        // 启动监控更新
        this.startMonitoring();
        this.startLogUpdates();
    }

    async loadData() {
        await Promise.all([
            this.loadSystemStats(),
            this.loadLogs(),
            this.loadBackupList(),
            this.loadCacheStats()
        ]);
    }

    async loadSystemStats() {
        // 模拟系统统计数据
        const stats = {
            cpu: '45%',
            memory: '68%',
            disk: '72%',
            network: '1.2MB/s',
            dbConnections: '23/100',
            dbQueryTime: '12ms',
            dbCacheHit: '94%',
            dbSize: '2.1GB',
            responseTime: '156ms',
            qps: '1,247',
            errorRate: '0.02%',
            onlineUsers: '234'
        };

        document.getElementById('cpu-usage').textContent = stats.cpu;
        document.getElementById('memory-usage').textContent = stats.memory;
        document.getElementById('disk-usage').textContent = stats.disk;
        document.getElementById('network-traffic').textContent = stats.network;
        document.getElementById('db-connections').textContent = stats.dbConnections;
        document.getElementById('db-query-time').textContent = stats.dbQueryTime;
        document.getElementById('db-cache-hit').textContent = stats.dbCacheHit;
        document.getElementById('db-size').textContent = stats.dbSize;
        document.getElementById('response-time').textContent = stats.responseTime;
        document.getElementById('qps').textContent = stats.qps;
        document.getElementById('error-rate').textContent = stats.errorRate;
        document.getElementById('online-users').textContent = stats.onlineUsers;
    }

    async loadLogs() {
        const logsContent = document.getElementById('logs-content');
        if (!logsContent) return;

        // 模拟日志数据
        const logs = [
            { time: '2025-01-25 14:32:15', level: 'info', source: 'api', message: 'User login successful: user_id=1234' },
            { time: '2025-01-25 14:31:58', level: 'warning', source: 'database', message: 'Slow query detected: SELECT * FROM users WHERE... (234ms)' },
            { time: '2025-01-25 14:31:42', level: 'error', source: 'auth', message: 'Authentication failed: invalid token' },
            { time: '2025-01-25 14:31:20', level: 'info', source: 'scheduler', message: 'Backup task completed successfully' },
            { time: '2025-01-25 14:30:55', level: 'debug', source: 'api', message: 'Cache hit for key: user_profile_1234' }
        ];

        logsContent.innerHTML = logs.map(log => `
            <div class="log-entry">
                <div class="log-time">${log.time}</div>
                <div class="log-level ${log.level}">${log.level.toUpperCase()}</div>
                <div class="log-source">${log.source}</div>
                <div class="log-message">${log.message}</div>
            </div>
        `).join('');
    }

    async loadBackupList() {
        const backupList = document.getElementById('backup-list');
        if (!backupList) return;

        const backups = [
            { name: 'backup_2025-01-25_14-00.sql', size: '234MB', time: '2小时前' },
            { name: 'backup_2025-01-25_02-00.sql', size: '231MB', time: '14小时前' },
            { name: 'backup_2025-01-24_14-00.sql', size: '228MB', time: '1天前' },
            { name: 'backup_2025-01-24_02-00.sql', size: '225MB', time: '1天前' }
        ];

        backupList.innerHTML = backups.map(backup => `
            <div class="backup-item">
                <span>${backup.name}</span>
                <span>${backup.size} - ${backup.time}</span>
            </div>
        `).join('');
    }

    async loadCacheStats() {
        document.getElementById('app-cache-size').textContent = '45MB';
        document.getElementById('db-cache-size').textContent = '128MB';
        document.getElementById('static-cache-size').textContent = '23MB';
    }

    startMonitoring() {
        this.monitoringInterval = setInterval(() => {
            this.loadSystemStats();
        }, 5000); // 每5秒更新一次
    }

    startLogUpdates() {
        this.logUpdateInterval = setInterval(() => {
            this.loadLogs();
        }, 10000); // 每10秒更新一次日志
    }

    clearLogs() {
        if (confirm('确定要清空所有日志吗？此操作不可撤销。')) {
            const logsContent = document.getElementById('logs-content');
            if (logsContent) {
                logsContent.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">日志已清空</div>';
            }
        }
    }

    exportLogs() {
        // 模拟导出日志
        const blob = new Blob(['模拟日志数据...'], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `logs_${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    createBackup() {
        if (confirm('确定要创建数据库备份吗？此过程可能需要几分钟时间。')) {
            // 模拟备份过程
            this.showNotification('正在创建备份...', 'info');
            setTimeout(() => {
                this.showNotification('备份创建成功', 'success');
                this.loadBackupList();
            }, 3000);
        }
    }

    clearCache() {
        if (confirm('确定要清空所有缓存吗？这可能会暂时影响系统性能。')) {
            this.showNotification('正在清空缓存...', 'info');
            setTimeout(() => {
                this.showNotification('缓存清空成功', 'success');
                this.loadCacheStats();
            }, 2000);
        }
    }

    systemCleanup() {
        const options = {
            temp: document.getElementById('cleanup-temp')?.checked,
            logs: document.getElementById('cleanup-logs')?.checked,
            sessions: document.getElementById('cleanup-sessions')?.checked
        };

        const selectedOptions = Object.entries(options)
            .filter(([_, selected]) => selected)
            .map(([option, _]) => option);

        if (selectedOptions.length === 0) {
            this.showNotification('请选择要清理的项目', 'warning');
            return;
        }

        if (confirm(`确定要清理选中的项目吗？\n${selectedOptions.join(', ')}`)) {
            this.showNotification('正在执行系统清理...', 'info');
            setTimeout(() => {
                this.showNotification('系统清理完成', 'success');
            }, 3000);
        }
    }

    showNotification(message, type) {
        if (this.eventBus) {
            this.eventBus.emit('notification', { message, type });
        }
    }

    async destroy() {
        // 清理定时器
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }

        if (this.logUpdateInterval) {
            clearInterval(this.logUpdateInterval);
            this.logUpdateInterval = null;
        }

        await super.destroy();
    }
}