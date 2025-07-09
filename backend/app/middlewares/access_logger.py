"""
访问日志记录中间件
自动记录所有HTTP请求到access_logs表，用于访问分析
"""

import time
import logging
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import uuid
import re

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AccessLoggerMiddleware:
    """访问日志记录中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            # 非HTTP请求直接传递
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # 创建响应捕获器
        response_body = []
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            status_code = 500
            logger.error(f"请求处理异常: {str(e)}")
            raise
        finally:
            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)  # 毫秒
            
            # 异步记录访问日志
            try:
                await self._log_access(request, status_code, response_time)
            except Exception as e:
                logger.error(f"记录访问日志失败: {str(e)}")
    
    async def _log_access(self, request: Request, status_code: int, response_time: int):
        """记录访问日志到数据库"""
        try:
            # 解析User-Agent
            user_agent_string = request.headers.get("user-agent", "")
            
            # 获取IP地址（考虑代理）
            ip_address = self._get_client_ip(request)
            
            # 提取用户ID（如果有认证token）
            user_id = await self._extract_user_id(request)
            
            # 生成session_id
            session_id = self._generate_session_id(request)
            
            # 设备类型检测
            device_type = self._detect_device_type(user_agent_string)
            
            # 浏览器和操作系统检测
            browser = self._parse_browser(user_agent_string)
            os = self._parse_os(user_agent_string)
            
            # 地理位置信息（简化处理，可以后续集成IP地址库）
            country, region, city = self._get_location_info(ip_address)
            
            # 准备数据库插入数据
            log_data = {
                "user_id": user_id,
                "session_id": session_id,
                "ip_address": ip_address,
                "user_agent": user_agent_string,
                "referer": request.headers.get("referer"),
                "request_path": str(request.url.path),
                "request_method": request.method,
                "status_code": status_code,
                "response_time": response_time,
                "device_type": device_type,
                "browser": browser,
                "os": os,
                "country": country,
                "region": region,
                "city": city
            }
            
            # 插入数据库
            async with AsyncSessionLocal() as db:
                await self._insert_access_log(db, log_data)
                
        except Exception as e:
            logger.error(f"处理访问日志数据失败: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 检查各种代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 如果都没有，使用客户端IP
        return request.client.host if request.client else "unknown"
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """从请求中提取用户ID"""
        try:
            # 从Authorization头提取JWT token
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # 这里可以解析JWT获取用户ID，简化处理
                # 实际项目中可以调用认证服务
                if token.startswith("demo_"):
                    return None  # 演示账号不记录
                return None  # 暂时返回None，可以后续完善
            return None
        except Exception:
            return None
    
    def _generate_session_id(self, request: Request) -> str:
        """生成会话ID"""
        # 简单的会话ID生成，可以基于IP和User-Agent
        ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{ip}-{user_agent}"))[:32]
    
    def _detect_device_type(self, user_agent_string: str) -> str:
        """检测设备类型"""
        ua_lower = user_agent_string.lower()
        if any(mobile in ua_lower for mobile in ['mobile', 'android', 'iphone', 'ipod']):
            return "mobile"
        elif 'ipad' in ua_lower or 'tablet' in ua_lower:
            return "tablet"
        else:
            return "desktop"
    
    def _parse_browser(self, user_agent_string: str) -> str:
        """解析浏览器信息"""
        ua_lower = user_agent_string.lower()
        if 'chrome' in ua_lower:
            return "Chrome"
        elif 'firefox' in ua_lower:
            return "Firefox"
        elif 'safari' in ua_lower:
            return "Safari"
        elif 'edge' in ua_lower:
            return "Edge"
        else:
            return "Unknown"
    
    def _parse_os(self, user_agent_string: str) -> str:
        """解析操作系统信息"""
        ua_lower = user_agent_string.lower()
        if 'windows' in ua_lower:
            return "Windows"
        elif 'mac' in ua_lower or 'darwin' in ua_lower:
            return "macOS"
        elif 'linux' in ua_lower:
            return "Linux"
        elif 'android' in ua_lower:
            return "Android"
        elif 'ios' in ua_lower or 'iphone' in ua_lower or 'ipad' in ua_lower:
            return "iOS"
        else:
            return "Unknown"
    
    def _get_location_info(self, ip_address: str) -> tuple:
        """获取地理位置信息（简化版本）"""
        # 这里可以集成IP地址库如MaxMind GeoIP
        # 暂时返回简化的信息
        if ip_address.startswith("192.168.") or ip_address.startswith("10.") or ip_address.startswith("172."):
            return "中国", "未知", "内网"
        else:
            return "中国", "未知", "未知"
    
    async def _insert_access_log(self, db: AsyncSession, log_data: dict):
        """插入访问日志到数据库"""
        try:
            insert_query = text("""
                INSERT INTO access_logs (
                    user_id, session_id, ip_address, user_agent, referer,
                    request_path, request_method, status_code, response_time,
                    device_type, browser, os, country, region, city, created_at
                ) VALUES (
                    :user_id, :session_id, :ip_address, :user_agent, :referer,
                    :request_path, :request_method, :status_code, :response_time,
                    :device_type, :browser, :os, :country, :region, :city, NOW()
                )
            """)
            
            await db.execute(insert_query, log_data)
            await db.commit()
            
        except Exception as e:
            logger.error(f"插入访问日志失败: {str(e)}")
            await db.rollback()
            
    def _should_log_request(self, request: Request) -> bool:
        """判断是否应该记录此请求"""
        path = request.url.path
        
        # 排除静态资源和健康检查
        excluded_paths = [
            "/static/", "/css/", "/js/", "/images/", "/favicon.ico",
            "/health", "/docs", "/redoc", "/openapi.json"
        ]
        
        for excluded in excluded_paths:
            if path.startswith(excluded):
                return False
        
        return True 