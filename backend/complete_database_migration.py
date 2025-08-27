#!/usr/bin/env python3
"""
Lawsker 完整数据库迁移脚本
包括所有新增表和数据的创建
"""
import os
import sys
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.load_config()

    def load_config(self):
        """加载数据库配置"""
        try:
            # 从环境变量加载配置
            self.config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'database': os.getenv('DB_NAME', 'lawsker'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'port': int(os.getenv('DB_PORT', 3306)),
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
            logger.info("数据库配置加载完成")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            sys.exit(1)

    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor()
            logger.info("数据库连接成功")
        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            sys.exit(1)

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("数据库连接已关闭")

    def execute_sql_file(self, file_path):
        """执行SQL文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            # 分割SQL语句
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    self.cursor.execute(statement)
            
            self.connection.commit()
            logger.info(f"SQL文件执行成功: {file_path}")
        except Exception as e:
            logger.error(f"SQL文件执行失败 {file_path}: {e}")
            self.connection.rollback()
            raise

    def check_table_exists(self, table_name):
        """检查表是否存在"""
        try:
            self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"检查表存在性失败: {e}")
            return False

    def create_migration_log_table(self):
        """创建迁移日志表"""
        sql = """
        CREATE TABLE IF NOT EXISTS migration_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('success', 'failed') NOT NULL,
            error_message TEXT,
            INDEX idx_migration_name (migration_name),
            INDEX idx_executed_at (executed_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        try:
            self.cursor.execute(sql)
            self.connection.commit()
            logger.info("迁移日志表创建成功")
        except Exception as e:
            logger.error(f"迁移日志表创建失败: {e}")
            raise

    def log_migration(self, migration_name, status, error_message=None):
        """记录迁移日志"""
        try:
            sql = """
            INSERT INTO migration_log (migration_name, status, error_message)
            VALUES (%s, %s, %s)
            """
            self.cursor.execute(sql, (migration_name, status, error_message))
            self.connection.commit()
        except Exception as e:
            logger.error(f"记录迁移日志失败: {e}")

    def is_migration_executed(self, migration_name):
        """检查迁移是否已执行"""
        try:
            sql = "SELECT COUNT(*) FROM migration_log WHERE migration_name = %s AND status = 'success'"
            self.cursor.execute(sql, (migration_name,))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"检查迁移状态失败: {e}")
            return False

    def run_migration(self, migration_file, migration_name):
        """运行单个迁移"""
        try:
            if self.is_migration_executed(migration_name):
                logger.info(f"迁移已执行，跳过: {migration_name}")
                return True

            logger.info(f"开始执行迁移: {migration_name}")
            self.execute_sql_file(migration_file)
            self.log_migration(migration_name, 'success')
            logger.info(f"迁移执行成功: {migration_name}")
            return True
        except Exception as e:
            error_msg = str(e)
            logger.error(f"迁移执行失败 {migration_name}: {error_msg}")
            self.log_migration(migration_name, 'failed', error_msg)
            return False

    def run_all_migrations(self):
        """运行所有迁移"""
        migrations = [
            ('migrations/010_optimize_database_indexes.sql', '010_optimize_database_indexes'),
            ('migrations/011_create_alert_tables.sql', '011_create_alert_tables'),
            ('migrations/012_add_encrypted_fields.sql', '012_add_encrypted_fields'),
            ('migrations/013_auth_system_tables.sql', '013_auth_system_tables'),
            ('migrations/013_business_optimization_tables.sql', '013_business_optimization_tables'),
            ('migrations/014_lawyer_promotion_tables.sql', '014_lawyer_promotion_tables'),
            ('migrations/015_lawyer_conversion_tracking.sql', '015_lawyer_conversion_tracking'),
            ('migrations/016_lawyer_activity_tracking.sql', '016_lawyer_activity_tracking'),
            ('migrations/017_enterprise_customer_satisfaction.sql', '017_enterprise_customer_satisfaction'),
            ('migrations/017_enterprise_satisfaction_simple.sql', '017_enterprise_satisfaction_simple'),
        ]

        success_count = 0
        total_count = len(migrations)

        for migration_file, migration_name in migrations:
            if os.path.exists(migration_file):
                if self.run_migration(migration_file, migration_name):
                    success_count += 1
            else:
                logger.warning(f"迁移文件不存在: {migration_file}")

        logger.info(f"迁移完成: {success_count}/{total_count} 成功")
        return success_count == total_count

    def create_initial_data(self):
        """创建初始数据"""
        try:
            logger.info("开始创建初始数据...")

            # 创建默认律师等级配置
            lawyer_levels_sql = """
            INSERT IGNORE INTO lawyer_levels (level, name, min_points, max_points, benefits, created_at) VALUES
            (1, '见习律师', 0, 999, '{"description": "刚入门的律师", "features": ["基础案件分配"]}', NOW()),
            (2, '初级律师', 1000, 2999, '{"description": "有一定经验的律师", "features": ["基础案件分配", "优先客服支持"]}', NOW()),
            (3, '中级律师', 3000, 5999, '{"description": "经验丰富的律师", "features": ["基础案件分配", "优先客服支持", "专业培训"]}', NOW()),
            (4, '高级律师', 6000, 9999, '{"description": "资深律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件"]}', NOW()),
            (5, '专家律师', 10000, 19999, '{"description": "专业领域专家", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询"]}', NOW()),
            (6, '资深专家', 20000, 39999, '{"description": "行业资深专家", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享"]}', NOW()),
            (7, '首席律师', 40000, 79999, '{"description": "首席级别律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件"]}', NOW()),
            (8, '合伙人级', 80000, 159999, '{"description": "合伙人级别", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件", "业务决策"]}', NOW()),
            (9, '传奇律师', 160000, 319999, '{"description": "传奇级别律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件", "业务决策", "平台代言"]}', NOW()),
            (10, '至尊律师', 320000, 999999999, '{"description": "至尊级别律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件", "业务决策", "平台代言", "无限特权"]}', NOW());
            """

            # 创建默认会员套餐
            membership_plans_sql = """
            INSERT IGNORE INTO lawyer_membership_plans (name, price, duration_months, features, points_multiplier, is_active, created_at) VALUES
            ('免费会员', 0.00, 120, '{"ai_credits": 20, "case_limit": 10, "support": "basic"}', 1.0, 1, NOW()),
            ('专业会员', 299.00, 12, '{"ai_credits": 100, "case_limit": 50, "support": "priority", "training": true}', 2.0, 1, NOW()),
            ('企业会员', 999.00, 12, '{"ai_credits": 500, "case_limit": 200, "support": "vip", "training": true, "analytics": true}', 3.0, 1, NOW());
            """

            # 创建默认系统配置
            system_config_sql = """
            INSERT IGNORE INTO system_config (config_key, config_value, description, created_at) VALUES
            ('credits_weekly_free', '1', '每周免费Credits数量', NOW()),
            ('credits_price', '50.00', 'Credits单价（元）', NOW()),
            ('batch_upload_credit_cost', '1', '批量上传消耗Credits数量', NOW()),
            ('lawyer_rejection_penalty', '100', '律师拒绝案件扣除积分', NOW()),
            ('case_completion_reward', '50', '案件完成奖励积分', NOW()),
            ('client_rating_multiplier', '10', '客户评分积分倍数', NOW()),
            ('enterprise_satisfaction_target', '95', '企业客户满意度目标（%）', NOW());
            """

            # 执行SQL
            for sql in [lawyer_levels_sql, membership_plans_sql, system_config_sql]:
                statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                for statement in statements:
                    if statement:
                        self.cursor.execute(statement)

            self.connection.commit()
            logger.info("初始数据创建完成")
        except Exception as e:
            logger.error(f"初始数据创建失败: {e}")
            self.connection.rollback()
            raise

    def verify_migration(self):
        """验证迁移结果"""
        try:
            logger.info("开始验证迁移结果...")

            # 检查关键表是否存在
            required_tables = [
                'users', 'lawyer_certification_requests', 'workspace_mappings',
                'demo_accounts', 'lawyer_points', 'lawyer_levels', 'lawyer_memberships',
                'lawyer_membership_plans', 'user_credits', 'credit_purchase_records',
                'enterprise_satisfaction_surveys', 'lawyer_promotion_campaigns',
                'lawyer_conversion_tracking', 'lawyer_activity_logs',
                'batch_abuse_monitoring', 'migration_log'
            ]

            missing_tables = []
            for table in required_tables:
                if not self.check_table_exists(table):
                    missing_tables.append(table)

            if missing_tables:
                logger.error(f"以下表缺失: {missing_tables}")
                return False

            # 检查数据完整性
            self.cursor.execute("SELECT COUNT(*) FROM lawyer_levels")
            level_count = self.cursor.fetchone()[0]
            if level_count < 10:
                logger.error(f"律师等级数据不完整，期望10个，实际{level_count}个")
                return False

            self.cursor.execute("SELECT COUNT(*) FROM lawyer_membership_plans")
            plan_count = self.cursor.fetchone()[0]
            if plan_count < 3:
                logger.error(f"会员套餐数据不完整，期望3个，实际{plan_count}个")
                return False

            logger.info("迁移验证通过")
            return True
        except Exception as e:
            logger.error(f"迁移验证失败: {e}")
            return False

    def run_complete_migration(self):
        """运行完整迁移流程"""
        try:
            logger.info("开始完整数据库迁移...")
            self.connect()
            self.create_migration_log_table()

            # 运行所有迁移
            if not self.run_all_migrations():
                logger.error("迁移执行失败")
                return False

            # 创建初始数据
            self.create_initial_data()

            # 验证迁移
            if not self.verify_migration():
                logger.error("迁移验证失败")
                return False

            logger.info("完整数据库迁移成功完成")
            return True
        except Exception as e:
            logger.error(f"迁移过程发生错误: {e}")
            return False
        finally:
            self.disconnect()

def main():
    """主函数"""
    print("=" * 60)
    print("Lawsker 完整数据库迁移工具")
    print("=" * 60)

    migrator = DatabaseMigrator()

    # 询问用户确认
    response = input("是否开始数据库迁移? (y/N): ").strip().lower()
    if response != 'y':
        print("迁移已取消")
        return

    # 执行迁移
    success = migrator.run_complete_migration()

    if success:
        print("\n" + "=" * 60)
        print("✅ 数据库迁移成功完成！")
        print("=" * 60)
        print("📋 迁移摘要:")
        print("  - 所有必需的表已创建")
        print("  - 初始数据已插入")
        print("  - 数据完整性验证通过")
        print("  - 迁移日志已记录")
        print("\n📁 日志文件: migration.log")
        print("🚀 系统已准备就绪，可以启动应用程序")
    else:
        print("\n" + "=" * 60)
        print("❌ 数据库迁移失败！")
        print("=" * 60)
        print("请检查 migration.log 文件获取详细错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()