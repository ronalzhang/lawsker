/**
 * 用户哈希系统
 * 用于安全的用户工作台访问
 */

class UserHashSystem {
    constructor() {
        this.baseURL = 'https://lawsker.com';
        this.hashMapping = new Map();
        this.init();
    }
    
    async init() {
        // 初始化用户哈希映射
        await this.loadUserHashMapping();
    }
    
    /**
     * 加载用户哈希映射
     */
    async loadUserHashMapping() {
        try {
            // 从API获取用户哈希映射
            const response = await fetch(`${this.baseURL}/api/v1/users/hash-mapping`);
            if (response.ok) {
                const mapping = await response.json();
                this.hashMapping = new Map(Object.entries(mapping));
            } else {
                // 使用默认映射
                this.setDefaultMapping();
            }
        } catch (error) {
            console.warn('无法加载用户哈希映射，使用默认映射:', error);
            this.setDefaultMapping();
        }
    }
    
    /**
     * 设置默认的用户哈希映射
     */
    setDefaultMapping() {
        const defaultMapping = {
            'lawyer1': { role: 'lawyer', id: '001' },
            'lawyer2': { role: 'lawyer', id: '002' },
            'user1': { role: 'user', id: '001' },
            'user2': { role: 'user', id: '002' }
        };
        
        this.hashMapping = new Map(Object.entries(defaultMapping));
    }
    
    /**
     * 根据用户哈希获取用户信息
     */
    getUserInfo(hash) {
        return this.hashMapping.get(hash);
    }
    
    /**
     * 根据用户ID生成哈希
     */
    generateUserHash(userId, role) {
        // 简单的哈希生成算法
        const hash = btoa(`${userId}-${role}-${Date.now()}`).replace(/[^a-zA-Z0-9]/g, '');
        return hash.substring(0, 8);
    }
    
    /**
     * 验证用户哈希
     */
    validateUserHash(hash) {
        return this.hashMapping.has(hash);
    }
    
    /**
     * 获取用户工作台URL
     */
    getUserWorkspaceURL(hash) {
        const userInfo = this.getUserInfo(hash);
        if (!userInfo) {
            return null;
        }
        
        return `${this.baseURL}/${hash}`;
    }
    
    /**
     * 重定向到用户工作台
     */
    redirectToUserWorkspace(hash) {
        const url = this.getUserWorkspaceURL(hash);
        if (url) {
            window.location.href = url;
        } else {
            console.error('无效的用户哈希:', hash);
            window.location.href = '/login.html';
        }
    }
    
    /**
     * 处理登录后的重定向
     */
    handleLoginRedirect(userData) {
        const { username, role } = userData;
        
        // 根据用户名和角色生成或查找哈希
        let hash = null;
        
        // 查找现有的哈希映射
        for (const [existingHash, userInfo] of this.hashMapping.entries()) {
            if (userInfo.role === role && userInfo.id === username.replace(/\D/g, '')) {
                hash = existingHash;
                break;
            }
        }
        
        // 如果没有找到，生成新的哈希
        if (!hash) {
            hash = this.generateUserHash(username, role);
            this.hashMapping.set(hash, { role, id: username.replace(/\D/g, '') });
        }
        
        // 重定向到用户工作台
        this.redirectToUserWorkspace(hash);
    }
}

// 创建全局实例
window.userHashSystem = new UserHashSystem();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserHashSystem;
} 