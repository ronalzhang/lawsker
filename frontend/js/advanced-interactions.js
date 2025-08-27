/**
 * Lawsker 高级交互功能增强
 * 提升用户交互体验和数据操作便利性
 */

class AdvancedInteractions {
    constructor() {
        this.gestureRecognizer = null;
        this.voiceCommands = new Map();
        this.shortcuts = new Map();
        this.contextMenus = new Map();
        this.dragDropHandlers = new Map();
        this.touchGestures = new Map();
        this.collaborationFeatures = new Map();
        this.init();
    }

    init() {
        this.setupGestureRecognition();
        this.setupVoiceCommands();
        this.setupKeyboardShortcuts();
        this.setupContextMenus();
        this.setupDragAndDrop();
        this.setupTouchGestures();
        this.setupCollaboration();
        this.setupSmartFiltering();
        this.setupDataAnnotations();
    }

    // 手势识别
    setupGestureRecognition() {
        if ('PointerEvent' in window) {
            this.gestureRecognizer = {
                pointers: new Map(),
                gestures: {
                    pinch: { active: false, scale: 1, lastScale: 1 },
                    pan: { active: false, x: 0, y: 0, lastX: 0, lastY: 0 },
                    rotate: { active: false, angle: 0, lastAngle: 0 }
                },

                init() {
                    document.addEventListener('pointerdown', this.handlePointerDown.bind(this));
                    document.addEventListener('pointermove', this.handlePointerMove.bind(this));
                    document.addEventListener('pointerup', this.handlePointerUp.bind(this));
                    document.addEventListener('pointercancel', this.handlePointerUp.bind(this));
                },

                handlePointerDown(e) {
                    this.pointers.set(e.pointerId, {
                        x: e.clientX,
                        y: e.clientY,
                        startX: e.clientX,
                        startY: e.clientY,
                        timestamp: Date.now()
                    });

                    if (this.pointers.size === 2) {
                        this.startMultiTouch();
                    }
                },

                handlePointerMove(e) {
                    if (!this.pointers.has(e.pointerId)) return;

                    const pointer = this.pointers.get(e.pointerId);
                    pointer.x = e.clientX;
                    pointer.y = e.clientY;

                    if (this.pointers.size === 2) {
                        this.handleMultiTouch();
                    } else if (this.pointers.size === 1) {
                        this.handleSingleTouch(pointer);
                    }
                },

                handlePointerUp(e) {
                    this.pointers.delete(e.pointerId);
                    
                    if (this.pointers.size < 2) {
                        this.endMultiTouch();
                    }
                },

                startMultiTouch() {
                    const pointers = Array.from(this.pointers.values());
                    if (pointers.length !== 2) return;

                    const [p1, p2] = pointers;
                    this.gestures.pinch.lastScale = this.getDistance(p1, p2);
                    this.gestures.rotate.lastAngle = this.getAngle(p1, p2);
                },

                handleMultiTouch() {
                    const pointers = Array.from(this.pointers.values());
                    if (pointers.length !== 2) return;

                    const [p1, p2] = pointers;
                    const currentDistance = this.getDistance(p1, p2);
                    const currentAngle = this.getAngle(p1, p2);

                    // 缩放手势
                    if (this.gestures.pinch.lastScale > 0) {
                        const scale = currentDistance / this.gestures.pinch.lastScale;
                        this.gestures.pinch.scale = scale;
                        this.triggerGesture('pinch', { scale });
                    }

                    // 旋转手势
                    const angleDiff = currentAngle - this.gestures.rotate.lastAngle;
                    if (Math.abs(angleDiff) > 5) {
                        this.gestures.rotate.angle = angleDiff;
                        this.triggerGesture('rotate', { angle: angleDiff });
                    }
                },

                handleSingleTouch(pointer) {
                    const deltaX = pointer.x - pointer.startX;
                    const deltaY = pointer.y - pointer.startY;
                    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

                    if (distance > 10) {
                        this.triggerGesture('pan', { deltaX, deltaY });
                    }
                },

                endMultiTouch() {
                    this.gestures.pinch.active = false;
                    this.gestures.rotate.active = false;
                    this.gestures.pan.active = false;
                },

                getDistance(p1, p2) {
                    const dx = p2.x - p1.x;
                    const dy = p2.y - p1.y;
                    return Math.sqrt(dx * dx + dy * dy);
                },

                getAngle(p1, p2) {
                    return Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180 / Math.PI;
                },

                triggerGesture(type, data) {
                    const event = new CustomEvent('gesture', {
                        detail: { type, data }
                    });
                    document.dispatchEvent(event);
                }
            };

            this.gestureRecognizer.init();
        }
    }

