// Lawsker 访问统计系统 - 前端通用版本
// 用于记录所有前端页面的用户访问数据

(function() {
    'use strict';
    
    // 访问统计核心功能
    const LawskerAnalytics = {
        // 初始化
        init() {
            try {
                this.recordPageView();
                this.startSessionTracking();
                console.log('Lawsker访问统计已启动');
            } catch (error) {
                console.warn('访问统计初始化失败:', error);
            }
        },

        // 记录页面访问
        recordPageView() {
            const now = new Date();
            const today = now.toDateString();
            const hour = now.getHours();
            const currentPage = window.location.pathname;
            
            // 获取现有数据
            let analytics = this.getStoredData();
            
            // 初始化今日数据
            if (!analytics[today]) {
                analytics[today] = {
                    pv: 0,
                    sessions: [],
                    hours: {},
                    pages: {},
                    referrers: {},
                    devices: {},
                    firstVisit: now.toISOString()
                };
            }
            
            const todayData = analytics[today];
            
            // 记录PV
            todayData.pv++;
            
            // 记录会话UV
            const sessionId = this.getSessionId();
            if (!todayData.sessions.includes(sessionId)) {
                todayData.sessions.push(sessionId);
            }
            
            // 记录小时分布
            if (!todayData.hours[hour]) {
                todayData.hours[hour] = 0;
            }
            todayData.hours[hour]++;
            
            // 记录页面访问
            if (!todayData.pages[currentPage]) {
                todayData.pages[currentPage] = 0;
            }
            todayData.pages[currentPage]++;
            
            // 记录来源
            const referrer = document.referrer || 'direct';
            const referrerDomain = this.extractDomain(referrer);
            if (!todayData.referrers[referrerDomain]) {
                todayData.referrers[referrerDomain] = 0;
            }
            todayData.referrers[referrerDomain]++;
            
            // 记录设备类型
            const deviceType = this.getDeviceType();
            if (!todayData.devices[deviceType]) {
                todayData.devices[deviceType] = 0;
            }
            todayData.devices[deviceType]++;
            
            // 清理过期数据（保留30天）
            this.cleanupOldData(analytics);
            
            // 保存数据
            this.saveData(analytics);
            
            // 输出统计信息
            console.log('页面访问已记录:', {
                page: currentPage,
                todayPV: todayData.pv,
                todayUV: todayData.sessions.length,
                sessionId: sessionId,
                deviceType: deviceType
            });
        },

        // 获取会话ID
        getSessionId() {
            const storageKey = 'lawsker_session_id';
            let sessionId = sessionStorage.getItem(storageKey);
            
            if (!sessionId) {
                // 生成基于用户特征的会话ID
                const userFingerprint = this.generateUserFingerprint();
                const timestamp = Date.now();
                sessionId = `sess_${userFingerprint}_${timestamp}`;
                sessionStorage.setItem(storageKey, sessionId);
            }
            
            return sessionId;
        },

        // 生成用户指纹
        generateUserFingerprint() {
            try {
                const features = [
                    navigator.userAgent,
                    navigator.language || navigator.userLanguage,
                    screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
                    new Date().getTimezoneOffset(),
                    navigator.platform,
                    navigator.cookieEnabled ? '1' : '0'
                ];
                
                // 添加Canvas指纹
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillStyle = '#f60';
                ctx.fillText('Lawsker Analytics', 2, 2);
                features.push(canvas.toDataURL());
                
                const fingerprint = features.join('|');
                return this.simpleHash(fingerprint);
            } catch (error) {
                // 备用方案
                return this.simpleHash(navigator.userAgent + Date.now());
            }
        },

        // 简单哈希函数
        simpleHash(str) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // 转为32位整数
            }
            return Math.abs(hash).toString(36);
        },

        // 获取设备类型
        getDeviceType() {
            const ua = navigator.userAgent;
            if (/tablet|ipad|playbook|silk/i.test(ua)) {
                return 'tablet';
            } else if (/mobile|iphone|ipod|android|blackberry|opera|mini|windows\sce|palm|smartphone|iemobile/i.test(ua)) {
                return 'mobile';
            } else {
                return 'desktop';
            }
        },

        // 提取域名
        extractDomain(url) {
            if (!url || url === 'direct') return 'direct';
            try {
                const domain = new URL(url).hostname;
                return domain.replace(/^www\./, '');
            } catch (error) {
                return 'unknown';
            }
        },

        // 获取存储的数据
        getStoredData() {
            try {
                return JSON.parse(localStorage.getItem('lawsker_analytics') || '{}');
            } catch (error) {
                console.warn('读取访问数据失败，使用空数据:', error);
                return {};
            }
        },

        // 保存数据
        saveData(data) {
            try {
                localStorage.setItem('lawsker_analytics', JSON.stringify(data));
            } catch (error) {
                console.warn('保存访问数据失败:', error);
            }
        },

        // 清理过期数据
        cleanupOldData(analytics) {
            const now = new Date();
            const retentionDays = 30;
            const cutoffDate = new Date(now.getTime() - retentionDays * 24 * 60 * 60 * 1000);
            
            Object.keys(analytics).forEach(dateStr => {
                if (new Date(dateStr) < cutoffDate) {
                    delete analytics[dateStr];
                }
            });
        },

        // 开始会话跟踪
        startSessionTracking() {
            // 记录会话开始时间
            if (!sessionStorage.getItem('lawsker_session_start')) {
                sessionStorage.setItem('lawsker_session_start', new Date().toISOString());
            }
            
            // 页面卸载时记录会话结束
            window.addEventListener('beforeunload', () => {
                this.recordSessionEnd();
            });
            
            // 页面隐藏时记录（移动端兼容）
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'hidden') {
                    this.recordSessionEnd();
                }
            });
        },

        // 记录会话结束
        recordSessionEnd() {
            const sessionStart = sessionStorage.getItem('lawsker_session_start');
            if (sessionStart) {
                const duration = Date.now() - new Date(sessionStart).getTime();
                const sessionData = {
                    duration: Math.round(duration / 1000), // 秒
                    endTime: new Date().toISOString(),
                    pages: this.getSessionPages()
                };
                
                // 可以在这里记录会话详细信息
                console.log('会话结束:', sessionData);
            }
        },

        // 获取本次会话访问的页面
        getSessionPages() {
            // 简化实现，后续可以扩展
            return [window.location.pathname];
        },

        // 获取统计摘要
        getSummary() {
            const analytics = this.getStoredData();
            const today = new Date().toDateString();
            const todayData = analytics[today] || { pv: 0, sessions: [], pages: {} };
            
            // 计算总数据
            let totalPV = 0;
            let totalSessions = new Set();
            let totalPages = {};
            
            Object.values(analytics).forEach(dayData => {
                totalPV += dayData.pv || 0;
                if (dayData.sessions) {
                    dayData.sessions.forEach(s => totalSessions.add(s));
                }
                if (dayData.pages) {
                    Object.entries(dayData.pages).forEach(([page, count]) => {
                        totalPages[page] = (totalPages[page] || 0) + count;
                    });
                }
            });
            
            return {
                todayPV: todayData.pv,
                todayUV: todayData.sessions.length,
                totalPV: totalPV,
                totalUV: totalSessions.size,
                topPages: this.getTopPages(totalPages),
                deviceStats: this.getDeviceStats(analytics)
            };
        },

        // 获取热门页面
        getTopPages(totalPages) {
            return Object.entries(totalPages)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 10)
                .map(([page, count]) => ({ page, count }));
        },

        // 获取设备统计
        getDeviceStats(analytics) {
            const deviceTotals = { desktop: 0, mobile: 0, tablet: 0 };
            
            Object.values(analytics).forEach(dayData => {
                if (dayData.devices) {
                    Object.entries(dayData.devices).forEach(([device, count]) => {
                        deviceTotals[device] = (deviceTotals[device] || 0) + count;
                    });
                }
            });
            
            return deviceTotals;
        }
    };

    // 页面加载完成后自动初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => LawskerAnalytics.init());
    } else {
        LawskerAnalytics.init();
    }

    // 暴露全局接口
    window.LawskerAnalytics = LawskerAnalytics;

})(); 