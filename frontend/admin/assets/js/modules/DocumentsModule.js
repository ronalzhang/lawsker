/**
 * 文书管理模块
 * 文书模板管理、分类管理、统计分析
 */

export class DocumentsModule extends BaseModule {
    constructor(eventBus) {
        super(eventBus);
        this.currentCategory = 'all';
        this.searchQuery = '';
        this.documents = [];
        this.categories = [];
    }

    async render() {
        this.container.innerHTML = `
            <div class="documents-container">
                <!-- 页面标题 -->
                <div class="page-header">
                    <h1 class="page-title">文书管理</h1>
                    <p class="page-description">管理法律文书模板、分类和使用统计</p>
                    <div class="page-actions">
                        <button class="btn btn-secondary" id="import-documents">批量导入</button>
                        <button class="btn btn-primary" id="add-document">新增文书</button>
                    </div>
                </div>

                <!-- 统计概览 -->
                <div class="stats-overview">
                    <div class="stat-card">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14,2 14,8 20,8"></polyline>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="total-documents">--</div>
                            <div class="stat-label">文书模板总数</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="monthly-usage">--</div>
                            <div class="stat-label">本月使用次数</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="categories-count">--</div>
                            <div class="stat-label">文书分类</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                                <circle cx="9" cy="7" r="4"></circle>
                                <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value" id="active-users">--</div>
                            <div class="stat-label">活跃用户</div>
                        </div>
                    </div>
                </div>

                <!-- 搜索和筛选 -->
                <div class="search-filters">
                    <div class="search-box">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                        <input type="text" id="document-search" placeholder="搜索文书名称、内容或标签...">
                    </div>
                    <div class="filter-controls">
                        <select id="category-filter">
                            <option value="all">所有分类</option>
                        </select>
                        <select id="status-filter">
                            <option value="all">所有状态</option>
                            <option value="active">启用</option>
                            <option value="inactive">禁用</option>
                            <option value="draft">草稿</option>
                        </select>
                        <select id="sort-by">
                            <option value="name">按名称排序</option>
                            <option value="created">按创建时间</option>
                            <option value="updated">按更新时间</option>
                            <option value="usage">按使用次数</option>
                        </select>
                    </div>
                </div>

                <!-- 分类管理 -->
                <div class="categories-section">
                    <div class="section-header">
                        <h2 class="section-title">文书分类</h2>
                        <button class="btn btn-secondary" id="manage-categories">管理分类</button>
                    </div>
                    <div class="categories-grid" id="categories-grid">
                        <!-- 分类卡片将动态加载 -->
                    </div>
                </div>

                <!-- 文书列表 -->
                <div class="documents-section">
                    <div class="section-header">
                        <h2 class="section-title">文书模板</h2>
                        <div class="view-controls">
                            <button class="view-btn active" data-view="grid">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="3" width="7" height="7"></rect>
                                    <rect x="14" y="3" width="7" height="7"></rect>
                                    <rect x="14" y="14" width="7" height="7"></rect>
                                    <rect x="3" y="14" width="7" height="7"></rect>
                                </svg>
                            </button>
                            <button class="view-btn" data-view="list">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="8" y1="6" x2="21" y2="6"></line>
                                    <line x1="8" y1="12" x2="21" y2="12"></line>
                                    <line x1="8" y1="18" x2="21" y2="18"></line>
                                    <line x1="3" y1="6" x2="3.01" y2="6"></line>
                                    <line x1="3" y1="12" x2="3.01" y2="12"></line>
                                    <line x1="3" y1="18" x2="3.01" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="documents-grid" id="documents-grid">
                        <!-- 文书卡片将动态加载 -->
                    </div>
                </div>

                <!-- 使用统计 -->
                <div class="usage-analytics">
                    <h2 class="section-title">使用统计</h2>
                    <div class="analytics-grid">
                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>热门文书排行</h3>
                                <select id="ranking-period">
                                    <option value="week">本周</option>
                                    <option value="month" selected>本月</option>
                                    <option value="quarter">本季度</option>
                                </select>
                            </div>
                            <div class="chart-body">
                                <div class="ranking-list" id="ranking-list">
                                    <!-- 排行列表将动态加载 -->
                                </div>
                            </div>
                        </div>

                        <div class="chart-container">
                            <div class="chart-header">
                                <h3>使用趋势</h3>
                                <select id="trend-period">
                                    <option value="7days">近7天</option>
                                    <option value="30days" selected>近30天</option>
                                    <option value="90days">近90天</option>
                                </select>
                            </div>
                            <div class="chart-body">
                                <canvas id="usage-trend-chart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 文书编辑模态框 -->
            <div id="document-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modal-title">新增文书</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="document-form">
                            <div class="form-group">
                                <label class="form-label">文书名称</label>
                                <input type="text" id="document-name" class="form-input" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">所属分类</label>
                                <select id="document-category" class="form-input" required>
                                    <!-- 分类选项将动态加载 -->
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">文书描述</label>
                                <textarea id="document-description" class="form-input" rows="3"></textarea>
                            </div>
                            <div class="form-group">
                                <label class="form-label">标签</label>
                                <input type="text" id="document-tags" class="form-input" placeholder="请输入标签，用逗号分隔">
                            </div>
                            <div class="form-group">
                                <label class="form-label">文书内容</label>
                                <div id="document-editor" class="editor-container">
                                    <div class="editor-toolbar">
                                        <button type="button" class="editor-btn" data-action="bold"><strong>B</strong></button>
                                        <button type="button" class="editor-btn" data-action="italic"><em>I</em></button>
                                        <button type="button" class="editor-btn" data-action="underline"><u>U</u></button>
                                        <span class="editor-separator">|</span>
                                        <button type="button" class="editor-btn" data-action="insertOrderedList">1.</button>
                                        <button type="button" class="editor-btn" data-action="insertUnorderedList">•</button>
                                        <span class="editor-separator">|</span>
                                        <button type="button" class="editor-btn" data-action="variable">变量</button>
                                    </div>
                                    <div id="editor-content" class="editor-content" contenteditable="true">
                                        请在此处输入文书内容...
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="document-active" checked>
                                    <span>启用此文书</span>
                                </label>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" id="modal-cancel">取消</button>
                        <button type="submit" class="btn btn-primary" id="modal-save">保存</button>
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
            .documents-container {
                max-width: 1200px;
                margin: 0 auto;
            }

            .page-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 32px;
                gap: 20px;
            }

            .page-actions {
                display: flex;
                gap: 12px;
            }

            .stats-overview {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }

            .search-filters {
                display: flex;
                gap: 20px;
                margin-bottom: 32px;
                align-items: center;
            }

            .search-box {
                position: relative;
                flex: 1;
                max-width: 400px;
            }

            .search-box svg {
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                color: var(--text-muted);
            }

            .search-box input {
                width: 100%;
                padding: 10px 16px 10px 44px;
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                color: var(--text-primary);
                font-size: 14px;
            }

            .filter-controls {
                display: flex;
                gap: 12px;
            }

            .filter-controls select {
                padding: 8px 12px;
                background: var(--bg-card);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                font-size: 14px;
                min-width: 120px;
            }

            .categories-section,
            .documents-section,
            .usage-analytics {
                margin-bottom: 40px;
            }

            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }

            .view-controls {
                display: flex;
                gap: 4px;
            }

            .view-btn {
                width: 36px;
                height: 36px;
                border: 1px solid var(--border-primary);
                background: transparent;
                color: var(--text-secondary);
                border-radius: var(--radius-md);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all var(--transition-fast);
            }

            .view-btn:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .view-btn.active {
                background: var(--primary);
                color: white;
                border-color: var(--primary);
            }

            .categories-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 16px;
            }

            .category-card {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 20px;
                text-align: center;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .category-card:hover {
                border-color: var(--border-accent);
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }

            .category-card.active {
                border-color: var(--primary);
                background: rgba(59, 130, 246, 0.1);
            }

            .category-icon {
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                border-radius: var(--radius-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 12px;
                color: white;
                font-size: 20px;
            }

            .category-name {
                color: var(--text-primary);
                font-weight: 600;
                margin-bottom: 4px;
            }

            .category-count {
                color: var(--text-secondary);
                font-size: 14px;
            }

            .documents-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }

            .documents-grid.list-view {
                grid-template-columns: 1fr;
            }

            .document-card {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                padding: 20px;
                transition: all var(--transition-fast);
                cursor: pointer;
            }

            .document-card:hover {
                border-color: var(--border-accent);
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }

            .document-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 12px;
            }

            .document-title {
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 4px;
            }

            .document-category {
                color: var(--text-secondary);
                font-size: 12px;
                background: var(--bg-tertiary);
                padding: 2px 8px;
                border-radius: var(--radius-sm);
            }

            .document-description {
                color: var(--text-secondary);
                font-size: 14px;
                line-height: 1.4;
                margin-bottom: 12px;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }

            .document-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin-bottom: 12px;
            }

            .document-tag {
                background: rgba(59, 130, 246, 0.1);
                color: var(--primary);
                font-size: 12px;
                padding: 2px 6px;
                border-radius: var(--radius-sm);
            }

            .document-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid var(--border-secondary);
            }

            .document-stats {
                display: flex;
                gap: 16px;
                font-size: 12px;
                color: var(--text-muted);
            }

            .document-actions {
                display: flex;
                gap: 8px;
            }

            .action-btn {
                width: 28px;
                height: 28px;
                border: none;
                background: transparent;
                color: var(--text-secondary);
                border-radius: var(--radius-sm);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all var(--transition-fast);
            }

            .action-btn:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .analytics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 24px;
            }

            .ranking-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
                max-height: 300px;
                overflow-y: auto;
            }

            .ranking-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: var(--bg-tertiary);
                border-radius: var(--radius-md);
            }

            .ranking-number {
                width: 24px;
                height: 24px;
                background: var(--primary);
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
                flex-shrink: 0;
            }

            .ranking-info {
                flex: 1;
            }

            .ranking-name {
                color: var(--text-primary);
                font-weight: 500;
                margin-bottom: 2px;
            }

            .ranking-category {
                color: var(--text-secondary);
                font-size: 12px;
            }

            .ranking-count {
                color: var(--text-primary);
                font-weight: 600;
                font-size: 14px;
            }

            /* 模态框样式 */
            .modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: var(--z-modal);
                backdrop-filter: blur(5px);
            }

            .modal-content {
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                width: 90%;
                max-width: 800px;
                max-height: 90vh;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }

            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px 24px;
                border-bottom: 1px solid var(--border-secondary);
            }

            .modal-header h3 {
                color: var(--text-primary);
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }

            .modal-close {
                width: 32px;
                height: 32px;
                border: none;
                background: transparent;
                color: var(--text-secondary);
                font-size: 24px;
                cursor: pointer;
                border-radius: var(--radius-sm);
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .modal-close:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .modal-body {
                padding: 24px;
                overflow-y: auto;
                flex: 1;
            }

            .modal-footer {
                display: flex;
                justify-content: flex-end;
                gap: 12px;
                padding: 20px 24px;
                border-top: 1px solid var(--border-secondary);
            }

            .form-group {
                margin-bottom: 20px;
            }

            .form-label {
                display: block;
                color: var(--text-primary);
                font-weight: 500;
                margin-bottom: 6px;
                font-size: 14px;
            }

            .form-input {
                width: 100%;
                padding: 10px 12px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                font-size: 14px;
            }

            .form-input:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }

            textarea.form-input {
                resize: vertical;
                min-height: 80px;
            }

            .editor-container {
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                overflow: hidden;
            }

            .editor-toolbar {
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 8px 12px;
                background: var(--bg-tertiary);
                border-bottom: 1px solid var(--border-secondary);
            }

            .editor-btn {
                width: 28px;
                height: 28px;
                border: none;
                background: transparent;
                color: var(--text-secondary);
                border-radius: var(--radius-sm);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                transition: all var(--transition-fast);
            }

            .editor-btn:hover {
                background: var(--bg-hover);
                color: var(--text-primary);
            }

            .editor-separator {
                color: var(--border-primary);
                margin: 0 4px;
            }

            .editor-content {
                min-height: 200px;
                padding: 12px;
                background: var(--bg-primary);
                color: var(--text-primary);
                font-size: 14px;
                line-height: 1.5;
                outline: none;
            }

            .editor-content:empty::before {
                content: attr(placeholder);
                color: var(--text-muted);
            }

            @media (max-width: 768px) {
                .page-header {
                    flex-direction: column;
                    align-items: stretch;
                }

                .search-filters {
                    flex-direction: column;
                    gap: 12px;
                }

                .filter-controls {
                    flex-wrap: wrap;
                }

                .categories-grid,
                .documents-grid {
                    grid-template-columns: 1fr;
                }

                .analytics-grid {
                    grid-template-columns: 1fr;
                }

                .modal-content {
                    width: 95%;
                    margin: 20px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        // 新增文书按钮
        document.getElementById('add-document')?.addEventListener('click', () => {
            this.showDocumentModal();
        });

        // 搜索功能
        document.getElementById('document-search')?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            this.filterDocuments();
        });

        // 筛选功能
        document.getElementById('category-filter')?.addEventListener('change', (e) => {
            this.currentCategory = e.target.value;
            this.filterDocuments();
        });

        // 视图切换
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                this.switchView(view);
            });
        });

        // 模态框事件
        document.getElementById('modal-cancel')?.addEventListener('click', () => {
            this.hideDocumentModal();
        });

        document.querySelector('.modal-close')?.addEventListener('click', () => {
            this.hideDocumentModal();
        });

        // 编辑器工具栏
        document.querySelectorAll('.editor-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleEditorAction(action);
            });
        });

        // 分类点击事件
        this.container.addEventListener('click', (e) => {
            const categoryCard = e.target.closest('.category-card');
            if (categoryCard) {
                const categoryId = categoryCard.dataset.categoryId;
                this.selectCategory(categoryId);
            }

            const documentCard = e.target.closest('.document-card');
            if (documentCard) {
                const documentId = documentCard.dataset.documentId;
                this.selectDocument(documentId);
            }
        });
    }

    async loadData() {
        await Promise.all([
            this.loadStats(),
            this.loadCategories(),
            this.loadDocuments(),
            this.loadUsageStats()
        ]);
    }

    async loadStats() {
        // 模拟统计数据
        const stats = {
            totalDocuments: 156,
            monthlyUsage: 1247,
            categoriesCount: 12,
            activeUsers: 89
        };

        document.getElementById('total-documents').textContent = stats.totalDocuments;
        document.getElementById('monthly-usage').textContent = stats.monthlyUsage;
        document.getElementById('categories-count').textContent = stats.categoriesCount;
        document.getElementById('active-users').textContent = stats.activeUsers;
    }

    async loadCategories() {
        // 模拟分类数据
        this.categories = [
            { id: 'all', name: '全部', count: 156, icon: '📄' },
            { id: 'contract', name: '合同协议', count: 45, icon: '📝' },
            { id: 'litigation', name: '诉讼文书', count: 32, icon: '⚖️' },
            { id: 'corporate', name: '公司法务', count: 28, icon: '🏢' },
            { id: 'intellectual', name: '知识产权', count: 19, icon: '💡' },
            { id: 'real-estate', name: '房地产', count: 16, icon: '🏠' },
            { id: 'labor', name: '劳动纠纷', count: 16, icon: '👥' }
        ];

        this.renderCategories();
        this.updateCategoryFilter();
    }

    renderCategories() {
        const categoriesGrid = document.getElementById('categories-grid');
        if (!categoriesGrid) return;

        categoriesGrid.innerHTML = this.categories.map(category => `
            <div class="category-card ${category.id === this.currentCategory ? 'active' : ''}" data-category-id="${category.id}">
                <div class="category-icon">${category.icon}</div>
                <div class="category-name">${category.name}</div>
                <div class="category-count">${category.count} 个文书</div>
            </div>
        `).join('');
    }

    updateCategoryFilter() {
        const categoryFilter = document.getElementById('category-filter');
        if (!categoryFilter) return;

        categoryFilter.innerHTML = this.categories.map(category => 
            `<option value="${category.id}">${category.name}</option>`
        ).join('');
    }

    async loadDocuments() {
        // 模拟文书数据
        this.documents = [
            {
                id: '1',
                title: '劳动合同模板',
                category: 'labor',
                categoryName: '劳动纠纷',
                description: '标准劳动合同模板，包含基本条款和权利义务说明',
                tags: ['劳动', '合同', '标准'],
                status: 'active',
                usageCount: 156,
                lastUsed: '2025-01-25',
                createdAt: '2025-01-15'
            },
            {
                id: '2',
                title: '起诉状模板',
                category: 'litigation',
                categoryName: '诉讼文书',
                description: '民事起诉状标准模板，适用于一般民事诉讼案件',
                tags: ['诉讼', '起诉状', '民事'],
                status: 'active',
                usageCount: 89,
                lastUsed: '2025-01-24',
                createdAt: '2025-01-10'
            },
            {
                id: '3',
                title: '购房合同',
                category: 'real-estate',
                categoryName: '房地产',
                description: '二手房买卖合同模板，包含交易条件和过户流程',
                tags: ['房产', '买卖', '合同'],
                status: 'active',
                usageCount: 67,
                lastUsed: '2025-01-23',
                createdAt: '2025-01-08'
            }
        ];

        this.renderDocuments();
    }

    renderDocuments() {
        const documentsGrid = document.getElementById('documents-grid');
        if (!documentsGrid) return;

        const filteredDocuments = this.filterDocuments();

        documentsGrid.innerHTML = filteredDocuments.map(doc => `
            <div class="document-card" data-document-id="${doc.id}">
                <div class="document-header">
                    <div>
                        <div class="document-title">${doc.title}</div>
                        <div class="document-category">${doc.categoryName}</div>
                    </div>
                    <div class="document-actions">
                        <button class="action-btn" title="编辑" onclick="event.stopPropagation(); window.adminApp.editDocument('${doc.id}')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="action-btn" title="复制" onclick="event.stopPropagation(); window.adminApp.copyDocument('${doc.id}')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                        <button class="action-btn" title="删除" onclick="event.stopPropagation(); window.adminApp.deleteDocument('${doc.id}')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3,6 5,6 21,6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="document-description">${doc.description}</div>
                <div class="document-tags">
                    ${doc.tags.map(tag => `<span class="document-tag">${tag}</span>`).join('')}
                </div>
                <div class="document-footer">
                    <div class="document-stats">
                        <span>使用 ${doc.usageCount} 次</span>
                        <span>最后使用 ${doc.lastUsed}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    filterDocuments() {
        let filtered = [...this.documents];

        // 按分类筛选
        if (this.currentCategory !== 'all') {
            filtered = filtered.filter(doc => doc.category === this.currentCategory);
        }

        // 按搜索关键词筛选
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(doc => 
                doc.title.toLowerCase().includes(query) ||
                doc.description.toLowerCase().includes(query) ||
                doc.tags.some(tag => tag.toLowerCase().includes(query))
            );
        }

        return filtered;
    }

