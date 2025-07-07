// Authentication Guard - JWT Token validation and route protection
class AuthGuard {
    constructor() {
        this.token = localStorage.getItem('authToken');
        this.userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
        // Do not init immediately - wait for DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        // Immediately check page access before any content is displayed
        const accessAllowed = this.checkPageAccess();
        if (!accessAllowed) {
            // Hide page content immediately if access is denied
            this.hidePageContent();
            return;
        }
        
        // Listen for storage changes
        window.addEventListener('storage', (e) => {
            if (e.key === 'authToken' || e.key === 'userInfo') {
                this.token = localStorage.getItem('authToken');
                this.userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
                this.checkPageAccess();
            }
        });
    }

    // Hide page content immediately
    hidePageContent() {
        if (document.body) {
            document.body.style.display = 'none';
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                document.body.style.display = 'none';
            });
        }
    }

    // Check page access permissions
    checkPageAccess() {
        const currentPath = window.location.pathname;
        const isPublicRoute = this.isPublicRoute(currentPath);
        const isDemoRoute = this.isDemoRoute(currentPath);
        const isAdminProRoute = currentPath === '/admin-pro' || currentPath === '/admin-pro.html' || currentPath.startsWith('/admin-pro/');
        
        console.log('Auth Guard - Checking page access:', {
            path: currentPath,
            isPublic: isPublicRoute,
            isDemo: isDemoRoute,
            isAdminPro: isAdminProRoute,
            hasToken: !!this.token
        });

        // Demo routes do not need authentication
        if (isDemoRoute) {
            console.log('Auth Guard - Demo route, allow access');
            return true;
        }

        // Public routes do not need authentication
        if (isPublicRoute) {
            console.log('Auth Guard - Public route, allow access');
            return true;
        }

        // Admin-pro route special handling - no JWT required, direct password verification
        if (isAdminProRoute) {
            console.log('Auth Guard - Admin-pro route, password verification');
            return this.checkAdminAccess();
        }

        // Routes requiring authentication
        if (!this.isAuthenticated()) {
            console.log('Auth Guard - Not authenticated, redirect to login');
            this.redirectToLogin();
            return false;
        }

        // Check user role permissions
        if (!this.hasRoutePermission(currentPath)) {
            console.log('Auth Guard - Insufficient permissions, redirect to home');
            this.redirectToHome();
            return false;
        }

        console.log('Auth Guard - Access granted');
        return true;
    }

    // Check if it's a public route
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

    // Check if it's a demo route
    isDemoRoute(path) {
        const demoRoutes = [
            '/user',
            '/legal',
            '/user/',
            '/legal/'
        ];
        // Only exact match demo routes are allowed, personal pages like /legal/001 need authentication
        return demoRoutes.includes(path) || demoRoutes.includes(path.replace(/\/$/, ''));
    }

    // Check if user is authenticated
    isAuthenticated() {
        if (!this.token) return false;
        
        try {
            const payload = JSON.parse(atob(this.token.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            
            // Check if token is expired
            if (payload.exp && payload.exp < now) {
                console.log('Auth Guard - Token expired');
                this.logout();
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('Auth Guard - Token parsing failed:', error);
            this.logout();
            return false;
        }
    }

    // Check admin access permissions
    checkAdminAccess() {
        // Check if admin password has been verified
        const adminAuth = sessionStorage.getItem('adminAuth');
        if (adminAuth) {
            const authData = JSON.parse(adminAuth);
            // Check if within 30 minutes
            if (Date.now() - authData.timestamp < 30 * 60 * 1000) {
                return true;
            }
        }

        // Need password verification
        const password = prompt('Please enter admin password:');
        if (password === '123abc74531') {
            // Save verification status
            sessionStorage.setItem('adminAuth', JSON.stringify({
                timestamp: Date.now(),
                verified: true
            }));
            return true;
        } else if (password !== null) {
            alert('Wrong password!');
        }

        return false;
    }

    // Check route permissions
    hasRoutePermission(path) {
        // Admin-pro route special handling - already handled in checkPageAccess
        if (path === '/admin-pro' || path === '/admin-pro.html' || path.startsWith('/admin-pro/')) {
            return true; // checkPageAccess already verified
        }

        if (!this.userInfo.role) return false;

        const userRole = this.userInfo.role;
        const userId = this.userInfo.id;

        // Admin can access all routes
        if (userRole === 'admin') return true;

        // Users can only access their own workspace
        if (path.startsWith('/user/')) {
            const pathUserId = path.split('/user/')[1];
            if (!pathUserId) return false; // Wrong path format
            
            // User ID to username mapping
            const userMapping = {
                '001': 'user1',
                '002': 'user2',
                '003': 'user3',
                '004': 'user4',
                '005': 'user5',
                '006': 'user1', // Reuse user1
                '007': 'user2', // Reuse user2
                '008': 'user3', // Reuse user3
                '009': 'user4', // Reuse user4
                '010': 'user5'  // Reuse user5
            };
            
            const expectedUsername = userMapping[pathUserId];
            const currentUsername = this.userInfo.username || this.userInfo.email?.split('@')[0];
            
            console.log('Auth Guard - User permission verification:', {
                pathUserId,
                expectedUsername,
                currentUsername,
                userRole
            });
            
            return (userRole === 'user' || userRole === 'sales') && currentUsername === expectedUsername;
        }

        // Lawyers can only access their own workspace
        if (path.startsWith('/legal/')) {
            const pathLawyerId = path.split('/legal/')[1];
            if (!pathLawyerId) return false; // Wrong path format
            
            // Lawyer ID to username mapping
            const lawyerMapping = {
                '001': 'lawyer1',
                '002': 'lawyer2',
                '003': 'lawyer3',
                '004': 'lawyer4',
                '005': 'lawyer5',
                '006': 'lawyer1', // Reuse lawyer1
                '007': 'lawyer2', // Reuse lawyer2
                '008': 'lawyer3', // Reuse lawyer3
                '009': 'lawyer4', // Reuse lawyer4
                '010': 'lawyer5'  // Reuse lawyer5
            };
            
            const expectedUsername = lawyerMapping[pathLawyerId];
            const currentUsername = this.userInfo.username || this.userInfo.email?.split('@')[0];
            
            console.log('Auth Guard - Lawyer permission verification:', {
                pathLawyerId,
                expectedUsername,
                currentUsername,
                userRole
            });
            
            return userRole === 'lawyer' && currentUsername === expectedUsername;
        }

        // Institution workspace permissions
        if (path.startsWith('/institution/')) {
            const pathInstitutionId = path.split('/institution/')[1];
            return userRole === 'institution' && pathInstitutionId === userId;
        }

        // Other login required pages
        const loginRequiredRoutes = [
            '/dashboard',
            '/calculator',
            '/withdrawal',
            '/admin'
        ];
        return loginRequiredRoutes.some(route => path.startsWith(route));
    }

    // Redirect to login page
    redirectToLogin() {
        const currentPath = window.location.pathname;
        const returnUrl = encodeURIComponent(currentPath);
        console.log('Auth Guard - Redirecting to login with returnUrl:', returnUrl);
        window.location.href = `/login.html?returnUrl=${returnUrl}`;
    }

    // Redirect to home page
    redirectToHome() {
        console.log('Auth Guard - Redirecting to home page');
        window.location.href = '/';
    }

    // Logout
    logout() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        this.token = null;
        this.userInfo = {};
        // Trigger logout event
        window.dispatchEvent(new CustomEvent('authLogout'));
    }

    // Login
    login(token, userInfo) {
        localStorage.setItem('authToken', token);
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
        this.token = token;
        this.userInfo = userInfo;
        // Trigger login event
        window.dispatchEvent(new CustomEvent('authLogin', { detail: { userInfo } }));
    }

    // Get user info
    getUserInfo() {
        return this.userInfo;
    }

    // Get auth header
    getAuthHeader() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }

    // Generate demo user data
    generateDemoUserData(type, id) {
        const demoUsers = {
            user: {
                id: id,
                name: `User${id}`,
                role: 'user',
                level: 'Legal Expert',
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
                name: `Lawyer${id}`,
                role: 'lawyer',
                level: 'Senior Lawyer',
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

// Global auth guard instance - Initialize immediately
console.log('Auth Guard - Initializing...');
window.authGuard = new AuthGuard();

// Export auth guard class
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthGuard;
} 