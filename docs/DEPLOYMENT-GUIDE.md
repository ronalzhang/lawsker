# Lawsker部署指南

## 📋 目录

- [环境要求](#环境要求)
- [服务器配置](#服务器配置)
- [应用部署](#应用部署)
- [数据库配置](#数据库配置)
- [NGINX配置](#nginx配置)
- [监控配置](#监控配置)
- [维护操作](#维护操作)

## 🖥️ 环境要求

### 服务器信息
- **IP地址**: 156.236.74.200
- **操作系统**: Ubuntu 20.04 LTS
- **CPU**: 4核心
- **内存**: 8GB
- **存储**: 100GB SSD

### 软件要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- NGINX 1.20+
- PM2 (进程管理)

## 🚀 服务器配置

### 1. 连接服务器
```bash
# 使用sshpass连接服务器
sshpass -p 'Pr971V3j' ssh root@156.236.74.200
```

### 2. 系统更新
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "apt update && apt upgrade -y"
```

### 3. 安装基础软件
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql redis-server nginx"
```

### 4. 安装PM2
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "npm install -g pm2"
```

## 📦 应用部署

### 1. 创建应用目录
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "mkdir -p /root/lawsker"
```

### 2. 后端部署

#### 创建虚拟环境
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker && python3.11 -m venv backend_env"
```

#### 激活虚拟环境并安装依赖
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker && source backend_env/bin/activate && pip install -r backend/requirements.txt"
```

#### 启动后端服务
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker && source backend_env/bin/activate && pm2 start backend/main.py --name lawsker-backend --interpreter python"
```

### 3. 前端部署

#### 用户端前端
```bash
# 安装依赖
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker/frontend-vue && npm install"

# 构建生产版本
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker/frontend-vue && npm run build"

# 使用PM2启动静态文件服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker && pm2 serve frontend-vue/dist 3000 --name lawsker-frontend"
```

#### 管理后台
```bash
# 安装依赖
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker/frontend-admin && npm install"

# 构建生产版本
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker/frontend-admin && npm run build"

# 使用PM2启动静态文件服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker && pm2 serve frontend-admin/dist 3001 --name lawsker-admin"
```

## 🗄️ 数据库配置

### 1. PostgreSQL配置
```bash
# 创建数据库和用户
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql -c \"CREATE DATABASE lawsker;\""
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql -c \"CREATE USER lawsker_user WITH PASSWORD 'your_password';\""
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE lawsker TO lawsker_user;\""
```

### 2. 运行数据库迁移
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker && source backend_env/bin/activate && python -m alembic upgrade head"
```

## 🌐 NGINX配置

### 1. 创建NGINX配置文件
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cat > /etc/nginx/sites-available/lawsker << 'EOF'
server {
    listen 80;
    server_name 156.236.74.200;

    # 用户端前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # 管理后台
    location /admin {
        proxy_pass http://localhost:3001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # API接口
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF"
```

### 2. 启用配置
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "ln -s /etc/nginx/sites-available/lawsker /etc/nginx/sites-enabled/"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "nginx -t && systemctl reload nginx"
```