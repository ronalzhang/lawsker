"""
API路由主文件
整合所有API端点路由
"""

from fastapi import APIRouter, Response
from app.middlewares.csrf_middleware import get_csrf_token

from app.api.v1.endpoints import auth, users, cases, finance, admin, ai, tasks, admin_analytics, document_library, document_send, websocket, automation, documents, unified_auth, lawyer_membership, credits, batch_upload, demo, conversion_optimization, abuse_analytics, demo_conversion, demo_analytics
from app.api.v1 import statistics, file_upload, ai_assignment, lawyer_verification

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(unified_auth.router, prefix="/unified-auth", tags=["统一认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(cases.router, prefix="/cases", tags=["案件管理"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(finance.router, prefix="/finance", tags=["财务管理"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI服务"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
api_router.include_router(admin_analytics.router, prefix="/admin", tags=["管理后台分析"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["统计数据"])
api_router.include_router(file_upload.router, prefix="/upload", tags=["文件上传"])
api_router.include_router(ai_assignment.router, prefix="/ai-assignment", tags=["AI分配"])
api_router.include_router(lawyer_verification.router, prefix="/lawyer-verification", tags=["律师认证"])
api_router.include_router(document_library.router, prefix="/document-library", tags=["文书库管理"])
api_router.include_router(document_send.router, prefix="/document-send", tags=["文书发送"])
api_router.include_router(websocket.router, prefix="/websocket", tags=["实时通信"])
api_router.include_router(automation.router, prefix="/automation", tags=["自动化运维"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档管理"])
api_router.include_router(lawyer_membership.router, prefix="/lawyer-membership", tags=["律师会员系统"])
api_router.include_router(credits.router, prefix="/credits", tags=["用户Credits系统"])
api_router.include_router(batch_upload.router, prefix="/batch-upload", tags=["批量上传控制"])
api_router.include_router(demo.router, prefix="/demo", tags=["演示账户系统"])
api_router.include_router(demo_conversion.router, prefix="/demo-conversion", tags=["演示账户转化优化"])
api_router.include_router(conversion_optimization.router, prefix="/conversion-optimization", tags=["转化率优化"])
api_router.include_router(abuse_analytics.router, prefix="/abuse-analytics", tags=["滥用分析监控"])
api_router.include_router(demo_analytics.router, prefix="/analytics", tags=["演示账户分析"])

# 直接添加CSRF端点
@api_router.get("/csrf/csrf-token")
async def get_csrf_token_endpoint(response: Response):
    """
    获取CSRF Token
    用于前端在发送POST/PUT/DELETE请求时包含CSRF保护
    """
    token_data = get_csrf_token()
    
    # 设置CSRF token到Cookie
    response.set_cookie(
        key="csrf_token",
        value=token_data["cookie_token"],
        max_age=3600,  # 1小时
        httponly=False,  # 需要被JavaScript访问
        secure=True,     # 生产环境必须为True
        samesite="strict"
    )
    
    return {
        "csrf_token": token_data["token"],
        "expires_in": 3600
    }

# 健康检查路由
@api_router.get("/health")
async def api_health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Lawsker API v1"
    } 