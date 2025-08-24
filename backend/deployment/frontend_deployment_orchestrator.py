#!/usr/bin/env python3
"""
前端部署编排器 - 整合前端构建、TypeScript修复和静态文件部署
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from .frontend_builder import FrontendBuilder, FrontendProject, create_default_projects
from .typescript_fixer import TypeScriptFixer
from .static_deployment_manager import StaticDeploymentManager, StaticDeployment, create_default_deployments


class FrontendDeploymentOrchestrator:
    """前端部署编排器"""
    
    def __init__(self, base_path: str = "/opt/lawsker"):
        self.base_path = Path(base_path)
        self.logger = self._setup_logger()
        
        # 初始化组件
        self.frontend_builder = None
        self.deployment_manager = StaticDeploymentManager(str(self.base_path))
        
        # 默认配置
        self.projects = create_default_projects()
        self.deployments = create_default_deployments()
    
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
    
    def initialize(self, projects: Optional[List[FrontendProject]] = None, 
                  deployments: Optional[List[StaticDeployment]] = None) -> bool:
        """初始化编排器"""
        try:
            if projects:
                self.projects = projects
            if deployments:
                self.deployments = deployments
            
            # 初始化前端构建器
            self.frontend_builder = FrontendBuilder(self.projects, str(self.base_path))
            
            self.logger.info("前端部署编排器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False
    
    def run_complete_deployment(self) -> Dict[str, any]:
        """运行完整的前端部署流程"""
        self.logger.info("开始完整的前端部署流程...")
        
        deployment_report = {
            "start_time": datetime.now().isoformat(),
            "phases": [],
            "projects": {},
            "overall_success": False,
            "summary": {
                "total_projects": len(self.projects),
                "successful_builds": 0,
                "successful_deployments": 0,
                "typescript_fixes": 0,
                "errors": []
            }
        }
        
        try:
            # 阶段1: 环境检查
            env_check_result = self._check_environment()
            deployment_report["phases"].append({
                "phase": "environment_check",
                "success": env_check_result["success"],
                "message": env_check_result["message"],
                "details": env_check_result
            })
            
            if not env_check_result["success"]:
                deployment_report["summary"]["errors"].append("环境检查失败")
                return deployment_report
            
            # 阶段2: TypeScript错误修复
            ts_fix_result = self._fix_typescript_errors()
            deployment_report["phases"].append({
                "phase": "typescript_fixes",
                "success": ts_fix_result["success"],
                "message": ts_fix_result["message"],
                "details": ts_fix_result
            })
            
            deployment_report["summary"]["typescript_fixes"] = ts_fix_result.get("projects_fixed", 0)
            
            # 阶段3: 项目构建
            build_result = self._build_all_projects()
            deployment_report["phases"].append({
                "phase": "project_builds",
                "success": build_result["success"],
                "message": build_result["message"],
                "details": build_result
            })
            
            deployment_report["summary"]["successful_builds"] = build_result.get("successful_builds", 0)
            deployment_report["projects"].update(build_result.get("project_results", {}))
            
            # 阶段4: 静态文件部署
            deploy_result = self._deploy_static_files()
            deployment_report["phases"].append({
                "phase": "static_deployment",
                "success": deploy_result["success"],
                "message": deploy_result["message"],
                "details": deploy_result
            })
            
            deployment_report["summary"]["successful_deployments"] = deploy_result.get("successful_deployments", 0)
            
            # 阶段5: 部署验证
            verification_result = self._verify_deployments()
            deployment_report["phases"].append({
                "phase": "deployment_verification",
                "success": verification_result["success"],
                "message": verification_result["message"],
                "details": verification_result
            })
            
            # 计算整体成功状态
            deployment_report["overall_success"] = all(
                phase["success"] for phase in deployment_report["phases"]
            )
            
            # 生成摘要
            if deployment_report["overall_success"]:
                deployment_report["summary"]["message"] = "前端部署完全成功"
            else:
                failed_phases = [phase["phase"] for phase in deployment_report["phases"] if not phase["success"]]
                deployment_report["summary"]["message"] = f"部分阶段失败: {', '.join(failed_phases)}"
                deployment_report["summary"]["errors"].extend(failed_phases)
            
        except Exception as e:
            deployment_report["summary"]["errors"].append(f"部署流程异常: {str(e)}")
            self.logger.error(f"部署流程异常: {e}")
        
        finally:
            deployment_report["end_time"] = datetime.now().isoformat()
            duration = datetime.fromisoformat(deployment_report["end_time"]) - datetime.fromisoformat(deployment_report["start_time"])
            deployment_report["duration_seconds"] = duration.total_seconds()
        
        return deployment_report
    
    def _check_environment(self) -> Dict[str, any]:
        """检查部署环境"""
        self.logger.info("检查部署环境...")
        
        result = {
            "success": False,
            "message": "",
            "checks": {}
        }
        
        try:
            # 检查Node.js环境
            if self.frontend_builder:
                node_check = self.frontend_builder.check_node_environment()
                result["checks"]["nodejs"] = node_check
            else:
                result["checks"]["nodejs"] = False
            
            # 检查项目路径
            project_paths_exist = []
            for project in self.projects:
                project_path = self.base_path / project.path
                exists = project_path.exists()
                project_paths_exist.append(exists)
                result["checks"][f"project_{project.name}_exists"] = exists
            
            # 检查部署目标路径权限
            deployment_paths_writable = []
            for deployment in self.deployments:
                target_path = Path(deployment.target_path)
                try:
                    target_path.mkdir(parents=True, exist_ok=True)
                    writable = os.access(target_path, os.W_OK)
                    deployment_paths_writable.append(writable)
                    result["checks"][f"deployment_{deployment.name}_writable"] = writable
                except Exception:
                    deployment_paths_writable.append(False)
                    result["checks"][f"deployment_{deployment.name}_writable"] = False
            
            # 检查Nginx配置目录
            nginx_config_writable = os.access("/etc/nginx/sites-available", os.W_OK)
            result["checks"]["nginx_config_writable"] = nginx_config_writable
            
            # 整体成功判断
            result["success"] = (
                result["checks"]["nodejs"] and
                all(project_paths_exist) and
                all(deployment_paths_writable) and
                nginx_config_writable
            )
            
            if result["success"]:
                result["message"] = "环境检查通过"
            else:
                failed_checks = [k for k, v in result["checks"].items() if not v]
                result["message"] = f"环境检查失败: {', '.join(failed_checks)}"
            
        except Exception as e:
            result["message"] = f"环境检查异常: {str(e)}"
            self.logger.error(f"环境检查异常: {e}")
        
        return result
    
    def _fix_typescript_errors(self) -> Dict[str, any]:
        """修复所有项目的TypeScript错误"""
        self.logger.info("修复TypeScript错误...")
        
        result = {
            "success": True,
            "message": "",
            "projects_fixed": 0,
            "project_results": {}
        }
        
        try:
            for project in self.projects:
                project_path = self.base_path / project.path
                
                # 检查是否有TypeScript文件
                if self.frontend_builder and self.frontend_builder._has_typescript_files(project_path):
                    self.logger.info(f"修复项目 {project.name} 的TypeScript错误...")
                    
                    ts_fixer = TypeScriptFixer(str(project_path))
                    fix_result = ts_fixer.run_full_fix()
                    
                    result["project_results"][project.name] = fix_result
                    
                    if fix_result.get("success", False):
                        result["projects_fixed"] += 1
                        self.logger.info(f"项目 {project.name} TypeScript错误修复成功")
                    else:
                        self.logger.warning(f"项目 {project.name} TypeScript错误修复失败")
                        result["success"] = False
                else:
                    result["project_results"][project.name] = {
                        "success": True,
                        "message": "无TypeScript文件，跳过修复"
                    }
            
            if result["success"]:
                result["message"] = f"成功修复 {result['projects_fixed']} 个项目的TypeScript错误"
            else:
                result["message"] = "部分项目TypeScript错误修复失败"
            
        except Exception as e:
            result["success"] = False
            result["message"] = f"TypeScript错误修复异常: {str(e)}"
            self.logger.error(f"TypeScript错误修复异常: {e}")
        
        return result
    
    def _build_all_projects(self) -> Dict[str, any]:
        """构建所有前端项目"""
        self.logger.info("构建所有前端项目...")
        
        result = {
            "success": True,
            "message": "",
            "successful_builds": 0,
            "project_results": {}
        }
        
        try:
            if not self.frontend_builder:
                result["success"] = False
                result["message"] = "前端构建器未初始化"
                return result
            
            build_results = self.frontend_builder.build_all_projects()
            
            if "error" in build_results:
                result["success"] = False
                result["message"] = build_results["error"]
                return result
            
            for project_name, build_result in build_results.items():
                result["project_results"][project_name] = build_result
                
                if build_result.get("status") in ["success", "recovered"]:
                    result["successful_builds"] += 1
                else:
                    result["success"] = False
            
            if result["success"]:
                result["message"] = f"成功构建 {result['successful_builds']} 个项目"
            else:
                result["message"] = f"构建完成，{result['successful_builds']} 个成功，{len(self.projects) - result['successful_builds']} 个失败"
            
        except Exception as e:
            result["success"] = False
            result["message"] = f"项目构建异常: {str(e)}"
            self.logger.error(f"项目构建异常: {e}")
        
        return result
    
    def _deploy_static_files(self) -> Dict[str, any]:
        """部署静态文件"""
        self.logger.info("部署静态文件...")
        
        result = {
            "success": True,
            "message": "",
            "successful_deployments": 0,
            "deployment_results": {}
        }
        
        try:
            deploy_results = self.deployment_manager.deploy_multiple_sites(self.deployments)
            
            for deployment_name, deploy_result in deploy_results.items():
                result["deployment_results"][deployment_name] = {
                    "success": deploy_result.success,
                    "message": deploy_result.message,
                    "files_copied": deploy_result.files_copied,
                    "nginx_config_generated": deploy_result.nginx_config_generated,
                    "verification_passed": deploy_result.verification_passed,
                    "errors": deploy_result.errors
                }
                
                if deploy_result.success:
                    result["successful_deployments"] += 1
                else:
                    result["success"] = False
            
            if result["success"]:
                result["message"] = f"成功部署 {result['successful_deployments']} 个站点"
            else:
                result["message"] = f"部署完成，{result['successful_deployments']} 个成功，{len(self.deployments) - result['successful_deployments']} 个失败"
            
        except Exception as e:
            result["success"] = False
            result["message"] = f"静态文件部署异常: {str(e)}"
            self.logger.error(f"静态文件部署异常: {e}")
        
        return result
    
    def _verify_deployments(self) -> Dict[str, any]:
        """验证部署结果"""
        self.logger.info("验证部署结果...")
        
        result = {
            "success": True,
            "message": "",
            "verified_deployments": 0,
            "verification_results": {}
        }
        
        try:
            for deployment in self.deployments:
                status = self.deployment_manager.get_deployment_status(deployment)
                result["verification_results"][deployment.name] = status
                
                # 判断部署是否成功
                deployment_success = (
                    status.get("target_exists", False) and
                    status.get("nginx_config_exists", False) and
                    status.get("nginx_enabled", False) and
                    status.get("http_accessible", False)
                )
                
                if deployment.ssl_enabled:
                    deployment_success = deployment_success and status.get("https_accessible", False)
                
                if deployment_success:
                    result["verified_deployments"] += 1
                else:
                    result["success"] = False
            
            if result["success"]:
                result["message"] = f"成功验证 {result['verified_deployments']} 个部署"
            else:
                result["message"] = f"验证完成，{result['verified_deployments']} 个成功，{len(self.deployments) - result['verified_deployments']} 个失败"
            
        except Exception as e:
            result["success"] = False
            result["message"] = f"部署验证异常: {str(e)}"
            self.logger.error(f"部署验证异常: {e}")
        
        return result
    
    def generate_deployment_report(self, deployment_result: Dict[str, any]) -> str:
        """生成部署报告"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("前端部署报告")
        report_lines.append("=" * 60)
        report_lines.append(f"开始时间: {deployment_result.get('start_time', 'N/A')}")
        report_lines.append(f"结束时间: {deployment_result.get('end_time', 'N/A')}")
        report_lines.append(f"总耗时: {deployment_result.get('duration_seconds', 0):.2f} 秒")
        report_lines.append(f"整体状态: {'成功' if deployment_result.get('overall_success', False) else '失败'}")
        report_lines.append("")
        
        # 摘要信息
        summary = deployment_result.get("summary", {})
        report_lines.append("摘要信息:")
        report_lines.append(f"  总项目数: {summary.get('total_projects', 0)}")
        report_lines.append(f"  成功构建: {summary.get('successful_builds', 0)}")
        report_lines.append(f"  成功部署: {summary.get('successful_deployments', 0)}")
        report_lines.append(f"  TypeScript修复: {summary.get('typescript_fixes', 0)}")
        
        if summary.get("errors"):
            report_lines.append(f"  错误: {', '.join(summary['errors'])}")
        
        report_lines.append("")
        
        # 阶段详情
        report_lines.append("阶段详情:")
        for phase in deployment_result.get("phases", []):
            status = "✓" if phase.get("success", False) else "✗"
            report_lines.append(f"  {status} {phase.get('phase', 'Unknown')}: {phase.get('message', 'N/A')}")
        
        report_lines.append("")
        
        # 项目详情
        if deployment_result.get("projects"):
            report_lines.append("项目构建详情:")
            for project_name, project_result in deployment_result["projects"].items():
                status = "✓" if project_result.get("status") in ["success", "recovered"] else "✗"
                report_lines.append(f"  {status} {project_name}: {project_result.get('status', 'Unknown')}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def save_deployment_report(self, deployment_result: Dict[str, any], output_path: Optional[str] = None) -> str:
        """保存部署报告"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/opt/lawsker/logs/frontend_deployment_report_{timestamp}.txt"
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 生成文本报告
            text_report = self.generate_deployment_report(deployment_result)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_report)
            
            # 同时保存JSON格式
            json_path = output_file.with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(deployment_result, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"部署报告已保存: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"保存部署报告失败: {e}")
            return ""


def main():
    """主函数 - 运行完整的前端部署流程"""
    import sys
    
    # 解析命令行参数
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/opt/lawsker"
    
    # 创建编排器
    orchestrator = FrontendDeploymentOrchestrator(base_path)
    
    # 初始化
    if not orchestrator.initialize():
        print("编排器初始化失败")
        sys.exit(1)
    
    # 运行完整部署
    result = orchestrator.run_complete_deployment()
    
    # 生成并保存报告
    report_path = orchestrator.save_deployment_report(result)
    
    # 输出结果
    print(orchestrator.generate_deployment_report(result))
    
    if result.get("overall_success", False):
        print(f"\n前端部署成功完成！报告已保存至: {report_path}")
        sys.exit(0)
    else:
        print(f"\n前端部署部分失败，请查看报告: {report_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()