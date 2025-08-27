/**
 * Lawsker 高级数据可视化组件库
 * 专为管理后台设计的美观易懂的数据可视化解决方案
 */

class LawskerDataViz {
    constructor() {
        this.charts = new Map();
        this.themes = {
            default: {
                primaryColor: '#2563eb',
                secondaryColor: '#7c3aed',
                successColor: '#059669',
                warningColor: '#d97706',
                errorColor: '#dc2626',
                gradients: {
                    primary: ['#667eea', '#764ba2'],
                    secondary: ['#f093fb', '#f5576c'],
                    success: ['#4facfe', '#00f2fe'],
                    warning: ['#fa709a', '#fee140']
                }
            }
        };
        this.currentTheme = this.themes.default;
        this.animationDuration = 800;
        this.init();
    }

    init() {
        this.setupGlobalStyles();
        this.registerEventListeners();
    }

    setupGlobalStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .lawsker-chart-container {
                position: relative;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }

            .lawsker-chart-container:hover {
                transform: translateY(-2px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
            }

            .lawsker-chart-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 2px solid #f3f4f6;
            }

            .lawsker-chart-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #374151;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .lawsker-chart-subtitle {
                font-size: 0.875rem;
                color: #6b7280;
                margin-top: 0.25rem;
            }

            .lawsker-chart-controls {
                display: flex;
                gap: 0.5rem;
                align-items: center;
            }

            .lawsker-control-btn {
                padding: 0.5rem 1rem;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 0.375rem;
                cursor: pointer;
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 0.25rem;
            }

            .lawsker-control-btn:hover {
                background: #f9fafb;
                border-color: #9ca3af;
            }

            .lawsker-control-btn.active {
                background: #2563eb;
                color: white;
                border-color: #2563eb;
            }

            .lawsker-chart-canvas {
                position: relative;
                height: 400px;
                width: 100%;
            }

            .lawsker-loading {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
            }

            .lawsker-spinner {
                width: 2rem;
                height: 2rem;
                border: 2px solid #e5e7eb;
                border-top: 2px solid #2563eb;
                border-radius: 50%;
                animation: lawsker-spin 1s linear infinite;
            }

            @keyframes lawsker-spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .lawsker-tooltip {
                position: absolute;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 0.75rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.875rem;
                pointer-events: none;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.2s ease;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                backdrop-filter: blur(10px);
            }

            .lawsker-tooltip.show {
                opacity: 1;
            }

            .lawsker-tooltip::after {
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border: 5px solid transparent;
                border-top-color: rgba(0, 0, 0, 0.9);
            }

            .lawsker-legend {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid #e5e7eb;
            }

            .lawsker-legend-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                color: #6b7280;
            }

            .lawsker-legend-color {
                width: 1rem;
                height: 1rem;
                border-radius: 0.25rem;
                flex-shrink: 0;
            }

            .lawsker-metric-card {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.7));
                backdrop-filter: blur(10px);
                border-radius: 1rem;
                padding: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .lawsker-metric-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }

            .lawsker-metric-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            }

            .lawsker-metric-value {
                font-size: 2rem;
                font-weight: 700;
                color: #1f2937;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .lawsker-metric-label {
                font-size: 0.875rem;
                color: #6b7280;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .lawsker-metric-change {
                display: flex;
                align-items: center;
                gap: 0.25rem;
                font-size: 0.875rem;
                font-weight: 500;
                margin-top: 0.5rem;
            }

            .lawsker-metric-change.positive {
                color: #059669;
            }

            .lawsker-metric-change.negative {
                color: #dc2626;
            }

            .lawsker-data-table {
                background: white;
                border-radius: 1rem;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border: 1px solid #e5e7eb;
            }

            .lawsker-table-header {
                background: linear-gradient(135deg, #f8fafc, #f1f5f9);
                padding: 1rem 1.5rem;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .lawsker-table-title {
                font-size: 1.125rem;
                font-weight: 600;
                color: #374151;
            }

            .lawsker-table-search {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                border: 1px solid #d1d5db;
                border-radius: 0.5rem;
                background: white;
            }

            .lawsker-table-search input {
                border: none;
                outline: none;
                font-size: 0.875rem;
                width: 200px;
            }

            .lawsker-table {
                width: 100%;
                border-collapse: collapse;
            }

            .lawsker-table th {
                background: #f9fafb;
                padding: 1rem 1.5rem;
                text-align: left;
                font-weight: 600;
                color: #374151;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid #e5e7eb;
            }

            .lawsker-table td {
                padding: 1rem 1.5rem;
                border-bottom: 1px solid #f3f4f6;
                color: #6b7280;
            }

            .lawsker-table tr:hover {
                background: #f9fafb;
            }

            .lawsker-status-badge {
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .lawsker-status-success {
                background: #dcfce7;
                color: #166534;
            }

            .lawsker-status-warning {
                background: #fef3c7;
                color: #92400e;
            }

            .lawsker-status-error {
                background: #fee2e2;
                color: #991b1b;
            }

            .lawsker-status-info {
                background: #dbeafe;
                color: #1e40af;
            }

            @media (max-width: 768px) {
                .lawsker-chart-header {
                    flex-direction: column;
                    gap: 1rem;
                    align-items: flex-start;
                }

                .lawsker-chart-controls {
                    width: 100%;
                    justify-content: flex-start;
                }

                .lawsker-table-header {
                    flex-direction: column;
                    gap: 1rem;
                    align-items: flex-start;
                }

                .lawsker-table-search input {
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(style);
    }

    registerEventListeners() {
        window.addEventListener('resize', () => {
            this.charts.forEach(chart => {
                if (chart.resize) {
                    chart.resize();
                }
            });
        });
    }

    // 创建实时数据流图表
    createRealtimeChart(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        const chartWrapper = this.createChartWrapper(container, {
            title: options.title || '实时数据监控',
            subtitle: options.subtitle || '数据每5秒自动更新',
            controls: [
                { text: '暂停', action: 'pause', icon: 'pause' },
                { text: '重置', action: 'reset', icon: 'refresh-cw' }
            ]
        });

        const canvas = chartWrapper.querySelector('.lawsker-chart-canvas canvas');
        const ctx = canvas.getContext('2d');

        const data = {
            labels: [],
            datasets: [{
                label: options.label || '实时数据',
                data: [],
                borderColor: this.currentTheme.primaryColor,
                backgroundColor: this.createGradient(ctx, this.currentTheme.gradients.primary),
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: this.currentTheme.primaryColor,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        };

        const chart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: this.animationDuration,
                    easing: 'easeInOutQuart'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.currentTheme.primaryColor,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return '时间: ' + context[0].label;
                            },
                            label: function(context) {
                                return options.label + ': ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6b7280',
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        grid: {
                            color: '#f3f4f6'
                        },
                        ticks: {
                            color: '#6b7280',
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });

        // 实时数据更新
        let isPaused = false;
        const updateInterval = setInterval(() => {
            if (!isPaused) {
                const now = new Date();
                const timeLabel = now.toLocaleTimeString();
                const value = Math.floor(Math.random() * 100) + 50;

                data.labels.push(timeLabel);
                data.datasets[0].data.push(value);

                // 保持最近50个数据点
                if (data.labels.length > 50) {
                    data.labels.shift();
                    data.datasets[0].data.shift();
                }

                chart.update('none');
            }
        }, 5000);

        // 控制按钮事件
        chartWrapper.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'pause') {
                isPaused = !isPaused;
                e.target.textContent = isPaused ? '继续' : '暂停';
            } else if (e.target.dataset.action === 'reset') {
                data.labels = [];
                data.datasets[0].data = [];
                chart.update();
            }
        });

        this.charts.set(containerId, { chart, updateInterval });
        return chart;
    }

    // 创建多维度分析图表
    createMultiDimensionChart(containerId, chartData, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        const chartWrapper = this.createChartWrapper(container, {
            title: options.title || '多维度数据分析',
            subtitle: options.subtitle || '支持多个维度的数据对比分析',
            controls: [
                { text: '柱状图', action: 'bar', icon: 'bar-chart-2' },
                { text: '折线图', action: 'line', icon: 'trending-up' },
                { text: '面积图', action: 'area', icon: 'activity' }
            ]
        });

        const chartDom = chartWrapper.querySelector('.lawsker-chart-canvas');
        chartDom.innerHTML = '<div id="' + containerId + '_echarts"></div>';
        const echartsContainer = chartDom.querySelector('#' + containerId + '_echarts');
        echartsContainer.style.height = '100%';
        
        const myChart = echarts.init(echartsContainer);

        const defaultOption = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross',
                    crossStyle: {
                        color: '#999'
                    }
                },
                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                borderColor: this.currentTheme.primaryColor,
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                }
            },
            legend: {
                data: chartData.series.map(s => s.name),
                textStyle: {
                    color: '#6b7280'
                },
                top: 10
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: chartData.categories,
                axisPointer: {
                    type: 'shadow'
                },
                axisLine: {
                    lineStyle: {
                        color: '#e5e7eb'
                    }
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#6b7280'
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#6b7280',
                    formatter: function(value) {
                        return value.toLocaleString();
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f3f4f6'
                    }
                }
            },
            series: chartData.series.map((serie, index) => ({
                name: serie.name,
                type: 'bar',
                data: serie.data,
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: this.currentTheme.gradients.primary[0] },
                        { offset: 1, color: this.currentTheme.gradients.primary[1] }
                    ])
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }))
        };

        myChart.setOption(defaultOption);

        // 图表类型切换
        chartWrapper.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (['bar', 'line', 'area'].includes(action)) {
                // 更新活动状态
                chartWrapper.querySelectorAll('.lawsker-control-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                e.target.classList.add('active');

                // 更新图表类型
                const newOption = { ...defaultOption };
                newOption.series = chartData.series.map((serie, index) => ({
                    ...newOption.series[index],
                    type: action === 'area' ? 'line' : action,
                    areaStyle: action === 'area' ? {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: this.currentTheme.gradients.primary[0] + '40' },
                            { offset: 1, color: this.currentTheme.gradients.primary[1] + '10' }
                        ])
                    } : undefined,
                    smooth: action === 'line' || action === 'area'
                }));

                myChart.setOption(newOption, true);
            }
        });

        this.charts.set(containerId, myChart);
        return myChart;
    }

    // 创建智能仪表盘
    createSmartDashboard(containerId, metrics, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        container.innerHTML = '';
        container.className = 'lawsker-dashboard-grid';
        
        const style = document.createElement('style');
        style.textContent = `
            .lawsker-dashboard-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
        `;
        document.head.appendChild(style);

        metrics.forEach((metric, index) => {
            const metricCard = this.createMetricCard(metric, options);
            container.appendChild(metricCard);
        });

        // 自动刷新
        if (options.autoRefresh) {
            setInterval(() => {
                this.updateDashboardMetrics(containerId, metrics);
            }, options.refreshInterval || 30000);
        }

        return container;
    }

    // 创建交互式数据表格
    createInteractiveTable(containerId, tableData, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        const tableWrapper = document.createElement('div');
        tableWrapper.className = 'lawsker-data-table';

        const header = document.createElement('div');
        header.className = 'lawsker-table-header';
        header.innerHTML = `
            <h3 class="lawsker-table-title">${options.title || '数据表格'}</h3>
            <div class="lawsker-table-search">
                <i data-feather="search"></i>
                <input type="text" placeholder="搜索..." id="${containerId}_search">
            </div>
        `;

        const tableContainer = document.createElement('div');
        tableContainer.style.overflowX = 'auto';

        const table = document.createElement('table');
        table.className = 'lawsker-table';

        // 创建表头
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        tableData.columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = column.title;
            th.style.cursor = 'pointer';
            th.addEventListener('click', () => {
                this.sortTable(table, column.key, tableData.data);
            });
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);

        // 创建表体
        const tbody = document.createElement('tbody');
        tbody.id = containerId + '_tbody';
        this.renderTableRows(tbody, tableData.data, tableData.columns);

        table.appendChild(thead);
        table.appendChild(tbody);
        tableContainer.appendChild(table);

        tableWrapper.appendChild(header);
        tableWrapper.appendChild(tableContainer);
        container.appendChild(tableWrapper);

        // 搜索功能
        const searchInput = header.querySelector('input');
        searchInput.addEventListener('input', (e) => {
            this.filterTable(tbody, tableData.data, tableData.columns, e.target.value);
        });

        // 初始化图标
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        return table;
    }

    // 辅助方法
    createChartWrapper(container, config) {
        container.innerHTML = '';
        container.className = 'lawsker-chart-container';

        const header = document.createElement('div');
        header.className = 'lawsker-chart-header';

        const titleSection = document.createElement('div');
        titleSection.innerHTML = `
            <h3 class="lawsker-chart-title">
                ${config.icon ? `<i data-feather="${config.icon}"></i>` : ''}
                ${config.title}
            </h3>
            ${config.subtitle ? `<p class="lawsker-chart-subtitle">${config.subtitle}</p>` : ''}
        `;

        const controls = document.createElement('div');
        controls.className = 'lawsker-chart-controls';
        
        if (config.controls) {
            config.controls.forEach((control, index) => {
                const btn = document.createElement('button');
                btn.className = 'lawsker-control-btn' + (index === 0 ? ' active' : '');
                btn.dataset.action = control.action;
                btn.innerHTML = `
                    ${control.icon ? `<i data-feather="${control.icon}"></i>` : ''}
                    ${control.text}
                `;
                controls.appendChild(btn);
            });
        }

        header.appendChild(titleSection);
        header.appendChild(controls);

        const chartCanvas = document.createElement('div');
        chartCanvas.className = 'lawsker-chart-canvas';
        chartCanvas.innerHTML = '<canvas></canvas>';

        container.appendChild(header);
        container.appendChild(chartCanvas);

        // 初始化图标
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        return container;
    }

    createGradient(ctx, colors) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, colors[0] + '40');
        gradient.addColorStop(1, colors[1] + '10');
        return gradient;
    }

    createMetricCard(metric, options) {
        const card = document.createElement('div');
        card.className = 'lawsker-metric-card';

        const changeClass = metric.change >= 0 ? 'positive' : 'negative';
        const changeIcon = metric.change >= 0 ? 'trending-up' : 'trending-down';

        card.innerHTML = `
            <div class="lawsker-metric-value">
                ${metric.icon ? `<i data-feather="${metric.icon}" style="color: ${this.currentTheme.primaryColor};"></i>` : ''}
                ${metric.value}
            </div>
            <div class="lawsker-metric-label">${metric.label}</div>
            <div class="lawsker-metric-change ${changeClass}">
                <i data-feather="${changeIcon}"></i>
                <span>${Math.abs(metric.change)}% ${metric.period || '本月'}</span>
            </div>
        `;

        // 初始化图标
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        return card;
    }

    renderTableRows(tbody, data, columns) {
        tbody.innerHTML = '';
        data.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(column => {
                const td = document.createElement('td');
                let value = row[column.key];
                
                if (column.render) {
                    value = column.render(value, row);
                } else if (column.type === 'status') {
                    value = `<span class="lawsker-status-badge lawsker-status-${value}">${value}</span>`;
                } else if (column.type === 'date') {
                    value = new Date(value).toLocaleDateString('zh-CN');
                }
                
                td.innerHTML = value;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    sortTable(table, key, data) {
        // 实现表格排序逻辑
        console.log('Sorting by:', key);
    }

    filterTable(tbody, data, columns, searchTerm) {
        const filteredData = data.filter(row => {
            return columns.some(column => {
                const value = row[column.key];
                return String(value).toLowerCase().includes(searchTerm.toLowerCase());
            });
        });
        this.renderTableRows(tbody, filteredData, columns);
    }

    updateDashboardMetrics(containerId, metrics) {
        // 实现仪表盘指标更新逻辑
        console.log('Updating dashboard metrics for:', containerId);
    }

    // 销毁图表
    destroy(containerId) {
        const chart = this.charts.get(containerId);
        if (chart) {
            if (chart.updateInterval) {
                clearInterval(chart.updateInterval);
            }
            if (chart.chart && chart.chart.destroy) {
                chart.chart.destroy();
            } else if (chart.dispose) {
                chart.dispose();
            }
            this.charts.delete(containerId);
        }
    }

    // 导出数据
    exportData(containerId, format = 'csv') {
        console.log(`Exporting data from ${containerId} as ${format}`);
        // 实现数据导出功能
    }

    // 设置主题
    setTheme(themeName) {
        if (this.themes[themeName]) {
            this.currentTheme = this.themes[themeName];
            // 重新渲染所有图表
            this.charts.forEach((chart, id) => {
                // 重新应用主题
            });
        }
    }
}

// 全局实例
window.LawskerDataViz = new LawskerDataViz();

// 导出为模块（如果支持）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LawskerDataViz;
}