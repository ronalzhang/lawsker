#!/usr/bin/env python3
"""
静态文件部署管理器 - 负责构建产物复制、Nginx配置生成和部署验证
"""

import os
import shutil
import subprocess
import logging
import requests
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import stat
import pwd
import grp


@dataclass
class StaticDeployment:
    """静态文件部署配置"""
    name: str
    source_path: str
    target_path: str
    nginx_config_path: str
    domain: str
    port: int = 80
    ssl_port: int = 443
    ssl_enabled: bool = True
    backup_enabled: bool = True
    owner: str = "www-data"
    group: str = "www-data"
    permissions: str = "755"


@dataclass
class DeploymentResult:
    """部署结果"""
    success: bool
    message: str
    deployment_time: str
    files_copied: int
    backup_path: Optional[str] = None
    nginx_config_generated: bool = False
    verification_passed: bool = False
    errors: List[str] = None


class StaticDeploymentManager:
    """静态文件部署管理器"""
    
    def __init__(self, base_path: str = "/opt/lawsker"):
        self.base_path = Path(base_path)
        self.logger = self._setup_logger()
        self.nginx_config_dir = Path("/etc/nginx/sites-available")
        self.nginx_enabled_dir = Path("/etc/nginx/sites-enabled")
        self.backup_dir = Path("/opt/lawsker/backups/static")
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def deploy_static_files(self, deployment: StaticDeployment) -> DeploymentResult:
        """部署静态文件"""
        self.logger.info(f"开始部署静态文件: {deployment.name}")
        
        start_time = datetime.now()
        result = DeploymentResult(
            success=False,
            message="",
            deployment_time=start_time.isoformat(),
            files_copied=0,
            errors=[]
        )
        
        try:
            # 步骤1: 验证源路径
            source_path = self.base_path / deployment.source_path
            if not source_path.exists():
                result.errors.append(f"源路径不存在: {source_path}")
                result.message = "源路径验证失败"
                return result
            
            # 步骤2: 创建备份
            if deployment.backup_enabled:
                backup_path = self._create_backup(deployment)
                if backup_path:
                    result.backup_path = str(backup_path)
                    self.logger.info(f"创建备份: {backup_path}")
            
            # 步骤3: 复制文件
            files_copied = self._copy_files(source_path, Path(deployment.target_path))
            result.files_copied = files_copied
            
            if files_copied == 0:
                result.errors.append("没有文件被复制")
                result.message = "文件复制失败"
                return result
            
            # 步骤4: 设置文件权限
            if self._set_file_permissions(Path(deployment.target_path), deployment):
                self.logger.info("文件权限设置成功")
            else:
                result.errors.append("文件权限设置失败")
            
            # 步骤5: 生成Nginx配置
            if self._generate_nginx_config(deployment):
                result.nginx_config_generated = True
                self.logger.info("Nginx配置生成成功")
            else:
                result.errors.append("Nginx配置生成失败")
            
            # 步骤6: 重载Nginx
            if self._reload_nginx():
                self.logger.info("Nginx重载成功")
            else:
                result.errors.append("Nginx重载失败")
            
            # 步骤7: 验证部署
            if self._verify_deployment(deployment):
                result.verification_passed = True
                self.logger.info("部署验证成功")
            else:
                result.errors.append("部署验证失败")
            
            # 判断整体成功状态
            result.success = (
                result.files_copied > 0 and
                result.nginx_config_generated and
                len(result.errors) == 0
            )
            
            if result.success:
                result.message = f"部署成功，复制了 {files_copied} 个文件"
            else:
                result.message = f"部署部分成功，存在 {len(result.errors)} 个问题"
            
        except Exception as e:
            result.errors.append(f"部署异常: {str(e)}")
            result.message = "部署过程中发生异常"
            self.logger.error(f"部署异常: {e}")
        
        return result
    
    def _create_backup(self, deployment: StaticDeployment) -> Optional[Path]:
        """创建部署备份"""
        try:
            target_path = Path(deployment.target_path)
            if not target_path.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{deployment.name}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # 复制现有文件到备份目录
            shutil.copytree(target_path, backup_path, dirs_exist_ok=True)
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return None
    
    def _copy_files(self, source_path: Path, target_path: Path) -> int:
        """复制文件到目标路径"""
        try:
            # 确保目标目录存在
            target_path.mkdir(parents=True, exist_ok=True)
            
            files_copied = 0
            
            if source_path.is_file():
                # 单个文件复制
                shutil.copy2(source_path, target_path)
                files_copied = 1
            else:
                # 目录复制
                for item in source_path.rglob("*"):
                    if item.is_file():
                        # 计算相对路径
                        relative_path = item.relative_to(source_path)
                        target_file = target_path / relative_path
                        
                        # 确保目标目录存在
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 复制文件
                        shutil.copy2(item, target_file)
                        files_copied += 1
            
            self.logger.info(f"复制了 {files_copied} 个文件")
            return files_copied
            
        except Exception as e:
            self.logger.error(f"文件复制失败: {e}")
            return 0
    
    def _set_file_permissions(self, target_path: Path, deployment: StaticDeployment) -> bool:
        """设置文件权限和所有权"""
        try:
            # 获取用户和组ID
            try:
                owner_uid = pwd.getpwnam(deployment.owner).pw_uid
                group_gid = grp.getgrnam(deployment.group).gr_gid
            except KeyError as e:
                self.logger.warning(f"用户或组不存在: {e}")
                return False
            
            # 设置权限
            permission_mode = int(deployment.permissions, 8)
            
            # 递归设置所有文件和目录
            for item in target_path.rglob("*"):
                try:
                    # 设置所有权
                    os.chown(item, owner_uid, group_gid)
                    
                    # 设置权限
                    if item.is_dir():
                        # 目录需要执行权限
                        os.chmod(item, permission_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    else:
                        # 文件权限
                        os.chmod(item, permission_mode)
                        
                except Exception as e:
                    self.logger.warning(f"设置权限失败: {item}, {e}")
            
            # 设置根目录权限
            os.chown(target_path, owner_uid, group_gid)
            os.chmod(target_path, permission_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置文件权限失败: {e}")
            return False
    
    def _generate_nginx_config(self, deployment: StaticDeployment) -> bool:
        """生成Nginx配置文件"""
        try:
            config_content = self._create_nginx_config_content(deployment)
            
            # 写入配置文件
            config_file = self.nginx_config_dir / f"{deployment.name}.conf"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 创建软链接到enabled目录
            enabled_link = self.nginx_enabled_dir / f"{deployment.name}.conf"
            if enabled_link.exists():
                enabled_link.unlink()
            
            enabled_link.symlink_to(config_file)
            
            # 测试Nginx配置
            result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Nginx配置测试失败: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"生成Nginx配置失败: {e}")
            return False
    
    def _create_nginx_config_content(self, deployment: StaticDeployment) -> str:
        """创建Nginx配置内容"""
        
        # 基础HTTP配置
        config = f"""# {deployment.name} 静态文件配置
# 生成时间: {datetime.now().isoformat()}

server {{
    listen {deployment.port};
    server_name {deployment.domain};
    
    root {deployment.target_path};
    index index.html index.htm;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 静态文件缓存
    location ~* \\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }}
    
    # HTML文件不缓存
    location ~* \\.html$ {{
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }}
    
    # 主要位置配置
    location / {{
        try_files $uri $uri/ /index.html;
        
        # 安全配置
        location ~ /\\. {{
            deny all;
        }}
        
        location ~ ~$ {{
            deny all;
        }}
    }}
    
    # 健康检查端点
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
    
    # 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    # 日志配置
    access_log /var/log/nginx/{deployment.name}_access.log;
    error_log /var/log/nginx/{deployment.name}_error.log;
}}
"""
        
        # 如果启用SSL，添加HTTPS配置
        if deployment.ssl_enabled:
            ssl_config = f"""
# HTTPS配置
server {{
    listen {deployment.ssl_port} ssl http2;
    server_name {deployment.domain};
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/{deployment.domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{deployment.domain}/privkey.pem;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    root {deployment.target_path};
    index index.html index.htm;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 静态文件缓存
    location ~* \\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }}
    
    # HTML文件不缓存
    location ~* \\.html$ {{
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }}
    
    # 主要位置配置
    location / {{
        try_files $uri $uri/ /index.html;
        
        # 安全配置
        location ~ /\\. {{
            deny all;
        }}
        
        location ~ ~$ {{
            deny all;
        }}
    }}
    
    # 健康检查端点
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
    
    # 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    # 日志配置
    access_log /var/log/nginx/{deployment.name}_ssl_access.log;
    error_log /var/log/nginx/{deployment.name}_ssl_error.log;
}}

# HTTP到HTTPS重定向
server {{
    listen {deployment.port};
    server_name {deployment.domain};
    return 301 https://$server_name$request_uri;
}}
"""
            config += ssl_config
        
        return config
    
    def _reload_nginx(self) -> bool:
        """重载Nginx配置"""
        try:
            # 首先测试配置
            test_result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True,
                text=True
            )
            
            if test_result.returncode != 0:
                self.logger.error(f"Nginx配置测试失败: {test_result.stderr}")
                return False
            
            # 重载配置
            reload_result = subprocess.run(
                ["systemctl", "reload", "nginx"],
                capture_output=True,
                text=True
            )
            
            if reload_result.returncode != 0:
                self.logger.error(f"Nginx重载失败: {reload_result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"重载Nginx失败: {e}")
            return False
    
    def _verify_deployment(self, deployment: StaticDeployment) -> bool:
        """验证部署结果"""
        self.logger.info(f"验证部署: {deployment.name}")
        
        try:
            # 等待Nginx重载完成
            time.sleep(2)
            
            # 测试HTTP访问
            http_success = self._test_http_access(deployment)
            
            # 如果启用SSL，测试HTTPS访问
            https_success = True
            if deployment.ssl_enabled:
                https_success = self._test_https_access(deployment)
            
            # 测试静态文件访问
            static_success = self._test_static_files(deployment)
            
            # 测试健康检查端点
            health_success = self._test_health_endpoint(deployment)
            
            overall_success = http_success and https_success and static_success and health_success
            
            self.logger.info(f"验证结果 - HTTP: {http_success}, HTTPS: {https_success}, "
                           f"静态文件: {static_success}, 健康检查: {health_success}")
            
            return overall_success
            
        except Exception as e:
            self.logger.error(f"部署验证异常: {e}")
            return False
    
    def _test_http_access(self, deployment: StaticDeployment) -> bool:
        """测试HTTP访问"""
        try:
            if deployment.ssl_enabled:
                # 如果启用SSL，HTTP应该重定向到HTTPS
                response = requests.get(
                    f"http://{deployment.domain}:{deployment.port}/health",
                    timeout=10,
                    allow_redirects=False
                )
                return response.status_code in [301, 302]
            else:
                # 直接HTTP访问
                response = requests.get(
                    f"http://{deployment.domain}:{deployment.port}/health",
                    timeout=10
                )
                return response.status_code == 200
                
        except Exception as e:
            self.logger.error(f"HTTP访问测试失败: {e}")
            return False
    
    def _test_https_access(self, deployment: StaticDeployment) -> bool:
        """测试HTTPS访问"""
        try:
            response = requests.get(
                f"https://{deployment.domain}:{deployment.ssl_port}/health",
                timeout=10,
                verify=False  # 在测试环境中可能需要跳过证书验证
            )
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"HTTPS访问测试失败: {e}")
            return False
    
    def _test_static_files(self, deployment: StaticDeployment) -> bool:
        """测试静态文件访问"""
        try:
            target_path = Path(deployment.target_path)
            
            # 查找index.html或其他主要文件
            test_files = ["index.html", "index.htm", "main.html"]
            
            for test_file in test_files:
                if (target_path / test_file).exists():
                    protocol = "https" if deployment.ssl_enabled else "http"
                    port = deployment.ssl_port if deployment.ssl_enabled else deployment.port
                    
                    response = requests.get(
                        f"{protocol}://{deployment.domain}:{port}/{test_file}",
                        timeout=10,
                        verify=False
                    )
                    
                    if response.status_code == 200:
                        return True
            
            # 如果没有找到测试文件，检查目录是否可访问
            protocol = "https" if deployment.ssl_enabled else "http"
            port = deployment.ssl_port if deployment.ssl_enabled else deployment.port
            
            response = requests.get(
                f"{protocol}://{deployment.domain}:{port}/",
                timeout=10,
                verify=False
            )
            
            return response.status_code in [200, 403]  # 200或403都表示服务器响应正常
            
        except Exception as e:
            self.logger.error(f"静态文件访问测试失败: {e}")
            return False
    
    def _test_health_endpoint(self, deployment: StaticDeployment) -> bool:
        """测试健康检查端点"""
        try:
            protocol = "https" if deployment.ssl_enabled else "http"
            port = deployment.ssl_port if deployment.ssl_enabled else deployment.port
            
            response = requests.get(
                f"{protocol}://{deployment.domain}:{port}/health",
                timeout=10,
                verify=False
            )
            
            return response.status_code == 200 and "healthy" in response.text
            
        except Exception as e:
            self.logger.error(f"健康检查端点测试失败: {e}")
            return False
    
    def rollback_deployment(self, deployment: StaticDeployment, backup_path: str) -> bool:
        """回滚部署"""
        self.logger.info(f"回滚部署: {deployment.name}")
        
        try:
            backup_path_obj = Path(backup_path)
            target_path = Path(deployment.target_path)
            
            if not backup_path_obj.exists():
                self.logger.error(f"备份路径不存在: {backup_path}")
                return False
            
            # 删除当前部署
            if target_path.exists():
                shutil.rmtree(target_path)
            
            # 恢复备份
            shutil.copytree(backup_path_obj, target_path)
            
            # 重新设置权限
            self._set_file_permissions(target_path, deployment)
            
            # 重载Nginx
            self._reload_nginx()
            
            self.logger.info("部署回滚成功")
            return True
            
        except Exception as e:
            self.logger.error(f"部署回滚失败: {e}")
            return False
    
    def get_deployment_status(self, deployment: StaticDeployment) -> Dict[str, any]:
        """获取部署状态"""
        status = {
            "name": deployment.name,
            "domain": deployment.domain,
            "target_path": deployment.target_path,
            "target_exists": Path(deployment.target_path).exists(),
            "nginx_config_exists": (self.nginx_config_dir / f"{deployment.name}.conf").exists(),
            "nginx_enabled": (self.nginx_enabled_dir / f"{deployment.name}.conf").exists(),
            "ssl_enabled": deployment.ssl_enabled,
            "last_modified": None,
            "file_count": 0,
            "total_size": 0
        }
        
        try:
            target_path = Path(deployment.target_path)
            if target_path.exists():
                # 获取最后修改时间
                status["last_modified"] = datetime.fromtimestamp(
                    target_path.stat().st_mtime
                ).isoformat()
                
                # 统计文件数量和大小
                file_count = 0
                total_size = 0
                
                for item in target_path.rglob("*"):
                    if item.is_file():
                        file_count += 1
                        total_size += item.stat().st_size
                
                status["file_count"] = file_count
                status["total_size"] = total_size
            
            # 测试访问状态
            status["http_accessible"] = self._test_http_access(deployment)
            if deployment.ssl_enabled:
                status["https_accessible"] = self._test_https_access(deployment)
            
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    def deploy_multiple_sites(self, deployments: List[StaticDeployment]) -> Dict[str, DeploymentResult]:
        """部署多个静态站点"""
        results = {}
        
        for deployment in deployments:
            self.logger.info(f"部署站点: {deployment.name}")
            result = self.deploy_static_files(deployment)
            results[deployment.name] = result
            
            if not result.success:
                self.logger.error(f"站点 {deployment.name} 部署失败: {result.message}")
            else:
                self.logger.info(f"站点 {deployment.name} 部署成功")
        
        return results


