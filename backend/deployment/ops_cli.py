#!/usr/bin/env python3
"""
运维工具命令行接口
提供统一的命令行接口来使用系统监控、故障诊断和自动化运维工具
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from system_monitor import SystemMonitor
from fault_diagnosis import FaultDiagnosisEngine
from automated_operations import AutomatedOperations

def format_json_output(data: Dict[str, Any], indent: int = 2) -> str:
    """格式化JSON输出"""
    return json.dumps(data, indent=indent, ensure_ascii=False)

def print_separator(title: str = ""):
    """打印分隔符"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)

def monitor_command(args):
    """监控命令"""
    try:
        monitor = SystemMonitor(args.config)
        
        if args.report:
            print("正在生成系统监控报告...")
            report = monitor.generate_report()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(format_json_output(report))
                print(f"监控报告已保存到: {args.output}")
            else:
                print_separator("系统监控报告")
                
                # 显示摘要信息
                summary = report.get("summary", {})
                print(f"系统健康状态: {summary.get('system_health', 'unknown')}")
                print(f"性能评分: {summary.get('performance_score', 0)}")
                print(f"运行服务: {summary.get('running_services', 0)}/{summary.get('total_services', 0)}")
                print(f"活跃告警: {summary.get('active_alerts', 0)}")
                
                # 显示系统指标
                metrics = report.get("system_metrics", {})
                if metrics:
                    print_separator("系统指标")
                    print(f"CPU使用率: {metrics.get('cpu_percent', 0):.1f}%")
                    print(f"内存使用率: {metrics.get('memory_percent', 0):.1f}%")
                    print(f"系统负载: {', '.join(f'{load:.2f}' for load in metrics.get('load_average', []))}")
                    
                    disk_usage = metrics.get('disk_usage', {})
                    if disk_usage:
                        print("磁盘使用率:")
                        for path, usage in disk_usage.items():
                            print(f"  {path}: {usage:.1f}%")
                
                # 显示服务状态
                services = report.get("services", [])
                if services:
                    print_separator("服务状态")
                    for service in services:
                        status = service.get('status', 'unknown')
                        name = service.get('name', 'unknown')
                        print(f"  {name}: {status}")
                        if service.get('response_time'):
                            print(f"    响应时间: {service['response_time']:.3f}s")
                
                # 显示异常
                anomalies = report.get("anomalies", [])
                if anomalies:
                    print_separator("检测到的异常")
                    for anomaly in anomalies:
                        print(f"  [{anomaly.get('severity', 'unknown').upper()}] {anomaly.get('rule_name', 'unknown')}")
                        print(f"    当前值: {anomaly.get('current_value', 'unknown')}")
                        print(f"    阈值: {anomaly.get('threshold', 'unknown')}")
        
        elif args.daemon:
            print("启动系统监控守护进程...")
            monitor.start_monitoring()
            try:
                print("监控已启动，按 Ctrl+C 停止")
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n正在停止监控...")
                monitor.stop_monitoring()
                print("监控已停止")
        
        else:
            print("请指定 --report 或 --daemon 参数")
            return False
        
        return True
        
    except Exception as e:
        print(f"监控命令执行失败: {e}")
        return False

def diagnose_command(args):
    """诊断命令"""
    try:
        engine = FaultDiagnosisEngine(args.config)
        
        if args.report:
            print("正在执行系统诊断...")
            report = engine.generate_diagnosis_report()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(format_json_output(report))
                print(f"诊断报告已保存到: {args.output}")
            else:
                print_separator("故障诊断报告")
                
                # 显示摘要
                summary = report.get("summary", {})
                print(f"总问题数: {summary.get('total_issues', 0)}")
                print(f"关键问题: {summary.get('critical_issues', 0)}")
                print(f"警告问题: {summary.get('warning_issues', 0)}")
                print(f"可自动修复: {summary.get('auto_fixable_issues', 0)}")
                print(f"系统健康评分: {summary.get('system_health_score', 0)}")
                
                # 显示问题分类
                categories = summary.get('categories', {})
                if categories:
                    print("\n问题分类:")
                    for category, count in categories.items():
                        print(f"  {category}: {count}")
                
                # 显示诊断结果
                results = report.get("diagnosis_results", [])
                if results:
                    print_separator("诊断结果")
                    for result in results:
                        severity = result.get('severity', 'unknown').upper()
                        title = result.get('title', 'unknown')
                        description = result.get('description', '')
                        
                        print(f"[{severity}] {title}")
                        if description:
                            print(f"  描述: {description}")
                        
                        recommendations = result.get('recommendations', [])
                        if recommendations:
                            print("  建议:")
                            for rec in recommendations[:3]:  # 只显示前3个建议
                                print(f"    - {rec}")
                        print()
                
                # 显示总体建议
                recommendations = report.get("recommendations", [])
                if recommendations:
                    print_separator("总体建议")
                    for rec in recommendations:
                        print(f"- {rec}")
        
        elif args.analyze_logs:
            print(f"正在分析日志文件: {args.analyze_logs}")
            result = engine.analyze_logs(args.analyze_logs, hours=args.hours or 24)
            
            print_separator("日志分析结果")
            print(f"日志文件: {result.log_file}")
            print(f"错误数量: {result.error_count}")
            print(f"警告数量: {result.warning_count}")
            print(f"分析摘要: {result.analysis_summary}")
            
            if result.critical_patterns:
                print("\n关键模式:")
                for pattern in result.critical_patterns[:5]:
                    print(f"  {pattern['title']} (匹配 {pattern['match_count']} 次)")
            
            if result.frequent_errors:
                print("\n频繁错误:")
                for error in result.frequent_errors[:5]:
                    print(f"  出现 {error['count']} 次: {error['error_pattern'][:100]}...")
        
        elif args.auto_fix:
            print(f"正在尝试自动修复问题: {args.auto_fix}")
            success = engine.auto_fix_issue(args.auto_fix)
            print(f"自动修复 {'成功' if success else '失败'}")
        
        else:
            print("请指定 --report、--analyze-logs 或 --auto-fix 参数")
            return False
        
        return True
        
    except Exception as e:
        print(f"诊断命令执行失败: {e}")
        return False

