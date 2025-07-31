#!/usr/bin/env python3
"""
数据库配置系统测试脚本
测试DatabaseConfigurator和MigrationManager的功能
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from deployment.database_configurator import DatabaseConfigurator, DatabaseConfig
from deployment.migration_manager import MigrationManager

def test_database_configurator():
    """测试数据库配置器"""
    print("=" * 60)
    print("测试数据库配置器")
    print("=" * 60)
    
    # 创建测试配置
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        name="lawsker_test",
        user="lawsker_test_user",
        password="test_password_123",
        admin_user="postgres",
        admin_password="postgres"
    )
    
    # 创建配置器
    configurator = DatabaseConfigurator(config, project_root=".")
    
    try:
        # 1. 检查PostgreSQL服务
        print("\n1. 检查PostgreSQL服务状态...")
        service_running = configurator.check_postgresql_service()
        print(f"   服务状态: {'运行中' if service_running else '未运行'}")
        
        if not service_running:
            print("   ⚠️  PostgreSQL服务未运行，跳过后续测试")
            return False
        
        # 2. 优化连接池配置
        print("\n2. 优化连接池配置...")
        pool_config = configurator.optimize_connection_pool()
        print(f"   连接池配置: {json.dumps(pool_config, indent=2)}")
        
        # 3. 生成PostgreSQL配置
        print("\n3. 生成PostgreSQL配置...")
        pg_config = configurator.generate_postgresql_config()
        print(f"   配置长度: {len(pg_config)} 字符")
        print(f"   配置预览: {pg_config[:200]}...")
        
        # 4. 获取数据库信息
        print("\n4. 获取数据库信息...")
        db_info = configurator.get_database_info()
        print(f"   系统内存: {db_info['system_info']['memory_gb']:.2f} GB")
        print(f"   CPU核心数: {db_info['system_info']['cpu_cores']}")
        
        # 5. 保存配置报告
        print("\n5. 保存配置报告...")
        report_path = configurator.save_configuration_report()
        if report_path:
            print(f"   报告已保存到: {report_path}")
        
        print("\n✅ 数据库配置器测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库配置器测试失败: {e}")
        return False

def test_migration_manager():
    """测试迁移管理器"""
    print("\n" + "=" * 60)
    print("测试迁移管理器")
    print("=" * 60)
    
    # 构建测试数据库URL
    database_url = "postgresql://postgres:postgres@localhost:5432/postgres"
    
    try:
        # 创建迁移管理器
        manager = MigrationManager(database_url, project_root=".")
        
        # 1. 获取迁移状态
        print("\n1. 获取迁移状态...")
        status = manager.get_migration_status()
        print(f"   当前版本: {status.current_revision}")
        print(f"   最新版本: {status.head_revision}")
        print(f"   是否最新: {status.is_up_to_date}")
        print(f"   待执行迁移: {len(status.pending_migrations)}")
        
        # 2. 获取迁移历史
        print("\n2. 获取迁移历史...")
        history = manager.get_migration_history()
        print(f"   总迁移数: {len(history)}")
        if history:
            print(f"   最新迁移: {history[0].revision} - {history[0].description}")
        
        # 3. 验证数据完整性
        print("\n3. 验证数据完整性...")
        integrity = manager.validate_data_integrity()
        print(f"   整体状态: {integrity['overall_status']}")
        print(f"   检查的表数: {integrity['statistics'].get('total_tables', 0)}")
        print(f"   发现问题: {len(integrity.get('issues', []))}")
        
        # 4. 获取备份列表
        print("\n4. 获取备份列表...")
        backups = manager.get_backup_list()
        print(f"   备份数量: {len(backups)}")
        if backups:
            latest = backups[0]
            print(f"   最新备份: {latest.backup_id} ({latest.backup_size / 1024 / 1024:.2f} MB)")
        
        # 5. 生成迁移报告
        print("\n5. 生成迁移报告...")
        report = manager.generate_migration_report()
        print(f"   报告生成时间: {report['timestamp']}")
        print(f"   建议数量: {len(report.get('recommendations', []))}")
        
        # 6. 保存迁移报告
        print("\n6. 保存迁移报告...")
        report_path = manager.save_migration_report()
        if report_path:
            print(f"   报告已保存到: {report_path}")
        
        print("\n✅ 迁移管理器测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("集成测试")
    print("=" * 60)
    
    try:
        # 测试配置和迁移的集成
        print("\n1. 测试配置和迁移的集成...")
        
        # 创建数据库配置
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            name="lawsker_integration_test",
            user="lawsker_integration_user",
            password="integration_test_123",
            admin_user="postgres",
            admin_password="postgres"
        )
        
        configurator = DatabaseConfigurator(config)
        
        # 检查服务状态
        if not configurator.check_postgresql_service():
            print("   ⚠️  PostgreSQL服务未运行，跳过集成测试")
            return False
        
        # 构建数据库URL
        database_url = (
            f"postgresql://{config.user}:{config.password}@"
            f"{config.host}:{config.port}/{config.name}"
        )
        
        # 创建迁移管理器
        manager = MigrationManager(database_url)
        
        # 获取系统信息
        db_info = configurator.get_database_info()
        migration_status = manager.get_migration_status()
        
        print(f"   数据库配置状态: {configurator.status.to_dict()}")
        print(f"   迁移状态: {migration_status.to_dict()}")
        
        print("\n✅ 集成测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("数据库配置系统测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    # 检查依赖
    try:
        import psycopg2
        import sqlalchemy
        import alembic
        import psutil
        print("✅ 所有依赖包已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        return False
    
    # 运行测试
    results = []
    
    # 测试数据库配置器
    results.append(("数据库配置器", test_database_configurator()))
    
    # 测试迁移管理器
    results.append(("迁移管理器", test_migration_manager()))
    
    # 集成测试
    results.append(("集成测试", test_integration()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)