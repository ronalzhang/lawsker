const express = require('express');
const path = require('path');
const app = express();
const port = 6060;

// 静态文件服务
app.use(express.static(__dirname, {
    setHeaders: (res, path) => {
        if (path.endsWith('.html')) {
            res.setHeader('Cache-Control', 'no-cache');
        }
        // 确保CSS文件正确的Content-Type
        if (path.endsWith('.css')) {
            res.setHeader('Content-Type', 'text/css');
        }
        // 确保JS文件正确的Content-Type
        if (path.endsWith('.js')) {
            res.setHeader('Content-Type', 'application/javascript');
        }
    }
}));

// 简单路由映射 - 避免path-to-regexp问题
const routeHandler = (filePath) => {
    return (req, res) => {
        res.sendFile(path.join(__dirname, filePath));
    };
};

// 个人化工作台路由系统
// 格式: /workspace/{role}/{userId}

// 律师个人工作台
app.get('/workspace/lawyer/:userId', (req, res) => {
    const userId = req.params.userId;
    console.log(`访问律师工作台: ${userId}`);
    
    // 设置用户信息到页面
    res.cookie('workspace_user_id', userId);
    res.cookie('workspace_role', 'lawyer');
    
    res.sendFile(path.join(__dirname, 'lawyer-workspace.html'));
});

// 用户个人工作台
app.get('/workspace/user/:userId', (req, res) => {
    const userId = req.params.userId;
    console.log(`访问用户工作台: ${userId}`);
    
    // 设置用户信息到页面
    res.cookie('workspace_user_id', userId);
    res.cookie('workspace_role', 'user');
    
    res.sendFile(path.join(__dirname, 'user-workspace.html'));
});

// 机构个人工作台
app.get('/workspace/institution/:userId', (req, res) => {
    const userId = req.params.userId;
    console.log(`访问机构工作台: ${userId}`);
    
    // 设置用户信息到页面
    res.cookie('workspace_user_id', userId);
    res.cookie('workspace_role', 'institution');
    
    res.sendFile(path.join(__dirname, 'institution-workspace.html'));
});

// 个人化工作台路由 - 使用哈希值
app.get('/workspace/:hash', (req, res) => {
    const { hash } = req.params;
    
    // 验证哈希格式（10位字母数字）
    if (!/^[a-zA-Z0-9]{10}$/.test(hash)) {
        return res.status(400).send('无效的哈希格式');
    }
    
    // 设置工作台信息cookie
    res.cookie('workspace_hash', hash, { 
        httpOnly: false, 
        secure: false, 
        maxAge: 24 * 60 * 60 * 1000 
    });
    
    // 返回通用工作台页面，具体角色判断在前端进行
    res.sendFile(path.join(__dirname, 'workspace.html'));
});

// 律师专用工作台路由
app.get('/lawyer-workspace/:hash', (req, res) => {
    const { hash } = req.params;
    
    // 验证哈希格式（10位字母数字）
    if (!/^[a-zA-Z0-9]{10}$/.test(hash)) {
        return res.status(400).send('无效的哈希格式');
    }
    
    // 设置工作台信息cookie
    res.cookie('workspace_hash', hash, { 
        httpOnly: false, 
        secure: false, 
        maxAge: 24 * 60 * 60 * 1000 
    });
    
    // 返回律师工作台页面
    res.sendFile(path.join(__dirname, 'lawyer-workspace-universal.html'));
});

// 用户专用工作台路由
app.get('/user-workspace/:hash', (req, res) => {
    const { hash } = req.params;
    
    // 验证哈希格式（10位字母数字）
    if (!/^[a-zA-Z0-9]{10}$/.test(hash)) {
        return res.status(400).send('无效的哈希格式');
    }
    
    // 设置工作台信息cookie
    res.cookie('workspace_hash', hash, { 
        httpOnly: false, 
        secure: false, 
        maxAge: 24 * 60 * 60 * 1000 
    });
    
    // 返回用户工作台页面
    res.sendFile(path.join(__dirname, 'user-workspace-universal.html'));
});

