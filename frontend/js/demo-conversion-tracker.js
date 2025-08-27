/**
 * 演示账户转化跟踪系统
 * 跟踪用户从演示账户到真实注册的转化路径
 */

class DemoConversionTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.events = [];
        this.startTime = Date.now();
        
        this.init();
    }
    
    init() {
        // 检查是否来自演示账户
        this.checkDemoSource();
        
        // 监听页面卸载事件，发送数据
        window.addEventListener('beforeunload', () => {
            this.sendEvents();
        });
        
        // 定期发送事件数据
        setInterval(() => {
            this.sendEvents();
        }, 30000); // 每30秒发送一次
    }
    
    generateSessionId() {
        return 'demo_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    checkDemoSource() {
        const urlParams = new URLSearchParams(window.location.search);
        const fromDemo = urlParams.get('from') === 'demo';
        const demoType = urlParams.get('demo_type');
        
        if (fromDemo) {
            this.trackEvent('demo_conversion_start', {
                demo_type: demoType,
                target_page: window.location.pathname
            });
        }
        
        // 检查是否在演示模式
        const isDemo = urlParams.get('demo') === 'true';
        if (isDemo) {
            this.trackEvent('demo_session_active', {
                demo_type: this.getDemoTypeFromPath(),
                workspace_id: this.getWorkspaceIdFromPath()
            });
        }
    }
    
    getDemoTypeFromPath() {
        const path = window.location.pathname;
        if (path.includes('/lawyer/')) return 'lawyer';
        if (path.includes('/user/')) return 'user';
        return 'unknown';
    }
    
    getWorkspaceIdFromPath() {
        const path = window.location.pathname;
        const matches = path.match(/\/(lawyer|user)\/([^\/\?]+)/);
        return matches ? matches[2] : null;
    }
    
    trackEvent(eventName, data = {}) {
        const event = {
            event: eventName,
            timestamp: Date.now(),
            session_id: this.sessionId,
            page: window.location.pathname,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            ...data
        };
        
        this.events.push(event);
        
        // 立即发送重要事件
        const immediateEvents = [
            'demo_conversion_start',
            'demo_to_registration',
            'demo_registration_complete'
        ];
        
        if (immediateEvents.includes(eventName)) {
            this.sendEvents();
        }
        
        console.log('Demo conversion event:', event);
    }
    
    trackDemoAccess(demoType, source = 'unknown') {
        this.trackEvent('demo_access', {
            demo_type: demoType,
            source: source,
            access_time: Date.now()
        });
    }
    
    trackDemoAction(action, details = {}) {
        this.trackEvent('demo_action', {
            action: action,
            details: details,
            session_duration: Date.now() - this.startTime
        });
    }
    
    trackConversionIntent(conversionType = 'registration') {
        this.trackEvent('demo_conversion_intent', {
            conversion_type: conversionType,
            session_duration: Date.now() - this.startTime,
            actions_count: this.events.filter(e => e.event === 'demo_action').length
        });
    }
    
    trackRegistrationStart(accountType) {
        this.trackEvent('demo_to_registration', {
            account_type: accountType,
            session_duration: Date.now() - this.startTime
        });
    }
    
    trackRegistrationComplete(accountType, userId) {
        this.trackEvent('demo_registration_complete', {
            account_type: accountType,
            user_id: userId,
            total_session_duration: Date.now() - this.startTime,
            conversion_successful: true
        });
    }
    
    async sendEvents() {
        if (this.events.length === 0) return;
        
        try {
            const eventsToSend = [...this.events];
            this.events = []; // 清空待发送事件
            
            const response = await fetch('/api/v1/analytics/demo-conversion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    events: eventsToSend
                })
            });
            
            if (!response.ok) {
                // 如果发送失败，重新加入队列
                this.events.unshift(...eventsToSend);
            }
        } catch (error) {
            console.error('Failed to send demo conversion events:', error);
            // 发送失败时不重新加入队列，避免无限重试
        }
    }
    
    // 获取转化统计数据
    getConversionStats() {
        const demoActions = this.events.filter(e => e.event === 'demo_action');
        const conversionIntents = this.events.filter(e => e.event === 'demo_conversion_intent');
        const registrations = this.events.filter(e => e.event === 'demo_to_registration');
        
        return {
            session_id: this.sessionId,
            session_duration: Date.now() - this.startTime,
            total_events: this.events.length,
            demo_actions: demoActions.length,
            conversion_intents: conversionIntents.length,
            registrations: registrations.length,
            conversion_rate: registrations.length > 0 ? 1 : 0
        };
    }
}

// 全局实例
window.demoConversionTracker = new DemoConversionTracker();

// 便捷方法
window.trackDemoAccess = (demoType, source) => {
    window.demoConversionTracker.trackDemoAccess(demoType, source);
};

window.trackDemoAction = (action, details) => {
    window.demoConversionTracker.trackDemoAction(action, details);
};

window.trackConversionIntent = (conversionType) => {
    window.demoConversionTracker.trackConversionIntent(conversionType);
};

window.trackRegistrationStart = (accountType) => {
    window.demoConversionTracker.trackRegistrationStart(accountType);
};

window.trackRegistrationComplete = (accountType, userId) => {
    window.demoConversionTracker.trackRegistrationComplete(accountType, userId);
};

// 自动跟踪页面访问
document.addEventListener('DOMContentLoaded', function() {
    // 跟踪页面加载
    window.demoConversionTracker.trackEvent('page_load', {
        load_time: Date.now(),
        page_title: document.title
    });
    
    // 跟踪链接点击
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link) {
            const href = link.getAttribute('href');
            if (href) {
                if (href.includes('/demo-account.html')) {
                    window.demoConversionTracker.trackEvent('demo_link_click', {
                        link_text: link.textContent.trim(),
                        link_href: href
                    });
                } else if (href.includes('/unified-auth.html')) {
                    window.demoConversionTracker.trackConversionIntent('registration');
                }
            }
        }
    });
});