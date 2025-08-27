/**
 * Lawsker AI智能助手系统
 * 实现自然语言交互和智能数据分析
 */

class LawskerAIAssistant {
    constructor() {
        this.isActive = false;
        this.conversationHistory = [];
        this.userPreferences = new Map();
        this.dataContext = new Map();
        this.insights = [];
        this.init();
    }

    init() {
        this.setupUI();
        this.setupNaturalLanguageProcessor();
        this.setupDataAnalyzer();
        this.setupPersonalizationEngine();
        this.startContextualAnalysis();
    }

    setupUI() {
        // 创建AI助手界面
        const aiContainer = document.createElement('div');
        aiContainer.id = 'ai-assistant';
        aiContainer.className = 'ai-assistant-container';
        aiContainer.innerHTML = `
            <div class="ai-header">
                <div class="ai-avatar">🤖</div>
                <div class="ai-title">Lawsker AI助手</div>
                <button class="ai-toggle" onclick="window.aiAssistant.toggle()">
                    <i data-feather="minimize-2"></i>
                </button>
            </div>
            <div class="ai-chat-area" id="aiChatArea">
                <div class="ai-welcome">
                    <p>👋 您好！我是您的智能数据分析助手。</p>
                    <p>您可以：</p>
                    <ul>
                        <li>🗣️ 用自然语言询问数据问题</li>
                        <li>📊 请我分析数据趋势</li>
                        <li>💡 获取智能洞察建议</li>
                        <li>🎨 让我推荐最佳图表类型</li>
                    </ul>
                </div>
            </div>
            <div class="ai-input-area">
                <input type="text" id="aiInput" placeholder="问我任何关于数据的问题..." />
                <button onclick="window.aiAssistant.sendMessage()" class="ai-send-btn">
                    <i data-feather="send"></i>
                </button>
            </div>
            <div class="ai-suggestions" id="aiSuggestions">
                <button onclick="window.aiAssistant.quickQuery('用户增长趋势如何？')">用户增长趋势如何？</button>
                <button onclick="window.aiAssistant.quickQuery('哪个律师等级最多？')">哪个律师等级最多？</button>
                <button onclick="window.aiAssistant.quickQuery('推荐最佳图表类型')">推荐最佳图表类型</button>
            </div>
        `;
        
        document.body.appendChild(aiContainer);
        
        // 设置输入事件
        document.getElementById('aiInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    setupNaturalLanguageProcessor() {
        this.nlp = {
            // 意图识别
            intents: {
                'data_query': ['显示', '查看', '分析', '统计', '多少', '如何'],
                'chart_recommendation': ['推荐', '建议', '最佳', '合适', '图表类型'],
                'trend_analysis': ['趋势', '变化', '增长', '下降', '波动'],
                'comparison': ['比较', '对比', '差异', '相比'],
                'prediction': ['预测', '预计', '未来', '趋势'],
                'insight': ['洞察', '发现', '问题', '机会', '建议']
            },

            // 实体识别
            entities: {
                'metrics': ['用户', '律师', '案件', '收入', '满意度', '转化率'],
                'time_periods': ['今天', '昨天', '本周', '上周', '本月', '上月', '今年'],
                'chart_types': ['柱状图', '折线图', '饼图', '散点图', '热力图', '雷达图']
            },

            processQuery(query) {
                const intent = this.detectIntent(query);
                const entities = this.extractEntities(query);
                return { intent, entities, query };
            },

            detectIntent(query) {
                for (const [intent, keywords] of Object.entries(this.intents)) {
                    if (keywords.some(keyword => query.includes(keyword))) {
                        return intent;
                    }
                }
                return 'general';
            },

            extractEntities(query) {
                const entities = {};
                for (const [type, values] of Object.entries(this.entities)) {
                    entities[type] = values.filter(value => query.includes(value));
                }
                return entities;
            }
        };
    }    se
tupDataAnalyzer() {
        this.dataAnalyzer = {
            // 智能数据分析
            analyzeData(data, context) {
                const analysis = {
                    summary: this.generateSummary(data),
                    trends: this.detectTrends(data),
                    anomalies: this.detectAnomalies(data),
                    insights: this.generateInsights(data),
                    recommendations: this.generateRecommendations(data, context)
                };
                return analysis;
            },

            generateSummary(data) {
                if (!data || data.length === 0) return "暂无数据";
                
                const total = data.reduce((sum, item) => sum + (item.value || 0), 0);
                const average = total / data.length;
                const max = Math.max(...data.map(item => item.value || 0));
                const min = Math.min(...data.map(item => item.value || 0));
                
                return `数据概览：总计 ${total.toLocaleString()}，平均值 ${average.toFixed(2)}，最高 ${max.toLocaleString()}，最低 ${min.toLocaleString()}`;
            },

            detectTrends(data) {
                if (!data || data.length < 2) return "数据不足以分析趋势";
                
                const values = data.map(item => item.value || 0);
                const trend = values[values.length - 1] - values[0];
                const trendPercent = ((trend / values[0]) * 100).toFixed(1);
                
                if (trend > 0) {
                    return `📈 呈上升趋势，增长 ${trendPercent}%`;
                } else if (trend < 0) {
                    return `📉 呈下降趋势，下降 ${Math.abs(trendPercent)}%`;
                } else {
                    return `➡️ 保持稳定，无明显变化`;
                }
            },

            detectAnomalies(data) {
                if (!data || data.length < 3) return [];
                
                const values = data.map(item => item.value || 0);
                const mean = values.reduce((a, b) => a + b) / values.length;
                const stdDev = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / values.length);
                
                const anomalies = [];
                values.forEach((value, index) => {
                    if (Math.abs(value - mean) > 2 * stdDev) {
                        anomalies.push({
                            index,
                            value,
                            deviation: ((value - mean) / stdDev).toFixed(2)
                        });
                    }
                });
                
                return anomalies;
            },

            generateInsights(data) {
                const insights = [];
                
                // 增长率分析
                if (data.length >= 2) {
                    const recent = data.slice(-3);
                    const growth = recent.map((item, i) => 
                        i > 0 ? ((item.value - recent[i-1].value) / recent[i-1].value * 100) : 0
                    ).filter(g => g !== 0);
                    
                    if (growth.length > 0) {
                        const avgGrowth = growth.reduce((a, b) => a + b) / growth.length;
                        if (avgGrowth > 10) {
                            insights.push("🚀 数据显示强劲增长势头，建议加大投入");
                        } else if (avgGrowth < -10) {
                            insights.push("⚠️ 数据呈下降趋势，需要关注并采取措施");
                        }
                    }
                }
                
                // 季节性分析
                if (data.length >= 12) {
                    insights.push("📅 建议分析季节性模式，优化资源配置");
                }
                
                return insights;
            },

            generateRecommendations(data, context) {
                const recommendations = [];
                
                if (context.chartType === 'line' && data.length > 20) {
                    recommendations.push("💡 数据点较多，建议使用数据聚合或添加筛选器");
                }
                
                if (context.hasNegativeValues) {
                    recommendations.push("📊 包含负值，建议使用堆叠柱状图或瀑布图");
                }
                
                recommendations.push("🎯 建议设置数据监控阈值，及时发现异常");
                
                return recommendations;
            }
        };
    }

    setupPersonalizationEngine() {
        this.personalization = {
            userProfile: {
                preferredChartTypes: [],
                frequentQueries: [],
                workingHours: { start: 9, end: 18 },
                dataInterests: []
            },

            learnFromInteraction(interaction) {
                // 学习用户偏好
                if (interaction.chartType) {
                    this.userProfile.preferredChartTypes.push(interaction.chartType);
                }
                
                if (interaction.query) {
                    this.userProfile.frequentQueries.push(interaction.query);
                }
                
                // 保存到本地存储
                localStorage.setItem('aiAssistantProfile', JSON.stringify(this.userProfile));
            },

            getPersonalizedSuggestions() {
                const suggestions = [];
                
                // 基于偏好推荐
                if (this.userProfile.preferredChartTypes.length > 0) {
                    const mostUsed = this.getMostFrequent(this.userProfile.preferredChartTypes);
                    suggestions.push(`基于您的使用习惯，推荐使用${mostUsed}图表`);
                }
                
                // 基于时间推荐
                const hour = new Date().getHours();
                if (hour >= 9 && hour <= 11) {
                    suggestions.push("早上好！建议查看昨日数据概览");
                } else if (hour >= 17 && hour <= 19) {
                    suggestions.push("下午好！建议生成今日数据报告");
                }
                
                return suggestions;
            },

            getMostFrequent(arr) {
                const frequency = {};
                arr.forEach(item => frequency[item] = (frequency[item] || 0) + 1);
                return Object.keys(frequency).reduce((a, b) => frequency[a] > frequency[b] ? a : b);
            }
        };
        
        // 加载用户配置
        const saved = localStorage.getItem('aiAssistantProfile');
        if (saved) {
            this.personalization.userProfile = { ...this.personalization.userProfile, ...JSON.parse(saved) };
        }
    }