// 兼容性重定向（保持向后兼容）
app.get('/legal/:hash', (req, res) => {
    res.redirect(`/workspace/${req.params.hash}`);
});

app.get('/user/:hash', (req, res) => {
    res.redirect(`/workspace/${req.params.hash}`);
});

app.get('/institution/:hash', (req, res) => {
    res.redirect(`/workspace/${req.params.hash}`);
});

// 演示页面（保持原有功能）
app.get('/legal', routeHandler('lawyer-workspace.html'));
app.get('/user', routeHandler('user-workspace.html'));
app.get('/institution', routeHandler('institution-workspace.html'));

// 管理员工作台
app.get('/admin', routeHandler('admin-config-optimized.html'));
app.get('/admin-config-optimized.html', routeHandler('admin-config-optimized.html'));

// 登录页面
app.get('/login', routeHandler('login.html'));
app.get('/login.html', routeHandler('login.html'));
app.get('/auth', routeHandler('auth.html'));
app.get('/auth.html', routeHandler('auth.html'));

// 其他静态页面
app.get('/dashboard', routeHandler('dashboard.html'));
app.get('/payment-settlement', routeHandler('payment-settlement.html'));
app.get('/withdrawal', routeHandler('withdrawal.html'));
app.get('/lawyer-certification', routeHandler('lawyer-certification.html'));
app.get('/lawyer-tasks', routeHandler('lawyer-tasks.html'));
app.get('/task-publish', routeHandler('task-publish.html'));
app.get('/task-execution', routeHandler('task-execution.html'));
app.get('/earnings-calculator', routeHandler('earnings-calculator.html'));
app.get('/business-flow-demo', routeHandler('business-flow-demo.html'));
app.get('/flow-test', routeHandler('flow-test.html'));
app.get('/send-records', routeHandler('send-records.html'));
app.get('/monitoring-dashboard', routeHandler('monitoring-dashboard.html'));
app.get('/ai-document-generator', routeHandler('ai-document-generator.html'));
app.get('/anonymous-task', routeHandler('anonymous-task.html'));

// 测试页面
app.get('/test-personalized', routeHandler('test-personalized-workspace.html'));
app.get('/test-personalized-workspace.html', routeHandler('test-personalized-workspace.html'));

// 首页
app.get('/', routeHandler('index.html'));
app.get('/index.html', routeHandler('index.html'));

// 404处理
app.use((req, res) => {
    res.status(404).sendFile(path.join(__dirname, '404.html'));
});

// 错误处理
app.use((err, req, res, next) => {
    console.error('服务器错误:', err);
    res.status(500).send('Internal Server Error');
});

// 用户工作台路由 - 基于用户哈希
app.get('/:userHash', async (req, res) => {
    const userHash = req.params.userHash;
    
    // 检查是否为已知的静态路由
    const staticRoutes = ['admin', 'login', 'legal', 'user', 'institution', 'api', 'docs', 'health'];
    if (staticRoutes.includes(userHash)) {
        return next();
    }
    
    try {
        // 这里应该根据userHash查询用户信息
        // 暂时使用简单的映射逻辑
        const userMapping = {
            'lawyer1': 'lawyer',
            'lawyer2': 'lawyer', 
            'user1': 'user',
            'user2': 'user'
        };
        
        const userRole = userMapping[userHash];
        
        if (userRole === 'lawyer') {
            res.sendFile(path.join(__dirname, 'lawyer-workspace.html'));
        } else if (userRole === 'user') {
            res.sendFile(path.join(__dirname, 'user-workspace.html'));
        } else {
            // 未知用户哈希，返回404
            res.status(404).sendFile(path.join(__dirname, '404.html'));
        }
    } catch (error) {
        console.error('用户工作台路由错误:', error);
        res.status(500).send('服务器错误');
    }
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Lawsker frontend server running on port ${port}`);
    console.log(`Static files served from: ${__dirname}`);
}); 