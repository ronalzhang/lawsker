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
    }
}));

// 简单路由映射 - 避免path-to-regexp问题
const routeHandler = (filePath) => {
    return (req, res) => {
        res.sendFile(path.join(__dirname, filePath));
    };
};

// 定义所有路由
app.get('/user', routeHandler('user-workspace.html'));
app.get('/legal', routeHandler('lawyer-workspace.html'));
app.get('/institution', routeHandler('institution-workspace.html'));
app.get('/calculator', routeHandler('earnings-calculator.html'));
app.get('/earnings-calculator', routeHandler('earnings-calculator.html'));
app.get('/withdraw', routeHandler('withdrawal.html'));
app.get('/submit', routeHandler('anonymous-task.html'));
app.get('/auth', routeHandler('login.html'));
app.get('/admin', routeHandler('admin-config.html'));
app.get('/admin-pro', routeHandler('admin-config-optimized.html'));
app.get('/console', routeHandler('dashboard.html'));

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
}); 