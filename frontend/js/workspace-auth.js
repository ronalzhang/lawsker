/**
 * 个人工作台权限验证脚本
 * 确保用户只能访问自己的工作台，包含个人业务和资金等隐私信息
 */

(function() {
    'use strict';
    
    // 获取当前URL路径信息
    const currentPath = window.location.pathname;
    const currentUrl = window.location.href;
    
    console.log('🔐 个人工作台权限验证开始', {
        path: currentPath,
        url: currentUrl
    });
    
    // 检查是否为个人工作台页面
    function isPersonalWorkspace() {
        return currentPath.includes('/workspace/') || 
               /\/(user|legal|institution)\/\d+/.test(currentPath);
    }
    
    // 检查是否为演示页面
    function isDemoPage() {
        return currentPath === '/user' || 
               currentPath === '/legal' || 
               currentPath === '/institution';
    }
    
    // 如果是演示页面，不需要权限验证
    if (isDemoPage()) {
        console.log('🎭 演示页面，跳过权限验证');
        // 设置演示模式标志
        window.isDemoMode = true;
        return;
    }
    
    // 如果不是个人工作台页面，不需要验证
    if (!isPersonalWorkspace()) {
        console.log('📄 非个人工作台页面，跳过权限验证');
        return;
    }
    
    // 设置为个人工作台模式
    window.isPersonalWorkspace = true;
    window.isDemoMode = false;
    
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
    
    // 解析URL中的用户ID和工作台类型
    const workspaceInfo = parseWorkspaceUrl(currentPath);
    
    if (!workspaceInfo) {
        console.log('❌ 无效的工作台URL');
        showAccessDenied('无效的工作台地址');
        return;
    }
    
    // 验证用户权限
    const hasAccess = validateWorkspaceAccess(userData, workspaceInfo);
    
    if (!hasAccess) {
        console.log('❌ 权限验证失败', {
            userRole: userData.role,
            userId: userData.id,
            requestedWorkspace: workspaceInfo
        });
        showAccessDenied('您没有权限访问此工作台');
        return;
    }
    
    console.log('✅ 权限验证通过', {
        user: userData.username,
        role: userData.role,
        workspace: workspaceInfo.type
    });
    
    // 将用户信息设置为全局变量，供工作台页面使用
    window.currentUser = userData;
    window.workspaceInfo = workspaceInfo;
    
    /**
     * 解析工作台URL
     */
    function parseWorkspaceUrl(path) {
        // 新格式: /workspace/lawyer/user-id
        const newFormatMatch = path.match(/^\/workspace\/(lawyer|user|institution)\/([^\/]+)$/);
        if (newFormatMatch) {
            return {
                type: newFormatMatch[1],
                userId: newFormatMatch[2],
                format: 'new'
            };
        }
        
        // 旧格式: /legal/123, /user/123, /institution/123
        const oldFormatMatch = path.match(/^\/(legal|user|institution)\/([^\/]+)$/);
        if (oldFormatMatch) {
            const typeMapping = {
                'legal': 'lawyer',
                'user': 'user', 
                'institution': 'institution'
            };
            return {
                type: typeMapping[oldFormatMatch[1]],
                userId: oldFormatMatch[2],
                format: 'old'
            };
        }
        
        return null;
    }
    
    /**
     * 验证工作台访问权限
     */
    function validateWorkspaceAccess(user, workspace) {
        // 检查角色匹配
        const roleMapping = {
            'lawyer': 'lawyer',
            'sales': ['user', 'lawyer'],  // 销售角色可以访问用户和律师工作台
            'institution': 'institution',
            'admin': 'admin'
        };
        
        const expectedWorkspaceType = roleMapping[user.role];
        
        // 管理员可以访问所有工作台
        if (user.role === 'admin') {
            return true;
        }
        
        // 检查工作台类型是否匹配用户角色
        const hasAccess = Array.isArray(expectedWorkspaceType) 
            ? expectedWorkspaceType.includes(workspace.type)
            : workspace.type === expectedWorkspaceType;
            
        if (!hasAccess) {
            console.log('❌ 工作台类型与用户角色不匹配', {
                userRole: user.role,
                expectedType: expectedWorkspaceType,
                requestedType: workspace.type
            });
            return false;
        }
        
        // 检查用户ID是否匹配（用户只能访问自己的工作台）
        if (workspace.userId !== user.id) {
            console.log('❌ 用户ID不匹配，试图访问他人工作台', {
                currentUserId: user.id,
                requestedUserId: workspace.userId
            });
            return false;
        }
        
        return true;
    }
    
    /**
     * 重定向到登录页面
     */
    function redirectToLogin() {
        const redirectUrl = encodeURIComponent(currentUrl);
        window.location.href = `/login.html?redirect=${redirectUrl}`;
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
                        <button onclick="window.location.href='/login.html'" 
                                style="background: #667eea; color: white; border: none; padding: 12px 24px; 
                                       border-radius: 8px; cursor: pointer; font-size: 16px;">重新登录</button>
                        <button onclick="window.history.back()" 
                                style="background: #f1f5f9; color: #64748b; border: none; padding: 12px 24px; 
                                       border-radius: 8px; cursor: pointer; font-size: 16px;">返回上页</button>
                    </div>
                </div>
            </div>
        `;
    }
    
})(); 