def ops_command(args):
    """运维命令"""
    try:
        ops = AutomatedOperations(args.config)
        
        if args.status:
            print("正在获取运维状态...")
            status = ops.get_status()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(format_json_output(status))
                print(f"状态信息已保存到: {args.output}")
            else:
                print_separator("自动化运维状态")
                print(f"调度器运行状态: {'运行中' if status.get('scheduler_running') else '已停止'}")
                print(f"维护窗口状态: {'是' if status.get('maintenance_window') else '否'}")
                
                tasks = status.get('tasks', [])
                if tasks:
                    print_separator("任务状态")
                    for task in tasks:
                        name = task.get('name', 'unknown')
                        enabled = '启用' if task.get('enabled') else '禁用'
                        success_count = task.get('success_count', 0)
                        failure_count = task.get('failure_count', 0)
                        last_run = task.get('last_run', '从未运行')
                        
                        print(f"  {name}: {enabled}")
                        print(f"    成功: {success_count}, 失败: {failure_count}")
                        print(f"    最后运行: {last_run}")
        
        elif args.task:
            print(f"正在执行任务: {args.task}")
            success = ops.execute_task(args.task)
            print(f"任务执行 {'成功' if success else '失败'}")
        
        elif args.daemon:
            print("启动自动化运维守护进程...")
            ops.start_scheduler()
            try:
                print("自动化运维已启动，按 Ctrl+C 停止")
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n正在停止自动化运维...")
                ops.stop_scheduler()
                print("自动化运维已停止")
        
        else:
            print("请指定 --status、--task 或 --daemon 参数")
            return False
        
        return True
        
    except Exception as e:
        print(f"运维命令执行失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Lawsker运维工具集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 生成系统监控报告
  python ops_cli.py monitor --report
  
  # 启动监控守护进程
  python ops_cli.py monitor --daemon
  
  # 执行故障诊断
  python ops_cli.py diagnose --report
  
  # 分析日志文件
  python ops_cli.py diagnose --analyze-logs /var/log/nginx/error.log
  
  # 自动修复问题
  python ops_cli.py diagnose --auto-fix high_memory_usage
  
  # 查看运维状态
  python ops_cli.py ops --status
  
  # 执行指定任务
  python ops_cli.py ops --task system_monitoring
  
  # 启动自动化运维
  python ops_cli.py ops --daemon
        """
    )
    
    # 全局参数
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 监控命令
    monitor_parser = subparsers.add_parser("monitor", help="系统监控")
    monitor_group = monitor_parser.add_mutually_exclusive_group(required=True)
    monitor_group.add_argument("--report", action="store_true", help="生成监控报告")
    monitor_group.add_argument("--daemon", action="store_true", help="启动监控守护进程")
    
    # 诊断命令
    diagnose_parser = subparsers.add_parser("diagnose", help="故障诊断")
    diagnose_group = diagnose_parser.add_mutually_exclusive_group(required=True)
    diagnose_group.add_argument("--report", action="store_true", help="生成诊断报告")
    diagnose_group.add_argument("--analyze-logs", help="分析指定日志文件")
    diagnose_group.add_argument("--auto-fix", help="自动修复指定问题ID")
    diagnose_parser.add_argument("--hours", type=int, help="日志分析时间窗口（小时）")
    
    # 运维命令
    ops_parser = subparsers.add_parser("ops", help="自动化运维")
    ops_group = ops_parser.add_mutually_exclusive_group(required=True)
    ops_group.add_argument("--status", action="store_true", help="显示运维状态")
    ops_group.add_argument("--task", help="执行指定任务")
    ops_group.add_argument("--daemon", action="store_true", help="启动运维守护进程")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 设置日志级别
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        success = False
        
        if args.command == "monitor":
            success = monitor_command(args)
        elif args.command == "diagnose":
            success = diagnose_command(args)
        elif args.command == "ops":
            success = ops_command(args)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()