    startContextualAnalysis() {
        // 定期分析当前页面数据
        setInterval(() => {
            this.analyzeCurrentContext();
        }, 30000); // 每30秒分析一次
        
        // 监听数据变化
        document.addEventListener('dataUpdated', (e) => {
            this.analyzeNewData(e.detail);
        });
    }

    analyzeCurrentContext() {
        // 分析当前显示的图表和数据
        const charts = document.querySelectorAll('.chart-container');
        const metrics = document.querySelectorAll('.metric-item');
        
        charts.forEach(chart => {
            const chartId = chart.id;
            if (chartId && !this.dataContext.has(chartId)) {
                this.dataContext.set(chartId, {
                    type: this.detectChartType(chart),
                    lastAnalyzed: Date.now(),
                    insights: []
                });
            }
        });
        
        // 生成智能建议
        this.generateSmartSuggestions();
    }

    detectChartType(chartElement) {
        // 基于元素特征检测图表类型
        if (chartElement.querySelector('canvas')) {
            return 'canvas-chart';
        } else if (chartElement.innerHTML.includes('echarts')) {
            return 'echarts';
        }
        return 'unknown';
    }

    generateSmartSuggestions() {
        const suggestions = this.personalization.getPersonalizedSuggestions();
        
        // 添加数据驱动的建议
        if (this.dataContext.size > 0) {
            suggestions.push("💡 我注意到您正在查看多个图表，需要我帮您生成综合分析报告吗？");
        }
        
        // 更新建议显示
        this.updateSuggestions(suggestions);
    }

    updateSuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('aiSuggestions');
        if (suggestionsContainer && suggestions.length > 0) {
            suggestionsContainer.innerHTML = suggestions.slice(0, 3).map(suggestion => 
                `<button onclick="window.aiAssistant.quickQuery('${suggestion}')">${suggestion}</button>`
            ).join('');
        }
    }

    // 公共方法
    toggle() {
        const container = document.getElementById('ai-assistant');
        container.classList.toggle('minimized');
        this.isActive = !container.classList.contains('minimized');
    }

    sendMessage() {
        const input = document.getElementById('aiInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addMessage('user', message);
        input.value = '';
        
        // 处理消息
        this.processMessage(message);
    }

    quickQuery(query) {
        this.addMessage('user', query);
        this.processMessage(query);
    }

    addMessage(sender, message) {
        const chatArea = document.getElementById('aiChatArea');
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ai-message-${sender}`;
        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;
        
        chatArea.appendChild(messageDiv);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    async processMessage(message) {
        // 显示思考状态
        this.addMessage('assistant', '🤔 让我分析一下...');
        
        // 模拟AI处理延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 移除思考消息
        const messages = document.querySelectorAll('.ai-message-assistant');
        if (messages.length > 0) {
            messages[messages.length - 1].remove();
        }
        
        // 处理查询
        const processed = this.nlp.processQuery(message);
        const response = await this.generateResponse(processed);
        
        this.addMessage('assistant', response);
        
        // 学习用户交互
        this.personalization.learnFromInteraction({
            query: message,
            intent: processed.intent,
            timestamp: Date.now()
        });
    }

    async generateResponse(processed) {
        const { intent, entities, query } = processed;
        
        switch (intent) {
            case 'data_query':
                return this.handleDataQuery(entities);
            case 'chart_recommendation':
                return this.handleChartRecommendation(entities);
            case 'trend_analysis':
                return this.handleTrendAnalysis(entities);
            case 'insight':
                return this.handleInsightRequest();
            default:
                return this.handleGeneralQuery(query);
        }
    }

    handleDataQuery(entities) {
        if (entities.metrics.includes('用户')) {
            return `📊 当前用户数据：
            • 总用户数：15,847 (+12.5% 本月)
            • 活跃用户：12,340 (+8.3% 本月)
            • 新增用户：2,156 (本月)
            
            💡 用户增长势头良好，建议继续优化用户体验以提升留存率。`;
        } else if (entities.metrics.includes('律师')) {
            return `⚖️ 律师数据概览：
            • 总律师数：3,256 (+15.7% 本月)
            • 活跃律师：2,890 (88.8% 活跃率)
            • 等级分布：见习律师占比最高 (435人)
            
            🎯 建议加强高级律师的招募和培养。`;
        }
        
        return "📈 我可以帮您分析用户、律师、案件、收入等各类数据，请告诉我您想了解哪个方面？";
    }

    handleChartRecommendation(entities) {
        return `📊 图表推荐：
        
        基于当前数据特征，我推荐：
        • 📈 **折线图**：适合展示时间趋势
        • 📊 **柱状图**：适合类别对比
        • 🥧 **饼图**：适合占比分析
        • 🎯 **雷达图**：适合多维度评估
        
        💡 您可以说"显示用户增长折线图"来生成特定图表。`;
    }

    handleTrendAnalysis(entities) {
        return `📈 趋势分析结果：
        
        • **用户增长**：📈 持续上升，月增长率 12.5%
        • **律师活跃度**：📊 稳定增长，活跃率 88.8%
        • **案件处理**：⚡ 效率提升，平均处理时间减少 15%
        • **收入表现**：💰 强劲增长，月增长率 22.1%
        
        🎯 **建议**：当前各项指标表现优秀，建议保持现有策略并适度扩大规模。`;
    }

    handleInsightRequest() {
        return `💡 智能洞察：
        
        🔍 **发现的机会**：
        • 见习律师数量最多，可加强培训转化
        • 用户满意度达94.2%，可作为营销亮点
        • 移动端使用率上升，建议优化移动体验
        
        ⚠️ **需要关注**：
        • 高级律师占比较低，影响服务质量
        • 部分地区用户增长放缓
        
        🎯 **行动建议**：
        1. 启动律师等级提升计划
        2. 加强移动端功能开发
        3. 针对性地区推广策略`;
    }

    handleGeneralQuery(query) {
        const responses = [
            "🤖 我是您的智能数据助手，可以帮您分析数据、生成洞察、推荐图表类型。",
            "📊 您可以问我关于用户、律师、案件、收入等任何数据问题。",
            "💡 试试说：'分析用户增长趋势' 或 '推荐合适的图表类型'。",
            "🎯 我还可以为您生成个性化的数据报告和智能建议。"
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }
}

// 全局实例
window.aiAssistant = new LawskerAIAssistant();

// 样式
const aiStyles = document.createElement('style');
aiStyles.textContent = `
    .ai-assistant-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        height: 600px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        z-index: 1000;
        display: flex;
        flex-direction: column;
        transition: all 0.3s ease;
    }

    .ai-assistant-container.minimized {
        height: 60px;
        width: 200px;
    }

    .ai-header {
        display: flex;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 20px 20px 0 0;
    }

    .ai-avatar {
        font-size: 1.5rem;
        margin-right: 0.5rem;
    }

    .ai-title {
        flex: 1;
        font-weight: 600;
    }

    .ai-toggle {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 0.25rem;
    }

    .ai-chat-area {
        flex: 1;
        padding: 1rem;
        overflow-y: auto;
        display: none;
    }

    .ai-assistant-container:not(.minimized) .ai-chat-area {
        display: block;
    }

    .ai-welcome {
        color: #6b7280;
        font-size: 0.875rem;
        line-height: 1.5;
    }

    .ai-welcome ul {
        margin: 0.5rem 0;
        padding-left: 1rem;
    }

    .ai-message {
        margin-bottom: 1rem;
        animation: fadeInUp 0.3s ease;
    }

    .ai-message-user {
        text-align: right;
    }

    .ai-message-user .message-content {
        background: #2563eb;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 1rem 1rem 0.25rem 1rem;
        display: inline-block;
        max-width: 80%;
    }

    .ai-message-assistant .message-content {
        background: #f3f4f6;
        color: #374151;
        padding: 0.75rem 1rem;
        border-radius: 1rem 1rem 1rem 0.25rem;
        display: inline-block;
        max-width: 80%;
        white-space: pre-line;
    }

    .message-time {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.25rem;
    }

    .ai-input-area {
        display: none;
        padding: 1rem;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        flex-direction: row;
        gap: 0.5rem;
    }

    .ai-assistant-container:not(.minimized) .ai-input-area {
        display: flex;
    }

    .ai-input-area input {
        flex: 1;
        padding: 0.75rem;
        border: 1px solid #d1d5db;
        border-radius: 1rem;
        outline: none;
        font-size: 0.875rem;
    }

    .ai-send-btn {
        padding: 0.75rem;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .ai-suggestions {
        display: none;
        padding: 0 1rem 1rem;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .ai-assistant-container:not(.minimized) .ai-suggestions {
        display: flex;
    }

    .ai-suggestions button {
        padding: 0.5rem 0.75rem;
        background: rgba(37, 99, 235, 0.1);
        color: #2563eb;
        border: 1px solid rgba(37, 99, 235, 0.2);
        border-radius: 1rem;
        cursor: pointer;
        font-size: 0.75rem;
        transition: all 0.2s ease;
    }

    .ai-suggestions button:hover {
        background: rgba(37, 99, 235, 0.2);
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @media (max-width: 768px) {
        .ai-assistant-container {
            width: calc(100vw - 40px);
            height: 500px;
            bottom: 10px;
            right: 10px;
            left: 10px;
        }
    }
`;

document.head.appendChild(aiStyles);