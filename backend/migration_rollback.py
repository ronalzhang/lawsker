#!/usr/bin/env python3
"""
数据库迁移回滚工具
在迁移失败时提供安全的回滚机制
"""

import asyncio
import asyncpg
import os
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RollbackResult:
    """回滚结果"""
    success: bool
    rollback_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    backup_restored: Optional[str] = None
    error_message: Optional[str] = None
    tables_dropped: List[str] = None

class MigrationRollback:
    """迁移回滚管理器"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/lawsker')
        self.backup_dir = Path("backups")
    
    async def emergency_rollback(self, backup_path: str) -> RollbackResult:
        """紧急回滚：从备份完全恢复数据库"""
        logger.info(f"🚨 开始紧急回滚，从备份恢复: {backup_path}")
        
        result = RollbackResult(
            success=False,
            rollback_type="emergency_restore",
            start_time=datetime.now()
        )
        
        try:
            if not os.path.exists(backup_path):
                raise Exception(f"备份文件不存在: {backup_path}")
            
            # 解析数据库URL
            db_params = self._parse_database_url(self.database_url)
            
            # 断开所有连接
            await self._terminate_connections(db_params)
            
            # 删除现有数据库
            await self._drop_database(db_params)
            
            # 重新创建数据库
            await self._create_database(db_params)
            
            # 从备份恢复
            success = await self._restore_from_backup(backup_path, db_params)
            
            if success:
                result.success = True
                result.backup_restored = backup_path
                logger.info("✅ 紧急回滚成功")
            else:
                raise Exception("备份恢复失败")
                
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"❌ 紧急回滚失败: {e}")
        
        result.end_time = datetime.now()
        return result
    
    async def selective_rollback(self) -> RollbackResult:
        """选择性回滚：只删除新创建的表和字段"""
        logger.info("🔄 开始选择性回滚，删除新创建的表和字段")
        
        result = RollbackResult(
            success=False,
            rollback_type="selective",
            start_time=datetime.now(),
            tables_dropped=[]
        )
        
        conn = None
        transaction = None
        
        try:
            conn = await asyncpg.connect(self.database_url)
            transaction = conn.transaction()
            await transaction.start()
            
            # 删除新创建的表（按依赖关系逆序）
            tables_to_drop = [
                "collection_success_stats",
                "enterprise_subscriptions", 
                "enterprise_service_packages",
                "enterprise_clients",
                "lawyer_assignment_suspensions",
                "lawyer_case_declines",
                "credit_purchase_records",
                "user_credits",
                "lawyer_online_sessions",
                "lawyer_point_transactions",
                "ai_tool_usage",
                "case_reviews",
                "matching_history",
                "case_invitations",
                "lawyer_level_details",
                "lawyer_levels",
                "batch_upload_tasks",
                "demo_accounts",
                "workspace_mappings",
                "lawyer_certification_requests"
            ]
            
            for table in tables_to_drop:
                try:
                    await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    result.tables_dropped.append(table)
                    logger.info(f"🗑️ 已删除表: {table}")
                except Exception as e:
                    logger.warning(f"⚠️ 删除表 {table} 失败: {e}")
            
            # 删除用户表的新字段
            user_fields_to_drop = ["workspace_id", "account_type", "email_verified", "registration_source"]
            
            for field in user_fields_to_drop:
                try:
                    await conn.execute(f"ALTER TABLE users DROP COLUMN IF EXISTS {field}")
                    logger.info(f"🗑️ 已删除用户表字段: {field}")
                except Exception as e:
                    logger.warning(f"⚠️ 删除用户表字段 {field} 失败: {e}")
            
            # 删除视图
            views_to_drop = ["lawyer_performance_summary", "case_matching_stats"]
            
            for view in views_to_drop:
                try:
                    await conn.execute(f"DROP VIEW IF EXISTS {view}")
                    logger.info(f"🗑️ 已删除视图: {view}")
                except Exception as e:
                    logger.warning(f"⚠️ 删除视图 {view} 失败: {e}")
            
            # 删除触发器函数
            try:
                await conn.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
                logger.info("🗑️ 已删除触发器函数")
            except Exception as e:
                logger.warning(f"⚠️ 删除触发器函数失败: {e}")
            
            await transaction.commit()
            result.success = True
            logger.info("✅ 选择性回滚成功")
            
        except Exception as e:
            if transaction:
                await transaction.rollback()
            result.error_message = str(e)
            logger.error(f"❌ 选择性回滚失败: {e}")
        
        finally:
            if conn:
                await conn.close()
        
        result.end_time = datetime.now()
        return result
    
    async def verify_rollback(self) -> bool:
        """验证回滚是否成功"""
        logger.info("🔍 验证回滚结果...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            try:
                # 检查新表是否已删除
                new_tables = [
                    "lawyer_certification_requests",
                    "workspace_mappings",
                    "demo_accounts",
                    "lawyer_levels",
                    "user_credits"
                ]
                
                for table in new_tables:
                    exists = await conn.fetchval(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                        table
                    )
                    if exists:
                        logger.error(f"❌ 表 {table} 仍然存在")
                        return False
                
                # 检查用户表字段是否已删除
                workspace_id_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'workspace_id')"
                )
                if workspace_id_exists:
                    logger.error("❌ 用户表workspace_id字段仍然存在")
                    return False
                
                # 检查原有表是否完整
                original_tables = ["users", "cases", "profiles"]
                for table in original_tables:
                    exists = await conn.fetchval(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                        table
                    )
                    if not exists:
                        logger.error(f"❌ 原有表 {table} 不存在")
                        return False
                
                logger.info("✅ 回滚验证成功")
                return True
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ 回滚验证失败: {e}")
            return False
    
    def _parse_database_url(self, url: str) -> Dict[str, str]:
        """解析数据库URL"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": parsed.username or "postgres",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") or "postgres"
        }
    
    async def _terminate_connections(self, db_params: Dict[str, str]):
        """终止数据库连接"""
        logger.info("🔌 终止数据库连接...")
        
        try:
            # 连接到postgres数据库来终止目标数据库的连接
            admin_conn = await asyncpg.connect(
                host=db_params["host"],
                port=db_params["port"],
                user=db_params["user"],
                password=db_params["password"],
                database="postgres"
            )
            
            try:
                await admin_conn.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = $1 AND pid <> pg_backend_pid()
                """, db_params["database"])
                
                logger.info("✅ 数据库连接已终止")
                
            finally:
                await admin_conn.close()
                
        except Exception as e:
            logger.warning(f"⚠️ 终止数据库连接失败: {e}")
    
    async def _drop_database(self, db_params: Dict[str, str]):
        """删除数据库"""
        logger.info(f"🗑️ 删除数据库: {db_params['database']}")
        
        admin_conn = await asyncpg.connect(
            host=db_params["host"],
            port=db_params["port"],
            user=db_params["user"],
            password=db_params["password"],
            database="postgres"
        )
        
        try:
            await admin_conn.execute(f'DROP DATABASE IF EXISTS "{db_params["database"]}"')
            logger.info("✅ 数据库已删除")
            
        finally:
            await admin_conn.close()
    
    async def _create_database(self, db_params: Dict[str, str]):
        """创建数据库"""
        logger.info(f"🏗️ 创建数据库: {db_params['database']}")
        
        admin_conn = await asyncpg.connect(
            host=db_params["host"],
            port=db_params["port"],
            user=db_params["user"],
            password=db_params["password"],
            database="postgres"
        )
        
        try:
            await admin_conn.execute(f'CREATE DATABASE "{db_params["database"]}"')
            logger.info("✅ 数据库已创建")
            
        finally:
            await admin_conn.close()
    
    async def _restore_from_backup(self, backup_path: str, db_params: Dict[str, str]) -> bool:
        """从备份恢复"""
        logger.info(f"📦 从备份恢复: {backup_path}")
        
        try:
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
                logger.error(f"❌ 备份恢复失败: {result.stderr}")
                return False
            
            logger.info("✅ 备份恢复成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 备份恢复失败: {e}")
            return False
    
    async def list_available_backups(self) -> List[str]:
        """列出可用的备份文件"""
        backups = []
        
        if self.backup_dir.exists():
            for backup_file in self.backup_dir.glob("*.sql"):
                backups.append(str(backup_file))
        
        return sorted(backups, reverse=True)  # 最新的在前面
    
    async def save_rollback_result(self, result: RollbackResult):
        """保存回滚结果"""
        try:
            rollback_log = "rollback_results.json"
            
            # 读取现有结果
            results = []
            if os.path.exists(rollback_log):
                with open(rollback_log, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            
            # 添加新结果
            result_dict = {
                "rollback_type": result.rollback_type,
                "success": result.success,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "backup_restored": result.backup_restored,
                "error_message": result.error_message,
                "tables_dropped": result.tables_dropped or []
            }
            
            results.append(result_dict)
            
            # 保存结果
            with open(rollback_log, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📝 回滚结果已保存到: {rollback_log}")
            
        except Exception as e:
            logger.error(f"❌ 保存回滚结果失败: {e}")

async def main():
    """主函数"""
    print("🔄 Lawsker数据库迁移回滚工具")
    print("=" * 50)
    
    rollback_manager = MigrationRollback()
    
    # 列出可用的备份
    backups = await rollback_manager.list_available_backups()
    
    if not backups:
        print("❌ 没有找到可用的备份文件")
        return
    
    print("📦 可用的备份文件:")
    for i, backup in enumerate(backups[:5], 1):  # 只显示最新的5个
        backup_name = os.path.basename(backup)
        backup_time = os.path.getmtime(backup)
        backup_date = datetime.fromtimestamp(backup_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {i}. {backup_name} ({backup_date})")
    
    print("\n选择回滚方式:")
    print("1. 选择性回滚 (推荐) - 只删除新创建的表和字段")
    print("2. 紧急回滚 - 从备份完全恢复数据库")
    print("3. 退出")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            # 选择性回滚
            result = await rollback_manager.selective_rollback()
            
        elif choice == "2":
            # 紧急回滚
            backup_choice = input(f"选择备份文件 (1-{min(5, len(backups))}): ").strip()
            
            try:
                backup_index = int(backup_choice) - 1
                if 0 <= backup_index < len(backups):
                    backup_path = backups[backup_index]
                    print(f"⚠️ 警告: 这将完全恢复数据库到备份时的状态，所有后续更改将丢失！")
                    confirm = input("确认执行紧急回滚? (yes/no): ").strip().lower()
                    
                    if confirm == "yes":
                        result = await rollback_manager.emergency_rollback(backup_path)
                    else:
                        print("❌ 回滚已取消")
                        return
                else:
                    print("❌ 无效的备份选择")
                    return
            except ValueError:
                print("❌ 无效的输入")
                return
                
        elif choice == "3":
            print("👋 退出")
            return
            
        else:
            print("❌ 无效的选择")
            return
        
        # 保存回滚结果
        await rollback_manager.save_rollback_result(result)
        
        # 输出结果
        print("\n" + "=" * 50)
        print("📊 回滚结果")
        print("=" * 50)
        print(f"回滚类型: {result.rollback_type}")
        print(f"状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"开始时间: {result.start_time}")
        print(f"结束时间: {result.end_time}")
        
        if result.backup_restored:
            print(f"恢复的备份: {result.backup_restored}")
        
        if result.tables_dropped:
            print(f"删除的表: {', '.join(result.tables_dropped)}")
        
        if result.error_message:
            print(f"错误信息: {result.error_message}")
        
        # 验证回滚
        if result.success:
            verification_success = await rollback_manager.verify_rollback()
            if verification_success:
                print("🎉 回滚验证成功！")
            else:
                print("⚠️ 回滚验证失败，请手动检查")
        
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
    except Exception as e:
        print(f"❌ 回滚过程中出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())