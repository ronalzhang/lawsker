"""
依赖验证脚本 - 关键依赖包检查和诊断工具
"""

import os
import sys
import json
import logging
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import pkg_resources
from packaging import version, requirements

from .dependency_manager import DependencyManager, DependencyInfo


@dataclass
class ValidationResult:
    """验证结果"""
    package_name: str
    status: str  # 'success', 'warning', 'error'
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class CompatibilityCheck:
    """兼容性检查结果"""
    package_name: str
    installed_version: str
    required_version: str
    is_compatible: bool
    compatibility_level: str  # 'exact', 'compatible', 'warning', 'incompatible'
    notes: List[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []


@dataclass
class DependencyReport:
    """依赖报告"""
    timestamp: str
    python_version: str
    virtual_env_path: str
    total_packages: int
    critical_packages: int
    validation_results: List[ValidationResult]
    compatibility_checks: List[CompatibilityCheck]
    conflicts: List[Dict[str, Any]]
    recommendations: List[str]
    overall_status: str  # 'healthy', 'warning', 'critical'


class DependencyValidator:
    """依赖验证器"""
    
    def __init__(self, dependency_manager: DependencyManager):
        """
        初始化依赖验证器
        
        Args:
            dependency_manager: 依赖管理器实例
        """
        self.dependency_manager = dependency_manager
        self.logger = logging.getLogger(__name__)
        
        # 已知的包冲突
        self.known_conflicts = {
            'asyncpg': ['psycopg2', 'psycopg2-binary'],
            'ujson': ['orjson'],
            'redis': ['aioredis'],
        }
        
        # 安全漏洞包版本
        self.security_vulnerabilities = {
            'cryptography': ['<41.0.0'],
            'pillow': ['<10.0.0'],
            'requests': ['<2.31.0'],
            'sqlalchemy': ['<2.0.0'],
        }
    
    def validate_all_dependencies(self) -> DependencyReport:
        """
        验证所有依赖包
        
        Returns:
            DependencyReport: 完整的依赖验证报告
        """
        try:
            self.logger.info("开始全面依赖验证")
            
            # 获取依赖信息
            dependencies = self.dependency_manager.get_dependency_info()
            venv_info = self.dependency_manager.get_virtual_environment_info()
            
            # 执行各种验证
            validation_results = []
            compatibility_checks = []
            conflicts = []
            recommendations = []
            
            # 1. 基础包验证
            basic_results = self._validate_basic_packages(dependencies)
            validation_results.extend(basic_results)
            
            # 2. 关键包验证
            critical_results = self._validate_critical_packages()
            validation_results.extend(critical_results)
            
            # 3. 版本兼容性检查
            compatibility_checks = self._check_version_compatibility(dependencies)
            
            # 4. 包冲突检测
            conflicts = self._detect_package_conflicts(dependencies)
            
            # 5. 安全漏洞检查
            security_results = self._check_security_vulnerabilities(dependencies)
            validation_results.extend(security_results)
            
            # 6. 导入测试
            import_results = self._test_package_imports()
            validation_results.extend(import_results)
            
            # 7. 生成建议
            recommendations = self._generate_recommendations(
                validation_results, compatibility_checks, conflicts
            )
            
            # 计算整体状态
            overall_status = self._calculate_overall_status(
                validation_results, compatibility_checks, conflicts
            )
            
            # 创建报告
            report = DependencyReport(
                timestamp=datetime.now().isoformat(),
                python_version=self.dependency_manager._get_python_version(),
                virtual_env_path=str(self.dependency_manager.venv_path),
                total_packages=len(dependencies),
                critical_packages=len(self.dependency_manager.CRITICAL_PACKAGES),
                validation_results=validation_results,
                compatibility_checks=compatibility_checks,
                conflicts=conflicts,
                recommendations=recommendations,
                overall_status=overall_status
            )
            
            self.logger.info(f"依赖验证完成，整体状态: {overall_status}")
            return report
            
        except Exception as e:
            self.logger.error(f"依赖验证异常: {str(e)}")
            raise
    
    def check_package_compatibility(self, package_name: str) -> CompatibilityCheck:
        """
        检查单个包的兼容性
        
        Args:
            package_name: 包名
            
        Returns:
            CompatibilityCheck: 兼容性检查结果
        """
        try:
            dependencies = self.dependency_manager.get_dependency_info()
            
            if package_name not in dependencies:
                return CompatibilityCheck(
                    package_name=package_name,
                    installed_version="Not installed",
                    required_version="Unknown",
                    is_compatible=False,
                    compatibility_level="incompatible",
                    notes=["Package not found in requirements"]
                )
            
            dep_info = dependencies[package_name]
            installed_version = dep_info.installed_version or "Not installed"
            required_version = dep_info.version
            
            if not dep_info.installed_version:
                return CompatibilityCheck(
                    package_name=package_name,
                    installed_version=installed_version,
                    required_version=required_version,
                    is_compatible=False,
                    compatibility_level="incompatible",
                    notes=["Package not installed"]
                )
            
            # 检查版本兼容性
            is_compatible, level, notes = self._check_single_version_compatibility(
                installed_version, required_version
            )
            
            return CompatibilityCheck(
                package_name=package_name,
                installed_version=installed_version,
                required_version=required_version,
                is_compatible=is_compatible,
                compatibility_level=level,
                notes=notes
            )
            
        except Exception as e:
            self.logger.error(f"检查包兼容性异常 {package_name}: {str(e)}")
            return CompatibilityCheck(
                package_name=package_name,
                installed_version="Error",
                required_version="Error",
                is_compatible=False,
                compatibility_level="incompatible",
                notes=[f"Check failed: {str(e)}"]
            )
    
    def diagnose_dependency_issues(self) -> Dict[str, Any]:
        """
        诊断依赖问题
        
        Returns:
            Dict[str, Any]: 诊断结果
        """
        try:
            self.logger.info("开始诊断依赖问题")
            
            diagnosis = {
                'environment_issues': [],
                'missing_packages': [],
                'version_conflicts': [],
                'import_failures': [],
                'security_issues': [],
                'performance_issues': [],
                'recommendations': []
            }
            
            # 1. 环境问题检查
            env_issues = self._diagnose_environment_issues()
            diagnosis['environment_issues'] = env_issues
            
            # 2. 缺失包检查
            missing_packages = self._find_missing_packages()
            diagnosis['missing_packages'] = missing_packages
            
            # 3. 版本冲突检查
            version_conflicts = self._find_version_conflicts()
            diagnosis['version_conflicts'] = version_conflicts
            
            # 4. 导入失败检查
            import_failures = self._find_import_failures()
            diagnosis['import_failures'] = import_failures
            
            # 5. 安全问题检查
            security_issues = self._find_security_issues()
            diagnosis['security_issues'] = security_issues
            
            # 6. 性能问题检查
            performance_issues = self._find_performance_issues()
            diagnosis['performance_issues'] = performance_issues
            
            # 7. 生成修复建议
            recommendations = self._generate_fix_recommendations(diagnosis)
            diagnosis['recommendations'] = recommendations
            
            self.logger.info("依赖问题诊断完成")
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"诊断依赖问题异常: {str(e)}")
            return {'error': str(e)}
    
    def generate_installation_report(self) -> Dict[str, Any]:
        """
        生成安装状态报告
        
        Returns:
            Dict[str, Any]: 安装状态报告
        """
        try:
            self.logger.info("生成安装状态报告")
            
            # 获取已安装包
            installed_packages = self.dependency_manager._get_installed_packages()
            
            # 获取要求的包
            dependencies = self.dependency_manager.get_dependency_info()
            
            report = {
                'summary': {
                    'total_required': len(dependencies),
                    'total_installed': len(installed_packages),
                    'critical_packages': len(self.dependency_manager.CRITICAL_PACKAGES),
                    'timestamp': datetime.now().isoformat()
                },
                'installed_packages': [],
                'missing_packages': [],
                'version_mismatches': [],
                'extra_packages': []
            }
            
            # 分析已安装的包
            for pkg_name, dep_info in dependencies.items():
                if dep_info.installed_version:
                    package_info = {
                        'name': pkg_name,
                        'required_version': dep_info.version,
                        'installed_version': dep_info.installed_version,
                        'is_critical': dep_info.is_critical,
                        'status': 'installed'
                    }
                    
                    # 检查版本匹配
                    if dep_info.version != 'latest':
                        is_match = self._versions_match(
                            dep_info.installed_version, dep_info.version
                        )
                        if not is_match:
                            package_info['status'] = 'version_mismatch'
                            report['version_mismatches'].append(package_info)
                    
                    report['installed_packages'].append(package_info)
                else:
                    # 缺失的包
                    missing_info = {
                        'name': pkg_name,
                        'required_version': dep_info.version,
                        'is_critical': dep_info.is_critical
                    }
                    report['missing_packages'].append(missing_info)
            
            # 查找额外安装的包
            required_names = set(dependencies.keys())
            installed_names = set(installed_packages.keys())
            extra_names = installed_names - required_names
            
            for pkg_name in extra_names:
                extra_info = {
                    'name': pkg_name,
                    'installed_version': installed_packages[pkg_name],
                    'note': 'Not in requirements file'
                }
                report['extra_packages'].append(extra_info)
            
            self.logger.info("安装状态报告生成完成")
            return report
            
        except Exception as e:
            self.logger.error(f"生成安装状态报告异常: {str(e)}")
            return {'error': str(e)}
    
    def save_report_to_file(self, report: DependencyReport, file_path: str) -> bool:
        """
        保存报告到文件
        
        Args:
            report: 依赖报告
            file_path: 文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            report_dict = asdict(report)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"报告已保存到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {str(e)}")
            return False
    
    # 私有方法
    
    def _validate_basic_packages(self, dependencies: Dict[str, DependencyInfo]) -> List[ValidationResult]:
        """验证基础包"""
        results = []
        
        for pkg_name, dep_info in dependencies.items():
            if dep_info.installed_version:
                result = ValidationResult(
                    package_name=pkg_name,
                    status='success',
                    message=f'Package installed: {dep_info.installed_version}',
                    details={
                        'required_version': dep_info.version,
                        'installed_version': dep_info.installed_version,
                        'is_critical': dep_info.is_critical
                    }
                )
            else:
                result = ValidationResult(
                    package_name=pkg_name,
                    status='error',
                    message='Package not installed',
                    details={
                        'required_version': dep_info.version,
                        'is_critical': dep_info.is_critical
                    }
                )
            
            results.append(result)
        
        return results
    
    def _validate_critical_packages(self) -> List[ValidationResult]:
        """验证关键包"""
        results = []
        verification_results = self.dependency_manager.verify_dependencies()
        
        for pkg_name in self.dependency_manager.CRITICAL_PACKAGES:
            is_valid = verification_results.get(pkg_name, False)
            import_valid = verification_results.get(f"{pkg_name}_import", False)
            
            if is_valid and import_valid:
                status = 'success'
                message = 'Critical package verified successfully'
            elif is_valid:
                status = 'warning'
                message = 'Package installed but import test failed'
            else:
                status = 'error'
                message = 'Critical package validation failed'
            
            result = ValidationResult(
                package_name=pkg_name,
                status=status,
                message=message,
                details={
                    'is_critical': True,
                    'version_check': is_valid,
                    'import_check': import_valid
                }
            )
            results.append(result)
        
        return results
    
    def _check_version_compatibility(self, dependencies: Dict[str, DependencyInfo]) -> List[CompatibilityCheck]:
        """检查版本兼容性"""
        checks = []
        
        for pkg_name, dep_info in dependencies.items():
            if dep_info.installed_version:
                check = self.check_package_compatibility(pkg_name)
                checks.append(check)
        
        return checks
    
    def _detect_package_conflicts(self, dependencies: Dict[str, DependencyInfo]) -> List[Dict[str, Any]]:
        """检测包冲突"""
        conflicts = []
        installed_packages = set(dep_info.name for dep_info in dependencies.values() 
                               if dep_info.installed_version)
        
        for pkg_name, conflicting_packages in self.known_conflicts.items():
            if pkg_name in installed_packages:
                for conflict_pkg in conflicting_packages:
                    if conflict_pkg in installed_packages:
                        conflict_info = {
                            'type': 'package_conflict',
                            'primary_package': pkg_name,
                            'conflicting_package': conflict_pkg,
                            'description': f'{pkg_name} conflicts with {conflict_pkg}',
                            'severity': 'warning',
                            'recommendation': f'Consider removing {conflict_pkg} or {pkg_name}'
                        }
                        conflicts.append(conflict_info)
        
        return conflicts
    
    def _check_security_vulnerabilities(self, dependencies: Dict[str, DependencyInfo]) -> List[ValidationResult]:
        """检查安全漏洞"""
        results = []
        
        for pkg_name, vulnerable_versions in self.security_vulnerabilities.items():
            if pkg_name in dependencies:
                dep_info = dependencies[pkg_name]
                if dep_info.installed_version:
                    is_vulnerable = self._is_version_vulnerable(
                        dep_info.installed_version, vulnerable_versions
                    )
                    
                    if is_vulnerable:
                        result = ValidationResult(
                            package_name=pkg_name,
                            status='error',
                            message=f'Security vulnerability detected in version {dep_info.installed_version}',
                            details={
                                'vulnerability_info': vulnerable_versions,
                                'current_version': dep_info.installed_version,
                                'recommendation': 'Upgrade to latest version'
                            }
                        )
                        results.append(result)
        
        return results
    
    def _test_package_imports(self) -> List[ValidationResult]:
        """测试包导入"""
        results = []
        import_tests = {
            'fastapi': 'import fastapi; fastapi.FastAPI()',
            'sqlalchemy': 'import sqlalchemy; sqlalchemy.create_engine("sqlite:///:memory:")',
            'redis': 'import redis',
            'celery': 'import celery',
            'cryptography': 'from cryptography.fernet import Fernet; Fernet.generate_key()',
            'pydantic': 'import pydantic; pydantic.BaseModel',
        }
        
        python_exe = self.dependency_manager._get_venv_python_executable()
        
        for pkg_name, test_code in import_tests.items():
            try:
                cmd = [python_exe, "-c", test_code]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    validation_result = ValidationResult(
                        package_name=f"{pkg_name}_import",
                        status='success',
                        message='Import test passed',
                        details={'test_code': test_code}
                    )
                else:
                    validation_result = ValidationResult(
                        package_name=f"{pkg_name}_import",
                        status='error',
                        message=f'Import test failed: {result.stderr}',
                        details={'test_code': test_code, 'error': result.stderr}
                    )
                
                results.append(validation_result)
                
            except Exception as e:
                validation_result = ValidationResult(
                    package_name=f"{pkg_name}_import",
                    status='error',
                    message=f'Import test exception: {str(e)}',
                    details={'test_code': test_code, 'exception': str(e)}
                )
                results.append(validation_result)
        
        return results
    
    def _generate_recommendations(self, validation_results: List[ValidationResult], 
                                compatibility_checks: List[CompatibilityCheck],
                                conflicts: List[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于验证结果的建议
        error_count = sum(1 for r in validation_results if r.status == 'error')
        warning_count = sum(1 for r in validation_results if r.status == 'warning')
        
        if error_count > 0:
            recommendations.append(f"发现 {error_count} 个严重问题，建议立即修复")
        
        if warning_count > 0:
            recommendations.append(f"发现 {warning_count} 个警告，建议关注")
        
        # 基于兼容性检查的建议
        incompatible_count = sum(1 for c in compatibility_checks if not c.is_compatible)
        if incompatible_count > 0:
            recommendations.append(f"发现 {incompatible_count} 个版本不兼容问题，建议更新相关包")
        
        # 基于冲突的建议
        if conflicts:
            recommendations.append(f"发现 {len(conflicts)} 个包冲突，建议解决冲突")
        
        # 通用建议
        if not recommendations:
            recommendations.append("依赖状态良好，建议定期检查更新")
        
        return recommendations
    
    def _calculate_overall_status(self, validation_results: List[ValidationResult],
                                compatibility_checks: List[CompatibilityCheck],
                                conflicts: List[Dict[str, Any]]) -> str:
        """计算整体状态"""
        error_count = sum(1 for r in validation_results if r.status == 'error')
        warning_count = sum(1 for r in validation_results if r.status == 'warning')
        incompatible_count = sum(1 for c in compatibility_checks if not c.is_compatible)
        
        if error_count > 0 or incompatible_count > 0 or len(conflicts) > 0:
            return 'critical'
        elif warning_count > 0:
            return 'warning'
        else:
            return 'healthy'
    
    def _check_single_version_compatibility(self, installed: str, required: str) -> Tuple[bool, str, List[str]]:
        """检查单个版本兼容性"""
        notes = []
        
        try:
            if required == 'latest':
                return True, 'compatible', ['Latest version requirement']
            
            installed_ver = version.parse(installed)
            required_ver = version.parse(required)
            
            if installed_ver == required_ver:
                return True, 'exact', ['Exact version match']
            elif installed_ver > required_ver:
                if installed_ver.major == required_ver.major:
                    return True, 'compatible', ['Newer compatible version']
                else:
                    return False, 'warning', ['Major version difference']
            else:
                return False, 'incompatible', ['Older version installed']
                
        except Exception as e:
            return False, 'incompatible', [f'Version parsing error: {str(e)}']
    
    def _diagnose_environment_issues(self) -> List[Dict[str, Any]]:
        """诊断环境问题"""
        issues = []
        
        # 检查虚拟环境
        venv_info = self.dependency_manager.get_virtual_environment_info()
        if not venv_info:
            issues.append({
                'type': 'environment',
                'issue': 'Virtual environment not found',
                'severity': 'critical',
                'fix': 'Create virtual environment'
            })
        
        # 检查Python版本
        python_version = self.dependency_manager._get_python_version()
        if not self.dependency_manager._is_python_version_compatible(python_version):
            issues.append({
                'type': 'environment',
                'issue': f'Python version {python_version} not compatible',
                'severity': 'critical',
                'fix': 'Upgrade Python to 3.8+'
            })
        
        return issues
    
    def _find_missing_packages(self) -> List[Dict[str, Any]]:
        """查找缺失的包"""
        missing = []
        dependencies = self.dependency_manager.get_dependency_info()
        
        for pkg_name, dep_info in dependencies.items():
            if not dep_info.installed_version:
                missing.append({
                    'name': pkg_name,
                    'required_version': dep_info.version,
                    'is_critical': dep_info.is_critical,
                    'fix': f'pip install {pkg_name}=={dep_info.version}'
                })
        
        return missing
    
    def _find_version_conflicts(self) -> List[Dict[str, Any]]:
        """查找版本冲突"""
        conflicts = []
        compatibility_checks = self._check_version_compatibility(
            self.dependency_manager.get_dependency_info()
        )
        
        for check in compatibility_checks:
            if not check.is_compatible:
                conflicts.append({
                    'package': check.package_name,
                    'installed': check.installed_version,
                    'required': check.required_version,
                    'level': check.compatibility_level,
                    'fix': f'pip install {check.package_name}=={check.required_version}'
                })
        
        return conflicts
    
    def _find_import_failures(self) -> List[Dict[str, Any]]:
        """查找导入失败"""
        failures = []
        import_results = self._test_package_imports()
        
        for result in import_results:
            if result.status == 'error':
                failures.append({
                    'package': result.package_name,
                    'error': result.message,
                    'details': result.details
                })
        
        return failures
    
    def _find_security_issues(self) -> List[Dict[str, Any]]:
        """查找安全问题"""
        issues = []
        security_results = self._check_security_vulnerabilities(
            self.dependency_manager.get_dependency_info()
        )
        
        for result in security_results:
            if result.status == 'error':
                issues.append({
                    'package': result.package_name,
                    'issue': result.message,
                    'details': result.details
                })
        
        return issues
    
    def _find_performance_issues(self) -> List[Dict[str, Any]]:
        """查找性能问题"""
        issues = []
        dependencies = self.dependency_manager.get_dependency_info()
        
        # 检查是否有性能优化的包
        performance_packages = {
            'orjson': 'Fast JSON library',
            'ujson': 'Ultra fast JSON library',
            'cachetools': 'Caching utilities',
            'redis[hiredis]': 'High performance Redis client'
        }
        
        for pkg_name, description in performance_packages.items():
            base_name = pkg_name.split('[')[0]
            if base_name not in dependencies:
                issues.append({
                    'type': 'performance',
                    'package': pkg_name,
                    'issue': f'Missing performance package: {description}',
                    'severity': 'info',
                    'fix': f'Consider installing {pkg_name}'
                })
        
        return issues
    
    def _generate_fix_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        # 环境问题修复
        if diagnosis['environment_issues']:
            recommendations.append("修复环境问题：重新创建虚拟环境")
        
        # 缺失包修复
        if diagnosis['missing_packages']:
            recommendations.append("安装缺失的包：pip install -r requirements.txt")
        
        # 版本冲突修复
        if diagnosis['version_conflicts']:
            recommendations.append("解决版本冲突：更新到兼容版本")
        
        # 导入失败修复
        if diagnosis['import_failures']:
            recommendations.append("修复导入问题：检查包安装和依赖")
        
        # 安全问题修复
        if diagnosis['security_issues']:
            recommendations.append("修复安全漏洞：升级到安全版本")
        
        return recommendations
    
    def _is_version_vulnerable(self, installed_version: str, vulnerable_patterns: List[str]) -> bool:
        """检查版本是否有漏洞"""
        try:
            installed_ver = version.parse(installed_version)
            
            for pattern in vulnerable_patterns:
                if pattern.startswith('<'):
                    threshold = version.parse(pattern[1:])
                    if installed_ver < threshold:
                        return True
                elif pattern.startswith('<='):
                    threshold = version.parse(pattern[2:])
                    if installed_ver <= threshold:
                        return True
                elif pattern.startswith('=='):
                    threshold = version.parse(pattern[2:])
                    if installed_ver == threshold:
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _versions_match(self, installed: str, required: str) -> bool:
        """检查版本是否匹配"""
        if required == 'latest':
            return True
        
        try:
            return version.parse(installed) == version.parse(required)
        except:
            return False