"""
数据库连接和会话管理
支持异步操作和连接池
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://...?command_timeout=30&...?connect_timeout=10&...?sslmode=require&", "postgresql+asyncpg://"),
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=300,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基础模型类
Base = declarative_base()


async def create_tables():
    """创建数据库表"""
    try:
        async with engine.begin() as conn:
            # 导入所有模型以确保表被创建
            from app.models import user, tenant, case, finance  # noqa
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ 数据库表创建成功")
    except Exception as e:
        logger.error("❌ 数据库表创建失败", error=str(e))
        raise


async def get_db() -> AsyncSession:
    """获取数据库会话依赖项"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("数据库会话错误", error=str(e))
            raise
        finally:
            await session.close()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def create_session(self) -> AsyncSession:
        """创建新的数据库会话"""
        return self.session_factory()
    
    async def execute_query(self, query: str, params: dict = None):
        """执行原生SQL查询"""
        async with self.session_factory() as session:
            try:
                result = await session.execute(query, params or {})
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error("SQL查询执行失败", query=query, error=str(e))
                raise
    
    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("数据库健康检查失败", error=str(e))
            return False


# 创建全局数据库管理器实例
db_manager = DatabaseManager()


# PostgreSQL 连接配置（如需要可在此添加PostgreSQL特定设置）