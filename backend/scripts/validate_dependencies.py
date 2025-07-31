#!/usr/bin/env python3
"""
依赖验证脚本 - 命令行工具
用于检查和诊断Python依赖包问题
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from deployment.dependency_manager import DependencyManager
from deployment.dependency_validator import DependencyValidator


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('dependency_validation.log')
        ]
    )


def print_validation_summary(report):
    """打印验证摘要"""
    print("\n" + "="*60)
    print("依赖验证报告摘要")
    print("="*60)
    print(f"时间: {report.timestamp}")
    print(f"Python版本: {report.python_version}")
    print(f"虚拟环境: {report.virtual_env_path}")
    print(f"总包数: {report.total_packages}")
    print(f"关键包数: {report.critical_packages}")
    print(f"整体状态: {report.overall_status}")
    
    # 统计结果
    success_count = sum(1 for r in report.validation_results if r.status == 'success')
    warning_count = sum(1 for r in report.validation_results if r.status == 'warning')
    error_count = sum(1 for r in report.validation_results if r.status == 'error')
    
    print(f"\n验证结果统计:")
    print(f"  ✓ 成功: {success_count}")
    print(f"  ⚠ 警告: {warning_count}")
    print(f"  ✗ 错误: {error_count}")
    
    # 兼容性检查
    compatible_count = sum(1 for c in report.compatibility_checks if c.is_compatible)
    incompatible_count = len(report.compatibility_checks) - compatible_count
    
    print(f"\n兼容性检查:")
    print(f"  ✓ 兼容: {compatible_count}")
    print(f"  ✗ 不兼容: {incompatible_count}")
    
    # 冲突
    if report.conflicts:
        print(f"\n发现冲突: {len(report.conflicts)}")
        for conflict in report.conflicts:
            print(f"  - {conflict.get('description', 'Unknown conflict')}")
    
    # 建议
    if report.recommendations:
        print(f"\n建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")


def print_detailed_results(report):
    """打印详细结果"""
    print("\n" + "="*60)
    print("详细验证结果")
    print("="*60)
    
    # 按状态分组显示
    for status in ['error', 'warning', 'success']:
        results = [r for r in report.validation_results if r.status == status]
        if results:
            status_symbol = {'error': '✗', 'warning': '⚠', 'success': '✓'}[status]
            print(f"\n{status_symbol} {status.upper()} ({len(results)}):")
            
            for result in results:
                print(f"  - {result.package_name}: {result.message}")
                if result.details and status != 'success':
                    for key, value in result.details.items():
                        print(f"    {key}: {value}")


def print_compatibility_details(report):
    """打印兼容性详情"""
    if not report.compatibility_checks:
        return
    
    print("\n" + "="*60)
    print("版本兼容性详情")
    print("="*60)
    
    for check in report.compatibility_checks:
        symbol = "✓" if check.is_compatible else "✗"
        print(f"{symbol} {check.package_name}:")
        print(f"  已安装: {check.installed_version}")
        print(f"  要求: {check.required_version}")
        print(f"  兼容级别: {check.compatibility_level}")
        
        if check.notes:
            for note in check.notes:
                print(f"  注意: {note}")
        print()


def validate_dependencies(args):
    """执行依赖验证"""
    try:
        # 初始化依赖管理器
        manager = DependencyManager(
            requirements_file=args.requirements,
            venv_path=args.venv,
            project_root=args.project_root
        )
        
        # 初始化验证器
        validator = DependencyValidator(manager)
        
        print("开始依赖验证...")
        
        # 执行验证
        report = validator.validate_all_dependencies()
        
        # 显示结果
        print_validation_summary(report)
        
        if args.detailed:
            print_detailed_results(report)
            print_compatibility_details(report)
        
        # 保存报告
        if args.output:
            validator.save_report_to_file(report, args.output)
            print(f"\n详细报告已保存到: {args.output}")
        
        # 返回退出码
        if report.overall_status == 'critical':
            return 1
        elif report.overall_status == 'warning':
            return 2 if args.strict else 0
        else:
            return 0
            
    except Exception as e:
        logging.error(f"验证过程异常: {str(e)}")
        return 1


def diagnose_issues(args):
    """诊断依赖问题"""
    try:
        # 初始化依赖管理器
        manager = DependencyManager(
            requirements_file=args.requirements,
            venv_path=args.venv,
            project_root=args.project_root
        )
        
        # 初始化验证器
        validator = DependencyValidator(manager)
        
        print("开始诊断依赖问题...")
        
        # 执行诊断
        diagnosis = validator.diagnose_dependency_issues()
        
        # 显示诊断结果
        print("\n" + "="*60)
        print("依赖问题诊断结果")
        print("="*60)
        
        for category, issues in diagnosis.items():
            if category == 'recommendations':
                continue
                
            if issues:
                print(f"\n{category.replace('_', ' ').title()}:")
                for issue in issues:
                    if isinstance(issue, dict):
                        print(f"  - {issue.get('issue', issue.get('name', str(issue)))}")
                        if 'fix' in issue:
                            print(f"    修复: {issue['fix']}")
                    else:
                        print(f"  - {issue}")
        
        # 显示建议
        if diagnosis.get('recommendations'):
            print(f"\n修复建议:")
            for i, rec in enumerate(diagnosis['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # 保存诊断结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(diagnosis, f, indent=2, ensure_ascii=False)
            print(f"\n诊断结果已保存到: {args.output}")
        
        return 0
        
    except Exception as e:
        logging.error(f"诊断过程异常: {str(e)}")
        return 1


def check_package(args):
    """检查单个包"""
    try:
        # 初始化依赖管理器
        manager = DependencyManager(
            requirements_file=args.requirements,
            venv_path=args.venv,
            project_root=args.project_root
        )
        
        # 初始化验证器
        validator = DependencyValidator(manager)
        
        print(f"检查包: {args.package}")
        
        # 检查包兼容性
        check_result = validator.check_package_compatibility(args.package)
        
        print(f"\n包名: {check_result.package_name}")
        print(f"已安装版本: {check_result.installed_version}")
        print(f"要求版本: {check_result.required_version}")
        print(f"兼容性: {'✓' if check_result.is_compatible else '✗'}")
        print(f"兼容级别: {check_result.compatibility_level}")
        
        if check_result.notes:
            print("注意事项:")
            for note in check_result.notes:
                print(f"  - {note}")
        
        return 0 if check_result.is_compatible else 1
        
    except Exception as e:
        logging.error(f"检查包异常: {str(e)}")
        return 1


def installation_report(args):
    """生成安装报告"""
    try:
        # 初始化依赖管理器
        manager = DependencyManager(
            requirements_file=args.requirements,
            venv_path=args.venv,
            project_root=args.project_root
        )
        
        # 初始化验证器
        validator = DependencyValidator(manager)
        
        print("生成安装状态报告...")
        
        # 生成报告
        report = validator.generate_installation_report()
        
        # 显示摘要
        summary = report['summary']
        print(f"\n安装状态摘要:")
        print(f"  要求包数: {summary['total_required']}")
        print(f"  已安装包数: {summary['total_installed']}")
        print(f"  关键包数: {summary['critical_packages']}")
        print(f"  生成时间: {summary['timestamp']}")
        
        # 显示详情
        if report['missing_packages']:
            print(f"\n缺失包 ({len(report['missing_packages'])}):")
            for pkg in report['missing_packages']:
                critical = " (关键)" if pkg['is_critical'] else ""
                print(f"  - {pkg['name']} {pkg['required_version']}{critical}")
        
        if report['version_mismatches']:
            print(f"\n版本不匹配 ({len(report['version_mismatches'])}):")
            for pkg in report['version_mismatches']:
                print(f"  - {pkg['name']}: {pkg['installed_version']} != {pkg['required_version']}")
        
        if report['extra_packages']:
            print(f"\n额外包 ({len(report['extra_packages'])}):")
            for pkg in report['extra_packages'][:10]:  # 只显示前10个
                print(f"  - {pkg['name']} {pkg['installed_version']}")
            if len(report['extra_packages']) > 10:
                print(f"  ... 还有 {len(report['extra_packages']) - 10} 个")
        
        # 保存报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n详细报告已保存到: {args.output}")
        
        return 0
        
    except Exception as e:
        logging.error(f"生成报告异常: {str(e)}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='依赖验证和诊断工具')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--requirements', '-r', default='requirements-prod.txt', 
                       help='Requirements文件路径')
    parser.add_argument('--venv', default='venv', help='虚拟环境路径')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--output', '-o', help='输出文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 验证命令
    validate_parser = subparsers.add_parser('validate', help='验证依赖')
    validate_parser.add_argument('--detailed', action='store_true', help='显示详细结果')
    validate_parser.add_argument('--strict', action='store_true', help='严格模式，警告也返回错误码')
    
    # 诊断命令
    diagnose_parser = subparsers.add_parser('diagnose', help='诊断问题')
    
    # 检查单个包命令
    check_parser = subparsers.add_parser('check', help='检查单个包')
    check_parser.add_argument('package', help='包名')
    
    # 安装报告命令
    report_parser = subparsers.add_parser('report', help='生成安装报告')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 设置默认命令
    if not args.command:
        args.command = 'validate'
        args.detailed = False
        args.strict = False
    
    # 执行命令
    try:
        if args.command == 'validate':
            return validate_dependencies(args)
        elif args.command == 'diagnose':
            return diagnose_issues(args)
        elif args.command == 'check':
            return check_package(args)
        elif args.command == 'report':
            return installation_report(args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        return 1
    except Exception as e:
        logging.error(f"未处理的异常: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())