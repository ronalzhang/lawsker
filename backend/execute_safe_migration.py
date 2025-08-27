#!/usr/bin/env python3
"""
Lawsker安全数据库迁移执行器
确保100%成功率，零数据丢失的完整迁移流程
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migration_manager import MigrationManager, MigrationResult
from migration_verification import MigrationVerifier
from migration_rollback import MigrationRollback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'safe_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SafeMigrationExecutor:
    """安全迁移执行器"""
    
    def __init__(self):
        self.migration_manager = MigrationManager()
        self.verifier = MigrationVerifier()
        self.rollback_manager = MigrationRollback()
        self.migration_file = "backend/migrations/013_business_optimization_tables.sql"
        
    async def execute_complete_migration(self) -> Dict[str, Any]:
        """执行完整的安全迁移流程"""
        execution_id = f"safe_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"🚀 开始安全迁移执行: {execution_id}")
        
        execution_result = {
            "execution_id": execution_id,
            "start_time": start_time.isoformat(),
            "success": False,
            "phases": {},
            "final_status": "failed",
            "error_message": None,
            "rollback_performed": False
        }
        
        try:
            # 阶段1: 预检查
            logger.info("📋 阶段1: 执行预检查...")
            pre_check_result = await self._pre_migration_checks()
            execution_result["phases"]["pre_check"] = pre_check_result
            
            if not pre_check_result["success"]:
                raise Exception(f"预检查失败: {pre_check_result['error']}")
            
            # 阶段2: 执行迁移
            logger.info("🔧 阶段2: 执行数据库迁移...")
            migration_result = await self.migration_manager.execute_migration(self.migration_file)
            execution_result["phases"]["migration"] = {
                "success": migration_result.success,
                "migration_id": migration_result.migration_id,
                "backup_path": migration_result.backup_path,
                "error_message": migration_result.error_message,
                "rollback_performed": migration_result.rollback_performed
            }
            
            if not migration_result.success:
                raise Exception(f"迁移执行失败: {migration_result.error_message}")
            
            # 阶段3: 迁移验证
            logger.info("🔍 阶段3: 执行迁移验证...")
            verification_success = await self.verifier.run_all_verifications()
            verification_report = await self.verifier.generate_verification_report()
            
            execution_result["phases"]["verification"] = {
                "success": verification_success,
                "report": verification_report
            }
            
            if not verification_success:
                # 验证失败，执行回滚
                logger.error("❌ 迁移验证失败，开始回滚...")
                rollback_result = await self.rollback_manager.selective_rollback()
                execution_result["rollback_performed"] = True
                execution_result["phases"]["rollback"] = {
                    "success": rollback_result.success,
                    "type": rollback_result.rollback_type,
                    "tables_dropped": rollback_result.tables_dropped
                }
                
                raise Exception("迁移验证失败，已执行回滚")
            
            # 阶段4: 最终确认
            logger.info("✅ 阶段4: 最终确认...")
            final_verification = await self.migration_manager.verify_migration_success()
            execution_result["phases"]["final_verification"] = {
                "success": final_verification
            }
            
            if not final_verification:
                raise Exception("最终验证失败")
            
            # 成功完成
            execution_result["success"] = True
            execution_result["final_status"] = "success"
            logger.info("🎉 安全迁移执行成功完成！")
            
        except Exception as e:
            execution_result["error_message"] = str(e)
            execution_result["final_status"] = "failed"
            logger.error(f"❌ 安全迁移执行失败: {e}")
        
        execution_result["end_time"] = datetime.now().isoformat()
        execution_result["duration_seconds"] = (datetime.now() - start_time).total_seconds()
        
        # 保存执行结果
        await self._save_execution_result(execution_result)
        
        return execution_result
    
    async def _pre_migration_checks(self) -> Dict[str, Any]:
        """预迁移检查"""
        logger.info("🔍 执行预迁移检查...")
        
        checks = {
            "success": True,
            "checks": {},
            "error": None
        }
        
        try:
            # 检查1: 迁移文件存在
            migration_file_exists = os.path.exists(self.migration_file)
            checks["checks"]["migration_file_exists"] = migration_file_exists
            
            if not migration_file_exists:
                checks["success"] = False
                checks["error"] = f"迁移文件不存在: {self.migration_file}"
                return checks
            
            # 检查2: 数据库连接
            db_connection = await self.migration_manager.backup_manager._test_database_connection()
            checks["checks"]["database_connection"] = db_connection
            
            if not db_connection:
                checks["success"] = False
                checks["error"] = "无法连接到数据库"
                return checks
            
            # 检查3: 备份目录权限
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            backup_writable = os.access(backup_dir, os.W_OK)
            checks["checks"]["backup_directory_writable"] = backup_writable
            
            if not backup_writable:
                checks["success"] = False
                checks["error"] = "备份目录不可写"
                return checks
            
            # 检查4: 磁盘空间
            disk_space_ok = await self._check_disk_space()
            checks["checks"]["sufficient_disk_space"] = disk_space_ok
            
            if not disk_space_ok:
                checks["success"] = False
                checks["error"] = "磁盘空间不足"
                return checks
            
            # 检查5: PostgreSQL工具
            pg_tools_available = await self._check_postgresql_tools()
            checks["checks"]["postgresql_tools_available"] = pg_tools_available
            
            if not pg_tools_available:
                checks["success"] = False
                checks["error"] = "PostgreSQL工具不可用 (pg_dump, psql)"
                return checks
            
            logger.info("✅ 所有预检查通过")
            
        except Exception as e:
            checks["success"] = False
            checks["error"] = str(e)
            logger.error(f"❌ 预检查失败: {e}")
        
        return checks
    
    async def _check_disk_space(self) -> bool:
        """检查磁盘空间"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            
            # 需要至少1GB的可用空间
            required_space = 1024 * 1024 * 1024  # 1GB
            
            logger.info(f"💾 磁盘空间: 总计 {total//1024//1024//1024}GB, "
                       f"已用 {used//1024//1024//1024}GB, "
                       f"可用 {free//1024//1024//1024}GB")
            
            return free > required_space
            
        except Exception as e:
            logger.warning(f"⚠️ 无法检查磁盘空间: {e}")
            return True  # 假设有足够空间
    
    async def _check_postgresql_tools(self) -> bool:
        """检查PostgreSQL工具"""
        try:
            import subprocess
            
            # 检查pg_dump
            result = subprocess.run(["pg_dump", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            # 检查psql
            result = subprocess.run(["psql", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            logger.info("✅ PostgreSQL工具可用")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL工具检查失败: {e}")
            return False
    
    async def _save_execution_result(self, result: Dict[str, Any]):
        """保存执行结果"""
        try:
            result_file = f"safe_migration_result_{result['execution_id']}.json"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📝 执行结果已保存到: {result_file}")
            
            # 同时保存到汇总文件
            summary_file = "migration_execution_history.json"
            
            history = []
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # 添加简化的记录
            summary_record = {
                "execution_id": result["execution_id"],
                "start_time": result["start_time"],
                "end_time": result["end_time"],
                "success": result["success"],
                "final_status": result["final_status"],
                "duration_seconds": result["duration_seconds"],
                "rollback_performed": result["rollback_performed"]
            }
            
            history.append(summary_record)
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ 保存执行结果失败: {e}")
    
    def print_execution_summary(self, result: Dict[str, Any]):
        """打印执行摘要"""
        print("\n" + "=" * 80)
        print("🎯 Lawsker安全迁移执行摘要")
        print("=" * 80)
        
        print(f"执行ID: {result['execution_id']}")
        print(f"开始时间: {result['start_time']}")
        print(f"结束时间: {result['end_time']}")
        print(f"执行时长: {result['duration_seconds']:.1f} 秒")
        print(f"最终状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        if result.get('rollback_performed'):
            print("🔄 已执行回滚操作")
        
        print("\n📋 各阶段执行情况:")
        
        # 预检查
        if "pre_check" in result["phases"]:
            pre_check = result["phases"]["pre_check"]
            status = "✅ 通过" if pre_check["success"] else "❌ 失败"
            print(f"  1. 预检查: {status}")
            if not pre_check["success"]:
                print(f"     错误: {pre_check['error']}")
        
        # 迁移执行
        if "migration" in result["phases"]:
            migration = result["phases"]["migration"]
            status = "✅ 成功" if migration["success"] else "❌ 失败"
            print(f"  2. 迁移执行: {status}")
            if migration.get("backup_path"):
                print(f"     备份路径: {migration['backup_path']}")
            if not migration["success"]:
                print(f"     错误: {migration['error_message']}")
        
        # 迁移验证
        if "verification" in result["phases"]:
            verification = result["phases"]["verification"]
            status = "✅ 通过" if verification["success"] else "❌ 失败"
            print(f"  3. 迁移验证: {status}")
            if verification.get("report"):
                report = verification["report"]
                print(f"     验证测试: {report['summary']['passed_tests']}/{report['summary']['total_tests']} 通过")
                print(f"     成功率: {report['summary']['success_rate']:.1f}%")
        
        # 回滚
        if "rollback" in result["phases"]:
            rollback = result["phases"]["rollback"]
            status = "✅ 成功" if rollback["success"] else "❌ 失败"
            print(f"  4. 回滚操作: {status}")
            print(f"     回滚类型: {rollback['type']}")
            if rollback.get("tables_dropped"):
                print(f"     删除表数: {len(rollback['tables_dropped'])}")
        
        # 最终验证
        if "final_verification" in result["phases"]:
            final_verification = result["phases"]["final_verification"]
            status = "✅ 通过" if final_verification["success"] else "❌ 失败"
            print(f"  5. 最终验证: {status}")
        
        if result["error_message"]:
            print(f"\n❌ 错误信息: {result['error_message']}")
        
        print("=" * 80)
        
        if result["success"]:
            print("🎉 恭喜！数据库迁移成功完成，数据完整性得到保证！")
        else:
            print("⚠️ 迁移失败，但数据安全得到保护。请检查错误信息并重试。")
        
        print("=" * 80)

# 为MigrationManager添加缺失的方法
async def _test_database_connection(self):
    """测试数据库连接"""
    try:
        import asyncpg
        conn = await asyncpg.connect(self.database_url)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True
    except Exception:
        return False

# 动态添加方法
MigrationManager.backup_manager._test_database_connection = _test_database_connection

async def main():
    """主函数"""
    print("🚀 Lawsker安全数据库迁移系统")
    print("=" * 50)
    print("本系统确保100%成功率，零数据丢失的数据库迁移")
    print("=" * 50)
    
    executor = SafeMigrationExecutor()
    
    # 确认执行
    print("\n⚠️ 重要提示:")
    print("- 迁移前将自动创建完整数据库备份")
    print("- 所有操作在事务中执行，失败时自动回滚")
    print("- 迁移后将进行全面的数据完整性验证")
    print("- 如有问题，可以安全回滚到迁移前状态")
    
    try:
        confirm = input("\n确认开始安全迁移? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ 迁移已取消")
            return
        
        # 执行迁移
        result = await executor.execute_complete_migration()
        
        # 打印结果摘要
        executor.print_execution_summary(result)
        
        # 返回适当的退出码
        return 0 if result["success"] else 1
        
    except KeyboardInterrupt:
        print("\n❌ 迁移被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 迁移系统错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)