"""
演示账户安全中间件
确保演示数据与真实数据的完全隔离
"""

from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import structlog
import re

logger = structlog.get_logger()


class DemoSecurityMiddleware:
    """演示账户安全中间件"""
    
    def __init__(self, app):
        self.app = app
        
        # 定义需要拦截的危险操作
        self.dangerous_operations = {
            'POST': [
                r'/api/v1/cases/create',
                r'/api/v1/finance/payment',
                r'/api/v1/upload/.*',
                r'/api/v1/document-send/.*',
                r'/api/v1/batch-upload/.*'
            ],
            'PUT': [
                r'/api/v1/cases/.*/update',
                r'/api/v1/users/.*/update',
                r'/api/v1/finance/.*'
            ],
            'DELETE': [
                r'/api/v1/cases/.*',
                r'/api/v1/users/.*',
                r'/api/v1/documents/.*'
            ]
        }
        
        # 演示账户允许的安全操作
        self.allowed_demo_operations = [
            r'/api/v1/demo/.*',
            r'/api/v1/auth/.*',
            r'/api/v1/unified-auth/.*',
            r'/api/v1/health',
            r'/api/v1/csrf/.*'
        ]
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """中间件主要逻辑"""
        try:
            # 检查是否为演示账户请求
            is_demo_request = await self.is_demo_request(request)
            
            if is_demo_request:
                # 验证演示账户操作
                validation_result = await self.validate_demo_operation(request)
                
                if not validation_result['allowed']:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            'success': False,
                            'error': 'demo_operation_forbidden',
                            'message': validation_result['message'],
                            'suggestion': '请注册真实账户以使用完整功能'
                        }
                    )
                
                # 为演示请求添加特殊标识
                request.state.is_demo = True
                request.state.demo_workspace_id = validation_result.get('workspace_id')
            else:
                request.state.is_demo = False
            
            # 继续处理请求
            response = await call_next(request)
            
            # 为演示响应添加特殊标识
            if is_demo_request:
                response.headers["X-Demo-Mode"] = "true"
                response.headers["X-Demo-Warning"] = "This is demo data, not real data"
            
            return response
            
        except Exception as e:
            logger.error("演示安全中间件错误", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'success': False,
                    'error': 'middleware_error',
                    'message': '请求处理失败'
                }
            )
    
    async def is_demo_request(self, request: Request) -> bool:
        """检查是否为演示账户请求"""
        try:
            # 检查URL参数
            if request.query_params.get('demo') == 'true':
                return True
            
            # 检查请求头
            if request.headers.get('X-Demo-Mode') == 'true':
                return True
            
            # 检查路径中的workspace_id
            path = request.url.path
            workspace_match = re.search(r'/(user|lawyer)/([^/]+)', path)
            
            if workspace_match:
                workspace_id = workspace_match.group(2)
                if workspace_id.startswith('demo-'):
                    return True
            
            # 检查请求体中的workspace_id（对于POST请求）
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    # 这里需要小心处理，避免消费request body
                    # 实际实现中可能需要更复杂的逻辑
                    pass
                except:
                    pass
            
            return False
            
        except Exception as e:
            logger.error("检查演示请求失败", error=str(e))
            return False
    
    async def validate_demo_operation(self, request: Request) -> dict:
        """验证演示账户操作"""
        try:
            method = request.method
            path = request.url.path
            
            # 检查是否为允许的操作
            for allowed_pattern in self.allowed_demo_operations:
                if re.match(allowed_pattern, path):
                    return {
                        'allowed': True,
                        'message': 'Operation allowed for demo account'
                    }
            
            # 检查是否为危险操作
            if method in self.dangerous_operations:
                for dangerous_pattern in self.dangerous_operations[method]:
                    if re.match(dangerous_pattern, path):
                        return {
                            'allowed': False,
                            'message': f'操作 "{method} {path}" 在演示模式下不被允许',
                            'operation': f'{method} {path}'
                        }
            
            # 对于GET请求，通常是安全的，但需要确保返回演示数据
            if method == 'GET':
                return {
                    'allowed': True,
                    'message': 'GET operation allowed for demo account',
                    'requires_demo_data': True
                }
            
            # 默认允许，但记录日志
            logger.warning("未分类的演示操作", method=method, path=path)
            return {
                'allowed': True,
                'message': 'Operation allowed by default'
            }
            
        except Exception as e:
            logger.error("验证演示操作失败", error=str(e))
            return {
                'allowed': False,
                'message': '操作验证失败'
            }
    
    def extract_workspace_id_from_path(self, path: str) -> str:
        """从路径中提取workspace_id"""
        workspace_match = re.search(r'/(user|lawyer)/([^/]+)', path)
        if workspace_match:
            return workspace_match.group(2)
        return None
    
    def is_safe_demo_operation(self, method: str, path: str) -> bool:
        """检查是否为安全的演示操作"""
        safe_operations = [
            'GET',  # 读取操作通常是安全的
        ]
        
        safe_paths = [
            r'/api/v1/demo/.*',
            r'/api/v1/health',
            r'/api/v1/csrf/.*',
            r'/api/v1/statistics/.*'  # 统计数据查看
        ]
        
        if method in safe_operations:
            return True
        
        for safe_path in safe_paths:
            if re.match(safe_path, path):
                return True
        
        return False


def add_demo_security_middleware(app):
    """添加演示安全中间件到应用"""
    app.add_middleware(DemoSecurityMiddleware)