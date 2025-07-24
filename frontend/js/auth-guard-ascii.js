// Authentication Guard - ASCII Version
// Protects pages from unauthorized access

class AuthGuard {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.checkPageAccess());
        } else {
            this.checkPageAccess();
        }
    }

    // Check if current page requires authentication
    checkPageAccess() {
        const currentPath = window.location.pathname;
        console.log('Checking access for:', currentPath);
        
        // Public pages that don't require authentication
        const publicPaths = [
            '/',
            '/index.html',
            '/login.html',
            '/login',
            '/anonymous-task.html',
            '/anonymous-task',
            '/legal',
            '/user',
            '/legal/',
            '/user/',
            '/js/auth-guard.js'
        ];

        // Check if it's a public path
        const isPublicPath = publicPaths.some(path => {
            if (path === currentPath) return true;
            if (path.endsWith('/') && currentPath.startsWith(path)) return true;
            return false;
        });

        if (isPublicPath) {
            console.log('Public path detected, allowing access');
            return;
        }

        // Check for admin routes (password verification)
        const isAdminProRoute = this.isAdminProPage(currentPath);
        
        if (isAdminProRoute) {
            console.log('Admin-pro route detected, checking admin access');
            if (!this.checkAdminAccess()) {
                console.log('Admin access denied');
                return;
            }
        } else {
            // Regular authentication check
            console.log('Protected route detected, checking authentication');
            const accessAllowed = this.checkAuthentication();
            if (!accessAllowed) {
                console.log('Authentication failed, redirecting to login');
                const returnUrl = encodeURIComponent(currentPath);
                window.location.href = `/login.html?returnUrl=${returnUrl}`;
                return;
            }
        }

        console.log('Access granted');
    }

    // Check if current page is admin-pro page
    isAdminProPage(currentPath) {
        // Check both URL path and file name
        const adminProPaths = [
            '/admin-pro',
            '/admin-pro/',
            '/admin-pro.html',
            '/admin-config-optimized.html'
        ];
        
        // Check direct path match
        if (adminProPaths.includes(currentPath)) {
            return true;
        }
        
        // Check if URL contains admin-pro parameter or file name
        if (currentPath.includes('admin-pro') || 
            currentPath.includes('admin-config-optimized') ||
            window.location.href.includes('admin-pro')) {
            return true;
        }
        
        return false;
    }

    // Check user authentication
    checkAuthentication() {
        // Check if user is logged in
        const token = localStorage.getItem('userToken');
        if (!token) {
            return false;
        }

        // Additional role-based checks can be added here
        return true;
    }

    // Check admin access permissions
    checkAdminAccess() {
        // Check if admin password has been verified recently
        const adminAuth = sessionStorage.getItem('adminAuth');
        if (adminAuth) {
            try {
                const authData = JSON.parse(adminAuth);
                // Check if within 30 minutes and for correct page
                if (Date.now() - authData.timestamp < 30 * 60 * 1000 && authData.page === 'admin-pro') {
                    console.log('Admin auth found and valid');
                    return true;
                }
            } catch (e) {
                // Invalid auth data, clear it
                sessionStorage.removeItem('adminAuth');
            }
        }

        // Show custom password modal
        console.log('No valid admin auth found, showing password modal');
        this.showPasswordModal();
        return false;
    }

    // Show glassmorphism password modal
    showPasswordModal() {
        // Hide page content immediately
        document.body.style.visibility = 'hidden';
        
        // Create modal overlay
        const modalOverlay = document.createElement('div');
        modalOverlay.id = 'admin-password-modal';
        modalOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(10px);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        // Create modal container
        const modalContainer = document.createElement('div');
        modalContainer.style.cssText = `
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 40px;
            min-width: 400px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            transform: translateY(-20px);
            transition: all 0.3s ease;
        `;

        // Create modal content
        modalContainer.innerHTML = `
            <div style="text-align: center; color: white;">
                <div style="font-size: 48px; margin-bottom: 20px;">🔐</div>
                <h2 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">管理员验证</h2>
                <p style="margin: 0 0 30px 0; opacity: 0.8; font-size: 14px;">请输入管理员密码以继续</p>
                
                <div style="position: relative; margin-bottom: 30px;">
                    <input 
                        type="password" 
                        id="admin-password-input"
                        placeholder="请输入密码"
                        style="
                            width: 100%;
                            padding: 15px 20px;
                            background: rgba(255, 255, 255, 0.1);
                            border: 1px solid rgba(255, 255, 255, 0.3);
                            border-radius: 12px;
                            color: white;
                            font-size: 16px;
                            outline: none;
                            box-sizing: border-box;
                            transition: all 0.3s ease;
                        "
                    />
                </div>
                
                <div style="display: flex; gap: 15px; justify-content: center;">
                    <button 
                        id="admin-cancel-btn"
                        style="
                            padding: 12px 24px;
                            background: rgba(255, 255, 255, 0.1);
                            border: 1px solid rgba(255, 255, 255, 0.3);
                            border-radius: 8px;
                            color: white;
                            font-size: 14px;
                            cursor: pointer;
                            transition: all 0.3s ease;
                            min-width: 80px;
                        "
                    >取消</button>
                    <button 
                        id="admin-confirm-btn"
                        style="
                            padding: 12px 24px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            border: none;
                            border-radius: 8px;
                            color: white;
                            font-size: 14px;
                            cursor: pointer;
                            transition: all 0.3s ease;
                            min-width: 80px;
                            font-weight: 600;
                        "
                    >确认</button>
                </div>
                
                <div id="admin-error-msg" style="
                    margin-top: 15px;
                    padding: 10px;
                    background: rgba(255, 87, 87, 0.1);
                    border: 1px solid rgba(255, 87, 87, 0.3);
                    border-radius: 8px;
                    color: #ff5757;
                    font-size: 14px;
                    display: none;
                ">密码错误，请重试</div>
            </div>
        `;

        modalOverlay.appendChild(modalContainer);
        document.body.appendChild(modalOverlay);

        // Animation in
        setTimeout(() => {
            modalOverlay.style.opacity = '1';
            modalContainer.style.transform = 'translateY(0)';
        }, 10);

        // Add CSS for input focus effects
        const style = document.createElement('style');
        style.textContent = `
            #admin-password-input:focus {
                border-color: rgba(102, 126, 234, 0.8) !important;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
            }
            #admin-cancel-btn:hover {
                background: rgba(255, 255, 255, 0.2) !important;
                transform: translateY(-1px) !important;
            }
            #admin-confirm-btn:hover {
                background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4) !important;
            }
        `;
        document.head.appendChild(style);

        // Event handlers
        const passwordInput = document.getElementById('admin-password-input');
        const confirmBtn = document.getElementById('admin-confirm-btn');
        const cancelBtn = document.getElementById('admin-cancel-btn');
        const errorMsg = document.getElementById('admin-error-msg');

        // Focus input
        setTimeout(() => passwordInput.focus(), 300);

        // Handle verification
        const verifyPassword = () => {
            const password = passwordInput.value;
            if (password === '123abc74531') {
                // Save verification status with page identifier
                sessionStorage.setItem('adminAuth', JSON.stringify({
                    timestamp: Date.now(),
                    verified: true,
                    page: 'admin-pro'
                }));
                
                // Success animation and close
                modalContainer.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    modalOverlay.style.opacity = '0';
                    modalContainer.style.transform = 'translateY(-20px)';
                    setTimeout(() => {
                        document.body.removeChild(modalOverlay);
                        document.head.removeChild(style);
                        // Show page content
                        document.body.style.visibility = 'visible';
                    }, 300);
                }, 200);
            } else {
                // Show error
                errorMsg.style.display = 'block';
                passwordInput.style.borderColor = 'rgba(255, 87, 87, 0.8)';
                passwordInput.style.animation = 'shake 0.5s ease-in-out';
                
                // Reset error after animation
                setTimeout(() => {
                    passwordInput.style.animation = '';
                    passwordInput.focus();
                    passwordInput.select();
                }, 500);
            }
        };

        // Handle cancel
        const cancelVerification = () => {
            modalOverlay.style.opacity = '0';
            modalContainer.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                document.body.removeChild(modalOverlay);
                document.head.removeChild(style);
                // Redirect to home
                window.location.href = '/';
            }, 300);
        };

        // Event listeners
        confirmBtn.addEventListener('click', verifyPassword);
        cancelBtn.addEventListener('click', cancelVerification);
        passwordInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                verifyPassword();
            } else if (e.key === 'Escape') {
                cancelVerification();
            }
        });

        // Hide error on input
        passwordInput.addEventListener('input', () => {
            errorMsg.style.display = 'none';
            passwordInput.style.borderColor = 'rgba(255, 255, 255, 0.3)';
        });

        // Add shake animation
        if (!document.getElementById('shake-animation')) {
            const shakeStyle = document.createElement('style');
            shakeStyle.id = 'shake-animation';
            shakeStyle.textContent = `
                @keyframes shake {
                    0%, 20%, 40%, 60%, 80%, 100% { transform: translateX(0); }
                    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                }
            `;
            document.head.appendChild(shakeStyle);
        }
    }
}

// Initialize auth guard
new AuthGuard(); 