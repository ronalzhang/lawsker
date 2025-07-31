#!/usr/bin/env python3
"""
前端构建器 - 负责Node.js环境检查、依赖安装、构建和部署
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


@dataclass
class FrontendProject:
    """前端项目配置"""
    name: str
    path: str
    build_command: str
    output_dir: str
    nginx_root: str
    domain: str
    port: Optional[int] = None
    env_file: Optional[str] = None


class FrontendBuilder:
    """前端构建器类"""
    
    def __init__(self, projects: List[FrontendProject], base_path: str = "/opt/lawsker"):
        self.projects = projects
        self.base_path = Path(base_path)
        self.logger = self._setup_logger()
        self.node_min_version = "18.0.0"
        self.npm_min_version = "8.0.0"
        
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
    
    def check_node_environment(self) -> bool:
        """检查Node.js和npm环境"""
        self.logger.info("检查Node.js环境...")
        
        try:
            # 检查Node.js版本
            node_result = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            node_version = node_result.stdout.strip().lstrip('v')
            self.logger.info(f"Node.js版本: {node_version}")
            
            if not self._version_compare(node_version, self.node_min_version):
                self.logger.error(f"Node.js版本过低，需要 >= {self.node_min_version}")
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Node.js未安装或无法访问: {e}")
            return False
        
        try:
            # 检查npm版本
            npm_result = subprocess.run(
                ["npm", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            npm_version = npm_result.stdout.strip()
            self.logger.info(f"npm版本: {npm_version}")
            
            if not self._version_compare(npm_version, self.npm_min_version):
                self.logger.error(f"npm版本过低，需要 >= {self.npm_min_version}")
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"npm未安装或无法访问: {e}")
            return False
        
        self.logger.info("Node.js环境检查通过")
        return True
    
    def _version_compare(self, version1: str, version2: str) -> bool:
        """比较版本号，返回version1 >= version2"""
        def version_tuple(v):
            return tuple(map(int, (v.split("."))))
        return version_tuple(version1) >= version_tuple(version2)
    
    def install_dependencies(self, project: FrontendProject) -> bool:
        """安装前端项目依赖"""
        project_path = self.base_path / project.path
        
        if not project_path.exists():
            self.logger.error(f"项目路径不存在: {project_path}")
            return False
        
        package_json_path = project_path / "package.json"
        if not package_json_path.exists():
            self.logger.error(f"package.json不存在: {package_json_path}")
            return False
        
        self.logger.info(f"为项目 {project.name} 安装依赖...")
        
        try:
            # 清理node_modules和package-lock.json
            node_modules_path = project_path / "node_modules"
            if node_modules_path.exists():
                self.logger.info("清理旧的node_modules...")
                shutil.rmtree(node_modules_path)
            
            lock_file = project_path / "package-lock.json"
            if lock_file.exists():
                lock_file.unlink()
            
            # 安装依赖
            result = subprocess.run(
                ["npm", "install", "--production=false"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                self.logger.error(f"依赖安装失败: {result.stderr}")
                return False
            
            self.logger.info(f"项目 {project.name} 依赖安装成功")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("依赖安装超时")
            return False
        except Exception as e:
            self.logger.error(f"依赖安装异常: {e}")
            return False
    
    def build_project(self, project: FrontendProject) -> bool:
        """构建前端项目"""
        project_path = self.base_path / project.path
        
        self.logger.info(f"构建项目 {project.name}...")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            if project.env_file:
                env_file_path = project_path / project.env_file
                if env_file_path.exists():
                    self._load_env_file(env_file_path, env)
            
            # 执行构建命令
            build_commands = project.build_command.split(" && ")
            
            for cmd in build_commands:
                cmd_parts = cmd.strip().split()
                self.logger.info(f"执行命令: {' '.join(cmd_parts)}")
                
                result = subprocess.run(
                    cmd_parts,
                    cwd=project_path,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=1200  # 20分钟超时
                )
                
                if result.returncode != 0:
                    self.logger.error(f"构建命令失败: {result.stderr}")
                    return False
                
                self.logger.info(f"命令执行成功: {cmd}")
            
            # 验证构建产物
            output_path = project_path / project.output_dir
            if not output_path.exists():
                self.logger.error(f"构建产物目录不存在: {output_path}")
                return False
            
            self.logger.info(f"项目 {project.name} 构建成功")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("构建超时")
            return False
        except Exception as e:
            self.logger.error(f"构建异常: {e}")
            return False
    
    def _load_env_file(self, env_file_path: Path, env: Dict[str, str]):
        """加载环境变量文件"""
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            self.logger.warning(f"加载环境变量文件失败: {e}")
    
    def monitor_build_process(self, project: FrontendProject) -> Dict[str, any]:
        """监控构建过程并记录详细信息"""
        start_time = datetime.now()
        project_path = self.base_path / project.path
        
        build_info = {
            "project": project.name,
            "start_time": start_time.isoformat(),
            "status": "started",
            "logs": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # 记录项目信息
            package_json_path = project_path / "package.json"
            if package_json_path.exists():
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_info = json.load(f)
                    build_info["package_info"] = {
                        "name": package_info.get("name"),
                        "version": package_info.get("version"),
                        "dependencies_count": len(package_info.get("dependencies", {})),
                        "dev_dependencies_count": len(package_info.get("devDependencies", {}))
                    }
            
            # 执行构建并监控
            if self.install_dependencies(project):
                build_info["dependencies_installed"] = True
                build_info["logs"].append("依赖安装成功")
                
                if self.build_project(project):
                    build_info["status"] = "success"
                    build_info["logs"].append("项目构建成功")
                else:
                    build_info["status"] = "build_failed"
                    build_info["errors"].append("项目构建失败")
            else:
                build_info["status"] = "dependencies_failed"
                build_info["errors"].append("依赖安装失败")
        
        except Exception as e:
            build_info["status"] = "error"
            build_info["errors"].append(f"构建监控异常: {str(e)}")
        
        finally:
            end_time = datetime.now()
            build_info["end_time"] = end_time.isoformat()
            build_info["duration"] = (end_time - start_time).total_seconds()
        
        return build_info
    
    def recover_from_build_failure(self, project: FrontendProject, error_info: Dict) -> bool:
        """构建失败恢复机制"""
        self.logger.info(f"尝试恢复项目 {project.name} 的构建失败...")
        
        project_path = self.base_path / project.path
        
        try:
            # 策略1: 清理缓存并重试
            self.logger.info("策略1: 清理npm缓存...")
            subprocess.run(["npm", "cache", "clean", "--force"], cwd=project_path)
            
            # 策略2: 删除node_modules重新安装
            self.logger.info("策略2: 重新安装依赖...")
            node_modules = project_path / "node_modules"
            if node_modules.exists():
                shutil.rmtree(node_modules)
            
            if not self.install_dependencies(project):
                self.logger.error("重新安装依赖失败")
                return False
            
            # 策略3: 尝试使用不同的构建选项
            self.logger.info("策略3: 使用备用构建选项...")
            
            # 设置更宽松的构建环境
            env = os.environ.copy()
            env["NODE_OPTIONS"] = "--max-old-space-size=4096"
            env["CI"] = "false"  # 禁用CI模式的严格检查
            
            build_commands = project.build_command.split(" && ")
            
            for cmd in build_commands:
                # 为TypeScript构建添加跳过类型检查选项
                if "vue-tsc" in cmd:
                    cmd = cmd.replace("vue-tsc", "vue-tsc --skipLibCheck")
                
                cmd_parts = cmd.strip().split()
                result = subprocess.run(
                    cmd_parts,
                    cwd=project_path,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30分钟超时
                )
                
                if result.returncode != 0:
                    self.logger.error(f"恢复构建失败: {result.stderr}")
                    return False
            
            self.logger.info(f"项目 {project.name} 构建恢复成功")
            return True
            
        except Exception as e:
            self.logger.error(f"构建恢复异常: {e}")
            return False
    
    def build_all_projects(self) -> Dict[str, Dict]:
        """构建所有前端项目"""
        results = {}
        
        # 首先检查Node.js环境
        if not self.check_node_environment():
            return {"error": "Node.js环境检查失败"}
        
        for project in self.projects:
            self.logger.info(f"开始构建项目: {project.name}")
            
            # 监控构建过程
            build_result = self.monitor_build_process(project)
            
            # 如果构建失败，尝试恢复
            if build_result["status"] not in ["success"]:
                self.logger.warning(f"项目 {project.name} 构建失败，尝试恢复...")
                if self.recover_from_build_failure(project, build_result):
                    build_result["status"] = "recovered"
                    build_result["logs"].append("构建恢复成功")
            
            results[project.name] = build_result
        
        return results
    
    def get_project_info(self, project: FrontendProject) -> Dict:
        """获取项目详细信息"""
        project_path = self.base_path / project.path
        info = {
            "name": project.name,
            "path": str(project_path),
            "exists": project_path.exists()
        }
        
        if project_path.exists():
            package_json = project_path / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                        info.update({
                            "package_name": package_data.get("name"),
                            "version": package_data.get("version"),
                            "description": package_data.get("description"),
                            "scripts": package_data.get("scripts", {}),
                            "dependencies": list(package_data.get("dependencies", {}).keys()),
                            "dev_dependencies": list(package_data.get("devDependencies", {}).keys())
                        })
                except Exception as e:
                    info["package_error"] = str(e)
            
            # 检查构建产物
            output_path = project_path / project.output_dir
            info["build_output_exists"] = output_path.exists()
            if output_path.exists():
                try:
                    info["build_files"] = [f.name for f in output_path.iterdir()]
                except Exception:
                    pass
        
        return info


def create_default_projects() -> List[FrontendProject]:
    """创建默认的前端项目配置"""
    return [
        FrontendProject(
            name="lawsker-frontend",
            path="frontend",
            build_command="echo 'Static files, no build needed'",
            output_dir=".",
            nginx_root="/var/www/lawsker/frontend",
            domain="lawsker.com"
        ),
        FrontendProject(
            name="lawsker-admin",
            path="frontend-admin",
            build_command="npm run build",
            output_dir="dist",
            nginx_root="/var/www/lawsker/admin",
            domain="admin.lawsker.com",
            env_file=".env.production"
        ),
        FrontendProject(
            name="lawsker-vue",
            path="frontend-vue",
            build_command="npm run build",
            output_dir="dist",
            nginx_root="/var/www/lawsker/app",
            domain="app.lawsker.com",
            env_file=".env.production"
        )
    ]


if __name__ == "__main__":
    # 测试用例
    projects = create_default_projects()
    builder = FrontendBuilder(projects)
    
    # 检查环境
    if builder.check_node_environment():
        print("Node.js环境检查通过")
        
        # 获取项目信息
        for project in projects:
            info = builder.get_project_info(project)
            print(f"项目信息: {json.dumps(info, indent=2, ensure_ascii=False)}")
    else:
        print("Node.js环境检查失败")