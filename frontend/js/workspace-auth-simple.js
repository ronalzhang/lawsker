/**
 * 简化的工作台权限验证脚本
 * 适用于直接访问的工作台页面（如 /lawyer-workspace.html）
 */

(function() {
    'use strict';
    
    console.log('🔐 工作台权限验证开始');
    
    // 获取登录信息
    const authToken = localStorage.getItem('authToken');
    const userInfo = localStorage.getItem('userInfo');
    
    // 检查是否已登录
    if (!authToken || !userInfo) {
        console.log('❌ 未登录，重定向到登录页面');
        redirectToLogin();
        return;
    }
    
    let userData;
    try {
        userData = JSON.parse(userInfo);
    } catch (e) {
        console.log('❌ 用户信息解析失败，重定向到登录页面');
        redirectToLogin();
        return;
    }
    
    // 获取当前页面路径
    const currentPath = window.location.pathname;
    
    // 根据页面路径确定期望的用户角色
    const pageRoleMapping = {
        '/lawyer-workspace.html': 'lawyer',
        '/user-workspace.html': 'user',
        '/institution-workspace.html': 'institution',
        '/admin-config-optimized.html': 'admin'
    };
    
    const expectedRole = pageRoleMapping[currentPath];
    
    if (!expectedRole) {
        console.log('❌ 未知的工作台页面:', currentPath);
        showAccessDenied('未知的工作台页面');
        return;
    }
    
    // 验证用户角色
    if (userData.role !== expectedRole) {
        console.log('❌ 用户角色不匹配', {
            userRole: userData.role,
            expectedRole: expectedRole,
            currentPage: currentPath
        });
        showAccessDenied(`此工作台仅限${getRoleDisplayName(expectedRole)}访问`);
        return;
    }
    
    console.log('✅ 权限验证通过', {
        user: userData.username,
        role: userData.role,
        workspace: currentPath
    });
    
    // 将用户信息设置为全局变量，供工作台页面使用
    window.currentUser = userData;
    window.workspaceInfo = {
        type: expectedRole,
        page: currentPath
    };
    
    /**
     * 重定向到登录页面
     */
    function redirectToLogin() {
        const redirectUrl = encodeURIComponent(window.location.href);
        window.location.href = `/auth?redirect=${redirectUrl}`;
    }
    
    /**
     * 显示访问被拒绝页面
     */
    function showAccessDenied(message) {
        document.body.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100vh; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div style="background: rgba(255,255,255,0.95); padding: 40px; border-radius: 20px; 
                           text-align: center; max-width: 500px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                    <div style="font-size: 64px; margin-bottom: 20px;">🔒</div>
                    <h1 style="color: #333; margin-bottom: 10px;">访问被拒绝</h1>
                    <p style="color: #666; margin-bottom: 30px;">${message}</p>
                    <div style="display: flex; gap: 15px; justify-content: center;">
                        <button onclick="window.location.href='/auth'" 
                                style="padding: 12px 24px; background: #667eea; color: white; border: none; 
                                       border-radius: 8px; cursor: pointer;">返回登录</button>
                        <button onclick="window.location.href='/'" 
                                style="padding: 12px 24px; background: #f8f9fa; color: #333; border: 1px solid #ddd; 
                                       border-radius: 8px; cursor: pointer;">返回首页</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 获取角色显示名称
     */
    function getRoleDisplayName(role) {
        const roleNames = {
            'lawyer': '律师',
            'user': '用户',
            'institution': '机构',
            'admin': '管理员'
        };
        return roleNames[role] || role;
    }
    
})(); 