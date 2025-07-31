"""
标准化错误处理机制
基于系统优化建议文档的具体要求
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import ValidationException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import traceback
import uuid

from app.core.logging import get_logger

logger = get_logger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    """标准化HTTP异常处理"""
    error_id = str(uuid.uuid4())
    
    # 记录错误日志
    logger.error(
        f"HTTP Exception [{error_id}]: {exc.status_code} - {exc.detail} - "
        f"Path: {request.url.path} - Method: {request.method} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "id": error_id,
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    """表单验证异常处理"""
    error_id = str(uuid.uuid4())
    
    # 格式化验证错误
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    # 记录错误日志
    logger.warning(
        f"Validation Error [{error_id}]: {len(formatted_errors)} validation errors - "
        f"Path: {request.url.path} - Method: {request.method} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "id": error_id,
                "code": 422,
                "message": "Validation failed",
                "type": "validation_error",
                "details": formatted_errors,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常处理"""
    error_id = str(uuid.uuid4())
    
    # 记录详细错误日志
    logger.error(
        f"Database Error [{error_id}]: {str(exc)} - "
        f"Path: {request.url.path} - Method: {request.method} - "
        f"Client: {request.client.host if request.client else 'unknown'} - "
        f"Traceback: {traceback.format_exc()}"
    )
    
    # 根据错误类型返回不同的用户友好消息
    user_message = "数据库操作失败，请稍后重试"
    
    if "duplicate key" in str(exc).lower():
        user_message = "数据已存在，请检查后重试"
    elif "foreign key" in str(exc).lower():
        user_message = "数据关联错误，请检查相关数据"
    elif "not null" in str(exc).lower():
        user_message = "必填字段不能为空"
    elif "timeout" in str(exc).lower():
        user_message = "数据库连接超时，请稍后重试"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "id": error_id,
                "code": 500,
                "message": user_message,
                "type": "database_error",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    error_id = str(uuid.uuid4())
    
    # 记录详细错误日志
    logger.error(
        f"Unhandled Exception [{error_id}]: {type(exc).__name__}: {str(exc)} - "
        f"Path: {request.url.path} - Method: {request.method} - "
        f"Client: {request.client.host if request.client else 'unknown'} - "
        f"Traceback: {traceback.format_exc()}"
    )
    
    # 根据异常类型返回不同的状态码和消息
    status_code = 500
    user_message = "服务器内部错误，请稍后重试"
    error_type = "internal_error"
    
    if isinstance(exc, ConnectionError):
        status_code = 503
        user_message = "服务暂时不可用，请稍后重试"
        error_type = "connection_error"
    elif isinstance(exc, TimeoutError):
        status_code = 504
        user_message = "请求超时，请稍后重试"
        error_type = "timeout_error"
    elif isinstance(exc, PermissionError):
        status_code = 403
        user_message = "权限不足，无法执行此操作"
        error_type = "permission_error"
    elif isinstance(exc, FileNotFoundError):
        status_code = 404
        user_message = "请求的资源不存在"
        error_type = "not_found_error"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "id": error_id,
                "code": status_code,
                "message": user_message,
                "type": error_type,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )

async def rate_limit_exception_handler(request: Request, exc: Exception):
    """限流异常处理"""
    error_id = str(uuid.uuid4())
    
    logger.warning(
        f"Rate Limit Exceeded [{error_id}]: "
        f"Path: {request.url.path} - Method: {request.method} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "id": error_id,
                "code": 429,
                "message": "请求过于频繁，请稍后重试",
                "type": "rate_limit_error",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path),
                "method": request.method,
                "retry_after": 60  # 建议60秒后重试
            }
        },
        headers={"Retry-After": "60"}
    )

async def authentication_exception_handler(request: Request, exc: Exception):
    """认证异常处理"""
    error_id = str(uuid.uuid4())
    
    logger.warning(
        f"Authentication Failed [{error_id}]: {str(exc)} - "
        f"Path: {request.url.path} - Method: {request.method} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "id": error_id,
                "code": 401,
                "message": "认证失败，请重新登录",
                "type": "authentication_error",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )

async def authorization_exception_handler(request: Request, exc: Exception):
    """授权异常处理"""
    error_id = str(uuid.uuid4())
    
    logger.warning(
        f"Authorization Failed [{error_id}]: {str(exc)} - "
        f"Path: {request.url.path} - Method: {request.method} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "id": error_id,
                "code": 403,
                "message": "权限不足，无法访问此资源",
                "type": "authorization_error",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )

# 错误处理器映射
ERROR_HANDLERS = {
    HTTPException: http_exception_handler,
    ValidationError: validation_exception_handler,
    SQLAlchemyError: database_exception_handler,
    Exception: general_exception_handler,
}

def setup_error_handlers(app):
    """设置错误处理器"""
    for exception_type, handler in ERROR_HANDLERS.items():
        app.add_exception_handler(exception_type, handler)
    
    logger.info("Error handlers configured successfully")

# 错误统计和监控
class ErrorMonitor:
    """错误监控器"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_rates = {}
    
    def record_error(self, error_type: str, path: str, method: str):
        """记录错误"""
        key = f"{error_type}:{method}:{path}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        # 记录到日志
        logger.info(f"Error recorded: {key} (count: {self.error_counts[key]})")
    
    def get_error_stats(self) -> dict:
        """获取错误统计"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_types": len(self.error_counts),
            "top_errors": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

# 全局错误监控器实例
error_monitor = ErrorMonitor()