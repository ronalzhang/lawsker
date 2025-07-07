// 认证守卫 - JWT Token验证和路由保护
class AuthGuard {
    constructor() {
        this.token = localStorage.getItem('authToken');
        this.userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
        this.init();
    }

    init() {
        // 检查当前页面是否需要认证
        this.checkPageAccess();
        
        // 监听存储变化
        window.addEventListener('storage', (e) => {
            if (e.key === 'authToken' || e.key === 'userInfo') {
                this.token = localStorage.getItem('authToken');
                this.userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
                this.checkPageAccess();
            }
        });
    }

    // 检查页面访问权限
    checkPageAccess() {
        const currentPath = window.location.pathname;
        const isPublicRoute = this.isPublicRoute(currentPath);
        const isDemoRoute = this.isDemoRoute(currentPath);
        
        console.log('检查页面访问权限:', {
            path: currentPath,
            isPublic: isPublicRoute,
            isDemo: isDemoRoute,
            hasToken: !!this.token
        });

        // 演示路由不需要认证
        if (isDemoRoute) {
            console.log('演示路由，允许访问');
            return true;
        }

        // 公共路由不需要认证
        if (isPublicRoute) {
            return true;
        }

        // 需要认证的路由
        if (!this.isAuthenticated()) {
            console.log('未认证，重定向到登录页');
            this.redirectToLogin();
            return false;
        }

        // 检查用户角色权限
        if (!this.hasRoutePermission(currentPath)) {
            console.log('权限不足，重定向到首页');
            this.redirectToHome();
            return false;
        }

        return true;
    }

    // 判断是否为公共路由
    isPublicRoute(path) {
        const publicRoutes = [
            '/',
            '/index.html',
            '/login.html',
            '/login',
            '/anonymous-task.html',
            '/anonymous-task'
        ];
        return publicRoutes.includes(path) || publicRoutes.includes(path.replace('.html', ''));
    }

    // 判断是否为演示路由
    isDemoRoute(path) {
        const demoRoutes = [
            '/user',
            '/legal',
            '/user/',
            '/legal/'
        ];
        return demoRoutes.some(route => path.startsWith(route));
    }

    // 检查用户是否已认证
    isAuthenticated() {
        if (!this.token) return false;
        
        try {
            const payload = JSON.parse(atob(this.token.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            
            // 检查token是否过期
            if (payload.exp && payload.exp < now) {
                console.log('Token已过期');
                this.logout();
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('Token解析失败:', error);
            this.logout();
            return false;
        }
    }

    // 检查管理后台访问权限
    checkAdminAccess() {
        // 检查是否已经验证过管理员密码
        const adminAuth = sessionStorage.getItem('adminAuth');
        if (adminAuth) {
            const authData = JSON.parse(adminAuth);
            // 检查是否在30分钟内
            if (Date.now() - authData.timestamp < 30 * 60 * 1000) {
                return true;
            }
        }

        // 需要密码验证
        const password = prompt('请输入管理员密码：');
        if (password === '123abc74531') {
            // 保存验证状态
            sessionStorage.setItem('adminAuth', JSON.stringify({
                timestamp: Date.now(),
                verified: true
            }));
            return true;
        } else if (password !== null) {
            alert('密码错误！');
        }

        return false;
    }

    // 检查路由权限
    hasRoutePermission(path) {
        if (!this.userInfo.role) return false;

        const userRole = this.userInfo.role;
        const userId = this.userInfo.id;

        // 管理员可以访问所有路由
        if (userRole === 'admin') return true;

        // 用户只能访问自己的工作台
        if (path.startsWith('/user/')) {
            const pathUserId = path.split('/user/')[1];
            return userRole === 'user' && pathUserId === userId;
        }

        // 律师只能访问自己的工作台
        if (path.startsWith('/legal/')) {
            const pathLawyerId = path.split('/legal/')[1];
            return userRole === 'lawyer' && pathLawyerId === userId;
        }

        // 机构工作台权限
        if (path.startsWith('/institution/')) {
            const pathInstitutionId = path.split('/institution/')[1];
            return userRole === 'institution' && pathInstitutionId === userId;
        }

        // 管理后台特殊处理 - 使用简单密码验证
        if (path === '/admin-pro' || path.startsWith('/admin-pro')) {
            return this.checkAdminAccess();
        }

        // 其他需要登录的页面
        const loginRequiredRoutes = [
            '/dashboard',
            '/calculator',
            '/withdrawal',
            '/admin'
        ];

        return loginRequiredRoutes.some(route => path.startsWith(route));
    }

    // 重定向到登录页
    redirectToLogin() {
        const currentPath = window.location.pathname;
        const returnUrl = encodeURIComponent(currentPath);
        window.location.href = `/login.html?returnUrl=${returnUrl}`;
    }

    // 重定向到首页
    redirectToHome() {
        window.location.href = '/';
    }

    // 登出
    logout() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        this.token = null;
        this.userInfo = {};
        
        // 触发登出事件
        window.dispatchEvent(new CustomEvent('authLogout'));
    }

    // 登录
    login(token, userInfo) {
        localStorage.setItem('authToken', token);
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
        this.token = token;
        this.userInfo = userInfo;
        
        // 触发登录事件
        window.dispatchEvent(new CustomEvent('authLogin', { detail: { userInfo } }));
    }

    // 获取用户信息
    getUserInfo() {
        return this.userInfo;
    }

    // 获取认证头部
    getAuthHeader() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }

    // 生成演示用户数据
    generateDemoUserData(type, id) {
        const demoUsers = {
            user: {
                id: id,
                name: `用户${id}`,
                role: 'user',
                level: '律客达人',
                avatar: id.charAt(0).toUpperCase(),
                stats: {
                    totalTasks: 5,
                    uploadedData: 3,
                    totalEarnings: 2580,
                    monthlyEarnings: 680
                }
            },
            legal: {
                id: id,
                name: `律师${id}`,
                role: 'lawyer',
                level: '资深律师',
                avatar: id.charAt(0).toUpperCase(),
                stats: {
                    totalCases: 15,
                    completedCases: 12,
                    totalEarnings: 25800,
                    monthlyEarnings: 6800
                }
            }
        };

        return demoUsers[type] || null;
    }
}

// 全局认证守卫实例
window.authGuard = new AuthGuard();

// 导出认证守卫类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthGuard;
} 