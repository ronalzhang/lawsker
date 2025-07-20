"""
邮件发送服务
基于163邮箱SMTP配置
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务"""
    
    def __init__(self):
        # 163邮箱SMTP配置
        self.smtp_server = "smtp.163.com"
        self.smtp_port = 25
        self.smtp_ssl_port = 465
        self.sender_email = "lawsker@163.com"
        self.sender_password = "AJ5KYvXUsUKXydV4"  # 授权码
        self.sender_name = "律思客平台"
        
    async def send_lawyer_letter(
        self,
        recipient_email: str,
        recipient_name: str,
        letter_title: str,
        letter_content: str,
        case_info: Dict[str, Any],
        lawyer_info: Dict[str, Any],
        attachment_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送律师函邮件
        
        Args:
            recipient_email: 收件人邮箱
            recipient_name: 收件人姓名
            letter_title: 律师函标题
            letter_content: 律师函内容
            case_info: 案件信息
            lawyer_info: 律师信息
            attachment_path: 附件路径（可选）
            
        Returns:
            发送结果
        """
        try:
            # 创建邮件对象
            message = MIMEMultipart()
            
            # 设置发件人信息
            message['From'] = f"{self.sender_name} <{self.sender_email}>"
            message['To'] = f"{recipient_name} <{recipient_email}>"
            message['Subject'] = Header(letter_title, 'utf-8')
            
            # 生成邮件正文
            email_body = self._generate_email_body(
                letter_content, case_info, lawyer_info, recipient_name
            )
            
            # 添加HTML正文
            html_part = MIMEText(email_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # 添加附件（如果有）
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=f"律师函_{case_info.get('case_number', 'unknown')}.pdf"
                    )
                    message.attach(attachment)
            
            # 发送邮件
            send_result = await self._send_email(message, recipient_email)
            
            if send_result['success']:
                logger.info(f"律师函邮件发送成功: {recipient_email}")
                return {
                    'success': True,
                    'message': '律师函邮件发送成功',
                    'sent_at': datetime.now().isoformat(),
                    'recipient': recipient_email,
                    'letter_title': letter_title
                }
            else:
                logger.error(f"律师函邮件发送失败: {send_result['error']}")
                return {
                    'success': False,
                    'error': send_result['error'],
                    'recipient': recipient_email
                }
                
        except Exception as e:
            logger.error(f"发送律师函邮件异常: {str(e)}")
            return {
                'success': False,
                'error': f"邮件发送异常: {str(e)}",
                'recipient': recipient_email
            }
    
    async def send_task_notification(
        self,
        recipient_email: str,
        recipient_name: str,
        task_info: Dict[str, Any],
        notification_type: str = "status_update"
    ) -> Dict[str, Any]:
        """
        发送任务通知邮件
        
        Args:
            recipient_email: 收件人邮箱
            recipient_name: 收件人姓名
            task_info: 任务信息
            notification_type: 通知类型 (status_update, completed, etc.)
            
        Returns:
            发送结果
        """
        try:
            message = MIMEMultipart()
            
            # 设置邮件头
            message['From'] = f"{self.sender_name} <{self.sender_email}>"
            message['To'] = f"{recipient_name} <{recipient_email}>"
            
            # 根据通知类型设置主题和内容
            if notification_type == "status_update":
                subject = f"【律思客】任务状态更新 - {task_info.get('title', '未知任务')}"
                body = self._generate_task_update_body(task_info, recipient_name)
            elif notification_type == "completed":
                subject = f"【律思客】任务已完成 - {task_info.get('title', '未知任务')}"
                body = self._generate_task_completion_body(task_info, recipient_name)
            else:
                subject = f"【律思客】任务通知 - {task_info.get('title', '未知任务')}"
                body = self._generate_generic_notification_body(task_info, recipient_name)
            
            message['Subject'] = Header(subject, 'utf-8')
            
            # 添加HTML正文
            html_part = MIMEText(body, 'html', 'utf-8')
            message.attach(html_part)
            
            # 发送邮件
            send_result = await self._send_email(message, recipient_email)
            
            if send_result['success']:
                logger.info(f"任务通知邮件发送成功: {recipient_email}")
                return {
                    'success': True,
                    'message': '通知邮件发送成功',
                    'sent_at': datetime.now().isoformat(),
                    'recipient': recipient_email,
                    'notification_type': notification_type
                }
            else:
                logger.error(f"任务通知邮件发送失败: {send_result['error']}")
                return send_result
                
        except Exception as e:
            logger.error(f"发送任务通知邮件异常: {str(e)}")
            return {
                'success': False,
                'error': f"邮件发送异常: {str(e)}",
                'recipient': recipient_email
            }
    
    async def _send_email(self, message: MIMEMultipart, recipient_email: str) -> Dict[str, Any]:
        """发送邮件的底层方法"""
        try:
            # 创建SMTP连接
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # 启用TLS加密
            
            # 登录
            server.login(self.sender_email, self.sender_password)
            
            # 发送邮件
            text = message.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            return {
                'success': True,
                'message': '邮件发送成功'
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                'success': False,
                'error': 'SMTP认证失败，请检查邮箱账号和授权码'
            }
        except smtplib.SMTPConnectError:
            return {
                'success': False,
                'error': 'SMTP连接失败，请检查网络连接'
            }
        except smtplib.SMTPException as e:
            return {
                'success': False,
                'error': f'SMTP发送失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'邮件发送异常: {str(e)}'
            }
    
    def _generate_email_body(
        self, 
        letter_content: str, 
        case_info: Dict[str, Any], 
        lawyer_info: Dict[str, Any],
        recipient_name: str
    ) -> str:
        """生成律师函邮件正文"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>律师函</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; white-space: pre-line; }}
                .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; color: #666; }}
                .warning {{ color: #d9534f; font-weight: bold; }}
                .info {{ background-color: #d9edf7; padding: 10px; border-left: 4px solid #31b0d5; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>律思客平台 - 律师函</h2>
                <p>案件编号: {case_info.get('case_number', 'N/A')}</p>
            </div>
            
            <div class="content">
                <p>尊敬的{recipient_name}：</p>
                
                <div class="info">
                    <strong>重要提醒：</strong>本律师函由律思客平台代为发送，具有法律效力。请认真阅读并按时履行相关义务。
                </div>
                
                {letter_content}
                
                <div class="info">
                    <strong>联系方式：</strong><br>
                    律师姓名：{lawyer_info.get('name', '未提供')}<br>
                    联系电话：{lawyer_info.get('phone', '未提供')}<br>
                    律师事务所：{lawyer_info.get('law_firm', '未提供')}<br>
                    执业证号：{lawyer_info.get('license_number', '未提供')}
                </div>
                
                <p class="warning">
                    请注意：收到本律师函后请立即与律师或委托人联系，逾期可能承担相应法律后果。
                </p>
            </div>
            
            <div class="footer">
                <p>本邮件由律思客平台自动发送，如有疑问请联系平台客服。</p>
                <p>律思客平台 | 专业的法律服务平台 | {datetime.now().strftime('%Y年%m月%d日')}</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_task_update_body(self, task_info: Dict[str, Any], recipient_name: str) -> str:
        """生成任务状态更新邮件正文"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                .header {{ background-color: #5cb85c; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task-info {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>任务状态更新通知</h2>
            </div>
            
            <div class="content">
                <p>尊敬的{recipient_name}：</p>
                
                <p>您的任务状态已更新，详情如下：</p>
                
                <div class="task-info">
                    <strong>任务标题：</strong>{task_info.get('title', '未知任务')}<br>
                    <strong>任务编号：</strong>{task_info.get('task_number', 'N/A')}<br>
                    <strong>当前状态：</strong>{task_info.get('status', '未知状态')}<br>
                    <strong>更新时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                
                <p>请登录律思客平台查看详细信息。</p>
            </div>
            
            <div class="footer">
                <p>律思客平台 | {datetime.now().strftime('%Y年%m月%d日')}</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_task_completion_body(self, task_info: Dict[str, Any], recipient_name: str) -> str:
        """生成任务完成邮件正文"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                .header {{ background-color: #337ab7; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task-info {{ background-color: #dff0d8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>任务完成通知</h2>
            </div>
            
            <div class="content">
                <p>尊敬的{recipient_name}：</p>
                
                <p>恭喜！您的任务已完成，详情如下：</p>
                
                <div class="task-info">
                    <strong>任务标题：</strong>{task_info.get('title', '未知任务')}<br>
                    <strong>任务编号：</strong>{task_info.get('task_number', 'N/A')}<br>
                    <strong>完成时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    <strong>执行律师：</strong>{task_info.get('lawyer_name', '系统处理')}
                </div>
                
                <p>感谢您使用律思客平台，如有任何问题请联系客服。</p>
            </div>
            
            <div class="footer">
                <p>律思客平台 | {datetime.now().strftime('%Y年%m月%d日')}</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_generic_notification_body(self, task_info: Dict[str, Any], recipient_name: str) -> str:
        """生成通用通知邮件正文"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                .header {{ background-color: #f0ad4e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>律思客平台通知</h2>
            </div>
            
            <div class="content">
                <p>尊敬的{recipient_name}：</p>
                
                <p>您有新的平台通知，相关任务信息：</p>
                
                <ul>
                    <li><strong>任务标题：</strong>{task_info.get('title', '未知任务')}</li>
                    <li><strong>任务编号：</strong>{task_info.get('task_number', 'N/A')}</li>
                    <li><strong>通知时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                
                <p>请登录律思客平台查看详细信息。</p>
            </div>
            
            <div class="footer">
                <p>律思客平台 | {datetime.now().strftime('%Y年%m月%d日')}</p>
            </div>
        </body>
        </html>
        """


def create_email_service() -> EmailService:
    """创建邮件服务实例"""
    return EmailService()