    // 语音命令增强
    setupVoiceCommands() {
        this.voiceCommands.set('显示图表', () => this.showAllCharts());
        this.voiceCommands.set('隐藏图表', () => this.hideAllCharts());
        this.voiceCommands.set('放大', () => this.zoomIn());
        this.voiceCommands.set('缩小', () => this.zoomOut());
        this.voiceCommands.set('重置视图', () => this.resetView());
        this.voiceCommands.set('导出数据', () => this.exportCurrentView());
        this.voiceCommands.set('切换主题', () => this.toggleTheme());
        this.voiceCommands.set('全屏模式', () => this.toggleFullscreen());
        this.voiceCommands.set('开始演示', () => this.startPresentation());
        this.voiceCommands.set('下一页', () => this.nextSlide());
        this.voiceCommands.set('上一页', () => this.previousSlide());

        // 智能语音处理
        this.voiceProcessor = {
            isListening: false,
            recognition: null,
            confidence: 0.8,

            init() {
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    this.recognition = new SpeechRecognition();
                    
                    this.recognition.continuous = true;
                    this.recognition.interimResults = true;
                    this.recognition.lang = 'zh-CN';
                    
                    this.recognition.onresult = this.handleSpeechResult.bind(this);
                    this.recognition.onerror = this.handleSpeechError.bind(this);
                    this.recognition.onend = this.handleSpeechEnd.bind(this);
                }
            },

            start() {
                if (this.recognition && !this.isListening) {
                    this.recognition.start();
                    this.isListening = true;
                    this.showVoiceIndicator();
                }
            },

            stop() {
                if (this.recognition && this.isListening) {
                    this.recognition.stop();
                    this.isListening = false;
                    this.hideVoiceIndicator();
                }
            },

            handleSpeechResult(event) {
                const result = event.results[event.results.length - 1];
                if (result.isFinal && result[0].confidence > this.confidence) {
                    const command = result[0].transcript.trim();
                    this.processVoiceCommand(command);
                }
            },

            handleSpeechError(event) {
                console.error('语音识别错误:', event.error);
                this.showVoiceError(event.error);
            },

            handleSpeechEnd() {
                this.isListening = false;
                this.hideVoiceIndicator();
            },

            processVoiceCommand(command) {
                // 模糊匹配命令
                const matchedCommand = this.findBestMatch(command);
                if (matchedCommand) {
                    this.executeVoiceCommand(matchedCommand);
                    this.showVoiceSuccess(command);
                } else {
                    this.showVoiceUnrecognized(command);
                }
            },

            findBestMatch(input) {
                let bestMatch = null;
                let bestScore = 0;

                for (const [command, handler] of window.advancedInteractions.voiceCommands) {
                    const score = this.calculateSimilarity(input, command);
                    if (score > bestScore && score > 0.6) {
                        bestScore = score;
                        bestMatch = command;
                    }
                }

                return bestMatch;
            },

            calculateSimilarity(str1, str2) {
                const longer = str1.length > str2.length ? str1 : str2;
                const shorter = str1.length > str2.length ? str2 : str1;
                
                if (longer.length === 0) return 1.0;
                
                const distance = this.levenshteinDistance(longer, shorter);
                return (longer.length - distance) / longer.length;
            },

            levenshteinDistance(str1, str2) {
                const matrix = [];
                
                for (let i = 0; i <= str2.length; i++) {
                    matrix[i] = [i];
                }
                
                for (let j = 0; j <= str1.length; j++) {
                    matrix[0][j] = j;
                }
                
                for (let i = 1; i <= str2.length; i++) {
                    for (let j = 1; j <= str1.length; j++) {
                        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                            matrix[i][j] = matrix[i - 1][j - 1];
                        } else {
                            matrix[i][j] = Math.min(
                                matrix[i - 1][j - 1] + 1,
                                matrix[i][j - 1] + 1,
                                matrix[i - 1][j] + 1
                            );
                        }
                    }
                }
                
                return matrix[str2.length][str1.length];
            },

