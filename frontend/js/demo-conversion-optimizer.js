/**
 * Demo Conversion Optimizer
 * 演示账户转化优化器
 * 
 * This module handles smart conversion prompts and optimization for demo accounts
 * to achieve the 30% conversion rate target.
 */

class DemoConversionOptimizer {
    constructor() {
        this.apiBase = '/api/v1/demo-conversion';
        this.workspaceId = null;
        this.sessionId = null;
        this.demoType = null;
        this.abTestVariant = 'control';
        this.sessionStartTime = Date.now();
        this.actionsCompleted = 0;
        this.conversionPromptShown = false;
        this.exitIntentDetected = false;
        
        // Conversion tracking events
        this.trackedEvents = new Set();
        
        // Initialize if in demo mode
        this.init();
    }
    
    init() {
        // Check if we're in demo mode
        const urlParams = new URLSearchParams(window.location.search);
        const isDemoMode = urlParams.get('demo') === 'true' || 
                          window.location.pathname.includes('/demo-') ||
                          document.body.classList.contains('demo-mode');
        
        if (isDemoMode) {
            this.extractDemoInfo();
            this.setupEventTracking();
            this.assignABTestVariant();
            this.startSessionTracking();
            this.setupExitIntentDetection();
        }
    }
    
    extractDemoInfo() {
        // Extract demo info from URL or page data
        const pathParts = window.location.pathname.split('/');
        
        // Look for demo workspace ID in path
        for (let i = 0; i < pathParts.length; i++) {
            if (pathParts[i].startsWith('demo-')) {
                this.workspaceId = pathParts[i];
                break;
            }
        }
        
        // Determine demo type from workspace ID or path
        if (this.workspaceId) {
            if (this.workspaceId.includes('lawyer')) {
                this.demoType = 'lawyer';
            } else if (this.workspaceId.includes('user')) {
                this.demoType = 'user';
            }
        }
        
        // Generate session ID
        this.sessionId = 'demo-session-' + Math.random().toString(36).substr(2, 9);
        
        console.log('Demo Conversion Optimizer initialized:', {
            workspaceId: this.workspaceId,
            demoType: this.demoType,
            sessionId: this.sessionId
        });
    }
    
    async assignABTestVariant() {
        if (!this.workspaceId || !this.sessionId) return;
        
        try {
            const response = await fetch(`${this.apiBase}/ab-test/assign`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    workspace_id: this.workspaceId,
                    session_id: this.sessionId,
                    demo_type: this.demoType
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.abTestVariant = result.data.assigned_variant;
                console.log('A/B Test variant assigned:', this.abTestVariant);
                
                // Apply variant-specific behaviors
                this.applyABTestVariant();
            }
        } catch (error) {
            console.error('Failed to assign A/B test variant:', error);
        }
    }
    
    applyABTestVariant() {
        switch (this.abTestVariant) {
            case 'aggressive_prompts':
                // Show prompts more frequently
                this.promptFrequency = 'high';
                setTimeout(() => this.checkConversionTrigger('time_based'), 120000); // 2 minutes
                break;
                
            case 'reward_focused':
                // Emphasize rewards and incentives
                this.showRewardBanner();
                break;
                
            case 'social_proof':
                // Show social proof elements
                this.showSocialProofElements();
                break;
                
            default:
                // Control group - standard behavior
                this.promptFrequency = 'normal';
                setTimeout(() => this.checkConversionTrigger('time_based'), 300000); // 5 minutes
                break;
        }
    }
    
    setupEventTracking() {
        // Track page views
        this.trackEvent('page_view', {
            page: window.location.pathname,
            timestamp: Date.now()
        });
        
        // Track clicks on important elements
        document.addEventListener('click', (event) => {
            this.handleClick(event);
        });
        
        // Track form interactions
        document.addEventListener('submit', (event) => {
            this.trackEvent('form_submit', {
                form: event.target.id || event.target.className,
                timestamp: Date.now()
            });
        });
        
        // Track scroll depth
        let maxScrollDepth = 0;
        window.addEventListener('scroll', () => {
            const scrollDepth = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
            if (scrollDepth > maxScrollDepth) {
                maxScrollDepth = scrollDepth;
                if (scrollDepth >= 50 && !this.trackedEvents.has('scroll_50')) {
                    this.trackEvent('scroll_50', { depth: scrollDepth });
                    this.trackedEvents.add('scroll_50');
                }
                if (scrollDepth >= 80 && !this.trackedEvents.has('scroll_80')) {
                    this.trackEvent('scroll_80', { depth: scrollDepth });
                    this.trackedEvents.add('scroll_80');
                }
            }
        });
    }
    
