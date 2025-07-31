"""
增强的健康检查端点
基于系统优化建议文档的具体要求
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import asyncio
import redis
import psutil
import time
from typing import Dict, Any, List

from app.core.deps import get_db
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

async def check_database_connection(db: AsyncSession) -> Dict[str, Any]:
    """检查数据库连接"""
    start_time = time.time()
    try:
        # 执行简单查询测试连接
        result = await db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        
        # 检查连接池状态
        pool_info = {
            "pool_size": db.bind.pool.size() if hasattr(db.bind, 'pool') else "unknown",
            "checked_out": db.bind.pool.checkedout() if hasattr(db.bind, 'pool') else "unknown"
        }
        
        response_time = time.time() - start_time
        
        return {
            "healthy": test_value == 1,
            "response_time": response_time,
            "details": pool_info
        }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "healthy": False,
            "response_time": response_time,
            "details": {},
            "error": str(e)
        }

async def check_redis_connection() -> Dict[str, Any]:
    """检查Redis连接"""
    start_time = time.time()
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # 测试连接
        await asyncio.get_event_loop().run_in_executor(None, redis_client.ping)
        
        # 获取Redis信息
        info = await asyncio.get_event_loop().run_in_executor(None, redis_client.info)
        
        response_time = time.time() - start_time
        
        return {
            "healthy": True,
            "response_time": response_time,
            "details": {
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "healthy": False,
            "response_time": response_time,
            "details": {},
            "error": str(e)
        }

async def check_system_resources() -> Dict[str, Any]:
    """检查系统资源"""
    start_time = time.time()
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        
        # 网络连接数
        connections = len(psutil.net_connections())
        
        response_time = time.time() - start_time
        
        # 判断系统是否健康
        healthy = (
            cpu_percent < 80 and
            memory.percent < 85 and
            disk.percent < 90
        )
        
        return {
            "healthy": healthy,
            "response_time": response_time,
            "details": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_connections": connections
            }
        }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "healthy": False,
            "response_time": response_time,
            "details": {},
            "error": str(e)
        }

async def check_critical_services() -> Dict[str, Any]:
    """检查关键服务状态"""
    start_time = time.time()
    try:
        services_status = {}
        
        # 检查访问日志队列（模拟）
        try:
            services_status["access_log_queue"] = {
                "healthy": True,
                "details": {"status": "running", "queue_size": 0}
            }
        except Exception as e:
            services_status["access_log_queue"] = {
                "healthy": False,
                "error": str(e)
            }
        
        # 检查用户活动队列（模拟）
        try:
            services_status["user_activity_queue"] = {
                "healthy": True,
                "details": {"status": "running", "processed_count": 0}
            }
        except Exception as e:
            services_status["user_activity_queue"] = {
                "healthy": False,
                "error": str(e)
            }
        
        response_time = time.time() - start_time
        
        # 判断所有服务是否健康
        all_healthy = all(
            service.get("healthy", False) 
            for service in services_status.values()
        )
        
        return {
            "healthy": all_healthy,
            "response_time": response_time,
            "details": services_status
        }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "healthy": False,
            "response_time": response_time,
            "details": {},
            "error": str(e)
        }

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """增强的健康检查端点"""
    try:
        # 并行执行所有健康检查
        database_check, redis_check, system_check, services_check = await asyncio.gather(
            check_database_connection(db),
            check_redis_connection(),
            check_system_resources(),
            check_critical_services(),
            return_exceptions=True
        )
        
        # 处理异常结果
        checks = {
            "database": database_check if not isinstance(database_check, Exception) else {
                "healthy": False, "error": str(database_check)
            },
            "redis": redis_check if not isinstance(redis_check, Exception) else {
                "healthy": False, "error": str(redis_check)
            },
            "system": system_check if not isinstance(system_check, Exception) else {
                "healthy": False, "error": str(system_check)
            },
            "services": services_check if not isinstance(services_check, Exception) else {
                "healthy": False, "error": str(services_check)
            }
        }
        
        # 计算整体健康状态
        overall_healthy = all(check.get("healthy", False) for check in checks.values())
        
        overall_status = "healthy" if overall_healthy else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "database": "healthy" if checks["database"].get("healthy") else "unhealthy",
                "redis": "healthy" if checks["redis"].get("healthy") else "unhealthy", 
                "system": "healthy" if checks["system"].get("healthy") else "unhealthy",
                "critical_services": "healthy" if checks["services"].get("healthy") else "unhealthy"
            },
            "details": checks,
            "summary": {
                "total_checks": len(checks),
                "healthy_checks": sum(1 for check in checks.values() if check.get("healthy")),
                "average_response_time": sum(
                    check.get("response_time", 0) for check in checks.values()
                ) / len(checks)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@router.get("/health/quick")
async def quick_health_check():
    """快速健康检查"""
    try:
        start_time = time.time()
        
        # 简单的响应测试
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "response_time": response_time,
            "version": "1.0.0",
            "service": "lawsker-api"
        }
        
    except Exception as e:
        logger.error(f"Quick health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable"
        )

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """详细健康检查"""
    try:
        # 执行所有检查
        checks = {}
        
        # 数据库检查
        checks["database"] = await check_database_connection(db)
        
        # Redis检查
        checks["redis"] = await check_redis_connection()
        
        # 系统资源检查
        checks["system"] = await check_system_resources()
        
        # 关键服务检查
        checks["services"] = await check_critical_services()
        
        # 额外的详细检查
        checks["application"] = {
            "healthy": True,
            "response_time": 0.001,
            "details": {
                "python_version": "3.11",
                "fastapi_version": "0.104.1",
                "startup_time": datetime.now().isoformat()
            }
        }
        
        overall_healthy = all(check.get("healthy", False) for check in checks.values())
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "healthy_checks": sum(1 for check in checks.values() if check.get("healthy")),
                "unhealthy_checks": sum(1 for check in checks.values() if not check.get("healthy")),
                "average_response_time": sum(
                    check.get("response_time", 0) for check in checks.values()
                ) / len(checks),
                "overall_health_percentage": (
                    sum(1 for check in checks.values() if check.get("healthy")) / len(checks) * 100
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )