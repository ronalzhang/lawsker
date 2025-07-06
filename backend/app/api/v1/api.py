"""
API路由主文件
整合所有API端点路由
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, cases, finance, admin, ai, tasks
from app.api.v1 import statistics, file_upload, ai_assignment

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(cases.router, prefix="/cases", tags=["案件管理"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(finance.router, prefix="/finance", tags=["财务管理"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI服务"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["统计数据"])
api_router.include_router(file_upload.router, prefix="/upload", tags=["文件上传"])
api_router.include_router(ai_assignment.router, prefix="/ai-assignment", tags=["AI分配"])

# 健康检查路由
@api_router.get("/health")
async def api_health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Lawsker API v1"
    } 