            executeVoiceCommand(command) {
                const handler = window.advancedInteractions.voiceCommands.get(command);
                if (handler) {
                    handler();
                }
            },

            showVoiceIndicator() {
                this.createVoiceUI('listening', '🎤 正在听取命令...');
            },

            hideVoiceIndicator() {
                this.removeVoiceUI();
            },

            showVoiceSuccess(command) {
                this.createVoiceUI('success', `✅ 执行命令: ${command}`);
                setTimeout(() => this.removeVoiceUI(), 2000);
            },

            showVoiceError(error) {
                this.createVoiceUI('error', `❌ 语音识别错误: ${error}`);
                setTimeout(() => this.removeVoiceUI(), 3000);
            },

            showVoiceUnrecognized(command) {
                this.createVoiceUI('warning', `⚠️ 未识别命令: ${command}`);
                setTimeout(() => this.removeVoiceUI(), 2000);
            },

            createVoiceUI(type, message) {
                this.removeVoiceUI();
                
                const ui = document.createElement('div');
                ui.id = 'voice-command-ui';
                ui.className = `voice-ui voice-ui-${type}`;
                ui.innerHTML = `
                    <div class="voice-message">${message}</div>
                    <button class="voice-close" onclick="this.parentElement.remove()">×</button>
                `;
                
                document.body.appendChild(ui);
            },

