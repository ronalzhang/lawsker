#!/bin/bash

# 服务器配置
SERVER_IP="156.227.235.192"
SERVER_PASSWORD="Pr971V3j"
SERVER_USER="root"

echo "🚀 开始部署NGINX配置..."

# 1. 上传NGINX配置文件
echo "📤 上传NGINX配置文件..."
sshpass -p "$SERVER_PASSWORD" scp nginx.conf "$SERVER_USER@$SERVER_IP:/etc/nginx/sites-available/lawsker.conf"

if [ $? -eq 0 ]; then
    echo "✅ NGINX配置文件上传成功"
else
    echo "❌ NGINX配置文件上传失败"
    exit 1
fi

# 2. 在服务器上执行配置操作
echo "🔧 在服务器上配置NGINX..."
sshpass -p "$SERVER_PASSWORD" ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
    # 创建符号链接启用站点
    ln -sf /etc/nginx/sites-available/lawsker.conf /etc/nginx/sites-enabled/lawsker.conf
    
    # 删除默认站点配置（如果存在）
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试NGINX配置
    nginx -t
    
    if [ $? -eq 0 ]; then
        echo "✅ NGINX配置测试通过"
        
        # 重启NGINX
        systemctl restart nginx
        
        if [ $? -eq 0 ]; then
            echo "✅ NGINX重启成功"
            systemctl status nginx --no-pager
        else
            echo "❌ NGINX重启失败"
            exit 1
        fi
    else
        echo "❌ NGINX配置测试失败"
        exit 1
    fi
EOF

if [ $? -eq 0 ]; then
    echo "🎉 NGINX配置部署完成！"
    echo ""
    echo "🌐 现在可以通过以下方式访问："
    echo "   - 首页: https://lawsker.com 或 https://156.227.235.192"
    echo "   - 控制台: https://lawsker.com/console"
    echo "   - 销售工作台: https://lawsker.com/sales"
    echo "   - 律师工作台: https://lawsker.com/legal"
    echo "   - 收益计算器: https://lawsker.com/calculator"
    echo "   - 提现管理: https://lawsker.com/withdraw"
    echo "   - 一键律师函: https://lawsker.com/submit"
    echo "   - 用户登录: https://lawsker.com/auth"
    echo "   - 系统管理: https://lawsker.com/admin"
    echo ""
    echo "⚠️  注意：域名lawsker.com需要您注册后解析到服务器IP"
else
    echo "❌ NGINX配置部署失败"
    exit 1
fi 