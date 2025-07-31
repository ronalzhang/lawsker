"""
Lawsker (律思客) - 后端主应用
AI驱动的O2O专业服务平台
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, create_tables
from app.api.v1.api import api_router
from app.middlewares.access_logger import AccessLoggerMiddleware


# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 Lawsker Backend 启动中...")
    await create_tables()
    logger.info("✅ 数据库表创建完成")
    
    # 启动访问日志处理器
    from app.services.access_log_processor import start_access_log_processor
    await start_access_log_processor()
    logger.info("✅ 访问日志处理器启动完成")
    
    # 启动用户活动处理器
    from app.services.user_activity_processor import start_user_activity_processor
    await start_user_activity_processor()
    logger.info("✅ 用户活动处理器启动完成")
    
    # 启动WebSocket管理器
    from app.services.websocket_manager import start_websocket_manager
    await start_websocket_manager()
    logger.info("✅ WebSocket管理器启动完成")
    
    # 启动实时数据聚合器
    from app.services.realtime_data_aggregator import start_realtime_data_aggregator
    await start_realtime_data_aggregator()
    logger.info("✅ 实时数据聚合器启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("👋 Lawsker Backend 关闭中...")
    from app.services.access_log_processor import stop_access_log_processor
    from app.services.user_activity_processor import stop_user_activity_processor
    from app.services.websocket_manager import stop_websocket_manager
    from app.services.realtime_data_aggregator import stop_realtime_data_aggregator
    await stop_access_log_processor()
    await stop_user_activity_processor()
    await stop_websocket_manager()
    await stop_realtime_data_aggregator()
    logger.info("✅ 所有处理器已停止")


# 创建FastAPI应用
app = FastAPI(
    title="Lawsker API",
    description="律思客 - AI驱动的O2O专业服务平台 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 访问日志中间件
app.add_middleware(AccessLoggerMiddleware)


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error("HTTP异常", status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error("未处理异常", error=str(exc), type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"message": "内部服务器错误", "status_code": 500}
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "Lawsker Backend",
        "version": "1.0.0"
    }


# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "Lawsker (律思客) API - 法律智慧，即刻送达",
        "docs_url": "/docs",
        "health_url": "/health",
        "version": "1.0.0"
    }


# 注册API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 