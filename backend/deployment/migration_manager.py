"""
数据库迁移管理器
提供Alembic迁移脚本执行、状态检查、回滚和数据完整性验证功能
"""

import os
import sys
import subprocess
import logging
import time
import shutil
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import tempfile
import hashlib

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
import structlog

logger = structlog.get_logger()

@dataclass
class MigrationInfo:
    """迁移信息数据类"""
    revision: str
    description: str
    is_head: bool = False
    is_current: bool = False
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class MigrationStatus:
    """迁移状态数据类"""
    current_revision: Optional[str] = None
    head_revision: Optional[str] = None
    pending_migrations: List[str] = None
    is_up_to_date: bool = False
    total_migrations: int = 0
    applied_migrations: int = 0
    
    def __post_init__(self):
        if self.pending_migrations is None:
            self.pending_migrations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class BackupInfo:
    """备份信息数据类"""
    backup_id: str
    backup_path: str
    database_name: str
    backup_size: int
    created_at: datetime
    migration_revision: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result

class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self, database_url: str, project_root: str = "."):
        self.database_url = database_url
        self.project_root = Path(project_root).resolve()
        self.logger = structlog.get_logger(__name__)
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Alembic配置
        self.alembic_cfg_path = self.project_root / "backend" / "alembic.ini"
        self.alembic_dir = self.project_root / "backend" / "alembic"
        self.versions_dir = self.alembic_dir / "versions"
        
        # 备份目录
        self.backup_dir = self.project_root / "backend" / "deployment" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Alembic配置
        self._init_alembic_config()
        
        # 状态跟踪
        self.status = MigrationStatus()
        
    def _init_alembic_config(self):
        """初始化Alembic配置"""
        try:
            if not self.alembic_cfg_path.exists():
                self.logger.error(f"Alembic配置文件不存在: {self.alembic_cfg_path}")
                raise FileNotFoundError(f"Alembic配置文件不存在: {self.alembic_cfg_path}")
            
            self.alembic_cfg = Config(str(self.alembic_cfg_path))
            self.alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)
            
            # 设置脚本位置
            script_location = str(self.alembic_dir)
            self.alembic_cfg.set_main_option("script_location", script_location)
            
            self.logger.info("✅ Alembic配置初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 初始化Alembic配置失败: {e}")
            raise
    
    def get_migration_status(self) -> MigrationStatus:
        """获取迁移状态"""
        try:
            self.logger.info("获取迁移状态...")
            
            # 获取脚本目录
            script = ScriptDirectory.from_config(self.alembic_cfg)
            
            # 获取头部版本（处理可能的错误）
            try:
                head_revision = script.get_current_head()
            except Exception as e:
                self.logger.warning(f"获取头部版本失败，可能存在迁移链问题: {e}")
                # 尝试获取所有版本并找到最新的
                try:
                    all_revisions = list(script.walk_revisions())
                    head_revision = all_revisions[0].revision if all_revisions else None
                except Exception:
                    head_revision = None
            
            # 获取当前版本
            current_revision = None
            try:
                engine = create_engine(self.database_url)
                with engine.connect() as connection:
                    context = MigrationContext.configure(connection)
                    current_revision = context.get_current_revision()
                engine.dispose()
            except Exception as e:
                self.logger.warning(f"获取当前版本失败: {e}")
            
            # 获取所有迁移（安全处理）
            total_migrations = 0
            applied_migrations = 0
            try:
                all_revisions = list(script.walk_revisions())
                total_migrations = len(all_revisions)
                
                # 计算已应用的迁移数量
                if current_revision:
                    for rev in all_revisions:
                        applied_migrations += 1
                        if rev.revision == current_revision:
                            break
            except Exception as e:
                self.logger.warning(f"获取迁移列表失败: {e}")
            
            # 获取待执行的迁移
            pending_migrations = []
            if current_revision != head_revision and head_revision:
                try:
                    for rev in script.walk_revisions(head_revision, current_revision):
                        if rev.revision != current_revision:
                            pending_migrations.append(rev.revision)
                except Exception as e:
                    self.logger.warning(f"获取待执行迁移失败: {e}")
            
            # 更新状态
            self.status = MigrationStatus(
                current_revision=current_revision,
                head_revision=head_revision,
                pending_migrations=pending_migrations,
                is_up_to_date=(current_revision == head_revision),
                total_migrations=total_migrations,
                applied_migrations=applied_migrations
            )
            
            self.logger.info(f"✅ 迁移状态获取完成: 当前版本={current_revision}, 最新版本={head_revision}")
            return self.status
            
        except Exception as e:
            self.logger.error(f"❌ 获取迁移状态失败: {e}")
            # 返回默认状态而不是抛出异常
            self.status = MigrationStatus()
            return self.status
    
    def get_migration_history(self) -> List[MigrationInfo]:
        """获取迁移历史"""
        try:
            self.logger.info("获取迁移历史...")
            
            script = ScriptDirectory.from_config(self.alembic_cfg)
            current_status = self.get_migration_status()
            
            migrations = []
            try:
                for rev in script.walk_revisions():
                    migration_info = MigrationInfo(
                        revision=rev.revision,
                        description=rev.doc or "No description",
                        is_head=(rev.revision == current_status.head_revision),
                        is_current=(rev.revision == current_status.current_revision)
                    )
                    
                    # 尝试从文件获取创建时间
                    try:
                        # 尝试多种文件名格式
                        possible_files = [
                            self.versions_dir / f"{rev.revision}_{rev.doc.replace(' ', '_').lower()}.py",
                            self.versions_dir / f"{rev.revision}.py",
                        ]
                        
                        # 也尝试查找包含revision的文件
                        for file_path in self.versions_dir.glob("*.py"):
                            if rev.revision in file_path.name:
                                possible_files.append(file_path)
                        
                        for version_file in possible_files:
                            if version_file.exists():
                                migration_info.created_at = datetime.fromtimestamp(version_file.stat().st_mtime)
                                break
                    except Exception:
                        pass  # 忽略文件时间获取错误
                    
                    migrations.append(migration_info)
            except Exception as e:
                self.logger.warning(f"遍历迁移时出错: {e}")
                # 尝试直接从文件系统获取迁移信息
                for file_path in self.versions_dir.glob("*.py"):
                    if file_path.name.startswith("__"):
                        continue
                    try:
                        # 从文件名提取revision
                        revision = file_path.stem.split("_")[0]
                        description = " ".join(file_path.stem.split("_")[1:]) if "_" in file_path.stem else "No description"
                        
                        migration_info = MigrationInfo(
                            revision=revision,
                            description=description,
                            is_head=False,
                            is_current=False,
                            created_at=datetime.fromtimestamp(file_path.stat().st_mtime)
                        )
                        migrations.append(migration_info)
                    except Exception:
                        continue
            
            self.logger.info(f"✅ 获取到 {len(migrations)} 个迁移记录")
            return migrations
            
        except Exception as e:
            self.logger.error(f"❌ 获取迁移历史失败: {e}")
            return []
    
    def create_backup(self, description: str = "") -> BackupInfo:
        """创建数据库备份"""
        try:
            self.logger.info("创建数据库备份...")
            
            # 解析数据库URL
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            # 生成备份ID和文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}_{hashlib.md5(description.encode()).hexdigest()[:8]}"
            backup_filename = f"{backup_id}.sql"
            backup_path = self.backup_dir / backup_filename
            
            # 构建pg_dump命令
            pg_dump_cmd = [
                "pg_dump",
                f"--host={parsed.hostname}",
                f"--port={parsed.port or 5432}",
                f"--username={parsed.username}",
                f"--dbname={parsed.path[1:]}",  # 去掉开头的 /
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges",
                f"--file={backup_path}"
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password
            
            # 执行备份
            self.logger.info(f"执行备份命令: {' '.join(pg_dump_cmd[:-1])} --file=...")
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump失败: {result.stderr}")
            
            # 获取备份文件大小
            backup_size = backup_path.stat().st_size
            
            # 获取当前迁移版本
            current_status = self.get_migration_status()
            
            # 创建备份信息
            backup_info = BackupInfo(
                backup_id=backup_id,
                backup_path=str(backup_path),
                database_name=parsed.path[1:],
                backup_size=backup_size,
                created_at=datetime.now(),
                migration_revision=current_status.current_revision
            )
            
            # 保存备份元数据
            metadata_path = self.backup_dir / f"{backup_id}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ 数据库备份完成: {backup_path} ({backup_size / 1024 / 1024:.2f} MB)")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"❌ 创建数据库备份失败: {e}")
            raise
    
    def restore_backup(self, backup_info: BackupInfo) -> bool:
        """恢复数据库备份"""
        try:
            self.logger.info(f"恢复数据库备份: {backup_info.backup_id}")
            
            backup_path = Path(backup_info.backup_path)
            if not backup_path.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            # 解析数据库URL
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            # 构建psql命令
            psql_cmd = [
                "psql",
                f"--host={parsed.hostname}",
                f"--port={parsed.port or 5432}",
                f"--username={parsed.username}",
                f"--dbname={parsed.path[1:]}",
                "--quiet",
                f"--file={backup_path}"
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password
            
            # 执行恢复
            self.logger.info(f"执行恢复命令: {' '.join(psql_cmd[:-1])} --file=...")
            result = subprocess.run(
                psql_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                raise Exception(f"psql恢复失败: {result.stderr}")
            
            self.logger.info("✅ 数据库备份恢复完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 恢复数据库备份失败: {e}")
            return False
    
    def run_migrations(self, target_revision: str = "head") -> bool:
        """执行数据库迁移"""
        try:
            self.logger.info(f"执行数据库迁移到版本: {target_revision}")
            
            # 获取当前状态
            current_status = self.get_migration_status()
            
            # 如果已经是最新版本，跳过
            if target_revision == "head" and current_status.is_up_to_date:
                self.logger.info("数据库已经是最新版本，跳过迁移")
                return True
            
            # 创建迁移前备份
            backup_info = self.create_backup(f"Migration backup before {target_revision}")
            
            try:
                # 执行迁移
                self.logger.info("开始执行迁移...")
                command.upgrade(self.alembic_cfg, target_revision)
                
                # 验证迁移结果
                new_status = self.get_migration_status()
                
                if target_revision == "head":
                    success = new_status.is_up_to_date
                else:
                    success = new_status.current_revision == target_revision
                
                if success:
                    self.logger.info("✅ 数据库迁移执行成功")
                    return True
                else:
                    raise Exception("迁移执行后状态验证失败")
                    
            except Exception as e:
                self.logger.error(f"迁移执行失败，尝试回滚: {e}")
                
                # 尝试恢复备份
                if self.restore_backup(backup_info):
                    self.logger.info("✅ 已回滚到迁移前状态")
                else:
                    self.logger.error("❌ 回滚失败，数据库可能处于不一致状态")
                
                raise
                
        except Exception as e:
            self.logger.error(f"❌ 执行数据库迁移失败: {e}")
            return False
    
    def rollback_migration(self, target_revision: str) -> bool:
        """回滚数据库迁移"""
        try:
            self.logger.info(f"回滚数据库迁移到版本: {target_revision}")
            
            # 创建回滚前备份
            backup_info = self.create_backup(f"Rollback backup before {target_revision}")
            
            try:
                # 执行回滚
                command.downgrade(self.alembic_cfg, target_revision)
                
                # 验证回滚结果
                new_status = self.get_migration_status()
                
                if new_status.current_revision == target_revision:
                    self.logger.info("✅ 数据库迁移回滚成功")
                    return True
                else:
                    raise Exception("回滚执行后状态验证失败")
                    
            except Exception as e:
                self.logger.error(f"回滚执行失败: {e}")
                raise
                
        except Exception as e:
            self.logger.error(f"❌ 回滚数据库迁移失败: {e}")
            return False
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """验证数据完整性"""
        try:
            self.logger.info("验证数据完整性...")
            
            engine = create_engine(self.database_url)
            inspector = inspect(engine)
            
            validation_results = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "checks": {
                    "tables": {},
                    "indexes": {},
                    "constraints": {},
                    "sequences": {}
                },
                "issues": [],
                "statistics": {}
            }
            
            # 检查表
            tables = inspector.get_table_names()
            validation_results["statistics"]["total_tables"] = len(tables)
            
            with engine.connect() as conn:
                for table_name in tables:
                    try:
                        # 检查表是否可访问
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = result.fetchone()[0]
                        
                        validation_results["checks"]["tables"][table_name] = {
                            "accessible": True,
                            "row_count": row_count
                        }
                        
                    except Exception as e:
                        validation_results["checks"]["tables"][table_name] = {
                            "accessible": False,
                            "error": str(e)
                        }
                        validation_results["issues"].append({
                            "type": "table_access_error",
                            "table": table_name,
                            "error": str(e)
                        })
                
                # 检查索引
                for table_name in tables:
                    try:
                        indexes = inspector.get_indexes(table_name)
                        validation_results["checks"]["indexes"][table_name] = {
                            "count": len(indexes),
                            "indexes": [idx["name"] for idx in indexes]
                        }
                    except Exception as e:
                        validation_results["issues"].append({
                            "type": "index_check_error",
                            "table": table_name,
                            "error": str(e)
                        })
                
                # 检查外键约束
                for table_name in tables:
                    try:
                        foreign_keys = inspector.get_foreign_keys(table_name)
                        validation_results["checks"]["constraints"][table_name] = {
                            "foreign_keys": len(foreign_keys)
                        }
                    except Exception as e:
                        validation_results["issues"].append({
                            "type": "constraint_check_error",
                            "table": table_name,
                            "error": str(e)
                        })
                
                # 检查序列
                try:
                    result = conn.execute(text("""
                        SELECT sequence_name 
                        FROM information_schema.sequences 
                        WHERE sequence_schema = 'public'
                    """))
                    sequences = [row[0] for row in result]
                    validation_results["checks"]["sequences"] = {
                        "count": len(sequences),
                        "sequences": sequences
                    }
                except Exception as e:
                    validation_results["issues"].append({
                        "type": "sequence_check_error",
                        "error": str(e)
                    })
            
            # 确定整体状态
            if validation_results["issues"]:
                validation_results["overall_status"] = "warning" if len(validation_results["issues"]) < 5 else "critical"
            
            self.logger.info(f"✅ 数据完整性验证完成: {validation_results['overall_status']}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"❌ 数据完整性验证失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    def get_backup_list(self) -> List[BackupInfo]:
        """获取备份列表"""
        try:
            backups = []
            
            for metadata_file in self.backup_dir.glob("backup_*.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    backup_info = BackupInfo(
                        backup_id=backup_data["backup_id"],
                        backup_path=backup_data["backup_path"],
                        database_name=backup_data["database_name"],
                        backup_size=backup_data["backup_size"],
                        created_at=datetime.fromisoformat(backup_data["created_at"]),
                        migration_revision=backup_data.get("migration_revision")
                    )
                    
                    # 检查备份文件是否存在
                    if Path(backup_info.backup_path).exists():
                        backups.append(backup_info)
                    
                except Exception as e:
                    self.logger.warning(f"读取备份元数据失败: {metadata_file} - {e}")
            
            # 按创建时间排序
            backups.sort(key=lambda x: x.created_at, reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"❌ 获取备份列表失败: {e}")
            return []
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """清理旧备份"""
        try:
            self.logger.info(f"清理旧备份，保留最新 {keep_count} 个...")
            
            backups = self.get_backup_list()
            
            if len(backups) <= keep_count:
                self.logger.info("备份数量未超过限制，无需清理")
                return 0
            
            # 删除多余的备份
            deleted_count = 0
            for backup in backups[keep_count:]:
                try:
                    # 删除备份文件
                    backup_path = Path(backup.backup_path)
                    if backup_path.exists():
                        backup_path.unlink()
                    
                    # 删除元数据文件
                    metadata_path = self.backup_dir / f"{backup.backup_id}.json"
                    if metadata_path.exists():
                        metadata_path.unlink()
                    
                    deleted_count += 1
                    self.logger.info(f"删除备份: {backup.backup_id}")
                    
                except Exception as e:
                    self.logger.warning(f"删除备份失败: {backup.backup_id} - {e}")
            
            self.logger.info(f"✅ 清理完成，删除了 {deleted_count} 个旧备份")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ 清理旧备份失败: {e}")
            return 0
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """生成迁移报告"""
        try:
            self.logger.info("生成迁移报告...")
            
            status = self.get_migration_status()
            history = self.get_migration_history()
            backups = self.get_backup_list()
            integrity = self.validate_data_integrity()
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "migration_status": status.to_dict(),
                "migration_history": [m.to_dict() for m in history],
                "backup_info": {
                    "total_backups": len(backups),
                    "latest_backup": backups[0].to_dict() if backups else None,
                    "total_backup_size": sum(b.backup_size for b in backups)
                },
                "data_integrity": integrity,
                "recommendations": []
            }
            
            # 生成建议
            if not status.is_up_to_date:
                report["recommendations"].append({
                    "type": "migration_needed",
                    "message": f"有 {len(status.pending_migrations)} 个待执行的迁移",
                    "action": "执行 run_migrations() 方法"
                })
            
            if len(backups) == 0:
                report["recommendations"].append({
                    "type": "no_backups",
                    "message": "没有找到数据库备份",
                    "action": "建议创建数据库备份"
                })
            elif len(backups) > 20:
                report["recommendations"].append({
                    "type": "too_many_backups",
                    "message": f"备份数量过多 ({len(backups)} 个)",
                    "action": "建议清理旧备份"
                })
            
            if integrity["overall_status"] != "healthy":
                report["recommendations"].append({
                    "type": "integrity_issues",
                    "message": f"数据完整性检查发现问题: {len(integrity.get('issues', []))} 个",
                    "action": "检查数据完整性验证结果"
                })
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ 生成迁移报告失败: {e}")
            return {"error": str(e)}
    
    def save_migration_report(self, filename: str = None) -> str:
        """保存迁移报告"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"migration_report_{timestamp}.json"
            
            report_path = self.backup_dir / filename
            report = self.generate_migration_report()
            
            # 自定义JSON编码器处理datetime对象
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super().default(obj)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            
            self.logger.info(f"✅ 迁移报告已保存到: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"❌ 保存迁移报告失败: {e}")
            return ""