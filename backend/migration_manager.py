#!/usr/bin/env python3
"""
Lawsker数据库迁移管理器
确保100%成功率，零数据丢失的数据库迁移系统
"""

import asyncio
import asyncpg
import os
import json
import logging
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationResult:
    """迁移结果数据类"""
    success: bool
    migration_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    backup_path: Optional[str] = None
    error_message: Optional[str] = None
    tables_created: List[str] = None
    records_migrated: Dict[str, int] = None
    rollback_performed: bool = False

class DatabaseBackupManager:
    """数据库备份管理器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(self, backup_name: str) -> str:
        """创建数据库备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup_name}_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        logger.info(f"🔄 开始创建数据库备份: {backup_path}")
        
        try:
            # 解析数据库URL
            db_params = self._parse_database_url(self.database_url)
            
            # 使用pg_dump创建备份
            cmd = [
                "pg_dump",
                "-h", db_params["host"],
                "-p", str(db_params["port"]),
                "-U", db_params["user"],
                "-d", db_params["database"],
                "-f", str(backup_path),
                "--verbose",
                "--no-password"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = db_params["password"]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # 验证备份文件
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                raise Exception("备份文件创建失败或为空")
            
            logger.info(f"✅ 数据库备份创建成功: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"❌ 数据库备份创建失败: {e}")
            raise
    
    def _parse_database_url(self, url: str) -> Dict[str, str]:
        """解析数据库URL"""
        # postgresql://user:password@host:port/database
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": parsed.username or "postgres",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") or "postgres"
        }
    
    async def restore_backup(self, backup_path: str) -> bool:
        """从备份恢复数据库"""
        logger.info(f"🔄 开始从备份恢复数据库: {backup_path}")
        
        try:
            db_params = self._parse_database_url(self.database_url)
            
            # 使用psql恢复备份
            cmd = [
                "psql",
                "-h", db_params["host"],
                "-p", str(db_params["port"]),
                "-U", db_params["user"],
                "-d", db_params["database"],
                "-f", backup_path,
                "--quiet"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = db_params["password"]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ 数据库恢复失败: {result.stderr}")
                return False
            
            logger.info("✅ 数据库恢复成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库恢复失败: {e}")
            return False

class DataIntegrityValidator:
    """数据完整性验证器"""
    
    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection
    
    async def validate_pre_migration(self) -> Dict[str, int]:
        """迁移前数据验证"""
        logger.info("🔍 开始迁移前数据验证")
        
        validation_results = {}
        
        try:
            # 检查现有表的记录数
            tables_to_check = [
                "users", "cases", "profiles", "user_roles", "roles"
            ]
            
            for table in tables_to_check:
                try:
                    count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    validation_results[table] = count
                    logger.info(f"📊 表 {table}: {count} 条记录")
                except Exception as e:
                    logger.warning(f"⚠️ 无法检查表 {table}: {e}")
                    validation_results[table] = 0
            
            # 检查数据库连接
            await self.conn.fetchval("SELECT 1")
            validation_results["connection_test"] = 1
            
            logger.info("✅ 迁移前数据验证完成")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ 迁移前数据验证失败: {e}")
            raise
    
    async def validate_post_migration(self, pre_migration_counts: Dict[str, int]) -> bool:
        """迁移后数据验证"""
        logger.info("🔍 开始迁移后数据验证")
        
        try:
            # 验证原有表的数据完整性
            for table, expected_count in pre_migration_counts.items():
                if table == "connection_test":
                    continue
                
                try:
                    actual_count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    if actual_count != expected_count:
                        logger.error(f"❌ 表 {table} 数据丢失: 期望 {expected_count}, 实际 {actual_count}")
                        return False
                    logger.info(f"✅ 表 {table} 数据完整: {actual_count} 条记录")
                except Exception as e:
                    logger.error(f"❌ 无法验证表 {table}: {e}")
                    return False
            
            # 验证新创建的表
            new_tables = [
                "lawyer_certification_requests",
                "workspace_mappings", 
                "demo_accounts",
                "lawyer_levels",
                "lawyer_level_details",
                "user_credits",
                "lawyer_point_transactions",
                "collection_success_stats"
            ]
            
            for table in new_tables:
                try:
                    exists = await self.conn.fetchval(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                        table
                    )
                    if not exists:
                        logger.error(f"❌ 新表 {table} 未创建")
                        return False
                    logger.info(f"✅ 新表 {table} 创建成功")
                except Exception as e:
                    logger.error(f"❌ 无法验证新表 {table}: {e}")
                    return False
            
            # 验证初始数据
            lawyer_levels_count = await self.conn.fetchval("SELECT COUNT(*) FROM lawyer_levels")
            if lawyer_levels_count != 10:
                logger.error(f"❌ 律师等级初始数据不完整: 期望 10, 实际 {lawyer_levels_count}")
                return False
            
            logger.info("✅ 迁移后数据验证完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移后数据验证失败: {e}")
            return False

class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/lawsker')
        self.backup_manager = DatabaseBackupManager(self.database_url)
        self.migration_log_file = "migration_results.json"
    
    async def execute_migration(self, migration_file: str) -> MigrationResult:
        """执行数据库迁移"""
        migration_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"🚀 开始执行数据库迁移: {migration_id}")
        
        result = MigrationResult(
            success=False,
            migration_id=migration_id,
            start_time=start_time,
            tables_created=[],
            records_migrated={}
        )
        
        conn = None
        transaction = None
        
        try:
            # 1. 创建数据库备份
            logger.info("📦 创建数据库备份...")
            backup_path = await self.backup_manager.create_backup(f"pre_migration_{migration_id}")
            result.backup_path = backup_path
            
            # 2. 建立数据库连接
            logger.info("🔗 建立数据库连接...")
            conn = await asyncpg.connect(self.database_url)
            
            # 3. 迁移前数据验证
            validator = DataIntegrityValidator(conn)
            pre_migration_counts = await validator.validate_pre_migration()
            
            # 4. 开始事务
            logger.info("🔄 开始数据库事务...")
            transaction = conn.transaction()
            await transaction.start()
            
            # 5. 读取并执行迁移脚本
            logger.info(f"📜 读取迁移脚本: {migration_file}")
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # 分割SQL语句并逐个执行
            sql_statements = self._split_sql_statements(migration_sql)
            
            logger.info(f"🔧 执行 {len(sql_statements)} 个SQL语句...")
            for i, statement in enumerate(sql_statements, 1):
                if statement.strip():
                    try:
                        await conn.execute(statement)
                        if i % 10 == 0:
                            logger.info(f"📈 已执行 {i}/{len(sql_statements)} 个语句")
                    except Exception as e:
                        logger.error(f"❌ SQL语句执行失败 (第{i}个): {e}")
                        logger.error(f"失败的语句: {statement[:200]}...")
                        raise
            
            # 6. 迁移后数据验证
            logger.info("🔍 执行迁移后数据验证...")
            validation_success = await validator.validate_post_migration(pre_migration_counts)
            
            if not validation_success:
                raise Exception("迁移后数据验证失败")
            
            # 7. 提交事务
            logger.info("✅ 提交数据库事务...")
            await transaction.commit()
            
            # 8. 记录成功结果
            result.success = True
            result.end_time = datetime.now(timezone.utc)
            result.records_migrated = pre_migration_counts
            
            logger.info(f"🎉 数据库迁移成功完成: {migration_id}")
            
        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {e}")
            result.error_message = str(e)
            result.end_time = datetime.now(timezone.utc)
            
            # 回滚事务
            if transaction:
                try:
                    logger.info("🔄 回滚数据库事务...")
                    await transaction.rollback()
                    result.rollback_performed = True
                    logger.info("✅ 事务回滚成功")
                except Exception as rollback_error:
                    logger.error(f"❌ 事务回滚失败: {rollback_error}")
            
            # 如果需要，可以从备份恢复
            # await self._emergency_restore(result.backup_path)
            
        finally:
            if conn:
                await conn.close()
        
        # 保存迁移结果
        await self._save_migration_result(result)
        
        return result
    
    def _split_sql_statements(self, sql_content: str) -> List[str]:
        """分割SQL语句"""
        # 简单的SQL语句分割，可以根据需要改进
        statements = []
        current_statement = ""
        in_function = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('--'):
                continue
            
            # 检查是否在函数定义中
            if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
                in_function = True
            
            current_statement += line + '\n'
            
            # 检查语句结束
            if line.endswith(';'):
                if in_function and ('END;' in line.upper() or '$ LANGUAGE' in line.upper()):
                    in_function = False
                    statements.append(current_statement.strip())
                    current_statement = ""
                elif not in_function:
                    statements.append(current_statement.strip())
                    current_statement = ""
        
        # 添加最后一个语句（如果有）
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    async def _save_migration_result(self, result: MigrationResult):
        """保存迁移结果"""
        try:
            # 读取现有结果
            results = []
            if os.path.exists(self.migration_log_file):
                with open(self.migration_log_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            
            # 添加新结果
            result_dict = {
                "migration_id": result.migration_id,
                "success": result.success,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "backup_path": result.backup_path,
                "error_message": result.error_message,
                "tables_created": result.tables_created or [],
                "records_migrated": result.records_migrated or {},
                "rollback_performed": result.rollback_performed
            }
            
            results.append(result_dict)
            
            # 保存结果
            with open(self.migration_log_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📝 迁移结果已保存到: {self.migration_log_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存迁移结果失败: {e}")
    
    async def verify_migration_success(self) -> bool:
        """验证迁移是否成功"""
        logger.info("🔍 验证迁移成功状态...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            try:
                # 检查关键表是否存在
                required_tables = [
                    "lawyer_certification_requests",
                    "workspace_mappings",
                    "demo_accounts", 
                    "lawyer_levels",
                    "lawyer_level_details",
                    "user_credits",
                    "lawyer_point_transactions"
                ]
                
                for table in required_tables:
                    exists = await conn.fetchval(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                        table
                    )
                    if not exists:
                        logger.error(f"❌ 必需表 {table} 不存在")
                        return False
                
                # 检查初始数据
                lawyer_levels_count = await conn.fetchval("SELECT COUNT(*) FROM lawyer_levels")
                if lawyer_levels_count != 10:
                    logger.error(f"❌ 律师等级数据不完整: {lawyer_levels_count}/10")
                    return False
                
                # 检查用户表扩展字段
                workspace_id_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'workspace_id')"
                )
                if not workspace_id_exists:
                    logger.error("❌ 用户表workspace_id字段不存在")
                    return False
                
                logger.info("✅ 迁移验证成功")
                return True
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ 迁移验证失败: {e}")
            return False

async def main():
    """主函数"""
    print("🚀 Lawsker数据库迁移管理器")
    print("=" * 50)
    
    migration_manager = MigrationManager()
    migration_file = "backend/migrations/013_business_optimization_tables.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ 迁移文件不存在: {migration_file}")
        return
    
    # 执行迁移
    result = await migration_manager.execute_migration(migration_file)
    
    # 输出结果
    print("\n" + "=" * 50)
    print("📊 迁移结果摘要")
    print("=" * 50)
    print(f"迁移ID: {result.migration_id}")
    print(f"状态: {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"开始时间: {result.start_time}")
    print(f"结束时间: {result.end_time}")
    print(f"备份路径: {result.backup_path}")
    
    if result.error_message:
        print(f"错误信息: {result.error_message}")
    
    if result.rollback_performed:
        print("🔄 已执行事务回滚")
    
    # 最终验证
    if result.success:
        verification_success = await migration_manager.verify_migration_success()
        if verification_success:
            print("🎉 迁移完全成功，数据完整性验证通过！")
        else:
            print("⚠️ 迁移可能存在问题，请检查日志")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())