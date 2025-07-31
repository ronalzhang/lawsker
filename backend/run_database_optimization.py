#!/usr/bin/env python3
"""
数据库性能调优脚本
执行慢查询分析、配置优化、监控设置等
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.database_optimizer import database_optimizer, run_database_optimization
from app.services.database_monitor import database_monitor, start_database_monitoring

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🗄️  LAWSKER数据库性能调优")
    print("=" * 60)
    print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def print_section_header(title: str):
    """打印章节标题"""
    print(f"\n{'='*20} {title} {'='*20}")

def print_slow_queries(slow_queries):
    """打印慢查询分析结果"""
    if not slow_queries:
        print("✅ 未发现慢查询")
        return
    
    print(f"⚠️  发现 {len(slow_queries)} 个慢查询:")
    print("-" * 60)
    
    for i, sq in enumerate(slow_queries[:10], 1):  # 只显示前10个
        query_preview = sq["query"][:100] + "..." if len(sq["query"]) > 100 else sq["query"]
        print(f"{i}. 执行时间: {sq['duration']:.2f}s")
        print(f"   查询: {query_preview}")
        print(f"   时间: {sq['timestamp']}")
        print()

def print_optimization_suggestions(suggestions):
    """打印优化建议"""
    if not suggestions:
        print("✅ 暂无优化建议")
        return
    
    # 索引建议
    index_recommendations = suggestions.get("index_recommendations", [])
    if index_recommendations:
        print(f"📊 索引优化建议 ({len(index_recommendations)} 项):")
        for i, rec in enumerate(index_recommendations, 1):
            print(f"  {i}. 表: {rec['table']}")
            print(f"     字段: {', '.join(rec['columns'])}")
            print(f"     SQL: {rec['index_sql']}")
            print(f"     原因: {rec['reason']}")
            print()
    
    # 查询重写建议
    query_rewrites = suggestions.get("query_rewrites", [])
    if query_rewrites:
        print(f"🔄 查询重写建议 ({len(query_rewrites)} 项):")
        for i, rewrite in enumerate(query_rewrites, 1):
            print(f"  {i}. 问题: {rewrite['issue']}")
            print(f"     建议: {rewrite['suggestion']}")
            print(f"     原因: {rewrite['reason']}")
            print()

def print_database_metrics(metrics):
    """打印数据库指标"""
    if not metrics:
        print("❌ 无法获取数据库指标")
        return
    
    print("📊 当前数据库指标:")
    print(f"  🔗 活跃连接: {metrics['connections_active']}")
    print(f"  🔗 总连接数: {metrics['connections_total']}")
    print(f"  ⚡ 每秒查询: {metrics['queries_per_second']:.2f}")
    print(f"  💾 缓存命中率: {metrics['cache_hit_ratio']:.2f}%")
    print(f"  💿 磁盘使用: {metrics['disk_usage_gb']:.2f} GB")
    print(f"  🧠 内存使用: {metrics['memory_usage_mb']:.2f} MB")
    print(f"  🖥️  CPU使用率: {metrics['cpu_usage_percent']:.2f}%")

def print_configuration_recommendations(config_rec):
    """打印配置建议"""
    if config_rec.get("status") != "success":
        print(f"❌ 配置优化失败: {config_rec.get('message', 'Unknown error')}")
        return
    
    recommendations = config_rec.get("recommendations", {})
    system_info = config_rec.get("system_info", {})
    
    print("⚙️  系统信息:")
    print(f"  💾 内存: {system_info.get('memory_gb', 0):.1f} GB")
    print(f"  🖥️  CPU核心: {system_info.get('cpu_count', 0)}")
    
    print("\n📝 PostgreSQL配置建议:")
    for param, value in recommendations.items():
        print(f"  {param} = {value}")

def save_optimization_report(results: dict):
    """保存优化报告"""
    try:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"database_optimization_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 优化报告已保存: {report_file}")
        
        # 生成PostgreSQL配置文件
        config_rec = results.get("configuration_recommendations", {})
        if config_rec.get("status") == "success":
            config_file = reports_dir / f"postgresql_optimized_{timestamp}.conf"
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(config_rec.get("config_content", ""))
            print(f"⚙️  PostgreSQL配置文件已生成: {config_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存报告失败: {str(e)}")
        return False

def generate_optimization_summary(results: dict):
    """生成优化摘要"""
    print("\n" + "="*60)
    print("📋 优化摘要")
    print("="*60)
    
    # 慢查询摘要
    slow_queries = results.get("slow_queries", [])
    print(f"🐌 慢查询: {len(slow_queries)} 个")
    
    # 优化建议摘要
    suggestions = results.get("optimization_suggestions", {})
    index_count = len(suggestions.get("index_recommendations", []))
    rewrite_count = len(suggestions.get("query_rewrites", []))
    print(f"📊 索引建议: {index_count} 个")
    print(f"🔄 查询重写建议: {rewrite_count} 个")
    
    # 配置优化摘要
    config_status = results.get("configuration_recommendations", {}).get("status")
    print(f"⚙️  配置优化: {'✅ 成功' if config_status == 'success' else '❌ 失败'}")
    
    # 读写分离摘要
    rw_status = results.get("read_write_splitting", {}).get("status")
    print(f"🔄 读写分离: {'✅ 已配置' if rw_status == 'success' else '⚠️  需要配置'}")
    
    # 监控设置摘要
    monitor_status = results.get("monitoring_setup", {}).get("status")
    print(f"📊 监控告警: {'✅ 已设置' if monitor_status == 'success' else '⚠️  需要设置'}")
    
    # 性能指标摘要
    metrics = results.get("database_metrics", {})
    if metrics:
        cache_hit_ratio = metrics.get("cache_hit_ratio", 0)
        connections_active = metrics.get("connections_active", 0)
        connections_total = metrics.get("connections_total", 1)
        connection_usage = (connections_active / connections_total) * 100
        
        print(f"\n📈 关键指标:")
        print(f"  💾 缓存命中率: {cache_hit_ratio:.1f}%")
        print(f"  🔗 连接使用率: {connection_usage:.1f}%")
        print(f"  ⚡ QPS: {metrics.get('queries_per_second', 0):.1f}")

def print_next_steps():
    """打印后续步骤"""
    print("\n" + "="*60)
    print("📋 后续步骤建议")
    print("="*60)
    print("1. 📊 审查生成的PostgreSQL配置文件")
    print("2. 🔧 在测试环境中应用配置更改")
    print("3. 📈 执行性能测试验证改进效果")
    print("4. 🗄️  根据索引建议创建数据库索引")
    print("5. 🔄 重写识别出的慢查询")
    print("6. 📊 启动数据库监控服务")
    print("7. ⚠️  设置告警通知渠道")
    print("8. 📅 定期运行性能分析")

async def run_interactive_optimization():
    """运行交互式优化"""
    print("🚀 开始数据库性能分析...")
    
    try:
        # 运行完整的性能分析
        results = await run_database_optimization()
        
        if "error" in results:
            print(f"❌ 性能分析失败: {results['error']}")
            return False
        
        # 显示慢查询分析结果
        print_section_header("慢查询分析")
        print_slow_queries(results.get("slow_queries", []))
        
        # 显示优化建议
        print_section_header("优化建议")
        print_optimization_suggestions(results.get("optimization_suggestions", {}))
        
        # 显示数据库指标
        print_section_header("数据库指标")
        print_database_metrics(results.get("database_metrics", {}))
        
        # 显示配置建议
        print_section_header("配置优化")
        print_configuration_recommendations(results.get("configuration_recommendations", {}))
        
        # 保存报告
        print_section_header("报告生成")
        save_optimization_report(results)
        
        # 生成摘要
        generate_optimization_summary(results)
        
        # 询问是否启动监控
        print_section_header("监控服务")
        response = input("是否启动数据库监控服务? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            print("🚀 启动数据库监控服务...")
            # 在后台启动监控（实际部署时应该使用进程管理器）
            asyncio.create_task(start_database_monitoring())
            print("✅ 数据库监控服务已启动")
        else:
            print("ℹ️  可以稍后手动启动监控服务")
        
        # 显示后续步骤
        print_next_steps()
        
        return True
        
    except Exception as e:
        print(f"❌ 优化过程中发生错误: {str(e)}")
        return False

async def run_quick_analysis():
    """运行快速分析"""
    print("⚡ 运行快速数据库分析...")
    
    try:
        # 只分析慢查询和基础指标
        slow_queries = await database_optimizer.analyze_slow_queries(hours=1)
        metrics = await database_optimizer.collect_database_metrics()
        
        print_section_header("快速分析结果")
        
        # 转换慢查询格式
        slow_queries_dict = [
            {
                "query": sq.query,
                "duration": sq.duration,
                "timestamp": sq.timestamp.isoformat()
            }
            for sq in slow_queries
        ]
        
        print_slow_queries(slow_queries_dict)
        
        # 转换指标格式
        metrics_dict = {
            "connections_active": metrics.connections_active,
            "connections_total": metrics.connections_total,
            "queries_per_second": metrics.queries_per_second,
            "cache_hit_ratio": metrics.cache_hit_ratio,
            "disk_usage_gb": metrics.disk_usage_gb,
            "memory_usage_mb": metrics.memory_usage_mb,
            "cpu_usage_percent": metrics.cpu_usage_percent
        }
        
        print_database_metrics(metrics_dict)
        
        return True
        
    except Exception as e:
        print(f"❌ 快速分析失败: {str(e)}")
        return False

def show_help():
    """显示帮助信息"""
    print("数据库性能调优工具")
    print("\n用法:")
    print("  python run_database_optimization.py [选项]")
    print("\n选项:")
    print("  --full, -f     运行完整的性能分析和优化")
    print("  --quick, -q    运行快速分析")
    print("  --monitor, -m  启动监控服务")
    print("  --help, -h     显示此帮助信息")
    print("\n示例:")
    print("  python run_database_optimization.py --full")
    print("  python run_database_optimization.py --quick")

async def main():
    """主函数"""
    print_banner()
    
    # 解析命令行参数
    args = sys.argv[1:]
    
    if not args or "--help" in args or "-h" in args:
        show_help()
        return
    
    try:
        if "--full" in args or "-f" in args:
            success = await run_interactive_optimization()
        elif "--quick" in args or "-q" in args:
            success = await run_quick_analysis()
        elif "--monitor" in args or "-m" in args:
            print("🚀 启动数据库监控服务...")
            await start_database_monitoring()
            success = True
        else:
            print("❌ 未知选项，使用 --help 查看帮助")
            success = False
        
        if success:
            print("\n✅ 数据库优化完成")
            sys.exit(0)
        else:
            print("\n❌ 数据库优化失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())