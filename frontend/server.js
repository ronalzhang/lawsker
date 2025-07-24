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

// 演示页面路由（无需认证）
app.get('/user', routeHandler('user-workspace.html'));
app.get('/legal', routeHandler('lawyer-workspace.html'));
// 注意：机构工作台项目已暂停开发
app.get('/institution', routeHandler('institution-workspace.html'));

// 个人工作台路由（需要认证和权限验证）
app.get('/workspace/lawyer/:userId', routeHandler('lawyer-workspace.html'));
app.get('/workspace/user/:userId', routeHandler('user-workspace.html'));
// 注意：机构工作台项目已暂停开发
app.get('/workspace/institution/:userId', routeHandler('institution-workspace.html'));

// 旧版个人路由（保持兼容性，但建议使用新格式）
app.get('/user/:userId', routeHandler('user-workspace.html'));
app.get('/legal/:lawyerId', routeHandler('lawyer-workspace.html'));
// 注意：机构工作台项目已暂停开发
app.get('/institution/:institutionId', routeHandler('institution-workspace.html'));
app.get('/calculator', routeHandler('earnings-calculator.html'));
app.get('/earnings-calculator', routeHandler('earnings-calculator.html'));
app.get('/withdraw', routeHandler('withdrawal.html'));
app.get('/submit', routeHandler('anonymous-task.html'));
app.get('/auth', routeHandler('login.html'));

// O2O业务流程页面路由
app.get('/task/publish', routeHandler('task-publish.html'));
app.get('/task/lawyer-tasks', routeHandler('lawyer-tasks.html'));
app.get('/task/ai-generator', routeHandler('ai-document-generator.html'));
app.get('/task/execution', routeHandler('task-execution.html'));
app.get('/payment/settlement', routeHandler('payment-settlement.html'));
app.get('/demo/business-flow', routeHandler('business-flow-demo.html'));

// 测试和维护页面路由
app.get('/test/flow', routeHandler('flow-test.html'));

// 管理后台路由 - 只允许admin-pro访问
app.get('/admin-pro', routeHandler('admin-config-clean.html'));
app.get('/admin-new', routeHandler('admin-fixed-final.html'));
app.get('/admin-test', routeHandler('admin-test-minimal.html'));
app.get('/admin-backup', routeHandler('admin-config-optimized.html'));
app.get('/console', routeHandler('dashboard.html'));

// 禁止直接访问HTML文件
app.get('/admin-config-optimized.html', (req, res) => {
    res.status(404).send('Not Found');
});

// 兼容性重定向
app.get('/sales', (req, res) => {
    res.redirect(301, '/user');
});

// 默认首页
app.get('/', routeHandler('index.html'));

// 404处理
app.use((req, res) => {
    res.status(404).sendFile(path.join(__dirname, 'index.html'));
});

// 错误处理
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).send('Internal Server Error');
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Lawsker frontend server running on port ${port}`);
    console.log(`Static files served from: ${__dirname}`);
}); 