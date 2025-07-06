const express = require('express');
const path = require('path');
const app = express();
const port = 6060;

// 静态文件服务
app.use(express.static(__dirname));

// 路由映射
const routes = {
    '/user': '/user-workspace.html',
    '/legal': '/lawyer-workspace.html',
    '/institution': '/institution-workspace.html',
    '/calculator': '/earnings-calculator.html',
    '/earnings-calculator': '/earnings-calculator.html',
    '/withdraw': '/withdrawal.html',
    '/submit': '/anonymous-task.html',
    '/auth': '/login.html',
    '/admin': '/admin-config.html',
    '/admin-pro': '/admin-config-optimized.html',
    '/console': '/dashboard.html'
};

// 处理路由重写
Object.keys(routes).forEach(route => {
    app.get(route, (req, res) => {
        res.sendFile(path.join(__dirname, routes[route]));
    });
});

// 兼容性重定向
app.get('/sales', (req, res) => {
    res.redirect(301, '/user');
});

// 默认首页
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// 处理404，返回首页
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, () => {
    console.log(`Lawsker frontend server running on port ${port}`);
}); 