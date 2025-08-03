/**
 * 用户哈希系统
 * 用于安全的用户工作台访问
 * 统一律师和用户的逻辑，使用10位哈希值
 */

class UserHashSystem {
    constructor() {
        this.baseURL = 'http://156.236.74.200/api/v1';
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
            const response = await fetch(`${this.baseURL}/users/hash-mapping`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });
            if (response.ok) {
                const mapping = await response.json();
                this.hashMapping = new Map(Object.entries(mapping));
                console.log('用户哈希映射已加载:', mapping);
            } else {
                console.warn('无法加载用户哈希映射，使用默认映射');
                this.setDefaultMapping();
            }
        } catch (error) {
            console.warn('无法加载用户哈希映射，使用默认映射:', error);
            this.setDefaultMapping();
        }
    }
    
    /**
     * 设置默认的用户哈希映射（仅用于演示）
     */
    setDefaultMapping() {
        const defaultMapping = {
            'a1b2c3d4e5': { id: '001', username: 'lawyer1', role: 'lawyer' },
            'f6g7h8i9j0': { id: '002', username: 'lawyer2', role: 'lawyer' },
            'k1l2m3n4o5': { id: '003', username: 'user1', role: 'user' },
            'p6q7r8s9t0': { id: '004', username: 'user2', role: 'user' }
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
     * 为用户生成10位哈希值
     */
    async generateUserHash(userId, username, role) {
        try {
            const response = await fetch(`${this.baseURL}/users/generate-hash/${userId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                return result.user_hash;
            } else {
                console.error('生成用户哈希失败:', response.statusText);
                return null;
            }
        } catch (error) {
            console.error('生成用户哈希时出错:', error);
            return null;
        }
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
        
        // 根据用户角色返回不同的工作台URL
        const role = userInfo.role;
        if (role === 'lawyer') {
            return `${window.location.origin}/lawyer-workspace/${hash}`;
        } else if (['user', 'sales'].includes(role)) {
            return `${window.location.origin}/user-workspace/${hash}`;
        } else {
            // 对于其他角色，使用用户工作台作为默认
            return `${window.location.origin}/user-workspace/${hash}`;
        }
    }
    
    /**
     * 重定向到用户工作台
     */
    redirectToUserWorkspace(hash) {
        const url = this.getUserWorkspaceURL(hash);
        if (url) {
            console.log('重定向到用户工作台:', url);
            window.location.href = url;
        } else {
            console.error('无效的用户哈希:', hash);
            window.location.href = '/login.html';
        }
    }
    
    /**
     * 处理登录后的重定向
     */
    async handleLoginRedirect(userData) {
        const { id, username, role } = userData;
        
        // 查找现有的哈希映射
        let hash = null;
        for (const [existingHash, userInfo] of this.hashMapping.entries()) {
            if (userInfo.id === id) {
                hash = existingHash;
                break;
            }
        }
        
        // 如果没有找到，生成新的哈希
        if (!hash) {
            console.log('为用户生成新的哈希值:', { id, username, role });
            hash = await this.generateUserHash(id, username, role);
            
            if (hash) {
                // 更新本地映射
                this.hashMapping.set(hash, { id, username, role });
                console.log('新哈希已生成:', hash);
            } else {
                console.error('无法生成用户哈希');
                window.location.href = '/login.html';
                return;
            }
        }
        
        // 重定向到用户工作台
        this.redirectToUserWorkspace(hash);
    }
    
    /**
     * 根据哈希获取用户信息
     */
    async getUserByHash(hash) {
        try {
            const response = await fetch(`${this.baseURL}/users/hash/${hash}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                console.error('获取用户信息失败:', response.statusText);
                return null;
            }
        } catch (error) {
            console.error('获取用户信息时出错:', error);
            return null;
        }
    }
    
    /**
     * 解析工作台URL中的哈希
     */
    parseWorkspaceUrl(url) {
        const match = url.match(/\/workspace\/([a-zA-Z0-9]{10})/);
        if (match) {
            return match[1];
        }
        return null;
    }
    
    /**
     * 验证工作台访问权限
     */
    validateWorkspaceAccess(userData, hash) {
        const userInfo = this.getUserInfo(hash);
        if (!userInfo) {
            return false;
        }
        
        // 检查用户ID是否匹配
        return userInfo.id === userData.id;
    }
}

// 创建全局实例
window.userHashSystem = new UserHashSystem();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserHashSystem;
} 