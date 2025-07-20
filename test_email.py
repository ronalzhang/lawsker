#!/usr/bin/env python3
"""
邮件发送测试脚本
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


def test_email_connection():
    """测试邮件连接和发送"""
    try:
        # 163邮箱SMTP配置
        smtp_server = "smtp.163.com"
        smtp_port = 25
        sender_email = "lawsker@163.com"
        sender_password = "AJ5KYvXUsUKXydV4"  # 授权码
        
        print("📧 开始测试邮件发送...")
        print(f"SMTP服务器: {smtp_server}:{smtp_port}")
        print(f"发件人: {sender_email}")
        
        # 创建SMTP连接
        print("\n🔗 连接SMTP服务器...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        # 启用TLS加密
        print("🔒 启用TLS加密...")
        server.starttls()
        
        # 登录
        print("🔑 验证登录凭据...")
        server.login(sender_email, sender_password)
        print("✅ 登录成功！")
        
        # 创建测试邮件
        message = MIMEMultipart()
        message['From'] = f"律思客平台 <{sender_email}>"
        message['To'] = "test@example.com"  # 测试邮箱
        message['Subject'] = Header("律思客平台邮件系统测试", 'utf-8')
        
        # 邮件正文
        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>邮件系统测试</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 20px;">
            <div style="background-color: #f4f4f4; padding: 20px; text-align: center;">
                <h2>律思客平台邮件系统测试</h2>
            </div>
            
            <div style="padding: 20px;">
                <p>您好！</p>
                
                <p>这是来自律思客平台的测试邮件。如果您收到这封邮件，说明我们的邮件发送系统工作正常。</p>
                
                <div style="background-color: #d9edf7; padding: 10px; border-left: 4px solid #31b0d5; margin: 10px 0;">
                    <strong>测试信息：</strong><br>
                    发送时间：2025年7月20日<br>
                    发送服务器：smtp.163.com<br>
                    发件人：lawsker@163.com
                </div>
                
                <p>如有任何问题，请联系平台客服。</p>
            </div>
            
            <div style="background-color: #f4f4f4; padding: 15px; text-align: center; color: #666;">
                <p>律思客平台 | 专业的法律服务平台</p>
            </div>
        </body>
        </html>
        """
        
        # 添加HTML正文
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)
        
        print("\n📝 创建测试邮件...")
        print("邮件主题: 律思客平台邮件系统测试")
        print("收件人: test@example.com")
        
        # 注意：这里只是测试连接，不实际发送
        print("\n⚠️  测试模式：不实际发送邮件")
        print("邮件内容预览:")
        print("="*50)
        print("From:", message['From'])
        print("To:", message['To'])
        print("Subject:", message['Subject'])
        print("Content-Type: text/html")
        print("="*50)
        
        # 关闭连接
        server.quit()
        print("\n✅ 邮件系统测试完成！")
        print("🎉 SMTP连接和认证均正常，邮件发送功能可用")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ SMTP认证失败: {e}")
        print("请检查邮箱账号和授权码是否正确")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ SMTP连接失败: {e}")
        print("请检查网络连接和SMTP服务器设置")
        return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_email_service_import():
    """测试邮件服务模块导入"""
    try:
        print("📦 测试邮件服务模块导入...")
        
        # 尝试导入邮件服务（需要在项目目录中运行）
        import sys
        import os
        
        # 添加backend路径
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        try:
            from app.services.email_service import EmailService, create_email_service
            print("✅ 邮件服务模块导入成功")
            
            # 测试创建服务实例
            email_service = create_email_service()
            print("✅ 邮件服务实例创建成功")
            print(f"📧 配置邮箱: {email_service.sender_email}")
            print(f"🖥️  SMTP服务器: {email_service.smtp_server}:{email_service.smtp_port}")
            
            return True
            
        except ImportError as e:
            print(f"❌ 邮件服务模块导入失败: {e}")
            print("请确保在项目根目录中运行此脚本")
            return False
            
    except Exception as e:
        print(f"❌ 模块测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🧪 律思客平台邮件系统测试")
    print("="*60)
    
    # 测试1: SMTP连接
    print("\n📋 测试1: SMTP连接和认证")
    test_result_1 = test_email_connection()
    
    # 测试2: 模块导入
    print("\n📋 测试2: 邮件服务模块")
    test_result_2 = test_email_service_import()
    
    # 总结
    print("\n" + "="*60)
    print("🏁 测试总结:")
    print(f"SMTP连接测试: {'✅ 通过' if test_result_1 else '❌ 失败'}")
    print(f"模块导入测试: {'✅ 通过' if test_result_2 else '❌ 失败'}")
    
    if test_result_1 and test_result_2:
        print("\n🎉 所有测试通过！邮件发送系统准备就绪")
    else:
        print("\n⚠️  部分测试失败，请检查配置")
    
    print("\n💡 下一步:")
    print("1. 在服务器上部署更新的代码")
    print("2. 重启后端服务")
    print("3. 在律师工作台测试发送功能")