def create_default_deployments() -> List[StaticDeployment]:
    """创建默认的部署配置"""
    return [
        StaticDeployment(
            name="lawsker-main",
            source_path="frontend",
            target_path="/var/www/lawsker/main",
            nginx_config_path="/etc/nginx/sites-available/lawsker-main.conf",
            domain="lawsker.com",
            ssl_enabled=True
        ),
        StaticDeployment(
            name="lawsker-admin",
            source_path="frontend/admin",
            target_path="/var/www/lawsker/admin",
            nginx_config_path="/etc/nginx/sites-available/lawsker-admin.conf",
            domain="admin.lawsker.com",
            ssl_enabled=True
        ),
        StaticDeployment(
            name="lawsker-app",
            source_path="frontend/dist",
            target_path="/var/www/lawsker/app",
            nginx_config_path="/etc/nginx/sites-available/lawsker-app.conf",
            domain="app.lawsker.com",
            ssl_enabled=True
        )
    ]


if __name__ == "__main__":
    # 测试用例
    import json
    
    manager = StaticDeploymentManager()
    deployments = create_default_deployments()
    
    # 获取部署状态
    for deployment in deployments:
        status = manager.get_deployment_status(deployment)
        print(f"部署状态: {json.dumps(status, indent=2, ensure_ascii=False)}")