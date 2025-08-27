/**
 * Enhanced Credits Management System
 * Provides clear display and user-friendly payment flow
 * Target: >95% user understanding rate
 */

class EnhancedCreditsManager {
    constructor() {
        this.currentData = null;
        this.isLoading = false;
        this.explanationShown = false;
        
        // Configuration
        this.config = {
            apiBase: '/api/v1/credits',
            refreshInterval: 30000, // 30 seconds
            animationDuration: 300,
            toastDuration: 4000
        };
        
        this.init();
    }

    async init() {
        await this.loadCreditsData();
        this.setupEventListeners();
        this.startAutoRefresh();
        this.showInitialExplanation();
    }

    /**
     * Load credits data with enhanced error handling
     */
    async loadCreditsData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            const response = await fetch(`${this.config.apiBase}/balance`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.currentData = result.data;
                this.updateDisplay();
                this.hideLoadingState();
            } else {
                throw new Error('获取Credits信息失败');
            }
        } catch (error) {
            console.error('加载Credits数据失败:', error);
            this.showError('无法获取Credits信息，请检查网络连接');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Update all display elements with current data
     */
    updateDisplay() {
        if (!this.currentData) return;

        // Update balance display
        this.updateBalanceDisplay();
        
        // Update info cards
        this.updateInfoCards();
        
        // Update progress indicators
        this.updateProgressIndicators();
        
        // Update recommendations
        this.updateRecommendations();
    }

    /**
     * Update balance display with animation
     */
    updateBalanceDisplay() {
        const balanceEl = document.getElementById('creditsAmount');
        const currentBalance = this.currentData.credits_remaining;
        
        if (balanceEl) {
            // Animate number change
            this.animateNumber(balanceEl, parseInt(balanceEl.textContent) || 0, currentBalance);
            
            // Update color based on balance level
            this.updateBalanceColor(balanceEl, currentBalance);
        }
    }

    /**
     * Update info cards with detailed information
     */
    updateInfoCards() {
        // Next reset date
        const nextResetEl = document.getElementById('nextResetDate');
        if (nextResetEl && this.currentData.next_reset_date) {
            const nextReset = new Date(this.currentData.next_reset_date);
            const daysUntilReset = Math.ceil((nextReset - new Date()) / (1000 * 60 * 60 * 24));
            
            nextResetEl.textContent = this.formatResetDate(nextReset, daysUntilReset);
        }

        // Total purchased
        const totalPurchasedEl = document.getElementById('totalPurchased');
        if (totalPurchasedEl) {
            totalPurchasedEl.textContent = this.currentData.credits_purchased;
        }

        // Usage statistics
        this.updateUsageStats();
    }

    /**
     * Update usage statistics with visual indicators
     */
    updateUsageStats() {
        const totalUsed = this.currentData.total_credits_used;
        const totalAvailable = this.currentData.credits_purchased + totalUsed;
        const usageRate = totalAvailable > 0 ? (totalUsed / totalAvailable) * 100 : 0;

        // Update usage rate display
        const usageRateEl = document.getElementById('usageRate');
        if (usageRateEl) {
            usageRateEl.textContent = `${usageRate.toFixed(1)}%`;
        }

        // Update usage progress bar
        const progressBar = document.getElementById('usageProgressBar');
        if (progressBar) {
            progressBar.style.width = `${usageRate}%`;
            progressBar.className = `usage-progress-fill ${this.getUsageRateClass(usageRate)}`;
        }
    }

    /**
     * Update progress indicators for better understanding
     */
    updateProgressIndicators() {
        // Weekly progress (days until reset)
        const nextReset = new Date(this.currentData.next_reset_date);
        const now = new Date();
        const weekStart = new Date(now);
        weekStart.setDate(now.getDate() - now.getDay() + 1); // Monday
        
        const weekProgress = ((now - weekStart) / (nextReset - weekStart)) * 100;
        
        const weekProgressEl = document.getElementById('weekProgress');
        if (weekProgressEl) {
            weekProgressEl.style.width = `${Math.min(weekProgress, 100)}%`;
        }
    }

    /**
     * Update recommendations based on usage patterns
     */
    updateRecommendations() {
        const recommendationsEl = document.getElementById('recommendations');
        if (!recommendationsEl) return;

        const recommendations = this.generateRecommendations();
        recommendationsEl.innerHTML = recommendations.map(rec => `
            <div class="recommendation-item ${rec.type}">
                <div class="recommendation-icon">${rec.icon}</div>
                <div class="recommendation-content">
                    <h4>${rec.title}</h4>
                    <p>${rec.description}</p>
                    ${rec.action ? `<button onclick="${rec.action}" class="recommendation-action">${rec.actionText}</button>` : ''}
                </div>
            </div>
        `).join('');
    }

    /**
     * Generate personalized recommendations
     */
    generateRecommendations() {
        const recommendations = [];
        const balance = this.currentData.credits_remaining;
        const totalUsed = this.currentData.total_credits_used;

        // Low balance warning
        if (balance === 0) {
            recommendations.push({
                type: 'warning',
                icon: '⚠️',
                title: 'Credits已用完',
                description: '您的Credits余额为0，无法进行批量上传。建议购买Credits或等待每周重置。',
                action: 'showPurchaseModal()',
                actionText: '立即购买'
            });
        } else if (balance === 1) {
            recommendations.push({
                type: 'info',
                icon: '💡',
                title: '余额较低',
                description: '您只剩1个Credit，建议提前购买以避免影响工作流程。',
                action: 'showPurchaseModal()',
                actionText: '购买更多'
            });
        }

        // Usage pattern recommendations
        if (totalUsed > 10) {
            recommendations.push({
                type: 'success',
                icon: '📊',
                title: '活跃用户',
                description: '您是平台的活跃用户！考虑购买更多Credits享受批量折扣。',
                action: 'showPurchaseModal()',
                actionText: '查看优惠'
            });
        }

        // First-time user guidance
        if (totalUsed === 0 && this.currentData.credits_purchased === 0) {
            recommendations.push({
                type: 'info',
                icon: '🎯',
                title: '新用户指南',
                description: '您有1个免费Credit可用于批量上传。每周一会自动重置为1个。',
                action: 'showUsageGuide()',
                actionText: '了解更多'
            });
        }

        return recommendations;
    }

    /**
     * Enhanced purchase flow with step-by-step guidance
     */
    async initiatePurchase(credits, price) {
        // Show purchase flow modal
        this.showPurchaseFlow({
            credits,
            price,
            unitPrice: price / credits,
            savings: this.calculateSavings(credits, price)
        });
    }

    /**
     * Show purchase flow modal with clear steps
     */
    showPurchaseFlow(purchaseData) {
        const modal = document.getElementById('purchaseFlowModal');
        if (!modal) {
            this.createPurchaseFlowModal();
        }

        // Update modal content
        this.updatePurchaseFlowContent(purchaseData);
        
        // Show modal with animation
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('show'), 10);
    }

    /**
     * Create purchase flow modal with enhanced UX
     */
    createPurchaseFlowModal() {
        const modalHTML = `
            <div id="purchaseFlowModal" class="purchase-flow-modal">
                <div class="purchase-flow-content">
                    <div class="purchase-flow-header">
                        <h2>购买 Credits</h2>
                        <button onclick="closePurchaseFlow()" class="close-button">×</button>
                    </div>
                    
                    <div class="purchase-flow-steps">
                        <div class="step active" data-step="1">
                            <div class="step-number">1</div>
                            <div class="step-title">确认订单</div>
                        </div>
                        <div class="step" data-step="2">
                            <div class="step-number">2</div>
                            <div class="step-title">选择支付</div>
                        </div>
                        <div class="step" data-step="3">
                            <div class="step-number">3</div>
                            <div class="step-title">完成购买</div>
                        </div>
                    </div>
                    
                    <div class="purchase-flow-body" id="purchaseFlowBody">
                        <!-- Content will be dynamically updated -->
                    </div>
                    
                    <div class="purchase-flow-footer">
                        <button id="purchaseFlowBack" class="btn-secondary" style="display: none;">上一步</button>
                        <button id="purchaseFlowNext" class="btn-primary">下一步</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.setupPurchaseFlowEvents();
    }

    /**
     * Setup purchase flow event listeners
     */
    setupPurchaseFlowEvents() {
        const nextBtn = document.getElementById('purchaseFlowNext');
        const backBtn = document.getElementById('purchaseFlowBack');
        
        nextBtn.addEventListener('click', () => this.handlePurchaseFlowNext());
        backBtn.addEventListener('click', () => this.handlePurchaseFlowBack());
    }

    /**
     * Calculate savings for bulk purchases
     */
    calculateSavings(credits, price) {
        const regularPrice = credits * 50; // Regular price is 50 per credit
        return regularPrice - price;
    }

    /**
     * Format reset date for better understanding
     */
    formatResetDate(date, daysUntil) {
        if (daysUntil <= 0) {
            return '今天重置';
        } else if (daysUntil === 1) {
            return '明天重置';
        } else if (daysUntil <= 7) {
            return `${daysUntil}天后重置`;
        } else {
            return date.toLocaleDateString('zh-CN', { 
                month: 'short', 
                day: 'numeric',
                weekday: 'short'
            });
        }
    }

    /**
     * Get usage rate class for styling
     */
    getUsageRateClass(rate) {
        if (rate < 30) return 'low';
        if (rate < 70) return 'medium';
        return 'high';
    }

    /**
     * Animate number changes
     */
    animateNumber(element, from, to) {
        const duration = this.config.animationDuration;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.round(from + (to - from) * progress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Update balance color based on level
     */
    updateBalanceColor(element, balance) {
        element.className = element.className.replace(/balance-\w+/g, '');
        
        if (balance === 0) {
            element.classList.add('balance-empty');
        } else if (balance === 1) {
            element.classList.add('balance-low');
        } else if (balance >= 5) {
            element.classList.add('balance-good');
        } else {
            element.classList.add('balance-normal');
        }
    }

    /**
     * Show initial explanation for new users
     */
    showInitialExplanation() {
        if (this.explanationShown || localStorage.getItem('creditsExplanationShown')) {
            return;
        }

        setTimeout(() => {
            this.showTooltip('creditsAmount', {
                title: '这是您的Credits余额',
                content: 'Credits用于批量上传任务。每周一免费获得1个，也可以购买更多。',
                position: 'bottom',
                duration: 8000
            });
            
            localStorage.setItem('creditsExplanationShown', 'true');
            this.explanationShown = true;
        }, 1000);
    }

    /**
     * Show contextual tooltip
     */
    showTooltip(targetId, options) {
        const target = document.getElementById(targetId);
        if (!target) return;

        const tooltip = document.createElement('div');
        tooltip.className = 'credits-tooltip';
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <h4>${options.title}</h4>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="tooltip-content">${options.content}</div>
        `;

        document.body.appendChild(tooltip);
        
        // Position tooltip
        const targetRect = target.getBoundingClientRect();
        tooltip.style.left = `${targetRect.left + targetRect.width / 2}px`;
        tooltip.style.top = `${targetRect.bottom + 10}px`;
        
        // Auto remove
        setTimeout(() => {
            if (tooltip.parentElement) {
                tooltip.remove();
            }
        }, options.duration || 5000);
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        const loadingElements = document.querySelectorAll('.credits-loading-target');
        loadingElements.forEach(el => {
            el.classList.add('loading');
        });
    }

    /**
     * Hide loading state
     */
    hideLoadingState() {
        const loadingElements = document.querySelectorAll('.credits-loading-target');
        loadingElements.forEach(el => {
            el.classList.remove('loading');
        });
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showToast('error', message);
    }

    /**
     * Show toast notification
     */
    showToast(type, message) {
        const toast = document.createElement('div');
        toast.className = `credits-toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${this.getToastIcon(type)}</div>
            <div class="toast-message">${message}</div>
            <button onclick="this.parentElement.remove()" class="toast-close">×</button>
        `;

        document.body.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, this.config.toastDuration);
    }

    /**
     * Get toast icon
     */
    getToastIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshCredits');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadCreditsData());
        }

        // Purchase buttons
        document.querySelectorAll('.purchase-credits-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const credits = parseInt(e.target.dataset.credits);
                const price = parseFloat(e.target.dataset.price);
                this.initiatePurchase(credits, price);
            });
        });
    }

    /**
     * Start auto refresh
     */
    startAutoRefresh() {
        setInterval(() => {
            if (!this.isLoading) {
                this.loadCreditsData();
            }
        }, this.config.refreshInterval);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.creditsManager = new EnhancedCreditsManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedCreditsManager;
}