    async loadUsageStats() {
        // 模拟使用统计数据
        const rankings = [
            { name: '劳动合同模板', category: '劳动纠纷', count: 156 },
            { name: '起诉状模板', category: '诉讼文书', count: 89 },
            { name: '购房合同', category: '房地产', count: 67 },
            { name: '商标注册申请', category: '知识产权', count: 45 },
            { name: '公司章程模板', category: '公司法务', count: 34 }
        ];

        const rankingList = document.getElementById('ranking-list');
        if (rankingList) {
            rankingList.innerHTML = rankings.map((item, index) => `
                <div class="ranking-item">
                    <div class="ranking-number">${index + 1}</div>
                    <div class="ranking-info">
                        <div class="ranking-name">${item.name}</div>
                        <div class="ranking-category">${item.category}</div>
                    </div>
                    <div class="ranking-count">${item.count}</div>
                </div>
            `).join('');
        }
    }

    selectCategory(categoryId) {
        this.currentCategory = categoryId;
        
        // 更新分类卡片状态
        document.querySelectorAll('.category-card').forEach(card => {
            card.classList.toggle('active', card.dataset.categoryId === categoryId);
        });

        // 更新文书列表
        this.renderDocuments();

        // 同步筛选器
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            categoryFilter.value = categoryId;
        }
    }

    selectDocument(documentId) {
        const document = this.documents.find(doc => doc.id === documentId);
        if (document) {
            this.showDocumentModal(document);
        }
    }

    switchView(view) {
        // 更新按钮状态
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        // 更新网格样式
        const documentsGrid = document.getElementById('documents-grid');
        if (documentsGrid) {
            documentsGrid.classList.toggle('list-view', view === 'list');
        }
    }

    showDocumentModal(document = null) {
        const modal = document.getElementById('document-modal');
        const title = document.getElementById('modal-title');
        
        if (document) {
            title.textContent = '编辑文书';
            // 填充表单数据
            this.fillDocumentForm(document);
        } else {
            title.textContent = '新增文书';
            this.clearDocumentForm();
        }

        modal.style.display = 'flex';
    }

    hideDocumentModal() {
        const modal = document.getElementById('document-modal');
        modal.style.display = 'none';
    }

    fillDocumentForm(document) {
        document.getElementById('document-name').value = document.title;
        document.getElementById('document-category').value = document.category;
        document.getElementById('document-description').value = document.description;
        document.getElementById('document-tags').value = document.tags.join(', ');
        document.getElementById('document-active').checked = document.status === 'active';
    }

    clearDocumentForm() {
        document.getElementById('document-name').value = '';
        document.getElementById('document-category').value = '';
        document.getElementById('document-description').value = '';
        document.getElementById('document-tags').value = '';
        document.getElementById('document-active').checked = true;
        document.getElementById('editor-content').innerHTML = '请在此处输入文书内容...';
    }

    handleEditorAction(action) {
        const editor = document.getElementById('editor-content');
        editor.focus();

        switch (action) {
            case 'bold':
                document.execCommand('bold');
                break;
            case 'italic':
                document.execCommand('italic');
                break;
            case 'underline':
                document.execCommand('underline');
                break;
            case 'insertOrderedList':
                document.execCommand('insertOrderedList');
                break;
            case 'insertUnorderedList':
                document.execCommand('insertUnorderedList');
                break;
            case 'variable':
                this.insertVariable();
                break;
        }
    }

    insertVariable() {
        const variable = prompt('请输入变量名称:');
        if (variable) {
            document.execCommand('insertText', false, `{{${variable}}}`);
        }
    }

    // 全局方法供按钮调用
    editDocument(id) {
        const document = this.documents.find(doc => doc.id === id);
        if (document) {
            this.showDocumentModal(document);
        }
    }

    copyDocument(id) {
        console.log('复制文书:', id);
        this.showNotification('文书复制成功', 'success');
    }

    deleteDocument(id) {
        if (confirm('确定要删除这个文书吗？此操作不可撤销。')) {
            this.documents = this.documents.filter(doc => doc.id !== id);
            this.renderDocuments();
            this.showNotification('文书删除成功', 'success');
        }
    }

    showNotification(message, type) {
        if (this.eventBus) {
            this.eventBus.emit('notification', { message, type });
        }
    }

    async destroy() {
        // 清理全局方法
        if (window.adminApp) {
            delete window.adminApp.editDocument;
            delete window.adminApp.copyDocument;
            delete window.adminApp.deleteDocument;
        }

        await super.destroy();
    }
}

// 将方法添加到全局对象以供按钮调用
window.adminApp = window.adminApp || {};
window.adminApp.editDocument = function(id) {
    // 这将被实例方法覆盖
};
window.adminApp.copyDocument = function(id) {
    // 这将被实例方法覆盖
};
window.adminApp.deleteDocument = function(id) {
    // 这将被实例方法覆盖
};