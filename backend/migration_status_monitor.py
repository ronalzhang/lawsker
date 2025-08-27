#!/usr/bin/env python3
"""
数据库迁移状态监控工具
实时监控迁移进度和系统状态
"""

import asyncio
import asyncpg
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SystemStatus:
    """系统状态"""
    timestamp: datetime
    database_connected: bool
    migration_tables_exist: bool
    data_integrity_ok: bool
    performance_metrics: Dict[str, Any]
    active_connections: int
    error_messages: List[str]

class MigrationStatusMonitor:
    """迁移状态监控器"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/lawsker')
        self.monitoring_active = False
        
    async def start_monitoring(self, duration_minutes: int = 60):
        """开始监控"""
        print(f"🔍 开始监控数据库迁移状态 ({duration_minutes} 分钟)")
        
        self.monitoring_active = True
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        status_history = []
        
        try:
            while self.monitoring_active and datetime.now() < end_time:
                status = await self._collect_system_status()
                status_history.append(status)
                
                # 打印当前状态
                self._print_status(status)
                
                # 检查是否有严重问题
                if not status.database_connected:
                    print("🚨 警告: 数据库连接丢失!")
                
                if not status.data_integrity_ok:
                    print("🚨 警告: 数据完整性问题!")
                
                # 等待下一次检查
                await asyncio.sleep(30)  # 每30秒检查一次
            
            # 生成监控报告
            await self._generate_monitoring_report(status_history)
            
        except KeyboardInterrupt:
            print("\n⏹️ 监控被用户停止")
        except Exception as e:
            print(f"❌ 监控过程中出错: {e}")
        finally:
            self.monitoring_active = False
    
    async def _collect_system_status(self) -> SystemStatus:
        """收集系统状态"""
        timestamp = datetime.now()
        error_messages = []
        
        # 初始化状态
        status = SystemStatus(
            timestamp=timestamp,
            database_connected=False,
            migration_tables_exist=False,
            data_integrity_ok=False,
            performance_metrics={},
            active_connections=0,
            error_messages=error_messages
        )
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            try:
                # 检查数据库连接
                await conn.fetchval("SELECT 1")
                status.database_connected = True
                
                # 检查迁移表是否存在
                migration_tables = [
                    "lawyer_certification_requests",
                    "workspace_mappings",
                    "demo_accounts",
                    "lawyer_levels",
                    "user_credits"
                ]
                
                existing_tables = 0
                for table in migration_tables:
                    exists = await conn.fetchval(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                        table
                    )
                    if exists:
                        existing_tables += 1
                
                status.migration_tables_exist = existing_tables == len(migration_tables)
                
                # 检查数据完整性
                integrity_ok = await self._check_data_integrity(conn)
                status.data_integrity_ok = integrity_ok
                
                # 收集性能指标
                performance_metrics = await self._collect_performance_metrics(conn)
                status.performance_metrics = performance_metrics
                
                # 获取活跃连接数
                active_connections = await conn.fetchval(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )
                status.active_connections = active_connections
                
            finally:
                await conn.close()
                
        except Exception as e:
            error_messages.append(f"数据库连接错误: {e}")
            status.database_connected = False
        
        return status
    
    async def _check_data_integrity(self, conn: asyncpg.Connection) -> bool:
        """检查数据完整性"""
        try:
            # 检查用户表的workspace_id
            users_without_workspace = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE workspace_id IS NULL"
            )
            
            if users_without_workspace > 0:
                return False
            
            # 检查律师等级数据
            if await conn.fetchval("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'lawyer_levels')"):
                lawyer_levels_count = await conn.fetchval("SELECT COUNT(*) FROM lawyer_levels")
                if lawyer_levels_count != 10:
                    return False
            
            # 检查外键约束
            fk_violations = await conn.fetchval("""
                SELECT COUNT(*) FROM (
                    SELECT conname FROM pg_constraint 
                    WHERE contype = 'f' AND NOT convalidated
                ) AS invalid_fks
            """)
            
            if fk_violations > 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _collect_performance_metrics(self, conn: asyncpg.Connection) -> Dict[str, Any]:
        """收集性能指标"""
        metrics = {}
        
        try:
            # 数据库大小
            db_size = await conn.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            metrics["database_size"] = db_size
            
            # 表数量
            table_count = await conn.fetchval(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            metrics["table_count"] = table_count
            
            # 索引数量
            index_count = await conn.fetchval(
                "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'"
            )
            metrics["index_count"] = index_count
            
            # 缓存命中率
            cache_hit_ratio = await conn.fetchval("""
                SELECT round(
                    100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2
                ) FROM pg_stat_database WHERE datname = current_database()
            """)
            metrics["cache_hit_ratio"] = f"{cache_hit_ratio}%"
            
            # 最大连接数
            max_connections = await conn.fetchval("SHOW max_connections")
            metrics["max_connections"] = max_connections
            
        except Exception as e:
            metrics["error"] = str(e)
        
        return metrics
    
    def _print_status(self, status: SystemStatus):
        """打印状态信息"""
        timestamp_str = status.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n📊 [{timestamp_str}] 系统状态检查")
        print("-" * 50)
        
        # 数据库连接
        db_status = "✅ 正常" if status.database_connected else "❌ 异常"
        print(f"数据库连接: {db_status}")
        
        # 迁移表
        tables_status = "✅ 完整" if status.migration_tables_exist else "❌ 不完整"
        print(f"迁移表状态: {tables_status}")
        
        # 数据完整性
        integrity_status = "✅ 正常" if status.data_integrity_ok else "❌ 异常"
        print(f"数据完整性: {integrity_status}")
        
        # 活跃连接
        print(f"活跃连接数: {status.active_connections}")
        
        # 性能指标
        if status.performance_metrics:
            print("性能指标:")
            for key, value in status.performance_metrics.items():
                if key != "error":
                    print(f"  {key}: {value}")
        
        # 错误信息
        if status.error_messages:
            print("错误信息:")
            for error in status.error_messages:
                print(f"  ❌ {error}")
    
    async def _generate_monitoring_report(self, status_history: List[SystemStatus]):
        """生成监控报告"""
        if not status_history:
            return
        
        report = {
            "monitoring_period": {
                "start_time": status_history[0].timestamp.isoformat(),
                "end_time": status_history[-1].timestamp.isoformat(),
                "duration_minutes": len(status_history) * 0.5,  # 每30秒一次检查
                "total_checks": len(status_history)
            },
            "summary": {
                "database_uptime": sum(1 for s in status_history if s.database_connected) / len(status_history) * 100,
                "migration_stability": sum(1 for s in status_history if s.migration_tables_exist) / len(status_history) * 100,
                "data_integrity_rate": sum(1 for s in status_history if s.data_integrity_ok) / len(status_history) * 100,
                "average_connections": sum(s.active_connections for s in status_history) / len(status_history)
            },
            "issues_detected": [],
            "performance_trends": {}
        }
        
        # 检测问题
        for i, status in enumerate(status_history):
            if not status.database_connected:
                report["issues_detected"].append({
                    "timestamp": status.timestamp.isoformat(),
                    "issue": "数据库连接丢失",
                    "check_number": i + 1
                })
            
            if not status.migration_tables_exist:
                report["issues_detected"].append({
                    "timestamp": status.timestamp.isoformat(),
                    "issue": "迁移表不完整",
                    "check_number": i + 1
                })
            
            if not status.data_integrity_ok:
                report["issues_detected"].append({
                    "timestamp": status.timestamp.isoformat(),
                    "issue": "数据完整性问题",
                    "check_number": i + 1
                })
        
        # 保存报告
        report_file = f"migration_monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 监控报告已保存到: {report_file}")
        
        # 打印摘要
        print("\n📊 监控摘要:")
        print(f"数据库正常运行时间: {report['summary']['database_uptime']:.1f}%")
        print(f"迁移表稳定性: {report['summary']['migration_stability']:.1f}%")
        print(f"数据完整性率: {report['summary']['data_integrity_rate']:.1f}%")
        print(f"平均连接数: {report['summary']['average_connections']:.1f}")
        
        if report["issues_detected"]:
            print(f"\n⚠️ 检测到 {len(report['issues_detected'])} 个问题")
        else:
            print("\n✅ 监控期间未发现问题")
    
    async def check_migration_status(self) -> Dict[str, Any]:
        """检查迁移状态（单次）"""
        print("🔍 检查当前迁移状态...")
        
        status = await self._collect_system_status()
        self._print_status(status)
        
        # 生成状态报告
        status_report = {
            "timestamp": status.timestamp.isoformat(),
            "database_connected": status.database_connected,
            "migration_tables_exist": status.migration_tables_exist,
            "data_integrity_ok": status.data_integrity_ok,
            "performance_metrics": status.performance_metrics,
            "active_connections": status.active_connections,
            "error_messages": status.error_messages,
            "overall_status": "healthy" if (
                status.database_connected and 
                status.migration_tables_exist and 
                status.data_integrity_ok
            ) else "issues_detected"
        }
        
        return status_report
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False

async def main():
    """主函数"""
    print("📊 Lawsker数据库迁移状态监控工具")
    print("=" * 50)
    
    monitor = MigrationStatusMonitor()
    
    print("选择监控模式:")
    print("1. 单次状态检查")
    print("2. 持续监控 (默认60分钟)")
    print("3. 自定义持续监控")
    print("4. 退出")
    
    try:
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            # 单次检查
            status_report = await monitor.check_migration_status()
            
            print(f"\n🎯 总体状态: {'✅ 健康' if status_report['overall_status'] == 'healthy' else '⚠️ 发现问题'}")
            
        elif choice == "2":
            # 默认持续监控
            await monitor.start_monitoring(60)
            
        elif choice == "3":
            # 自定义持续监控
            try:
                duration = int(input("请输入监控时长 (分钟): ").strip())
                if duration > 0:
                    await monitor.start_monitoring(duration)
                else:
                    print("❌ 无效的时长")
            except ValueError:
                print("❌ 无效的输入")
                
        elif choice == "4":
            print("👋 退出")
            return
            
        else:
            print("❌ 无效的选择")
            
    except KeyboardInterrupt:
        print("\n⏹️ 监控被用户停止")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"❌ 监控工具错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())