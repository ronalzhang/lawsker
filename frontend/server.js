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

// 路由映射 - 使用简单的字符串匹配
app.get('/user', (req, res) => {
    res.sendFile(path.join(__dirname, 'user-workspace.html'));
});

app.get('/legal', (req, res) => {
    res.sendFile(path.join(__dirname, 'lawyer-workspace.html'));
});

app.get('/institution', (req, res) => {
    res.sendFile(path.join(__dirname, 'institution-workspace.html'));
});

app.get('/calculator', (req, res) => {
    res.sendFile(path.join(__dirname, 'earnings-calculator.html'));
});

app.get('/earnings-calculator', (req, res) => {
    res.sendFile(path.join(__dirname, 'earnings-calculator.html'));
});

app.get('/withdraw', (req, res) => {
    res.sendFile(path.join(__dirname, 'withdrawal.html'));
});

app.get('/submit', (req, res) => {
    res.sendFile(path.join(__dirname, 'anonymous-task.html'));
});

app.get('/auth', (req, res) => {
    res.sendFile(path.join(__dirname, 'login.html'));
});

app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'admin-config.html'));
});

app.get('/admin-pro', (req, res) => {
    res.sendFile(path.join(__dirname, 'admin-config-optimized.html'));
});

app.get('/console', (req, res) => {
    res.sendFile(path.join(__dirname, 'dashboard.html'));
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

app.listen(port, '0.0.0.0', () => {
    console.log(`Lawsker frontend server running on port ${port}`);
}); 