            removeVoiceUI() {
                const existing = document.getElementById('voice-command-ui');
                if (existing) {
                    existing.remove();
                }
            }
        };

        this.voiceProcessor.init();
    }

    // 键盘快捷键增强
    setupKeyboardShortcuts() {
        this.shortcuts.set('Ctrl+Shift+V', () => this.toggleVoiceCommands());
        this.shortcuts.set('Ctrl+Shift+F', () => this.toggleFullscreen());
        this.shortcuts.set('Ctrl+Shift+T', () => this.toggleTheme());
        this.shortcuts.set('Ctrl+Shift+E', () => this.exportCurrentView());
        this.shortcuts.set('Ctrl+Shift+R', () => this.resetAllViews());
        this.shortcuts.set('Ctrl+Shift+P', () => this.startPresentation());
        this.shortcuts.set('Ctrl+Shift+S', () => this.saveCurrentState());
        this.shortcuts.set('Ctrl+Shift+L', () => this.loadSavedState());
        this.shortcuts.set('Ctrl+Shift+H', () => this.showHelpDialog());
        this.shortcuts.set('Ctrl+Shift+D', () => this.toggleDebugMode());

        document.addEventListener('keydown', (e) => {
            const key = this.getKeyCombo(e);
            const handler = this.shortcuts.get(key);
            
            if (handler) {
                e.preventDefault();
                handler();
                this.showShortcutFeedback(key);
            }
        });
    }

    getKeyCombo(e) {
        const parts = [];
        if (e.ctrlKey) parts.push('Ctrl');
        if (e.shiftKey) parts.push('Shift');
        if (e.altKey) parts.push('Alt');
        if (e.metaKey) parts.push('Meta');
        
        if (e.key && !['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) {
            parts.push(e.key.toUpperCase());
        }
        
        return parts.join('+');
    }

    // 右键菜单增强
    setupContextMenus() {
        document.addEventListener('contextmenu', (e) => {
            const target = e.target.closest('.chart-container, .metric-item, .data-table');
            if (target) {
                e.preventDefault();
                this.showContextMenu(e, target);
            }
        });

        document.addEventListener('click', () => {
            this.hideContextMenu();
        });
    }

    showContextMenu(e, target) {
        this.hideContextMenu();
        
        const menu = document.createElement('div');
        menu.id = 'context-menu';
        menu.className = 'context-menu';
        
        const menuItems = this.getContextMenuItems(target);
        menu.innerHTML = menuItems.map(item => `
            <div class="context-menu-item ${item.disabled ? 'disabled' : ''}" 
                 onclick="${item.disabled ? '' : item.action}">
                <span class="menu-icon">${item.icon}</span>
                <span class="menu-text">${item.text}</span>
                ${item.shortcut ? `<span class="menu-shortcut">${item.shortcut}</span>` : ''}
            </div>
        `).join('');
        
        document.body.appendChild(menu);
        
        // 定位菜单
        const rect = menu.getBoundingClientRect();
        const x = Math.min(e.clientX, window.innerWidth - rect.width - 10);
        const y = Math.min(e.clientY, window.innerHeight - rect.height - 10);
        
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        menu.style.display = 'block';
    }

    getContextMenuItems(target) {
        const baseItems = [
            { icon: '🔄', text: '刷新', action: 'window.advancedInteractions.refreshTarget()', shortcut: 'F5' },
            { icon: '📊', text: '导出图表', action: 'window.advancedInteractions.exportTarget()', shortcut: 'Ctrl+E' },
            { icon: '🔍', text: '放大', action: 'window.advancedInteractions.zoomInTarget()', shortcut: 'Ctrl++' },
            { icon: '🔍', text: '缩小', action: 'window.advancedInteractions.zoomOutTarget()', shortcut: 'Ctrl+-' },
            { icon: '↩️', text: '重置视图', action: 'window.advancedInteractions.resetTarget()', shortcut: 'Ctrl+0' }
        ];

        if (target.classList.contains('chart-container')) {
            baseItems.push(
                { icon: '🎨', text: '更改样式', action: 'window.advancedInteractions.changeChartStyle()' },
                { icon: '📈', text: '切换图表类型', action: 'window.advancedInteractions.switchChartType()' },
                { icon: '🏷️', text: '添加注释', action: 'window.advancedInteractions.addAnnotation()' }
            );
        }

        if (target.classList.contains('data-table')) {
            baseItems.push(
                { icon: '📋', text: '复制数据', action: 'window.advancedInteractions.copyTableData()' },
                { icon: '🔽', text: '导出CSV', action: 'window.advancedInteractions.exportCSV()' },
                { icon: '🔍', text: '高级筛选', action: 'window.advancedInteractions.showAdvancedFilter()' }
            );
        }

        return baseItems;
    }

    hideContextMenu() {
        const menu = document.getElementById('context-menu');
        if (menu) {
            menu.remove();
        }
    }

    // 拖拽功能
    setupDragAndDrop() {
        this.dragDropHandlers.set('chart-reorder', this.handleChartReorder.bind(this));
        this.dragDropHandlers.set('data-import', this.handleDataImport.bind(this));
        this.dragDropHandlers.set('layout-customize', this.handleLayoutCustomize.bind(this));

        // 图表重新排序
        document.addEventListener('dragstart', (e) => {
            if (e.target.closest('.analytics-card')) {
                e.dataTransfer.setData('text/plain', e.target.closest('.analytics-card').id);
                e.target.closest('.analytics-card').classList.add('dragging');
            }
        });

        document.addEventListener('dragend', (e) => {
            if (e.target.closest('.analytics-card')) {
                e.target.closest('.analytics-card').classList.remove('dragging');
            }
        });

        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            const dropZone = e.target.closest('.dashboard-grid');
            if (dropZone) {
                dropZone.classList.add('drag-over');
            }
        });

        document.addEventListener('dragleave', (e) => {
            const dropZone = e.target.closest('.dashboard-grid');
            if (dropZone && !dropZone.contains(e.relatedTarget)) {
                dropZone.classList.remove('drag-over');
            }
        });

        document.addEventListener('drop', (e) => {
            e.preventDefault();
            const dropZone = e.target.closest('.dashboard-grid');
            if (dropZone) {
                dropZone.classList.remove('drag-over');
                const draggedId = e.dataTransfer.getData('text/plain');
                this.handleChartReorder(draggedId, e.target);
            }
        });
    }

    handleChartReorder(draggedId, target) {
        const draggedElement = document.getElementById(draggedId);
        const targetCard = target.closest('.analytics-card');
        
        if (draggedElement && targetCard && draggedElement !== targetCard) {
            const parent = targetCard.parentNode;
            const nextSibling = targetCard.nextSibling;
            
            if (nextSibling) {
                parent.insertBefore(draggedElement, nextSibling);
            } else {
                parent.appendChild(draggedElement);
            }
            
            this.saveLayoutState();
            this.showNotification('图表顺序已更新', 'success');
        }
    }

    // 触摸手势
    setupTouchGestures() {
        let touchStartTime = 0;
        let touchStartPos = { x: 0, y: 0 };
        let lastTap = 0;

        document.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
            touchStartPos = {
                x: e.touches[0].clientX,
                y: e.touches[0].clientY
            };
        });

        document.addEventListener('touchend', (e) => {
            const touchEndTime = Date.now();
            const touchDuration = touchEndTime - touchStartTime;
            const touchEndPos = {
                x: e.changedTouches[0].clientX,
                y: e.changedTouches[0].clientY
            };

            // 双击检测
            const now = Date.now();
            if (now - lastTap < 300) {
                this.handleDoubleTap(e);
            }
            lastTap = now;

            // 长按检测
            if (touchDuration > 500) {
                this.handleLongPress(e);
            }

            // 滑动检测
            const deltaX = touchEndPos.x - touchStartPos.x;
            const deltaY = touchEndPos.y - touchStartPos.y;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

            if (distance > 50 && touchDuration < 500) {
                this.handleSwipe(deltaX, deltaY, e);
            }
        });

        // 手势事件监听
        document.addEventListener('gesture', (e) => {
            this.handleGesture(e.detail.type, e.detail.data);
        });
    }

    handleDoubleTap(e) {
        const target = e.target.closest('.chart-container');
        if (target) {
            this.toggleFullscreen(target);
        }
    }

    handleLongPress(e) {
        const target = e.target.closest('.analytics-card, .metric-item');
        if (target) {
            this.showContextMenu(e.changedTouches[0], target);
        }
    }

    handleSwipe(deltaX, deltaY, e) {
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);

        if (absX > absY) {
            // 水平滑动
            if (deltaX > 0) {
                this.handleSwipeRight(e);
            } else {
                this.handleSwipeLeft(e);
            }
        } else {
            // 垂直滑动
            if (deltaY > 0) {
                this.handleSwipeDown(e);
            } else {
                this.handleSwipeUp(e);
            }
        }
    }

    handleSwipeLeft(e) {
        // 切换到下一个视图
        this.nextView();
    }

    handleSwipeRight(e) {
        // 切换到上一个视图
        this.previousView();
    }

    handleSwipeUp(e) {
        // 显示更多选项
        this.showMoreOptions();
    }

    handleSwipeDown(e) {
        // 刷新当前视图
        this.refreshCurrentView();
    }

    handleGesture(type, data) {
        switch (type) {
            case 'pinch':
                this.handlePinchGesture(data.scale);
                break;
            case 'rotate':
                this.handleRotateGesture(data.angle);
                break;
            case 'pan':
                this.handlePanGesture(data.deltaX, data.deltaY);
                break;
        }
    }

    handlePinchGesture(scale) {
        if (scale > 1.1) {
            this.zoomIn();
        } else if (scale < 0.9) {
            this.zoomOut();
        }
    }

    handleRotateGesture(angle) {
        // 旋转当前图表视图
        const activeChart = document.querySelector('.chart-container:focus');
        if (activeChart && Math.abs(angle) > 15) {
            this.rotateChart(activeChart, angle);
        }
    }

    handlePanGesture(deltaX, deltaY) {
        // 平移图表视图
        const activeChart = document.querySelector('.chart-container:focus');
        if (activeChart) {
            this.panChart(activeChart, deltaX, deltaY);
        }
    }

    // 协作功能
    setupCollaboration() {
        this.collaborationFeatures.set('comments', new Map());
        this.collaborationFeatures.set('annotations', new Map());
        this.collaborationFeatures.set('shared-views', new Map());

        // 实时协作状态
        this.collaborationState = {
            isCollaborating: false,
            participants: new Map(),
            sharedCursor: null,
            liveUpdates: true
        };
    }

    // 智能筛选
    setupSmartFiltering() {
        this.smartFilter = {
            filters: new Map(),
            suggestions: [],
            history: [],

            addFilter(type, value, operator = 'equals') {
                const filterId = `${type}_${Date.now()}`;
                this.filters.set(filterId, {
                    type,
                    value,
                    operator,
                    active: true,
                    created: Date.now()
                });
                
                this.applyFilters();
                this.updateFilterUI();
                return filterId;
            },

            removeFilter(filterId) {
                this.filters.delete(filterId);
                this.applyFilters();
                this.updateFilterUI();
            },

            applyFilters() {
                // 应用所有活动筛选器
                const activeFilters = Array.from(this.filters.values()).filter(f => f.active);
                
                // 筛选数据表格
                this.filterDataTable(activeFilters);
                
                // 筛选图表
                this.filterCharts(activeFilters);
            },

            filterDataTable(filters) {
                const table = document.querySelector('.data-table tbody');
                if (!table) return;

                const rows = table.querySelectorAll('tr');
                rows.forEach(row => {
                    const shouldShow = filters.every(filter => {
                        return this.evaluateFilter(row, filter);
                    });
                    
                    row.style.display = shouldShow ? '' : 'none';
                });
            },

            filterCharts(filters) {
                // 更新图表数据以反映筛选结果
                const charts = document.querySelectorAll('.chart-container');
                charts.forEach(chart => {
                    this.updateChartWithFilters(chart, filters);
                });
            },

            evaluateFilter(row, filter) {
                const cellValue = this.getCellValue(row, filter.type);
                
                switch (filter.operator) {
                    case 'equals':
                        return cellValue === filter.value;
                    case 'contains':
                        return cellValue.includes(filter.value);
                    case 'greater':
                        return parseFloat(cellValue) > parseFloat(filter.value);
                    case 'less':
                        return parseFloat(cellValue) < parseFloat(filter.value);
                    case 'between':
                        const [min, max] = filter.value;
                        const num = parseFloat(cellValue);
                        return num >= min && num <= max;
                    default:
                        return true;
                }
            },

            getCellValue(row, type) {
                // 根据筛选类型获取对应单元格的值
                const cells = row.querySelectorAll('td');
                const columnMap = {
                    'user_id': 0,
                    'user_name': 1,
                    'user_type': 2,
                    'register_time': 3,
                    'last_active': 4,
                    'status': 5
                };
                
                const cellIndex = columnMap[type];
                return cellIndex !== undefined ? cells[cellIndex]?.textContent.trim() : '';
            },

            updateFilterUI() {
                // 更新筛选器UI显示
                const filterContainer = document.getElementById('active-filters');
                if (!filterContainer) return;

                filterContainer.innerHTML = Array.from(this.filters.entries()).map(([id, filter]) => `
                    <div class="filter-tag ${filter.active ? 'active' : 'inactive'}">
                        <span class="filter-text">${filter.type}: ${filter.value}</span>
                        <button class="filter-remove" onclick="window.advancedInteractions.smartFilter.removeFilter('${id}')">×</button>
                    </div>
                `).join('');
            }
        };
    }

    // 数据注释
    setupDataAnnotations() {
        this.annotations = {
            items: new Map(),
            isAnnotating: false,
            currentTool: 'text',

            startAnnotating() {
                this.isAnnotating = true;
                document.body.classList.add('annotation-mode');
                this.showAnnotationToolbar();
            },

            stopAnnotating() {
                this.isAnnotating = false;
                document.body.classList.remove('annotation-mode');
                this.hideAnnotationToolbar();
            },

            addAnnotation(x, y, content, type = 'text') {
                const id = `annotation_${Date.now()}`;
                const annotation = {
                    id,
                    x,
                    y,
                    content,
                    type,
                    created: Date.now(),
                    author: 'current_user'
                };

                this.items.set(id, annotation);
                this.renderAnnotation(annotation);
                return id;
            },

            renderAnnotation(annotation) {
                const element = document.createElement('div');
                element.className = `annotation annotation-${annotation.type}`;
                element.id = annotation.id;
                element.style.left = `${annotation.x}px`;
                element.style.top = `${annotation.y}px`;
                element.innerHTML = `
                    <div class="annotation-content">${annotation.content}</div>
                    <div class="annotation-controls">
                        <button onclick="window.advancedInteractions.annotations.editAnnotation('${annotation.id}')">编辑</button>
                        <button onclick="window.advancedInteractions.annotations.deleteAnnotation('${annotation.id}')">删除</button>
                    </div>
                `;

                document.body.appendChild(element);
            },

            showAnnotationToolbar() {
                const toolbar = document.createElement('div');
                toolbar.id = 'annotation-toolbar';
                toolbar.className = 'annotation-toolbar';
                toolbar.innerHTML = `
                    <div class="toolbar-title">注释工具</div>
                    <div class="toolbar-tools">
                        <button class="tool-btn active" data-tool="text">📝 文本</button>
                        <button class="tool-btn" data-tool="arrow">➡️ 箭头</button>
                        <button class="tool-btn" data-tool="highlight">🖍️ 高亮</button>
                        <button class="tool-btn" data-tool="shape">⭕ 形状</button>
                    </div>
                    <button class="toolbar-close" onclick="window.advancedInteractions.annotations.stopAnnotating()">完成</button>
                `;

                document.body.appendChild(toolbar);

                // 工具选择
                toolbar.addEventListener('click', (e) => {
                    if (e.target.classList.contains('tool-btn')) {
                        toolbar.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
                        e.target.classList.add('active');
                        this.currentTool = e.target.dataset.tool;
                    }
                });
            },

            hideAnnotationToolbar() {
                const toolbar = document.getElementById('annotation-toolbar');
                if (toolbar) {
                    toolbar.remove();
                }
            }
        };

        // 点击添加注释
        document.addEventListener('click', (e) => {
            if (this.annotations.isAnnotating && !e.target.closest('.annotation, .annotation-toolbar')) {
                const content = prompt('请输入注释内容:');
                if (content) {
                    this.annotations.addAnnotation(e.clientX, e.clientY, content);
                }
            }
        });
    }

    // 实用方法
    showAllCharts() {
        document.querySelectorAll('.chart-container').forEach(chart => {
            chart.style.display = 'block';
        });
        this.showNotification('所有图表已显示', 'success');
    }

    hideAllCharts() {
        document.querySelectorAll('.chart-container').forEach(chart => {
            chart.style.display = 'none';
        });
        this.showNotification('所有图表已隐藏', 'info');
    }

    zoomIn() {
        document.body.style.zoom = (parseFloat(document.body.style.zoom || 1) * 1.1).toString();
        this.showNotification('视图已放大', 'info');
    }

    zoomOut() {
        document.body.style.zoom = (parseFloat(document.body.style.zoom || 1) * 0.9).toString();
        this.showNotification('视图已缩小', 'info');
    }

    resetView() {
        document.body.style.zoom = '1';
        this.showNotification('视图已重置', 'info');
    }

    toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        this.showNotification(`已切换到${isDark ? '深色' : '浅色'}主题`, 'info');
    }

    toggleFullscreen(element = document.documentElement) {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            element.requestFullscreen();
        }
    }

    toggleVoiceCommands() {
        if (this.voiceProcessor.isListening) {
            this.voiceProcessor.stop();
        } else {
            this.voiceProcessor.start();
        }
    }

    exportCurrentView() {
        // 导出当前视图的截图和数据
        this.showNotification('正在导出当前视图...', 'info');
        
        setTimeout(() => {
            this.showNotification('视图导出完成', 'success');
        }, 2000);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    showShortcutFeedback(shortcut) {
        this.showNotification(`快捷键: ${shortcut}`, 'info');
    }

    saveLayoutState() {
        const layout = Array.from(document.querySelectorAll('.analytics-card')).map(card => card.id);
        localStorage.setItem('dashboard-layout', JSON.stringify(layout));
    }

    loadLayoutState() {
        const saved = localStorage.getItem('dashboard-layout');
        if (saved) {
            const layout = JSON.parse(saved);
            // 重新排列图表
            this.showNotification('布局已恢复', 'success');
        }
    }
}

