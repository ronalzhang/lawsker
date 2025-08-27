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
from app.middlewares.performance_middleware import (
    PerformanceMiddleware, 
    ConcurrencyLimitMiddleware,
    ResponseCompressionMiddleware,
    CacheControlMiddleware
)
from app.core.performance_monitor import performance_optimizer
from app.core.database_performance import initialize_database_performance
from app.core.advanced_cache import initialize_cache_system
from app.core.cache import get_redis_client


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
    
    # 初始化性能优化系统
    try:
        await performance_optimizer.initialize()
        logger.info("✅ 性能优化系统启动完成")
    except Exception as e:
        logger.error(f"❌ 性能优化系统启动失败: {e}")
    
    # 初始化数据库性能优化
    try:
        await initialize_database_performance()
        logger.info("✅ 数据库性能优化初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库性能优化初始化失败: {e}")
    
    # 初始化缓存系统
    try:
        redis_client = await get_redis_client()
        await initialize_cache_system(redis_client)
        logger.info("✅ 缓存系统初始化完成")
    except Exception as e:
        logger.error(f"❌ 缓存系统初始化失败: {e}")
    
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
    
    # 关闭性能优化系统
    try:
        await performance_optimizer.shutdown()
        logger.info("✅ 性能优化系统已关闭")
    except Exception as e:
        logger.error(f"❌ 性能优化系统关闭失败: {e}")
    
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

# 性能监控中间件（按顺序添加）
app.add_middleware(CacheControlMiddleware)
app.add_middleware(ResponseCompressionMiddleware)
app.add_middleware(ConcurrencyLimitMiddleware, max_concurrent_requests=1000)
app.add_middleware(PerformanceMiddleware)

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

# 数据库健康检查端点
@app.get("/health/db")
async def database_health_check():
    """数据库健康检查端点"""
    try:
        from app.core.database import get_db
        async with get_db() as db:
            from sqlalchemy import text
            result = await db.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0"
            }
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# 性能指标端点
@app.get("/metrics/performance")
async def performance_metrics():
    """性能指标端点"""
    try:
        from app.core.advanced_cache import get_cache_manager
        cache_manager = await get_cache_manager()
        cache_stats = cache_manager.multi_cache.get_stats()
        
        import psutil
        system_stats = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0
        }
        
        return {
            "status": "ok",
            "cache_stats": cache_stats,
            "system_stats": system_stats,
            "timestamp": structlog.processors.TimeStamper(fmt="iso")
        }
    except Exception as e:
        logger.error(f"性能指标获取失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get performance metrics"}
        )


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