    handleClick(event) {
        const target = event.target;
        const clickData = {
            element: target.tagName.toLowerCase(),
            className: target.className,
            id: target.id,
            text: target.textContent?.substring(0, 50),
            timestamp: Date.now()
        };
        
        // Track specific important clicks
        if (target.matches('.case-item, .lawyer-card, .dashboard-widget')) {
            this.trackEvent('important_element_click', clickData);
            this.actionsCompleted++;
            this.checkConversionTrigger('action_based');
        }
        
        // Track navigation clicks
        if (target.matches('a, button')) {
            this.trackEvent('navigation_click', clickData);
        }
        
        // Track feature access attempts
        if (target.matches('.restricted-feature, .premium-feature')) {
            this.trackEvent('feature_restricted', clickData);
            this.checkConversionTrigger('feature_limit');
        }
    }
    
    async trackEvent(eventType, eventData = {}) {
        if (!this.workspaceId) return;
        
        try {
            const response = await fetch(`${this.apiBase}/track-event`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    workspace_id: this.workspaceId,
                    event_type: eventType,
                    event_data: {
                        ...eventData,
                        session_id: this.sessionId,
                        ab_variant: this.abTestVariant,
                        session_duration: Date.now() - this.sessionStartTime,
                        actions_completed: this.actionsCompleted
                    },
                    session_id: this.sessionId
                })
            });
            
            const result = await response.json();
            if (result.success && result.data.conversion_prompt) {
                this.showConversionPrompt(result.data.conversion_prompt);
            }
        } catch (error) {
            console.error('Failed to track event:', error);
        }
    }
    
    async checkConversionTrigger(triggerType) {
        if (!this.workspaceId || this.conversionPromptShown) return;
        
        try {
            const sessionData = {
                session_duration: Date.now() - this.sessionStartTime,
                actions_completed: this.actionsCompleted,
                ab_variant: this.abTestVariant
            };
            
            const response = await fetch(
                `${this.apiBase}/conversion-prompt/${this.workspaceId}?event_type=${triggerType}&session_data=${encodeURIComponent(JSON.stringify(sessionData))}`
            );
            
            const result = await response.json();
            if (result.success && result.data.show_prompt) {
                this.showConversionPrompt(result.data.prompt);
            }
        } catch (error) {
            console.error('Failed to check conversion trigger:', error);
        }
    }
    
    showConversionPrompt(promptData) {
        if (this.conversionPromptShown) return;
        
        this.conversionPromptShown = true;
        
        // Create conversion prompt modal
        const modal = this.createConversionModal(promptData);
        document.body.appendChild(modal);
        
        // Show modal with animation
        setTimeout(() => {
            modal.classList.add('show');
        }, 100);
        
        // Track prompt shown
        this.trackEvent('conversion_prompt_shown', {
            prompt_type: promptData.type,
            priority: promptData.priority
        });
    }
    
    createConversionModal(promptData) {
        const modal = document.createElement('div');
        modal.className = 'conversion-modal';
        modal.innerHTML = `
            <div class="conversion-modal-overlay"></div>
            <div class="conversion-modal-content">
                <div class="conversion-modal-header">
                    <div class="conversion-icon">
                        ${this.getConversionIcon(promptData.type)}
                    </div>
                    <button class="conversion-modal-close" onclick="this.closest('.conversion-modal').remove()">
                        ×
                    </button>
                </div>
                <div class="conversion-modal-body">
                    <h3 class="conversion-title">${promptData.message}</h3>
                    <p class="conversion-incentive">${promptData.incentive}</p>
                    <div class="conversion-benefits">
                        ${this.getConversionBenefits()}
                    </div>
                </div>
                <div class="conversion-modal-footer">
                    <button class="conversion-btn-primary" onclick="demoConversionOptimizer.handleConversionClick('register')">
                        立即注册
                    </button>
                    <button class="conversion-btn-secondary" onclick="demoConversionOptimizer.handleConversionClick('later')">
                        稍后注册
                    </button>
                </div>
            </div>
        `;
        
        // Add styles
        this.addConversionModalStyles();
        
        return modal;
    }
    
    getConversionIcon(type) {
        const icons = {
            'time_based': '⏰',
            'action_based': '🎯',
            'feature_limit': '🔒',
            'completion_reward': '🎉',
            'exit_intent': '👋'
        };
        return icons[type] || '💡';
    }
    
    getConversionBenefits() {
        const benefits = this.demoType === 'lawyer' ? [
            '✅ 接受真实案件委托',
            '✅ 获得案件收入',
            '✅ 建立专业声誉',
            '✅ 免费AI咨询额度'
        ] : [
            '✅ 发布真实法律需求',
            '✅ 获得专业法律服务',
            '✅ 享受平台保障',
            '✅ 专属客户经理'
        ];
        
        return benefits.map(benefit => `<div class="conversion-benefit">${benefit}</div>`).join('');
    }
    
    addConversionModalStyles() {
        if (document.getElementById('conversion-modal-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'conversion-modal-styles';
        styles.textContent = `
            .conversion-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 10000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }
            
            .conversion-modal.show {
                opacity: 1;
                visibility: visible;
            }
            
            .conversion-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.6);
                backdrop-filter: blur(4px);
            }
            
            .conversion-modal-content {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                max-width: 480px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
            }
            
            .conversion-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.5rem 1.5rem 0;
            }
            
            .conversion-icon {
                font-size: 2rem;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                color: white;
            }
            
            .conversion-modal-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #6b7280;
                padding: 0.5rem;
                border-radius: 50%;
                transition: all 0.2s ease;
            }
            
            .conversion-modal-close:hover {
                background: #f3f4f6;
                color: #374151;
            }
            
            .conversion-modal-body {
                padding: 1.5rem;
            }
            
            .conversion-title {
                font-size: 1.25rem;
                font-weight: 700;
                color: #1f2937;
                margin-bottom: 0.5rem;
            }
            
            .conversion-incentive {
                color: #6b7280;
                margin-bottom: 1.5rem;
                font-size: 0.95rem;
            }
            
            .conversion-benefits {
                margin-bottom: 1.5rem;
            }
            
            .conversion-benefit {
                color: #374151;
                margin-bottom: 0.5rem;
                font-size: 0.9rem;
            }
            
            .conversion-modal-footer {
                padding: 0 1.5rem 1.5rem;
                display: flex;
                gap: 1rem;
            }
            
            .conversion-btn-primary {
                flex: 1;
                background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .conversion-btn-primary:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            }
            
            .conversion-btn-secondary {
                flex: 1;
                background: #f3f4f6;
                color: #374151;
                border: none;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .conversion-btn-secondary:hover {
                background: #e5e7eb;
            }
            
            @media (max-width: 640px) {
                .conversion-modal-content {
                    width: 95%;
                }
                
                .conversion-modal-footer {
                    flex-direction: column;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    handleConversionClick(action) {
        // Track conversion action
        this.trackEvent('conversion_action', {
            action: action,
            prompt_type: 'modal'
        });
        
        if (action === 'register') {
            // Redirect to registration with demo context
            const params = new URLSearchParams({
                from: 'demo',
                demo_type: this.demoType,
                workspace_id: this.workspaceId,
                ab_variant: this.abTestVariant
            });
            
            window.location.href = `/unified-auth.html?${params.toString()}`;
        } else {
            // Close modal and set reminder
            document.querySelector('.conversion-modal')?.remove();
            this.scheduleReminderPrompt();
        }
    }
    
    scheduleReminderPrompt() {
        // Schedule a reminder prompt after 5 minutes
        setTimeout(() => {
            if (!this.conversionPromptShown) {
                this.showReminderPrompt();
            }
        }, 300000); // 5 minutes
    }
    
    showReminderPrompt() {
        const reminderData = {
            type: 'reminder',
            priority: 'medium',
            message: '还在体验演示功能吗？',
            incentive: '注册账户享受完整功能，仅需1分钟'
        };
        
        this.showConversionPrompt(reminderData);
    }
    
    setupExitIntentDetection() {
        let exitIntentShown = false;
        
        document.addEventListener('mouseleave', (event) => {
            if (event.clientY <= 0 && !exitIntentShown && !this.conversionPromptShown) {
                exitIntentShown = true;
                this.exitIntentDetected = true;
                
                const exitIntentData = {
                    type: 'exit_intent',
                    priority: 'high',
                    message: '等等！不要错过这个机会',
                    incentive: '注册即可获得新用户专属优惠'
                };
                
                this.showConversionPrompt(exitIntentData);
                this.trackEvent('exit_intent_detected');
            }
        });
    }
    
    showRewardBanner() {
        const banner = document.createElement('div');
        banner.className = 'demo-reward-banner';
        banner.innerHTML = `
            <div class="reward-banner-content">
                <span class="reward-icon">🎁</span>
                <span class="reward-text">注册即可获得新用户专属礼包</span>
                <button class="reward-btn" onclick="demoConversionOptimizer.handleConversionClick('register')">
                    立即获取
                </button>
            </div>
        `;
        
        // Add banner styles
        const styles = document.createElement('style');
        styles.textContent = `
            .demo-reward-banner {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, #f59e0b, #d97706);
                color: white;
                padding: 0.75rem;
                text-align: center;
                z-index: 9999;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .reward-banner-content {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 1rem;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .reward-icon {
                font-size: 1.2rem;
            }
            
            .reward-text {
                font-weight: 600;
            }
            
            .reward-btn {
                background: white;
                color: #d97706;
                border: none;
                border-radius: 6px;
                padding: 0.5rem 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .reward-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }
            
            @media (max-width: 640px) {
                .reward-banner-content {
                    flex-direction: column;
                    gap: 0.5rem;
                }
            }
        `;
        
        document.head.appendChild(styles);
        document.body.insertBefore(banner, document.body.firstChild);
        
        // Adjust body padding to account for banner
        document.body.style.paddingTop = '60px';
    }
    
    showSocialProofElements() {
        // Add social proof indicators
        const socialProof = document.createElement('div');
        socialProof.className = 'demo-social-proof';
        socialProof.innerHTML = `
            <div class="social-proof-item">
                <span class="social-proof-number">10,000+</span>
                <span class="social-proof-label">注册用户</span>
            </div>
            <div class="social-proof-item">
                <span class="social-proof-number">5,000+</span>
                <span class="social-proof-label">专业律师</span>
            </div>
            <div class="social-proof-item">
                <span class="social-proof-number">98%</span>
                <span class="social-proof-label">客户满意度</span>
            </div>
        `;
        
        // Add to page (find a suitable container)
        const container = document.querySelector('.dashboard-header, .main-content, body');
        if (container) {
            container.appendChild(socialProof);
        }
    }
    
    startSessionTracking() {
        // Track session milestones
        const milestones = [60000, 180000, 300000, 600000]; // 1min, 3min, 5min, 10min
        
        milestones.forEach(milestone => {
            setTimeout(() => {
                this.trackEvent('session_milestone', {
                    milestone: milestone / 1000 + 's',
                    actions_completed: this.actionsCompleted
                });
                
                // Check for conversion trigger at certain milestones
                if (milestone === 300000) { // 5 minutes
                    this.checkConversionTrigger('time_based');
                }
            }, milestone);
        });
    }
    
    // Method to be called when user actually registers
    async recordConversionSuccess(userId) {
        if (!this.workspaceId) return;
        
        try {
            const response = await fetch(`${this.apiBase}/record-conversion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    workspace_id: this.workspaceId,
                    user_id: userId,
                    conversion_source: 'demo'
                })
            });
            
            const result = await response.json();
            if (result.success) {
                console.log('Demo conversion recorded successfully');
            }
        } catch (error) {
            console.error('Failed to record conversion success:', error);
        }
    }
}

// Initialize global instance
const demoConversionOptimizer = new DemoConversionOptimizer();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DemoConversionOptimizer;
}