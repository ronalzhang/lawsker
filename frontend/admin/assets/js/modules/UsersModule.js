/**
 * 用户管理模块
 * 用户列表、律师审核、权限管理
 */

export class UsersModule extends BaseModule {
    constructor(eventBus) {
        super(eventBus);
        this.currentTab = 'users';
        this.users = [];
        this.lawyers = [];
    }

    async render() {
        this.container.innerHTML = `
            <div class="users-container">
                <!-- 页面标题 -->
                <div class="page-header">
                    <h1 class="page-title">用户管理</h1>
                    <p class="page-description">管理用户账户、律师认证和权限设置</p>
                </div>

                <!-- 标签页导航 -->
                <div class="tab-navigation">
                    <button class="tab-btn active" data-tab="users">用户管理</button>
                    <button class="tab-btn" data-tab="lawyers">律师审核</button>
                    <button class="tab-btn" data-tab="permissions">权限管理</button>
                </div>

                <!-- 用户管理标签页 -->
                <div class="tab-content active" id="users-tab">
                    <div class="section-header">
                        <h2>用户列表</h2>
                        <button class="btn btn-primary" id="add-user">添加用户</button>
                    </div>
                    <div class="users-table">
                        <div class="table-header">
                            <div class="table-cell">用户</div>
                            <div class="table-cell">类型</div>
                            <div class="table-cell">注册时间</div>
                            <div class="table-cell">状态</div>
                            <div class="table-cell">操作</div>
                        </div>
                        <div class="table-body" id="users-list">
                            <!-- 用户列表将动态加载 -->
                        </div>
                    </div>
                </div>

                <!-- 律师审核标签页 -->
                <div class="tab-content" id="lawyers-tab">
                    <div class="section-header">
                        <h2>律师认证审核</h2>
                        <div class="filter-group">
                            <select id="audit-status-filter">
                                <option value="all">所有状态</option>
                                <option value="pending">待审核</option>
                                <option value="approved">已通过</option>
                                <option value="rejected">已拒绝</option>
                            </select>
                        </div>
                    </div>
                    <div class="lawyers-grid" id="lawyers-grid">
                        <!-- 律师审核卡片将动态加载 -->
                    </div>
                </div>

                <!-- 权限管理标签页 -->
                <div class="tab-content" id="permissions-tab">
                    <div class="section-header">
                        <h2>权限管理</h2>
                    </div>
                    <div class="permissions-content">
                        <div class="roles-section">
                            <h3>角色管理</h3>
                            <div class="roles-grid">
                                <div class="role-card">
                                    <h4>管理员</h4>
                                    <p>系统管理员，拥有所有权限</p>
                                    <div class="role-permissions">
                                        <span class="permission-tag">用户管理</span>
                                        <span class="permission-tag">系统设置</span>
                                        <span class="permission-tag">数据分析</span>
                                    </div>
                                </div>
                                <div class="role-card">
                                    <h4>律师</h4>
                                    <p>认证律师，提供法律服务</p>
                                    <div class="role-permissions">
                                        <span class="permission-tag">接收任务</span>
                                        <span class="permission-tag">文书生成</span>
                                    </div>
                                </div>
                                <div class="role-card">
                                    <h4>用户</h4>
                                    <p>普通用户，可发布法律需求</p>
                                    <div class="role-permissions">
                                        <span class="permission-tag">发布任务</span>
                                        <span class="permission-tag">咨询服务</span>
                                    </div>
                                </div>
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
            .users-container {
                max-width: 1200px;
                margin: 0 auto;
            }

            .tab-navigation {
                display: flex;
                gap: 4px;
                margin-bottom: 32px;
                background: var(--bg-card);
                padding: 4px;
                border-radius: var(--radius-lg);
                border: 1px solid var(--border-primary);
            }

            .tab-btn {
                flex: 1;
                padding: 12px 24px;
                border: none;
                background: transparent;
                color: var(--text-secondary);
                border-radius: var(--radius-md);
                cursor: pointer;
                font-weight: 500;
                transition: all var(--transition-fast);
            }

            .tab-btn:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .tab-btn.active {
                background: var(--primary);
                color: white;
                box-shadow: var(--shadow-sm);
            }

            .tab-content {
                display: none;
            }

            .tab-content.active {
                display: block;
            }

            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
            }

            .section-header h2 {
                color: var(--text-primary);
                font-size: 20px;
                font-weight: 600;
                margin: 0;
            }

            .filter-group {
                display: flex;
                gap: 12px;
                align-items: center;
            }

            .users-table {
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                overflow: hidden;
            }

            .table-header {
                display: grid;
                grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
                gap: 16px;
                padding: 16px 24px;
                background: var(--bg-tertiary);
                border-bottom: 1px solid var(--border-secondary);
                font-weight: 600;
                color: var(--text-primary);
                font-size: 14px;
            }

            .table-body {
                max-height: 600px;
                overflow-y: auto;
            }

            .table-row {
                display: grid;
                grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
                gap: 16px;
                padding: 16px 24px;
                border-bottom: 1px solid var(--border-secondary);
                transition: background var(--transition-fast);
            }

            .table-row:hover {
                background: var(--bg-hover);
            }

            .table-row:last-child {
                border-bottom: none;
            }

            .table-cell {
                display: flex;
                align-items: center;
                color: var(--text-primary);
                font-size: 14px;
            }

            .user-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .user-avatar {
                width: 40px;
                height: 40px;
                background: var(--primary);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                font-size: 14px;
            }

            .user-details {
                flex: 1;
            }

            .user-name {
                font-weight: 500;
                margin-bottom: 2px;
            }

            .user-email {
                color: var(--text-secondary);
                font-size: 12px;
            }

            .user-type {
                padding: 4px 8px;
                border-radius: var(--radius-sm);
                font-size: 12px;
                font-weight: 500;
            }

            .user-type.admin {
                background: rgba(239, 68, 68, 0.1);
                color: var(--danger);
            }

            .user-type.lawyer {
                background: rgba(59, 130, 246, 0.1);
                color: var(--primary);
            }

            .user-type.user {
                background: rgba(16, 185, 129, 0.1);
                color: var(--success);
            }

            .status-badge {
                padding: 4px 8px;
                border-radius: var(--radius-sm);
                font-size: 12px;
                font-weight: 500;
            }

            .status-active {
                background: rgba(16, 185, 129, 0.1);
                color: var(--success);
            }

            .status-inactive {
                background: rgba(156, 163, 175, 0.1);
                color: var(--text-muted);
            }

            .status-banned {
                background: rgba(239, 68, 68, 0.1);
                color: var(--danger);
            }

            .action-buttons {
                display: flex;
                gap: 8px;
            }

            .action-btn {
                padding: 4px 8px;
                border: none;
                border-radius: var(--radius-sm);
                font-size: 12px;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .action-btn.edit {
                background: rgba(59, 130, 246, 0.1);
                color: var(--primary);
            }

            .action-btn.delete {
                background: rgba(239, 68, 68, 0.1);
                color: var(--danger);
            }

            .lawyers-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
            }

            .lawyer-card {
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 20px;
                transition: all var(--transition-fast);
            }

            .lawyer-card:hover {
                border-color: var(--border-accent);
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }

            .lawyer-header {
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 16px;
            }

            .lawyer-avatar {
                width: 60px;
                height: 60px;
                background: var(--primary);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                font-size: 20px;
            }

            .lawyer-info h3 {
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 4px;
            }

            .lawyer-info p {
                color: var(--text-secondary);
                font-size: 14px;
                margin: 0;
            }

            .lawyer-details {
                margin-bottom: 16px;
            }

            .detail-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 14px;
            }

            .detail-label {
                color: var(--text-secondary);
            }

            .detail-value {
                color: var(--text-primary);
                font-weight: 500;
            }

            .lawyer-actions {
                display: flex;
                gap: 8px;
                justify-content: flex-end;
            }

            .roles-section {
                margin-bottom: 32px;
            }

            .roles-section h3 {
                color: var(--text-primary);
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 16px;
            }

            .roles-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }

            .role-card {
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 20px;
            }

            .role-card h4 {
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 8px;
            }

            .role-card p {
                color: var(--text-secondary);
                font-size: 14px;
                margin-bottom: 16px;
            }

            .role-permissions {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .permission-tag {
                background: rgba(59, 130, 246, 0.1);
                color: var(--primary);
                font-size: 12px;
                padding: 4px 8px;
                border-radius: var(--radius-sm);
            }

            @media (max-width: 768px) {
                .table-header,
                .table-row {
                    grid-template-columns: 1fr;
                    gap: 8px;
                }

                .table-cell {
                    justify-content: space-between;
                }

                .lawyers-grid {
                    grid-template-columns: 1fr;
                }

                .roles-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchTab(tab);
            });
        });
    }

    async loadData() {
        await Promise.all([
            this.loadUsers(),
            this.loadLawyers()
        ]);
    }

    async loadUsers() {
        // 模拟用户数据
        this.users = [
            {
                id: '1',
                name: '张三',
                email: 'zhangsan@example.com',
                type: 'user',
                status: 'active',
                registeredAt: '2025-01-15'
            },
            {
                id: '2',
                name: '李律师',
                email: 'li.lawyer@example.com',
                type: 'lawyer',
                status: 'active',
                registeredAt: '2025-01-10'
            },
            {
                id: '3',
                name: '王管理员',
                email: 'admin@example.com',
                type: 'admin',
                status: 'active',
                registeredAt: '2025-01-01'
            }
        ];

        this.renderUsers();
    }

    renderUsers() {
        const usersList = document.getElementById('users-list');
        if (!usersList) return;

        usersList.innerHTML = this.users.map(user => `
            <div class="table-row">
                <div class="table-cell">
                    <div class="user-info">
                        <div class="user-avatar">${user.name.charAt(0)}</div>
                        <div class="user-details">
                            <div class="user-name">${user.name}</div>
                            <div class="user-email">${user.email}</div>
                        </div>
                    </div>
                </div>
                <div class="table-cell">
                    <span class="user-type ${user.type}">${this.getUserTypeLabel(user.type)}</span>
                </div>
                <div class="table-cell">${user.registeredAt}</div>
                <div class="table-cell">
                    <span class="status-badge status-${user.status}">${this.getStatusLabel(user.status)}</span>
                </div>
                <div class="table-cell">
                    <div class="action-buttons">
                        <button class="action-btn edit">编辑</button>
                        <button class="action-btn delete">删除</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async loadLawyers() {
        // 模拟律师审核数据
        this.lawyers = [
            {
                id: '1',
                name: '王律师',
                email: 'wang.lawyer@example.com',
                phone: '138****1234',
                licenseNumber: 'A20250001',
                firm: '某某律师事务所',
                specialty: '合同纠纷',
                experience: '5年',
                status: 'pending',
                appliedAt: '2025-01-20'
            },
            {
                id: '2',
                name: '李律师',
                email: 'li.lawyer@example.com',
                phone: '139****5678',
                licenseNumber: 'A20250002',
                firm: '知名律师事务所',
                specialty: '知识产权',
                experience: '8年',
                status: 'approved',
                appliedAt: '2025-01-18'
            }
        ];

        this.renderLawyers();
    }

    renderLawyers() {
        const lawyersGrid = document.getElementById('lawyers-grid');
        if (!lawyersGrid) return;

        lawyersGrid.innerHTML = this.lawyers.map(lawyer => `
            <div class="lawyer-card">
                <div class="lawyer-header">
                    <div class="lawyer-avatar">${lawyer.name.charAt(0)}</div>
                    <div class="lawyer-info">
                        <h3>${lawyer.name}</h3>
                        <p>${lawyer.email}</p>
                    </div>
                </div>
                <div class="lawyer-details">
                    <div class="detail-row">
                        <span class="detail-label">执业证号</span>
                        <span class="detail-value">${lawyer.licenseNumber}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">所属律所</span>
                        <span class="detail-value">${lawyer.firm}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">专业领域</span>
                        <span class="detail-value">${lawyer.specialty}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">执业经验</span>
                        <span class="detail-value">${lawyer.experience}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">申请时间</span>
                        <span class="detail-value">${lawyer.appliedAt}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">状态</span>
                        <span class="detail-value">
                            <span class="status-badge status-${lawyer.status}">
                                ${this.getAuditStatusLabel(lawyer.status)}
                            </span>
                        </span>
                    </div>
                </div>
                <div class="lawyer-actions">
                    ${lawyer.status === 'pending' ? `
                        <button class="btn btn-success btn-sm" onclick="approveLawyer('${lawyer.id}')">通过</button>
                        <button class="btn btn-danger btn-sm" onclick="rejectLawyer('${lawyer.id}')">拒绝</button>
                    ` : ''}
                    <button class="btn btn-secondary btn-sm">查看详情</button>
                </div>
            </div>
        `).join('');
    }

    switchTab(tab) {
        this.currentTab = tab;

        // 更新标签按钮状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        // 更新内容显示
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tab}-tab`);
        });
    }

    getUserTypeLabel(type) {
        const labels = {
            'admin': '管理员',
            'lawyer': '律师',
            'user': '用户'
        };
        return labels[type] || type;
    }

    getStatusLabel(status) {
        const labels = {
            'active': '正常',
            'inactive': '停用',
            'banned': '封禁'
        };
        return labels[status] || status;
    }

    getAuditStatusLabel(status) {
        const labels = {
            'pending': '待审核',
            'approved': '已通过',
            'rejected': '已拒绝'
        };
        return labels[status] || status;
    }
}