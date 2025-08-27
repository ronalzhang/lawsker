"""
工作台路由中间件
处理基于workspace_id的安全访问和路由
"""

from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.models.user import User

logger = structlog.get_logger()


class WorkspaceMiddleware:
    """工作台访问中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # 检查是否是工作台路由
            if self.is_workspace_route(request.url.path):
                try:
                    await self.validate_workspace_access(request)
                except HTTPException as e:
                    # 返回错误响应
                    response = RedirectResponse(
                        url="/auth/login?error=workspace_access_denied",
                        status_code=302
                    )
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)
    
    def is_workspace_route(self, path: str) -> bool:
        """检查是否是工作台路由"""
        workspace_patterns = [
            '/user/',
            '/lawyer/',
            '/admin/'
        ]
        
        return any(path.startswith(pattern) for pattern in workspace_patterns)
    
    async def validate_workspace_access(self, request: Request):
        """验证工作台访问权限"""
        path = request.url.path
        
        # 提取workspace_id
        workspace_id = self.extract_workspace_id(path)
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的工作台ID"
            )
        
        # 检查是否是演示账户
        if workspace_id.startswith('demo-'):
            # 演示账户允许访问
            return
        
        # 获取当前用户
        current_user = await self.get_current_user_from_request(request)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要登录"
            )
        
        # 验证用户是否有权限访问该工作台
        if not await self.check_workspace_permission(current_user['id'], workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该工作台"
            )
        
        # 验证用户类型与路由匹配
        workspace_type = self.get_workspace_type_from_path(path)
        if not await self.check_user_type_match(current_user['id'], workspace_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户类型与工作台不匹配"
            )
    
    def extract_workspace_id(self, path: str) -> Optional[str]:
        """从路径中提取workspace_id"""
        parts = path.strip('/').split('/')
        
        if len(parts) >= 2:
            # 路径格式: /user/{workspace_id} 或 /lawyer/{workspace_id}
            return parts[1]
        
        return None
    
    def get_workspace_type_from_path(self, path: str) -> str:
        """从路径获取工作台类型"""
        if path.startswith('/user/'):
            return 'user'
        elif path.startswith('/lawyer/'):
            return 'lawyer'
        elif path.startswith('/admin/'):
            return 'admin'
        else:
            return 'unknown'
    
    async def get_current_user_from_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """从请求中获取当前用户信息"""
        try:
            # 从Authorization头或Cookie中获取token
            authorization = request.headers.get("Authorization")
            if not authorization:
                # 尝试从Cookie获取
                token = request.cookies.get("access_token")
                if token:
                    authorization = f"Bearer {token}"
            
            if not authorization:
                return None
            
            # 这里应该调用认证服务验证token
            # 简化实现，实际应该集成现有的认证逻辑
            from app.services.auth_service import AuthService
            
            # 获取数据库连接
            db = next(get_db())
            auth_service = AuthService(db)
            
            token = authorization.replace("Bearer ", "")
            user_info = await auth_service.get_current_user_from_token(token)
            
            return user_info
            
        except Exception as e:
            logger.error("获取当前用户失败", error=str(e))
            return None
    
    async def check_workspace_permission(self, user_id: str, workspace_id: str) -> bool:
        """检查用户是否有权限访问指定工作台"""
        try:
            # 获取数据库连接
            db = next(get_db())
            
            # 查询用户的workspace_id
            result = await db.execute(
                select(User.workspace_id)
                .where(User.id == user_id)
            )
            
            user_workspace_id = result.scalar_one_or_none()
            
            return user_workspace_id == workspace_id
            
        except Exception as e:
            logger.error("检查工作台权限失败", error=str(e), user_id=user_id, workspace_id=workspace_id)
            return False
    
    async def check_user_type_match(self, user_id: str, workspace_type: str) -> bool:
        """检查用户类型是否与工作台类型匹配"""
        try:
            # 获取数据库连接
            db = next(get_db())
            
            # 查询用户的account_type
            result = await db.execute(
                select(User.account_type)
                .where(User.id == user_id)
            )
            
            user_account_type = result.scalar_one_or_none()
            
            # 匹配规则
            type_mapping = {
                'user': ['user'],
                'lawyer': ['lawyer', 'lawyer_pending'],
                'admin': ['admin']
            }
            
            allowed_types = type_mapping.get(workspace_type, [])
            return user_account_type in allowed_types
            
        except Exception as e:
            logger.error("检查用户类型匹配失败", error=str(e), user_id=user_id, workspace_type=workspace_type)
            return False


def create_workspace_middleware():
    """创建工作台中间件实例"""
    return WorkspaceMiddleware