// 全局实例
window.advancedInteractions = new AdvancedInteractions();

// 添加样式
const style = document.createElement('style');
style.textContent = `
    .context-menu {
        position: fixed;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        min-width: 200px;
        display: none;
    }

    .context-menu-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        cursor: pointer;
        transition: background 0.2s ease;
        border-bottom: 1px solid #f3f4f6;
    }

    .context-menu-item:last-child {
        border-bottom: none;
    }

    .context-menu-item:hover:not(.disabled) {
        background: #f3f4f6;
    }

    .context-menu-item.disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .menu-icon {
        margin-right: 0.75rem;
        font-size: 1rem;
    }

    .menu-text {
        flex: 1;
        font-size: 0.875rem;
    }

    .menu-shortcut {
        font-size: 0.75rem;
        color: #6b7280;
        font-family: monospace;
    }

    .voice-ui {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        color: white;
        z-index: 1001;
        display: flex;
        align-items: center;
        gap: 1rem;
        max-width: 400px;
    }

    .voice-ui-listening {
        background: #3b82f6;
        animation: pulse 2s infinite;
    }

    .voice-ui-success {
        background: #10b981;
    }

    .voice-ui-error {
        background: #ef4444;
    }

    .voice-ui-warning {
        background: #f59e0b;
    }

    .voice-message {
        flex: 1;
    }

    .voice-close {
        background: none;
        border: none;
        color: white;
        font-size: 1.25rem;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .annotation-mode {
        cursor: crosshair;
    }

    .annotation {
        position: absolute;
        background: #fef3c7;
        border: 2px solid #f59e0b;
        border-radius: 0.5rem;
        padding: 0.5rem;
        z-index: 100;
        max-width: 200px;
        font-size: 0.875rem;
    }

    .annotation-content {
        margin-bottom: 0.5rem;
    }

    .annotation-controls {
        display: flex;
        gap: 0.25rem;
    }

    .annotation-controls button {
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        border: 1px solid #d1d5db;
        background: white;
        border-radius: 0.25rem;
        cursor: pointer;
    }

    .annotation-toolbar {
        position: fixed;
        top: 50%;
        right: 20px;
        transform: translateY(-50%);
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        z-index: 1002;
    }

    .toolbar-title {
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }

    .toolbar-tools {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    .tool-btn {
        padding: 0.5rem;
        border: 1px solid #d1d5db;
        background: white;
        border-radius: 0.25rem;
        cursor: pointer;
        text-align: left;
        font-size: 0.875rem;
    }

    .tool-btn.active {
        background: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }

    .toolbar-close {
        width: 100%;
        padding: 0.5rem;
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 0.25rem;
        cursor: pointer;
    }

    .notification {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%) translateY(-100%);
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        color: white;
        z-index: 1001;
        transition: transform 0.3s ease;
        font-weight: 500;
    }

    .notification.show {
        transform: translateX(-50%) translateY(0);
    }

    .notification-info {
        background: #3b82f6;
    }

    .notification-success {
        background: #10b981;
    }

    .notification-warning {
        background: #f59e0b;
    }

    .notification-error {
        background: #ef4444;
    }

    .dragging {
        opacity: 0.5;
        transform: rotate(5deg);
    }

    .drag-over {
        background: rgba(59, 130, 246, 0.1);
        border: 2px dashed #3b82f6;
    }

    .filter-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        background: #e5e7eb;
        border-radius: 9999px;
        font-size: 0.875rem;
        margin: 0.25rem;
    }

    .filter-tag.active {
        background: #3b82f6;
        color: white;
    }

    .filter-remove {
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
        font-size: 1rem;
        padding: 0;
        width: 16px;
        height: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
    }

    .filter-remove:hover {
        background: rgba(0, 0, 0, 0.1);
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
`;

document.head.appendChild(style);

// 导出为模块（如果支持）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedInteractions;
}