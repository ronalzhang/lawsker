/**
 * 个人化工作台权限验证脚本
 * 支持个人化URL和用户数据加载
 */

(function() {
    'use strict';
    
    console.log('🔐 个人化工作台权限验证开始');
    
    // 获取当前URL路径信息
    const currentPath = window.location.pathname;
    const urlParams = new URLSearchParams(window.location.search);
    
    // 解析URL中的用户信息
    const workspaceInfo = parseWorkspaceUrl(currentPath);
    
    // 获取登录信息
    const authToken = localStorage.getItem('authToken');
    const userInfo = localStorage.getItem('userInfo');
    
    // 检查是否为演示页面
    if (isDemoPage(currentPath)) {
        console.log('🎭 演示页面，跳过权限验证');
        window.isDemoMode = true;
        window.currentUser = getDemoUserInfo();
        return;
    }
    
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
    
    // 验证工作台访问权限
    if (workspaceInfo) {
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
            workspace: workspaceInfo
        });
        
        // 设置工作台信息
        window.currentUser = userData;
        window.workspaceInfo = workspaceInfo;
        window.isPersonalWorkspace = true;
        window.isDemoMode = false;
        
        // 加载用户个人数据
        loadPersonalData(userData, workspaceInfo);
    } else {
        console.log('⚠️ 无法解析工作台URL，使用默认模式');
        window.currentUser = userData;
        window.isDemoMode = false;
    }
    
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
     * 检查是否为演示页面
     */
    function isDemoPage(path) {
        return path === '/user' || 
               path === '/legal' || 
               path === '/institution' ||
               path === '/lawyer-workspace.html' ||
               path === '/user-workspace.html' ||
               path === '/institution-workspace.html';
    }
    
    /**
     * 验证工作台访问权限
     */
    function validateWorkspaceAccess(userData, workspaceInfo) {
        // 检查用户角色是否匹配
        if (userData.role !== workspaceInfo.type) {
            return false;
        }
        
        // 检查用户ID是否匹配（如果URL中有用户ID）
        if (workspaceInfo.userId && workspaceInfo.userId !== 'demo') {
            const userId = userData.id || userData.user_id;
            if (userId && userId.toString() !== workspaceInfo.userId) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * 加载用户个人数据
     */
    async function loadPersonalData(userData, workspaceInfo) {
        try {
            console.log('📊 加载用户个人数据:', workspaceInfo);
            
            // 根据工作台类型加载不同的数据
            switch (workspaceInfo.type) {
                case 'lawyer':
                    await loadLawyerPersonalData(userData, workspaceInfo);
                    break;
                case 'user':
                    await loadUserPersonalData(userData, workspaceInfo);
                    break;
                case 'institution':
                    await loadInstitutionPersonalData(userData, workspaceInfo);
                    break;
            }
        } catch (error) {
            console.error('加载个人数据失败:', error);
        }
    }
    
    /**
     * 加载律师个人数据
     */
    async function loadLawyerPersonalData(userData, workspaceInfo) {
        // 更新页面标题和用户信息
        updatePageTitle(`律师工作台 - ${userData.name || userData.username}`);
        updateUserInfo(userData);
        
        // 加载律师统计数据
        await loadLawyerStats(userData.id);
        
        // 加载律师案件列表
        await loadLawyerCases(userData.id);
        
        // 加载律师提现统计
        await loadLawyerWithdrawalStats(userData.id);
    }
    
    /**
     * 加载用户个人数据
     */
    async function loadUserPersonalData(userData, workspaceInfo) {
        // 更新页面标题和用户信息
        updatePageTitle(`用户工作台 - ${userData.name || userData.username}`);
        updateUserInfo(userData);
        
        // 加载用户统计数据
        await loadUserStats(userData.id);
        
        // 加载用户任务列表
        await loadUserTasks(userData.id);
    }
    
    /**
     * 加载机构个人数据
     */
    async function loadInstitutionPersonalData(userData, workspaceInfo) {
        // 更新页面标题和用户信息
        updatePageTitle(`机构工作台 - ${userData.name || userData.username}`);
        updateUserInfo(userData);
        
        // 加载机构统计数据
        await loadInstitutionStats(userData.id);
    }
    
    /**
     * 更新页面标题
     */
    function updatePageTitle(title) {
        document.title = title;
        const titleElement = document.querySelector('.page-title');
        if (titleElement) {
            titleElement.textContent = title.split(' - ')[0];
        }
    }
    
    /**
     * 更新用户信息显示
     */
    function updateUserInfo(userData) {
        const userNameElement = document.getElementById('userName');
        const userAvatarElement = document.getElementById('userAvatar');
        
        if (userNameElement) {
            userNameElement.textContent = userData.name || userData.username || '用户';
        }
        
        if (userAvatarElement) {
            const name = userData.name || userData.username || '用户';
            userAvatarElement.textContent = name.charAt(0);
        }
    }
    
    /**
     * 获取演示用户信息
     */
    function getDemoUserInfo() {
        const currentPath = window.location.pathname;
        
        if (currentPath.includes('lawyer') || currentPath === '/legal') {
            return {
                id: 'demo-lawyer',
                username: '张律师',
                role: 'lawyer',
                name: '张律师'
            };
        } else if (currentPath.includes('user') || currentPath === '/user') {
            return {
                id: 'demo-user',
                username: '李用户',
                role: 'user',
                name: '李用户'
            };
        } else {
            return {
                id: 'demo',
                username: '演示用户',
                role: 'user',
                name: '演示用户'
            };
        }
    }
    
    /**
     * 重定向到登录页面
     */
    function redirectToLogin() {
        const currentUrl = encodeURIComponent(window.location.href);
        window.location.href = `/login?redirect=${currentUrl}`;
    }
    
    /**
     * 显示访问被拒绝
     */
    function showAccessDenied(message) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 500px;">
                <div class="modal-header">
                    <h3>🚫 访问被拒绝</h3>
                </div>
                <div class="modal-body">
                    <p style="margin: 20px 0; font-size: 16px; color: #666;">${message}</p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="window.location.href='/login'">
                        返回登录
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // 导出函数供页面使用
    window.loadLawyerStats = loadLawyerStats;
    window.loadLawyerCases = loadLawyerCases;
    window.loadLawyerWithdrawalStats = loadLawyerWithdrawalStats;
    window.loadUserStats = loadUserStats;
    window.loadUserTasks = loadUserTasks;
    window.loadInstitutionStats = loadInstitutionStats;
    
    // 这些函数需要在具体的工作台页面中实现
    async function loadLawyerStats(userId) {
        console.log('加载律师统计数据:', userId);
        // 实现律师统计数据加载
    }
    
    async function loadLawyerCases(userId) {
        console.log('加载律师案件列表:', userId);
        // 实现律师案件列表加载
    }
    
    async function loadLawyerWithdrawalStats(userId) {
        console.log('加载律师提现统计:', userId);
        // 实现律师提现统计加载
    }
    
    async function loadUserStats(userId) {
        console.log('加载用户统计数据:', userId);
        // 实现用户统计数据加载
    }
    
    async function loadUserTasks(userId) {
        console.log('加载用户任务列表:', userId);
        // 实现用户任务列表加载
    }
    
    async function loadInstitutionStats(userId) {
        console.log('加载机构统计数据:', userId);
        // 实现机构统计数据加载
    }
})(); 