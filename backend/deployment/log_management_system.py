"""
日志管理系统
实现结构化日志配置、日志收集聚合、轮转清理和搜索分析功能
"""
import os
import json
import yaml
import gzip
import shutil
import asyncio
import logging
import logging.handlers
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogFormat(Enum):
    """日志格式"""
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"

@dataclass
class LogConfig:
    """日志配置"""
    name: str
    level: LogLevel
    format: LogFormat
    file_path: str
    max_size: str = "100MB"
    backup_count: int = 10
    rotation_interval: str = "daily"
    compression: bool = True

@dataclass
class LogAggregationConfig:
    """日志聚合配置"""
    enabled: bool = True
    sources: List[str] = None
    destination: str = "/var/log/lawsker/aggregated"
    format: LogFormat = LogFormat.JSON
    filters: List[str] = None

class LogManagementSystem:
    """日志管理系统"""
    
    def __init__(self, base_log_dir: str = "/var/log/lawsker"):
        self.base_log_dir = Path(base_log_dir)
        self.logger = get_logger(__name__)
        self.config_dir = Path("monitoring/logs/config")
        self.scripts_dir = Path("scripts/logs")
        
    async def setup_log_management(self) -> Dict[str, Any]:
        """设置日志管理系统"""
        self.logger.info("Setting up log management system")
        
        setup_results = {
            "log_configs": [],
            "aggregation": {},
            "rotation": {},
            "search_tools": {},
            "monitoring": {},
            "status": "success",
            "errors": []
        }
        
        try:
            # 1. 创建目录结构
            await self._create_directories()
            
            # 2. 配置结构化日志
            log_configs_result = await self._configure_structured_logging()
            setup_results["log_configs"] = log_configs_result
            
            # 3. 设置日志聚合
            aggregation_result = await self._setup_log_aggregation()
            setup_results["aggregation"] = aggregation_result
            
            # 4. 配置日志轮转
            rotation_result = await self._configure_log_rotation()
            setup_results["rotation"] = rotation_result
            
            # 5. 创建搜索工具
            search_result = await self._create_search_tools()
            setup_results["search_tools"] = search_result
            
            # 6. 设置日志监控
            monitoring_result = await self._setup_log_monitoring()
            setup_results["monitoring"] = monitoring_result
            
            self.logger.info("Log management system setup completed")
            return setup_results
            
        except Exception as e:
            self.logger.error(f"Log management setup failed: {str(e)}")
            setup_results["status"] = "error"
            setup_results["errors"].append(str(e))
            return setup_results    

    async def _create_directories(self):
        """创建目录结构"""
        directories = [
            self.base_log_dir,
            self.base_log_dir / "application",
            self.base_log_dir / "system",
            self.base_log_dir / "security",
            self.base_log_dir / "access",
            self.base_log_dir / "error",
            self.base_log_dir / "aggregated",
            self.base_log_dir / "archived",
            self.config_dir,
            self.scripts_dir,
            Path("monitoring/logs/templates"),
            Path("monitoring/logs/dashboards")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # 设置适当的权限
            os.chmod(directory, 0o755)
    
    async def _configure_structured_logging(self) -> List[Dict[str, Any]]:
        """配置结构化日志"""
        self.logger.info("Configuring structured logging")
        
        # 定义日志配置
        log_configs = [
            LogConfig(
                name="application",
                level=LogLevel.INFO,
                format=LogFormat.JSON,
                file_path=str(self.base_log_dir / "application" / "app.log"),
                max_size="100MB",
                backup_count=10
            ),
            LogConfig(
                name="api",
                level=LogLevel.INFO,
                format=LogFormat.JSON,
                file_path=str(self.base_log_dir / "application" / "api.log"),
                max_size="200MB",
                backup_count=15
            ),
            LogConfig(
                name="database",
                level=LogLevel.WARNING,
                format=LogFormat.JSON,
                file_path=str(self.base_log_dir / "application" / "database.log"),
                max_size="50MB",
                backup_count=7
            ),
            LogConfig(
                name="security",
                level=LogLevel.INFO,
                format=LogFormat.JSON,
                file_path=str(self.base_log_dir / "security" / "security.log"),
                max_size="100MB",
                backup_count=30  # 保留更长时间的安全日志
            ),
            LogConfig(
                name="access",
                level=LogLevel.INFO,
                format=LogFormat.JSON,
                file_path=str(self.base_log_dir / "access" / "access.log"),
                max_size="500MB",
                backup_count=7
            ),
            LogConfig(
                name="error",
                level=LogLevel.ERROR,
                format=LogFormat.JSON,
                file_path=str(self.base_log_dir / "error" / "error.log"),
                max_size="100MB",
                backup_count=20
            )
        ]
        
        results = []
        
        for config in log_configs:
            try:
                result = await self._create_log_config(config)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to configure log {config.name}: {str(e)}")
                results.append({
                    "name": config.name,
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def _create_log_config(self, config: LogConfig) -> Dict[str, Any]:
        """创建日志配置"""
        try:
            # 创建日志目录
            log_file = Path(config.file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 生成Python logging配置
            logging_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    f"{config.name}_formatter": self._get_formatter_config(config.format)
                },
                "handlers": {
                    f"{config.name}_handler": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": config.file_path,
                        "maxBytes": self._parse_size(config.max_size),
                        "backupCount": config.backup_count,
                        "formatter": f"{config.name}_formatter",
                        "level": config.level.value
                    }
                },
                "loggers": {
                    config.name: {
                        "handlers": [f"{config.name}_handler"],
                        "level": config.level.value,
                        "propagate": False
                    }
                }
            }
            
            # 保存配置文件
            config_file = self.config_dir / f"{config.name}_logging.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(logging_config, f, indent=2)
            
            # 生成logrotate配置
            logrotate_config = await self._create_logrotate_config(config)
            
            return {
                "name": config.name,
                "status": "configured",
                "config_file": str(config_file),
                "log_file": config.file_path,
                "logrotate_config": logrotate_config,
                "message": f"Log configuration created for {config.name}"
            }
            
        except Exception as e:
            return {
                "name": config.name,
                "status": "error",
                "message": str(e)
            }
    
    def _get_formatter_config(self, format_type: LogFormat) -> Dict[str, Any]:
        """获取格式化器配置"""
        if format_type == LogFormat.JSON:
            return {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d"
            }
        elif format_type == LogFormat.STRUCTURED:
            return {
                "format": "[%(asctime)s] %(levelname)s in %(name)s [%(pathname)s:%(lineno)d]: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        else:  # TEXT
            return {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    async def _create_logrotate_config(self, config: LogConfig) -> str:
        """创建logrotate配置"""
        logrotate_content = f"""{config.file_path} {{
    {config.rotation_interval}
    rotate {config.backup_count}
    size {config.max_size}
    missingok
    notifempty
    create 644 www-data www-data
    {"compress" if config.compression else "nocompress"}
    {"delaycompress" if config.compression else ""}
    postrotate
        systemctl reload lawsker-backend || true
    endscript
}}
"""
        
        logrotate_file = Path(f"/etc/logrotate.d/lawsker-{config.name}")
        
        try:
            with open(logrotate_file, 'w') as f:
                f.write(logrotate_content)
            
            return str(logrotate_file)
            
        except Exception as e:
            self.logger.warning(f"Could not create logrotate config: {str(e)}")
            return f"Config content: {logrotate_content}"
    
    async def _setup_log_aggregation(self) -> Dict[str, Any]:
        """设置日志聚合"""
        self.logger.info("Setting up log aggregation")
        
        try:
            # 配置日志聚合
            aggregation_config = LogAggregationConfig(
                enabled=True,
                sources=[
                    str(self.base_log_dir / "application" / "*.log"),
                    str(self.base_log_dir / "security" / "*.log"),
                    str(self.base_log_dir / "access" / "*.log"),
                    str(self.base_log_dir / "error" / "*.log"),
                    "/var/log/nginx/*.log",
                    "/var/log/postgresql/*.log"
                ],
                destination=str(self.base_log_dir / "aggregated"),
                format=LogFormat.JSON,
                filters=["ERROR", "WARNING", "CRITICAL"]
            )
            
            # 创建聚合脚本
            aggregation_script = await self._create_aggregation_script(aggregation_config)
            
            # 创建Fluentd配置（如果使用）
            fluentd_config = await self._create_fluentd_config(aggregation_config)
            
            # 创建Logstash配置（如果使用）
            logstash_config = await self._create_logstash_config(aggregation_config)
            
            return {
                "status": "success",
                "config": {
                    "enabled": aggregation_config.enabled,
                    "sources_count": len(aggregation_config.sources),
                    "destination": aggregation_config.destination,
                    "format": aggregation_config.format.value
                },
                "scripts": {
                    "aggregation_script": aggregation_script,
                    "fluentd_config": fluentd_config,
                    "logstash_config": logstash_config
                },
                "message": "Log aggregation configured successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Log aggregation setup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_aggregation_script(self, config: LogAggregationConfig) -> str:
        """创建日志聚合脚本"""
        script_content = f"""#!/usr/bin/env python3
# Log Aggregation Script
# Generated automatically by LogManagementSystem

import json
import glob
import gzip
from datetime import datetime
from pathlib import Path

class LogAggregator:
    def __init__(self):
        self.sources = {config.sources}
        self.destination = Path("{config.destination}")
        self.destination.mkdir(parents=True, exist_ok=True)
    
    def aggregate_logs(self):
        aggregated_file = self.destination / f"aggregated_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.log"
        
        with open(aggregated_file, 'w') as output:
            for source_pattern in self.sources:
                for log_file in glob.glob(source_pattern):
                    try:
                        self.process_log_file(log_file, output)
                    except Exception as e:
                        print(f"Error processing {{log_file}}: {{e}}")
        
        # 压缩聚合文件
        with open(aggregated_file, 'rb') as f_in:
            with gzip.open(f"{{aggregated_file}}.gz", 'wb') as f_out:
                f_out.writelines(f_in)
        
        aggregated_file.unlink()  # 删除未压缩文件
        print(f"Log aggregation completed: {{aggregated_file}}.gz")
    
    def process_log_file(self, log_file, output):
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # 尝试解析JSON格式日志
                    log_entry = json.loads(line.strip())
                    log_entry['source_file'] = log_file
                    log_entry['aggregated_at'] = datetime.now().isoformat()
                    
                    output.write(json.dumps(log_entry) + '\\n')
                    
                except json.JSONDecodeError:
                    # 处理非JSON格式日志
                    structured_entry = {{
                        'timestamp': datetime.now().isoformat(),
                        'message': line.strip(),
                        'source_file': log_file,
                        'aggregated_at': datetime.now().isoformat()
                    }}
                    
                    output.write(json.dumps(structured_entry) + '\\n')

if __name__ == '__main__':
    aggregator = LogAggregator()
    aggregator.aggregate_logs()
"""
        
        script_file = self.scripts_dir / "log_aggregator.py"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _create_fluentd_config(self, config: LogAggregationConfig) -> str:
        """创建Fluentd配置"""
        fluentd_config = f"""# Fluentd Configuration for Lawsker Log Aggregation

<source>
  @type tail
  path {','.join(config.sources)}
  pos_file /var/log/fluentd/lawsker.log.pos
  tag lawsker.*
  format json
  time_format %Y-%m-%d %H:%M:%S
</source>

<filter lawsker.**>
  @type record_transformer
  <record>
    hostname ${{hostname}}
    aggregated_at ${{time}}
  </record>
</filter>

<match lawsker.**>
  @type file
  path {config.destination}/fluentd
  append true
  time_slice_format %Y%m%d_%H
  time_slice_wait 10m
  time_format %Y-%m-%dT%H:%M:%S%z
  buffer_type file
  buffer_path /var/log/fluentd/lawsker.buffer
  flush_interval 30s
  compress gzip
</match>
"""
        
        config_file = self.config_dir / "fluentd.conf"
        
        with open(config_file, 'w') as f:
            f.write(fluentd_config)
        
        return str(config_file)
    
    async def _create_logstash_config(self, config: LogAggregationConfig) -> str:
        """创建Logstash配置"""
        logstash_config = f"""# Logstash Configuration for Lawsker Log Aggregation

input {{
  file {{
    path => {json.dumps(config.sources)}
    start_position => "beginning"
    sincedb_path => "/var/lib/logstash/sincedb_lawsker"
    codec => "json"
    tags => ["lawsker"]
  }}
}}

filter {{
  if [tags] and "lawsker" in [tags] {{
    mutate {{
      add_field => {{ "aggregated_at" => "%{{@timestamp}}" }}
      add_field => {{ "hostname" => "%{{host}}" }}
    }}
    
    date {{
      match => [ "timestamp", "ISO8601" ]
    }}
  }}
}}

output {{
  file {{
    path => "{config.destination}/logstash-%{{+YYYY.MM.dd}}.log"
    codec => json_lines
  }}
  
  elasticsearch {{
    hosts => ["localhost:9200"]
    index => "lawsker-logs-%{{+YYYY.MM.dd}}"
  }}
}}
"""
        
        config_file = self.config_dir / "logstash.conf"
        
        with open(config_file, 'w') as f:
            f.write(logstash_config)
        
        return str(config_file)    
 
   async def _configure_log_rotation(self) -> Dict[str, Any]:
        """配置日志轮转"""
        self.logger.info("Configuring log rotation")
        
        try:
            # 创建主轮转脚本
            rotation_script = await self._create_rotation_script()
            
            # 创建清理脚本
            cleanup_script = await self._create_cleanup_script()
            
            # 创建压缩脚本
            compression_script = await self._create_compression_script()
            
            # 设置定时任务
            cron_config = await self._setup_rotation_cron()
            
            return {
                "status": "success",
                "scripts": {
                    "rotation_script": rotation_script,
                    "cleanup_script": cleanup_script,
                    "compression_script": compression_script
                },
                "cron_config": cron_config,
                "message": "Log rotation configured successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Log rotation configuration failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_rotation_script(self) -> str:
        """创建日志轮转脚本"""
        script_content = f"""#!/bin/bash
# Log Rotation Script for Lawsker
# Generated automatically by LogManagementSystem

LOG_BASE_DIR="{self.base_log_dir}"
ARCHIVE_DIR="$LOG_BASE_DIR/archived"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Starting log rotation at $(date)"

# 创建归档目录
mkdir -p "$ARCHIVE_DIR"

# 轮转应用日志
rotate_logs() {{
    local log_dir="$1"
    local retention_days="$2"
    
    if [ -d "$log_dir" ]; then
        echo "Rotating logs in $log_dir"
        
        # 查找需要轮转的日志文件
        find "$log_dir" -name "*.log" -size +100M -exec {{}} \\;
            echo "Rotating large log file: {{}}"
            mv {{}} "$ARCHIVE_DIR/$(basename {{}}).$TIMESTAMP"
            touch {{}}
            chmod 644 {{}}
        \\;
        
        # 删除旧的归档文件
        find "$ARCHIVE_DIR" -name "*.log.*" -mtime +$retention_days -delete
        
        echo "Log rotation completed for $log_dir"
    fi
}}

# 轮转不同类型的日志
rotate_logs "$LOG_BASE_DIR/application" 30
rotate_logs "$LOG_BASE_DIR/security" 90
rotate_logs "$LOG_BASE_DIR/access" 7
rotate_logs "$LOG_BASE_DIR/error" 60

# 压缩归档文件
find "$ARCHIVE_DIR" -name "*.log.*" -not -name "*.gz" -exec gzip {{}} \\;

# 重新加载服务
systemctl reload lawsker-backend 2>/dev/null || true
systemctl reload nginx 2>/dev/null || true

echo "Log rotation completed at $(date)"
"""
        
        script_file = self.scripts_dir / "rotate_logs.sh"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _create_cleanup_script(self) -> str:
        """创建日志清理脚本"""
        script_content = f"""#!/bin/bash
# Log Cleanup Script for Lawsker
# Generated automatically by LogManagementSystem

LOG_BASE_DIR="{self.base_log_dir}"
ARCHIVE_DIR="$LOG_BASE_DIR/archived"

echo "Starting log cleanup at $(date)"

# 清理函数
cleanup_logs() {{
    local log_type="$1"
    local retention_days="$2"
    local log_dir="$LOG_BASE_DIR/$log_type"
    
    if [ -d "$log_dir" ]; then
        echo "Cleaning up $log_type logs older than $retention_days days"
        
        # 删除旧的日志文件
        find "$log_dir" -name "*.log.*" -mtime +$retention_days -delete
        
        # 删除空目录
        find "$log_dir" -type d -empty -delete 2>/dev/null || true
        
        echo "Cleanup completed for $log_type logs"
    fi
}}

# 清理不同类型的日志
cleanup_logs "application" 30
cleanup_logs "access" 7
cleanup_logs "error" 60
cleanup_logs "security" 90

# 清理聚合日志
if [ -d "$LOG_BASE_DIR/aggregated" ]; then
    echo "Cleaning up aggregated logs older than 30 days"
    find "$LOG_BASE_DIR/aggregated" -name "*.log.gz" -mtime +30 -delete
fi

# 清理归档日志
if [ -d "$ARCHIVE_DIR" ]; then
    echo "Cleaning up archived logs older than 180 days"
    find "$ARCHIVE_DIR" -name "*.log.gz" -mtime +180 -delete
fi

# 清理临时文件
find "$LOG_BASE_DIR" -name "*.tmp" -mtime +1 -delete 2>/dev/null || true

# 报告磁盘使用情况
echo "Current disk usage for log directory:"
du -sh "$LOG_BASE_DIR"

echo "Log cleanup completed at $(date)"
"""
        
        script_file = self.scripts_dir / "cleanup_logs.sh"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _create_compression_script(self) -> str:
        """创建日志压缩脚本"""
        script_content = f"""#!/usr/bin/env python3
# Log Compression Script for Lawsker
# Generated automatically by LogManagementSystem

import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class LogCompressor:
    def __init__(self):
        self.base_dir = Path("{self.base_log_dir}")
        self.compression_age_days = 1  # 压缩1天前的日志
    
    def compress_old_logs(self):
        print(f"Starting log compression at {{datetime.now()}}")
        
        cutoff_time = datetime.now() - timedelta(days=self.compression_age_days)
        compressed_count = 0
        
        # 遍历所有日志目录
        for log_dir in self.base_dir.rglob("*.log"):
            if log_dir.is_file():
                # 检查文件修改时间
                file_mtime = datetime.fromtimestamp(log_dir.stat().st_mtime)
                
                if file_mtime < cutoff_time and not log_dir.name.endswith('.gz'):
                    try:
                        self.compress_file(log_dir)
                        compressed_count += 1
                        print(f"Compressed: {{log_dir}}")
                        
                    except Exception as e:
                        print(f"Error compressing {{log_dir}}: {{e}}")
        
        print(f"Compression completed. {{compressed_count}} files compressed.")
    
    def compress_file(self, file_path):
        compressed_path = Path(str(file_path) + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 保持原文件的权限和时间戳
        stat_info = file_path.stat()
        os.chmod(compressed_path, stat_info.st_mode)
        os.utime(compressed_path, (stat_info.st_atime, stat_info.st_mtime))
        
        # 删除原文件
        file_path.unlink()

if __name__ == '__main__':
    compressor = LogCompressor()
    compressor.compress_old_logs()
"""
        
        script_file = self.scripts_dir / "compress_logs.py"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _setup_rotation_cron(self) -> Dict[str, Any]:
        """设置日志轮转定时任务"""
        try:
            cron_entries = [
                {
                    "schedule": "0 2 * * *",  # 每天凌晨2点
                    "command": f"{self.scripts_dir}/rotate_logs.sh",
                    "description": "Daily log rotation"
                },
                {
                    "schedule": "0 3 * * 0",  # 每周日凌晨3点
                    "command": f"{self.scripts_dir}/cleanup_logs.sh",
                    "description": "Weekly log cleanup"
                },
                {
                    "schedule": "0 1 * * *",  # 每天凌晨1点
                    "command": f"python3 {self.scripts_dir}/compress_logs.py",
                    "description": "Daily log compression"
                }
            ]
            
            # 生成crontab内容
            crontab_content = "# Lawsker Log Management Cron Jobs\\n"
            for entry in cron_entries:
                crontab_content += f"{entry['schedule']} {entry['command']} >> /var/log/lawsker/cron.log 2>&1\\n"
            
            return {
                "status": "configured",
                "entries": cron_entries,
                "crontab_content": crontab_content,
                "message": "Add these entries to crontab manually: crontab -e"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_search_tools(self) -> Dict[str, Any]:
        """创建日志搜索工具"""
        self.logger.info("Creating log search tools")
        
        try:
            # 创建日志搜索脚本
            search_script = await self._create_search_script()
            
            # 创建日志分析脚本
            analysis_script = await self._create_analysis_script()
            
            # 创建实时监控脚本
            monitor_script = await self._create_monitor_script()
            
            # 创建Web搜索界面配置
            web_interface_config = await self._create_web_interface_config()
            
            return {
                "status": "success",
                "tools": {
                    "search_script": search_script,
                    "analysis_script": analysis_script,
                    "monitor_script": monitor_script,
                    "web_interface_config": web_interface_config
                },
                "message": "Log search tools created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Search tools creation failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_search_script(self) -> str:
        """创建日志搜索脚本"""
        script_content = f"""#!/usr/bin/env python3
# Log Search Tool for Lawsker
# Generated automatically by LogManagementSystem

import json
import gzip
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import re

class LogSearcher:
    def __init__(self, base_dir="{self.base_log_dir}"):
        self.base_dir = Path(base_dir)
    
    def search(self, query, log_type=None, start_time=None, end_time=None, 
               case_sensitive=False, regex=False, max_results=100):
        results = []
        
        # 确定搜索目录
        if log_type:
            search_dirs = [self.base_dir / log_type]
        else:
            search_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            # 搜索日志文件
            for log_file in search_dir.rglob("*.log*"):
                try:
                    matches = self.search_file(
                        log_file, query, start_time, end_time,
                        case_sensitive, regex, max_results - len(results)
                    )
                    results.extend(matches)
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    print(f"Error searching {{log_file}}: {{e}}")
            
            if len(results) >= max_results:
                break
        
        return results[:max_results]
    
    def search_file(self, file_path, query, start_time, end_time,
                   case_sensitive, regex, max_results):
        matches = []
        
        # 确定文件打开方式
        if file_path.suffix == '.gz':
            open_func = gzip.open
            mode = 'rt'
        else:
            open_func = open
            mode = 'r'
        
        try:
            with open_func(file_path, mode, encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # 尝试解析JSON格式
                        log_entry = json.loads(line.strip())
                        timestamp_str = log_entry.get('timestamp', log_entry.get('asctime', ''))
                        message = log_entry.get('message', str(log_entry))
                        
                    except json.JSONDecodeError:
                        # 处理纯文本格式
                        log_entry = {{'raw_line': line.strip()}}
                        timestamp_str = ''
                        message = line.strip()
                    
                    # 时间过滤
                    if start_time or end_time:
                        if not self.time_in_range(timestamp_str, start_time, end_time):
                            continue
                    
                    # 内容匹配
                    if self.match_content(message, query, case_sensitive, regex):
                        matches.append({{
                            'file': str(file_path),
                            'line_number': line_num,
                            'timestamp': timestamp_str,
                            'content': message,
                            'full_entry': log_entry
                        }})
                        
                        if len(matches) >= max_results:
                            break
                            
        except Exception as e:
            print(f"Error reading file {{file_path}}: {{e}}")
        
        return matches
    
    def time_in_range(self, timestamp_str, start_time, end_time):
        if not timestamp_str:
            return True
        
        try:
            # 尝试多种时间格式
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    log_time = datetime.strptime(timestamp_str[:19], fmt)
                    break
                except ValueError:
                    continue
            else:
                return True  # 无法解析时间，包含在结果中
            
            if start_time and log_time < start_time:
                return False
            if end_time and log_time > end_time:
                return False
            
            return True
            
        except Exception:
            return True
    
    def match_content(self, content, query, case_sensitive, regex):
        if not case_sensitive:
            content = content.lower()
            query = query.lower()
        
        if regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(query, content, flags))
            except re.error:
                return False
        else:
            return query in content

def main():
    parser = argparse.ArgumentParser(description='Search Lawsker logs')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--type', help='Log type (application, security, etc.)')
    parser.add_argument('--start', help='Start time (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end', help='End time (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    parser.add_argument('--regex', action='store_true', help='Use regex for search')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum results')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # 解析时间参数
    start_time = None
    end_time = None
    
    if args.start:
        start_time = datetime.strptime(args.start, '%Y-%m-%d %H:%M:%S')
    if args.end:
        end_time = datetime.strptime(args.end, '%Y-%m-%d %H:%M:%S')
    
    # 执行搜索
    searcher = LogSearcher()
    results = searcher.search(
        args.query, args.type, start_time, end_time,
        args.case_sensitive, args.regex, args.max_results
    )
    
    # 输出结果
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"Found {{len(results)}} matches:")
        for result in results:
            print(f"{{result['file']}}:{{result['line_number']}} [{{result['timestamp']}}] {{result['content']}}")

if __name__ == '__main__':
    main()
"""
        
        script_file = self.scripts_dir / "search_logs.py"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file) 
   
    async def _create_analysis_script(self) -> str:
        """创建日志分析脚本"""
        script_content = f"""#!/usr/bin/env python3
# Log Analysis Tool for Lawsker
# Generated automatically by LogManagementSystem

import json
import gzip
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

class LogAnalyzer:
    def __init__(self, base_dir="{self.base_log_dir}"):
        self.base_dir = Path(base_dir)
    
    def analyze(self, log_type=None, start_time=None, end_time=None, analysis_type="summary"):
        if analysis_type == "summary":
            return self.generate_summary(log_type, start_time, end_time)
        elif analysis_type == "errors":
            return self.analyze_errors(log_type, start_time, end_time)
        elif analysis_type == "performance":
            return self.analyze_performance(log_type, start_time, end_time)
        elif analysis_type == "security":
            return self.analyze_security(log_type, start_time, end_time)
        else:
            return {{"error": "Unknown analysis type"}}
    
    def generate_summary(self, log_type, start_time, end_time):
        stats = {{
            "total_entries": 0,
            "log_levels": Counter(),
            "services": Counter(),
            "time_range": {{"start": None, "end": None}},
            "files_processed": 0
        }}
        
        for log_file in self.get_log_files(log_type):
            stats["files_processed"] += 1
            
            for entry in self.read_log_entries(log_file, start_time, end_time):
                stats["total_entries"] += 1
                
                # 统计日志级别
                level = entry.get("levelname", entry.get("level", "UNKNOWN"))
                stats["log_levels"][level] += 1
                
                # 统计服务
                service = entry.get("name", entry.get("service", "unknown"))
                stats["services"][service] += 1
                
                # 更新时间范围
                timestamp = entry.get("timestamp", entry.get("asctime"))
                if timestamp:
                    if not stats["time_range"]["start"] or timestamp < stats["time_range"]["start"]:
                        stats["time_range"]["start"] = timestamp
                    if not stats["time_range"]["end"] or timestamp > stats["time_range"]["end"]:
                        stats["time_range"]["end"] = timestamp
        
        return stats
    
    def analyze_errors(self, log_type, start_time, end_time):
        errors = {{
            "error_count": 0,
            "error_types": Counter(),
            "error_messages": Counter(),
            "error_timeline": defaultdict(int),
            "top_errors": []
        }}
        
        for log_file in self.get_log_files(log_type):
            for entry in self.read_log_entries(log_file, start_time, end_time):
                level = entry.get("levelname", entry.get("level", "")).upper()
                
                if level in ["ERROR", "CRITICAL", "FATAL"]:
                    errors["error_count"] += 1
                    
                    # 错误类型统计
                    error_type = entry.get("exc_info", entry.get("exception", "Unknown"))
                    errors["error_types"][str(error_type)[:100]] += 1
                    
                    # 错误消息统计
                    message = entry.get("message", "")[:200]
                    errors["error_messages"][message] += 1
                    
                    # 时间线统计
                    timestamp = entry.get("timestamp", entry.get("asctime", ""))
                    if timestamp:
                        hour = timestamp[:13]  # YYYY-MM-DD HH
                        errors["error_timeline"][hour] += 1
        
        # 获取最常见的错误
        errors["top_errors"] = errors["error_messages"].most_common(10)
        
        return errors
    
    def analyze_performance(self, log_type, start_time, end_time):
        performance = {{
            "response_times": [],
            "request_counts": Counter(),
            "slow_requests": [],
            "avg_response_time": 0,
            "p95_response_time": 0,
            "p99_response_time": 0
        }}
        
        for log_file in self.get_log_files(log_type):
            for entry in self.read_log_entries(log_file, start_time, end_time):
                # 查找响应时间信息
                response_time = None
                
                # 尝试多种响应时间字段
                for field in ["response_time", "duration", "elapsed", "time_taken"]:
                    if field in entry:
                        try:
                            response_time = float(entry[field])
                            break
                        except (ValueError, TypeError):
                            continue
                
                if response_time is not None:
                    performance["response_times"].append(response_time)
                    
                    # 记录慢请求（>3秒）
                    if response_time > 3.0:
                        performance["slow_requests"].append({{
                            "timestamp": entry.get("timestamp", ""),
                            "response_time": response_time,
                            "request": entry.get("request", entry.get("message", ""))[:100]
                        }})
                
                # 统计请求类型
                method = entry.get("method", entry.get("request_method", ""))
                path = entry.get("path", entry.get("request_path", ""))
                if method and path:
                    performance["request_counts"][f"{{method}} {{path}}"[:100]] += 1
        
        # 计算统计值
        if performance["response_times"]:
            performance["avg_response_time"] = statistics.mean(performance["response_times"])
            performance["p95_response_time"] = statistics.quantiles(performance["response_times"], n=20)[18]  # 95th percentile
            performance["p99_response_time"] = statistics.quantiles(performance["response_times"], n=100)[98]  # 99th percentile
        
        return performance
    
    def analyze_security(self, log_type, start_time, end_time):
        security = {{
            "failed_logins": 0,
            "suspicious_ips": Counter(),
            "blocked_requests": 0,
            "security_events": [],
            "attack_patterns": Counter()
        }}
        
        for log_file in self.get_log_files(log_type):
            for entry in self.read_log_entries(log_file, start_time, end_time):
                message = entry.get("message", "").lower()
                
                # 检测失败登录
                if any(pattern in message for pattern in ["login failed", "authentication failed", "invalid credentials"]):
                    security["failed_logins"] += 1
                    
                    # 提取IP地址
                    ip = entry.get("remote_addr", entry.get("client_ip", ""))
                    if ip:
                        security["suspicious_ips"][ip] += 1
                
                # 检测被阻止的请求
                if any(pattern in message for pattern in ["blocked", "denied", "forbidden"]):
                    security["blocked_requests"] += 1
                
                # 检测攻击模式
                attack_patterns = [
                    "sql injection", "xss", "csrf", "brute force",
                    "directory traversal", "file inclusion", "command injection"
                ]
                
                for pattern in attack_patterns:
                    if pattern in message:
                        security["attack_patterns"][pattern] += 1
                        security["security_events"].append({{
                            "timestamp": entry.get("timestamp", ""),
                            "type": pattern,
                            "message": message[:200],
                            "ip": entry.get("remote_addr", "")
                        }})
        
        return security
    
    def get_log_files(self, log_type):
        if log_type:
            search_dirs = [self.base_dir / log_type]
        else:
            search_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        
        log_files = []
        for search_dir in search_dirs:
            if search_dir.exists():
                log_files.extend(search_dir.rglob("*.log*"))
        
        return log_files
    
    def read_log_entries(self, file_path, start_time, end_time):
        # 确定文件打开方式
        if file_path.suffix == '.gz':
            open_func = gzip.open
            mode = 'rt'
        else:
            open_func = open
            mode = 'r'
        
        try:
            with open_func(file_path, mode, encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        # 处理非JSON格式
                        entry = {{"message": line.strip()}}
                    
                    # 时间过滤
                    if start_time or end_time:
                        timestamp_str = entry.get("timestamp", entry.get("asctime", ""))
                        if timestamp_str and not self.time_in_range(timestamp_str, start_time, end_time):
                            continue
                    
                    yield entry
                    
        except Exception as e:
            print(f"Error reading {{file_path}}: {{e}}")
    
    def time_in_range(self, timestamp_str, start_time, end_time):
        try:
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    log_time = datetime.strptime(timestamp_str[:19], fmt)
                    break
                except ValueError:
                    continue
            else:
                return True
            
            if start_time and log_time < start_time:
                return False
            if end_time and log_time > end_time:
                return False
            
            return True
            
        except Exception:
            return True

def main():
    parser = argparse.ArgumentParser(description='Analyze Lawsker logs')
    parser.add_argument('--type', help='Log type to analyze')
    parser.add_argument('--start', help='Start time (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end', help='End time (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--analysis', choices=['summary', 'errors', 'performance', 'security'],
                       default='summary', help='Type of analysis')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # 解析时间参数
    start_time = None
    end_time = None
    
    if args.start:
        start_time = datetime.strptime(args.start, '%Y-%m-%d %H:%M:%S')
    if args.end:
        end_time = datetime.strptime(args.end, '%Y-%m-%d %H:%M:%S')
    
    # 执行分析
    analyzer = LogAnalyzer()
    results = analyzer.analyze(args.type, start_time, end_time, args.analysis)
    
    # 输出结果
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"Log Analysis Results ({{args.analysis}}):")
        print("=" * 50)
        
        if args.analysis == "summary":
            print(f"Total entries: {{results['total_entries']}}")
            print(f"Files processed: {{results['files_processed']}}")
            print(f"Log levels: {{dict(results['log_levels'])}}")
            print(f"Services: {{dict(results['services'])}}")
            
        elif args.analysis == "errors":
            print(f"Total errors: {{results['error_count']}}")
            print(f"Top error messages:")
            for msg, count in results['top_errors']:
                print(f"  {{count}}: {{msg}}")
                
        elif args.analysis == "performance":
            print(f"Average response time: {{results['avg_response_time']:.3f}}s")
            print(f"95th percentile: {{results['p95_response_time']:.3f}}s")
            print(f"99th percentile: {{results['p99_response_time']:.3f}}s")
            print(f"Slow requests (>3s): {{len(results['slow_requests'])}}")
            
        elif args.analysis == "security":
            print(f"Failed logins: {{results['failed_logins']}}")
            print(f"Blocked requests: {{results['blocked_requests']}}")
            print(f"Security events: {{len(results['security_events'])}}")
            print(f"Top suspicious IPs: {{dict(results['suspicious_ips'].most_common(5))}}")

if __name__ == '__main__':
    main()
"""
        
        script_file = self.scripts_dir / "analyze_logs.py"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _create_monitor_script(self) -> str:
        """创建实时日志监控脚本"""
        script_content = f"""#!/usr/bin/env python3
# Real-time Log Monitor for Lawsker
# Generated automatically by LogManagementSystem

import time
import json
import argparse
from pathlib import Path
from datetime import datetime
import select
import sys

class LogMonitor:
    def __init__(self, base_dir="{self.base_log_dir}"):
        self.base_dir = Path(base_dir)
        self.file_positions = {{}}
    
    def monitor(self, log_type=None, filters=None, follow=True):
        log_files = self.get_log_files(log_type)
        
        if not log_files:
            print("No log files found to monitor")
            return
        
        print(f"Monitoring {{len(log_files)}} log files...")
        for log_file in log_files:
            print(f"  - {{log_file}}")
        
        # 初始化文件位置
        for log_file in log_files:
            if log_file.exists():
                self.file_positions[log_file] = log_file.stat().st_size
        
        try:
            while follow:
                self.check_files(log_files, filters)
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\\nMonitoring stopped")
    
    def check_files(self, log_files, filters):
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            current_size = log_file.stat().st_size
            last_position = self.file_positions.get(log_file, 0)
            
            if current_size > last_position:
                self.read_new_content(log_file, last_position, filters)
                self.file_positions[log_file] = current_size
            elif current_size < last_position:
                # 文件被轮转或截断
                self.file_positions[log_file] = 0
                self.read_new_content(log_file, 0, filters)
    
    def read_new_content(self, log_file, start_position, filters):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(start_position)
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        formatted_line = self.format_entry(entry, log_file)
                    except json.JSONDecodeError:
                        formatted_line = f"[{{datetime.now().strftime('%H:%M:%S')}}] [{{log_file.name}}] {{line}}"
                    
                    if self.should_display(formatted_line, filters):
                        print(formatted_line)
                        
        except Exception as e:
            print(f"Error reading {{log_file}}: {{e}}")
    
    def format_entry(self, entry, log_file):
        timestamp = entry.get("timestamp", entry.get("asctime", datetime.now().isoformat()))
        level = entry.get("levelname", entry.get("level", "INFO"))
        message = entry.get("message", str(entry))
        
        # 颜色编码
        color_codes = {{
            "DEBUG": "\\033[36m",    # 青色
            "INFO": "\\033[32m",     # 绿色
            "WARNING": "\\033[33m",  # 黄色
            "ERROR": "\\033[31m",    # 红色
            "CRITICAL": "\\033[35m"  # 紫色
        }}
        
        reset_code = "\\033[0m"
        color = color_codes.get(level.upper(), "")
        
        return f"{{color}}[{{timestamp[:19]}}] [{{log_file.name}}] [{{level}}] {{message}}{{reset_code}}"
    
    def should_display(self, line, filters):
        if not filters:
            return True
        
        line_lower = line.lower()
        
        for filter_term in filters:
            if filter_term.lower() in line_lower:
                return True
        
        return False
    
    def get_log_files(self, log_type):
        if log_type:
            search_dirs = [self.base_dir / log_type]
        else:
            search_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        
        log_files = []
        for search_dir in search_dirs:
            if search_dir.exists():
                # 只监控当前的日志文件，不包括轮转的文件
                for log_file in search_dir.glob("*.log"):
                    if not any(suffix in log_file.name for suffix in ['.1', '.2', '.gz']):
                        log_files.append(log_file)
        
        return log_files

def main():
    parser = argparse.ArgumentParser(description='Monitor Lawsker logs in real-time')
    parser.add_argument('--type', help='Log type to monitor')
    parser.add_argument('--filter', nargs='+', help='Filter terms to highlight')
    parser.add_argument('--no-follow', action='store_true', help='Don\\'t follow log files')
    
    args = parser.parse_args()
    
    monitor = LogMonitor()
    monitor.monitor(args.type, args.filter, not args.no_follow)

if __name__ == '__main__':
    main()
"""
        
        script_file = self.scripts_dir / "monitor_logs.py"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _create_web_interface_config(self) -> str:
        """创建Web搜索界面配置"""
        config = {
            "interface": {
                "title": "Lawsker Log Search",
                "description": "Search and analyze Lawsker system logs",
                "features": [
                    "Real-time log search",
                    "Advanced filtering",
                    "Log analysis and statistics",
                    "Export search results"
                ]
            },
            "elasticsearch": {
                "enabled": False,
                "host": "localhost",
                "port": 9200,
                "index_pattern": "lawsker-logs-*"
            },
            "kibana": {
                "enabled": False,
                "host": "localhost",
                "port": 5601,
                "dashboards": [
                    "lawsker-overview",
                    "lawsker-errors",
                    "lawsker-performance",
                    "lawsker-security"
                ]
            },
            "grafana_loki": {
                "enabled": False,
                "loki_url": "http://localhost:3100",
                "grafana_url": "http://localhost:3000"
            }
        }
        
        config_file = self.config_dir / "web_interface.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        return str(config_file)
    
    async def _setup_log_monitoring(self) -> Dict[str, Any]:
        """设置日志监控"""
        self.logger.info("Setting up log monitoring")
        
        try:
            # 创建日志监控配置
            monitoring_config = {
                "enabled": True,
                "metrics": {
                    "log_volume": True,
                    "error_rate": True,
                    "response_time": True,
                    "disk_usage": True
                },
                "alerts": {
                    "high_error_rate": {
                        "threshold": 0.1,
                        "window": "5m"
                    },
                    "disk_space_low": {
                        "threshold": 0.9,
                        "window": "1m"
                    },
                    "log_volume_spike": {
                        "threshold": 1000,
                        "window": "1m"
                    }
                }
            }
            
            # 保存监控配置
            config_file = self.config_dir / "monitoring.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(monitoring_config, f, indent=2)
            
            # 创建监控脚本
            monitoring_script = await self._create_monitoring_script()
            
            return {
                "status": "success",
                "config_file": str(config_file),
                "monitoring_script": monitoring_script,
                "metrics_enabled": list(monitoring_config["metrics"].keys()),
                "alerts_configured": len(monitoring_config["alerts"]),
                "message": "Log monitoring configured successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Log monitoring setup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_monitoring_script(self) -> str:
        """创建日志监控脚本"""
        script_content = f"""#!/usr/bin/env python3
# Log Monitoring Script for Lawsker
# Generated automatically by LogManagementSystem

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque

class LogMonitoringService:
    def __init__(self):
        self.base_dir = Path("{self.base_log_dir}")
        self.metrics = {{
            "log_volume": deque(maxlen=300),  # 5分钟的数据
            "error_count": deque(maxlen=300),
            "response_times": deque(maxlen=1000),
            "disk_usage": deque(maxlen=60)  # 1小时的数据
        }}
        
    def collect_metrics(self):
        while True:
            try:
                timestamp = datetime.now()
                
                # 收集日志量指标
                log_volume = self.get_log_volume()
                self.metrics["log_volume"].append((timestamp, log_volume))
                
                # 收集错误率指标
                error_count = self.get_error_count()
                self.metrics["error_count"].append((timestamp, error_count))
                
                # 收集磁盘使用率
                disk_usage = self.get_disk_usage()
                self.metrics["disk_usage"].append((timestamp, disk_usage))
                
                # 检查告警条件
                self.check_alerts()
                
                # 输出指标到Prometheus格式
                self.export_prometheus_metrics()
                
                time.sleep(60)  # 每分钟收集一次
                
            except Exception as e:
                print(f"Error collecting metrics: {{e}}")
                time.sleep(60)
    
    def get_log_volume(self):
        total_size = 0
        
        for log_file in self.base_dir.rglob("*.log"):
            if log_file.exists():
                total_size += log_file.stat().st_size
        
        return total_size
    
    def get_error_count(self):
        error_count = 0
        cutoff_time = datetime.now() - timedelta(minutes=1)
        
        for log_file in self.base_dir.rglob("*.log"):
            if not log_file.exists():
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # 只读取最后几KB的内容
                    f.seek(max(0, log_file.stat().st_size - 10240))
                    
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            level = entry.get("levelname", "").upper()
                            
                            if level in ["ERROR", "CRITICAL"]:
                                timestamp_str = entry.get("timestamp", "")
                                if timestamp_str:
                                    log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                    if log_time > cutoff_time:
                                        error_count += 1
                                        
                        except (json.JSONDecodeError, ValueError):
                            continue
                            
            except Exception:
                continue
        
        return error_count
    
    def get_disk_usage(self):
        import shutil
        
        try:
            total, used, free = shutil.disk_usage(self.base_dir)
            return used / total
        except Exception:
            return 0
    
    def check_alerts(self):
        # 检查错误率告警
        if len(self.metrics["error_count"]) >= 5:
            recent_errors = [count for _, count in list(self.metrics["error_count"])[-5:]]
            avg_error_rate = sum(recent_errors) / len(recent_errors)
            
            if avg_error_rate > 10:  # 每分钟超过10个错误
                self.send_alert("high_error_rate", f"High error rate: {{avg_error_rate}} errors/min")
        
        # 检查磁盘使用率告警
        if self.metrics["disk_usage"]:
            current_usage = self.metrics["disk_usage"][-1][1]
            if current_usage > 0.9:
                self.send_alert("disk_space_low", f"Disk usage: {{current_usage:.1%}}")
        
        # 检查日志量激增
        if len(self.metrics["log_volume"]) >= 2:
            current_volume = self.metrics["log_volume"][-1][1]
            previous_volume = self.metrics["log_volume"][-2][1]
            
            if current_volume > previous_volume * 2:  # 日志量翻倍
                self.send_alert("log_volume_spike", f"Log volume spike: {{current_volume}} bytes")
    
    def send_alert(self, alert_type, message):
        alert_data = {{
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
            "severity": "warning"
        }}
        
        # 写入告警日志
        alert_file = self.base_dir / "alerts.log"
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert_data) + '\\n')
        
        print(f"ALERT [{{alert_type}}]: {{message}}")
    
    def export_prometheus_metrics(self):
        metrics_file = Path("/tmp/lawsker_log_metrics.prom")
        
        with open(metrics_file, 'w') as f:
            # 日志量指标
            if self.metrics["log_volume"]:
                current_volume = self.metrics["log_volume"][-1][1]
                f.write(f"lawsker_log_volume_bytes {{current_volume}}\\n")
            
            # 错误计数指标
            if self.metrics["error_count"]:
                current_errors = self.metrics["error_count"][-1][1]
                f.write(f"lawsker_log_errors_total {{current_errors}}\\n")
            
            # 磁盘使用率指标
            if self.metrics["disk_usage"]:
                current_usage = self.metrics["disk_usage"][-1][1]
                f.write(f"lawsker_log_disk_usage_ratio {{current_usage}}\\n")

if __name__ == '__main__':
    monitor = LogMonitoringService()
    monitor.collect_metrics()
"""
        
        script_file = self.scripts_dir / "log_monitoring.py"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def get_log_management_status(self) -> Dict[str, Any]:
        """获取日志管理系统状态"""
        try:
            # 统计日志文件
            log_files_count = 0
            total_log_size = 0
            
            for log_file in self.base_log_dir.rglob("*.log*"):
                if log_file.is_file():
                    log_files_count += 1
                    total_log_size += log_file.stat().st_size
            
            # 检查脚本文件
            scripts = {
                "search": self.scripts_dir / "search_logs.py",
                "analyze": self.scripts_dir / "analyze_logs.py",
                "monitor": self.scripts_dir / "monitor_logs.py",
                "rotate": self.scripts_dir / "rotate_logs.sh",
                "cleanup": self.scripts_dir / "cleanup_logs.sh",
                "compress": self.scripts_dir / "compress_logs.py"
            }
            
            scripts_status = {}
            for name, script_path in scripts.items():
                scripts_status[name] = {
                    "exists": script_path.exists(),
                    "executable": script_path.exists() and os.access(script_path, os.X_OK),
                    "path": str(script_path)
                }
            
            return {
                "status": "success",
                "statistics": {
                    "log_files_count": log_files_count,
                    "total_log_size_mb": round(total_log_size / (1024 * 1024), 2),
                    "base_directory": str(self.base_log_dir),
                    "config_directory": str(self.config_dir),
                    "scripts_directory": str(self.scripts_dir)
                },
                "scripts": scripts_status,
                "directories": {
                    "application": (self.base_log_dir / "application").exists(),
                    "security": (self.base_log_dir / "security").exists(),
                    "access": (self.base_log_dir / "access").exists(),
                    "error": (self.base_log_dir / "error").exists(),
                    "aggregated": (self.base_log_dir / "aggregated").exists(),
                    "archived": (self.base_log_dir / "archived").exists()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get log management status: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }