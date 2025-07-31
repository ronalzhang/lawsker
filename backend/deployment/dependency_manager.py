"""
依赖管理系统 - DependencyManager类
负责Python虚拟环境创建、依赖安装和验证
"""

import os
import sys
import subprocess
import logging
import json
import pkg_resources
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from packaging import version
import tempfile
import shutil


@dataclass
class DependencyInfo:
    """依赖包信息"""
    name: str
    version: str
    installed_version: Optional[str] = None
    is_critical: bool = False
    conflicts: List[str] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


@dataclass
class VenvInfo:
    """虚拟环境信息"""
    path: str
    python_version: str
    pip_version: str
    is_active: bool = False


class DependencyManager:
    """依赖管理器"""
    
    # 关键依赖包列表
    CRITICAL_PACKAGES = {
        'fastapi': '0.104.1',
        'uvicorn': '0.24.0',
        'sqlalchemy': '2.0.23',
        'redis': '5.0.1',
        'celery': '5.3.4',
        'cryptography': '41.0.7',
        'prometheus-client': '0.19.0',
        'psycopg2-binary': '2.9.9',
        'pydantic': '2.5.0'
    }
    
    def __init__(self, requirements_file: str, venv_path: str, project_root: str = None):
        """
        初始化依赖管理器
        
        Args:
            requirements_file: requirements文件路径
            venv_path: 虚拟环境路径
            project_root: 项目根目录
        """
        self.requirements_file = Path(requirements_file)
        self.venv_path = Path(venv_path)
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.logger = logging.getLogger(__name__)
        
        # 确保路径存在
        self.venv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 备份目录
        self.backup_dir = self.project_root / "deployment" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_virtual_environment(self) -> bool:
        """
        创建Python虚拟环境
        
        Returns:
            bool: 创建是否成功
        """
        try:
            self.logger.info(f"开始创建虚拟环境: {self.venv_path}")
            
            # 检查Python版本
            python_version = self._get_python_version()
            if not self._is_python_version_compatible(python_version):
                self.logger.error(f"Python版本不兼容: {python_version}")
                return False
            
            # 删除已存在的虚拟环境
            if self.venv_path.exists():
                self.logger.info("删除已存在的虚拟环境")
                shutil.rmtree(self.venv_path)
            
            # 创建虚拟环境
            cmd = [sys.executable, "-m", "venv", str(self.venv_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"创建虚拟环境失败: {result.stderr}")
                return False
            
            # 升级pip
            if not self._upgrade_pip():
                self.logger.warning("升级pip失败，继续使用默认版本")
            
            self.logger.info("虚拟环境创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建虚拟环境异常: {str(e)}")
            return False
    
    def install_dependencies(self) -> bool:
        """
        安装Python依赖包
        
        Returns:
            bool: 安装是否成功
        """
        try:
            self.logger.info("开始安装依赖包")
            
            # 检查虚拟环境
            if not self._check_virtual_environment():
                self.logger.error("虚拟环境不可用")
                return False
            
            # 检查requirements文件
            if not self.requirements_file.exists():
                self.logger.error(f"Requirements文件不存在: {self.requirements_file}")
                return False
            
            # 创建备份
            self._create_dependency_backup()
            
            # 解析requirements文件
            dependencies = self._parse_requirements_file()
            if not dependencies:
                self.logger.error("无法解析requirements文件")
                return False
            
            # 分批安装依赖
            success = self._install_dependencies_batch(dependencies)
            
            if success:
                self.logger.info("依赖包安装完成")
                return True
            else:
                self.logger.error("依赖包安装失败，尝试回滚")
                self._rollback_dependencies()
                return False
                
        except Exception as e:
            self.logger.error(f"安装依赖包异常: {str(e)}")
            return False
    
    def verify_dependencies(self) -> Dict[str, bool]:
        """
        验证关键依赖包
        
        Returns:
            Dict[str, bool]: 依赖包验证结果
        """
        try:
            self.logger.info("开始验证依赖包")
            results = {}
            
            # 获取已安装的包
            installed_packages = self._get_installed_packages()
            
            # 验证关键依赖
            for package_name, expected_version in self.CRITICAL_PACKAGES.items():
                try:
                    if package_name in installed_packages:
                        installed_version = installed_packages[package_name]
                        is_compatible = self._check_version_compatibility(
                            installed_version, expected_version
                        )
                        results[package_name] = is_compatible
                        
                        if is_compatible:
                            self.logger.info(f"✓ {package_name}: {installed_version}")
                        else:
                            self.logger.warning(
                                f"✗ {package_name}: {installed_version} (期望: {expected_version})"
                            )
                    else:
                        results[package_name] = False
                        self.logger.error(f"✗ {package_name}: 未安装")
                        
                except Exception as e:
                    results[package_name] = False
                    self.logger.error(f"✗ {package_name}: 验证失败 - {str(e)}")
            
            # 验证导入能力
            import_results = self._verify_package_imports()
            results.update(import_results)
            
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            
            self.logger.info(f"依赖验证完成: {success_count}/{total_count} 成功")
            return results
            
        except Exception as e:
            self.logger.error(f"验证依赖包异常: {str(e)}")
            return {}
    
    def update_dependencies(self) -> bool:
        """
        更新依赖包
        
        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.info("开始更新依赖包")
            
            # 创建备份
            backup_path = self._create_dependency_backup()
            
            # 获取当前安装的包
            current_packages = self._get_installed_packages()
            
            # 更新pip
            if not self._upgrade_pip():
                self.logger.warning("升级pip失败")
            
            # 重新安装依赖
            if self.install_dependencies():
                # 验证更新结果
                verification_results = self.verify_dependencies()
                failed_packages = [k for k, v in verification_results.items() if not v]
                
                if failed_packages:
                    self.logger.warning(f"以下包验证失败: {failed_packages}")
                    # 可以选择回滚或继续
                
                self.logger.info("依赖包更新完成")
                return True
            else:
                self.logger.error("依赖包更新失败，回滚到备份版本")
                self._restore_from_backup(backup_path)
                return False
                
        except Exception as e:
            self.logger.error(f"更新依赖包异常: {str(e)}")
            return False
    
    def rollback_dependencies(self) -> bool:
        """
        回滚依赖包到上一个版本
        
        Returns:
            bool: 回滚是否成功
        """
        try:
            self.logger.info("开始回滚依赖包")
            
            # 查找最新的备份
            backup_files = list(self.backup_dir.glob("requirements_backup_*.txt"))
            if not backup_files:
                self.logger.error("没有找到备份文件")
                return False
            
            # 选择最新的备份
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            return self._restore_from_backup(latest_backup)
            
        except Exception as e:
            self.logger.error(f"回滚依赖包异常: {str(e)}")
            return False
    
    def get_dependency_info(self) -> Dict[str, DependencyInfo]:
        """
        获取依赖包详细信息
        
        Returns:
            Dict[str, DependencyInfo]: 依赖包信息
        """
        try:
            dependencies = {}
            installed_packages = self._get_installed_packages()
            
            # 解析requirements文件
            required_packages = self._parse_requirements_file()
            
            for pkg_name, pkg_version in required_packages.items():
                installed_version = installed_packages.get(pkg_name)
                is_critical = pkg_name in self.CRITICAL_PACKAGES
                
                dependencies[pkg_name] = DependencyInfo(
                    name=pkg_name,
                    version=pkg_version,
                    installed_version=installed_version,
                    is_critical=is_critical
                )
            
            return dependencies
            
        except Exception as e:
            self.logger.error(f"获取依赖信息异常: {str(e)}")
            return {}
    
    def get_virtual_environment_info(self) -> Optional[VenvInfo]:
        """
        获取虚拟环境信息
        
        Returns:
            Optional[VenvInfo]: 虚拟环境信息
        """
        try:
            if not self.venv_path.exists():
                return None
            
            # 获取Python版本
            python_exe = self._get_venv_python_executable()
            result = subprocess.run(
                [python_exe, "--version"], 
                capture_output=True, text=True
            )
            python_version = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            # 获取pip版本
            result = subprocess.run(
                [python_exe, "-m", "pip", "--version"], 
                capture_output=True, text=True
            )
            pip_version = result.stdout.split()[1] if result.returncode == 0 else "Unknown"
            
            # 检查是否激活
            is_active = os.environ.get('VIRTUAL_ENV') == str(self.venv_path)
            
            return VenvInfo(
                path=str(self.venv_path),
                python_version=python_version,
                pip_version=pip_version,
                is_active=is_active
            )
            
        except Exception as e:
            self.logger.error(f"获取虚拟环境信息异常: {str(e)}")
            return None
    
    # 私有方法
    
    def _get_python_version(self) -> str:
        """获取Python版本"""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _is_python_version_compatible(self, python_version: str) -> bool:
        """检查Python版本兼容性"""
        try:
            major, minor, patch = map(int, python_version.split('.'))
            # 要求Python 3.8+
            return major == 3 and minor >= 8
        except:
            return False
    
    def _get_venv_python_executable(self) -> str:
        """获取虚拟环境Python可执行文件路径"""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "python.exe")
        else:  # Unix/Linux/macOS
            return str(self.venv_path / "bin" / "python")
    
    def _get_venv_pip_executable(self) -> str:
        """获取虚拟环境pip可执行文件路径"""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:  # Unix/Linux/macOS
            return str(self.venv_path / "bin" / "pip")
    
    def _check_virtual_environment(self) -> bool:
        """检查虚拟环境是否可用"""
        python_exe = self._get_venv_python_executable()
        return Path(python_exe).exists()
    
    def _upgrade_pip(self) -> bool:
        """升级pip"""
        try:
            python_exe = self._get_venv_python_executable()
            cmd = [python_exe, "-m", "pip", "install", "--upgrade", "pip"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _parse_requirements_file(self) -> Dict[str, str]:
        """解析requirements文件"""
        try:
            dependencies = {}
            
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 处理-r引用的文件
                if line.startswith('-r '):
                    ref_file = line[3:].strip()
                    ref_path = self.requirements_file.parent / ref_file
                    if ref_path.exists():
                        ref_deps = self._parse_requirements_file_path(ref_path)
                        dependencies.update(ref_deps)
                    continue
                
                # 解析包名和版本
                if '==' in line:
                    name, version = line.split('==', 1)
                    name = name.strip()
                    version = version.strip()
                    # 处理额外依赖，如redis[hiredis]
                    if '[' in name:
                        name = name.split('[')[0]
                    dependencies[name] = version
                elif '>=' in line:
                    name = line.split('>=')[0].strip()
                    if '[' in name:
                        name = name.split('[')[0]
                    dependencies[name] = 'latest'
                else:
                    # 没有版本指定的包
                    name = line.strip()
                    if '[' in name:
                        name = name.split('[')[0]
                    dependencies[name] = 'latest'
            
            return dependencies
            
        except Exception as e:
            self.logger.error(f"解析requirements文件失败: {str(e)}")
            return {}
    
    def _parse_requirements_file_path(self, file_path: Path) -> Dict[str, str]:
        """解析指定路径的requirements文件"""
        original_file = self.requirements_file
        self.requirements_file = file_path
        result = self._parse_requirements_file()
        self.requirements_file = original_file
        return result
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """获取已安装的包列表"""
        try:
            python_exe = self._get_venv_python_executable()
            cmd = [python_exe, "-m", "pip", "list", "--format=json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
            
            packages = json.loads(result.stdout)
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
            
        except Exception as e:
            self.logger.error(f"获取已安装包列表失败: {str(e)}")
            return {}
    
    def _install_dependencies_batch(self, dependencies: Dict[str, str]) -> bool:
        """分批安装依赖"""
        try:
            python_exe = self._get_venv_python_executable()
            
            # 首先安装关键依赖
            critical_deps = {k: v for k, v in dependencies.items() 
                           if k in self.CRITICAL_PACKAGES}
            
            if critical_deps:
                self.logger.info("安装关键依赖包...")
                if not self._install_package_batch(python_exe, critical_deps):
                    return False
            
            # 然后安装其他依赖
            other_deps = {k: v for k, v in dependencies.items() 
                         if k not in self.CRITICAL_PACKAGES}
            
            if other_deps:
                self.logger.info("安装其他依赖包...")
                if not self._install_package_batch(python_exe, other_deps):
                    self.logger.warning("部分非关键依赖安装失败，继续执行")
            
            return True
            
        except Exception as e:
            self.logger.error(f"批量安装依赖失败: {str(e)}")
            return False
    
    def _install_package_batch(self, python_exe: str, packages: Dict[str, str]) -> bool:
        """安装一批包"""
        try:
            # 使用requirements文件安装
            cmd = [python_exe, "-m", "pip", "install", "-r", str(self.requirements_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"安装失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("安装超时")
            return False
        except Exception as e:
            self.logger.error(f"安装异常: {str(e)}")
            return False
    
    def _check_version_compatibility(self, installed: str, expected: str) -> bool:
        """检查版本兼容性"""
        try:
            if expected == 'latest':
                return True
            
            installed_ver = version.parse(installed)
            expected_ver = version.parse(expected)
            
            # 允许小版本差异
            return (installed_ver.major == expected_ver.major and 
                   installed_ver.minor >= expected_ver.minor)
            
        except Exception:
            return False
    
    def _verify_package_imports(self) -> Dict[str, bool]:
        """验证包导入能力"""
        import_tests = {
            'fastapi': 'import fastapi',
            'sqlalchemy': 'import sqlalchemy',
            'redis': 'import redis',
            'celery': 'import celery',
            'cryptography': 'from cryptography.fernet import Fernet',
            'prometheus_client': 'import prometheus_client',
            'psycopg2': 'import psycopg2',
            'pydantic': 'import pydantic'
        }
        
        results = {}
        python_exe = self._get_venv_python_executable()
        
        for package, import_cmd in import_tests.items():
            try:
                cmd = [python_exe, "-c", import_cmd]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                results[f"{package}_import"] = result.returncode == 0
                
                if result.returncode != 0:
                    self.logger.warning(f"导入测试失败 {package}: {result.stderr}")
                    
            except Exception as e:
                results[f"{package}_import"] = False
                self.logger.error(f"导入测试异常 {package}: {str(e)}")
        
        return results
    
    def _create_dependency_backup(self) -> Path:
        """创建依赖备份"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"requirements_backup_{timestamp}.txt"
            
            # 备份当前requirements文件
            if self.requirements_file.exists():
                shutil.copy2(self.requirements_file, backup_file)
            
            # 备份已安装包列表
            python_exe = self._get_venv_python_executable()
            if Path(python_exe).exists():
                freeze_file = self.backup_dir / f"pip_freeze_{timestamp}.txt"
                cmd = [python_exe, "-m", "pip", "freeze"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    with open(freeze_file, 'w') as f:
                        f.write(result.stdout)
            
            self.logger.info(f"依赖备份已创建: {backup_file}")
            return backup_file
            
        except Exception as e:
            self.logger.error(f"创建依赖备份失败: {str(e)}")
            return None
    
    def _rollback_dependencies(self) -> bool:
        """回滚依赖"""
        return self.rollback_dependencies()
    
    def _restore_from_backup(self, backup_file: Path) -> bool:
        """从备份恢复"""
        try:
            if not backup_file.exists():
                self.logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 重新创建虚拟环境
            if not self.create_virtual_environment():
                return False
            
            # 使用备份文件安装依赖
            python_exe = self._get_venv_python_executable()
            cmd = [python_exe, "-m", "pip", "install", "-r", str(backup_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("从备份恢复成功")
                return True
            else:
                self.logger.error(f"从备份恢复失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"从备份恢复异常: {str(e)}")
            return False