#!/usr/bin/env python3
"""
Lawsker PostgreSQL数据库迁移脚本
适用于服务器环境的PostgreSQL数据库
"""
import os
import sys
import logging
import psycopg2
from psycopg2 import Error
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgresql_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PostgreSQLMigrator:
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
                'user': os.getenv('DB_USER', 'lawsker_user'),
                'password': os.getenv('DB_PASSWORD', 'lawsker_password'),
                'port': int(os.getenv('DB_PORT', 5432))
            }
            logger.info("PostgreSQL配置加载完成")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            sys.exit(1)

    def connect(self):
        """连接数据库"""
        try:
            self.connection = psycopg2.connect(**self.config)
            self.cursor = self.connection.cursor()
            logger.info("PostgreSQL连接成功")
        except Error as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            sys.exit(1)

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("PostgreSQL连接已关闭")

    def execute_sql(self, sql):
        """执行SQL语句"""
        try:
            self.cursor.execute(sql)
            self.connection.commit()
        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            self.connection.rollback()
            raise

    def check_table_exists(self, table_name):
        """检查表是否存在"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"检查表存在性失败: {e}")
            return False

    def create_migration_log_table(self):
        """创建迁移日志表"""
        sql = """
        CREATE TABLE IF NOT EXISTS migration_log (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed')),
            error_message TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_migration_name ON migration_log(migration_name);
        CREATE INDEX IF NOT EXISTS idx_executed_at ON migration_log(executed_at);
        """
        try:
            self.execute_sql(sql)
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

    def create_core_tables(self):
        """创建核心表结构"""
        try:
            logger.info("开始创建核心表结构...")

            # 用户表
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                phone VARCHAR(20),
                user_type VARCHAR(20) DEFAULT 'client' CHECK (user_type IN ('client', 'lawyer', 'admin')),
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 律师认证请求表
            lawyer_certification_table = """
            CREATE TABLE IF NOT EXISTS lawyer_certification_requests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                license_number VARCHAR(50) NOT NULL,
                law_firm VARCHAR(100),
                specialization TEXT,
                experience_years INTEGER,
                education TEXT,
                certifications TEXT,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewer_id INTEGER REFERENCES users(id),
                review_notes TEXT
            );
            """

            # 工作区映射表
            workspace_mappings_table = """
            CREATE TABLE IF NOT EXISTS workspace_mappings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                workspace_type VARCHAR(20) NOT NULL CHECK (workspace_type IN ('client', 'lawyer', 'admin')),
                is_default BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 演示账户表
            demo_accounts_table = """
            CREATE TABLE IF NOT EXISTS demo_accounts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                demo_type VARCHAR(20) NOT NULL CHECK (demo_type IN ('client', 'lawyer')),
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 律师积分表
            lawyer_points_table = """
            CREATE TABLE IF NOT EXISTS lawyer_points (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                total_earned INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 律师等级表
            lawyer_levels_table = """
            CREATE TABLE IF NOT EXISTS lawyer_levels (
                id SERIAL PRIMARY KEY,
                level INTEGER UNIQUE NOT NULL,
                name VARCHAR(50) NOT NULL,
                min_points INTEGER NOT NULL,
                max_points INTEGER NOT NULL,
                benefits JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 律师会员表
            lawyer_memberships_table = """
            CREATE TABLE IF NOT EXISTS lawyer_memberships (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                plan_id INTEGER,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                auto_renew BOOLEAN DEFAULT false
            );
            """

            # 律师会员套餐表
            lawyer_membership_plans_table = """
            CREATE TABLE IF NOT EXISTS lawyer_membership_plans (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                duration_months INTEGER NOT NULL,
                features JSONB,
                points_multiplier DECIMAL(3,2) DEFAULT 1.0,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 用户积分表
            user_credits_table = """
            CREATE TABLE IF NOT EXISTS user_credits (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                credits INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 积分购买记录表
            credit_purchase_records_table = """
            CREATE TABLE IF NOT EXISTS credit_purchase_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                credits_purchased INTEGER NOT NULL,
                amount_paid DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(50),
                transaction_id VARCHAR(100),
                status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 系统配置表
            system_config_table = """
            CREATE TABLE IF NOT EXISTS system_config (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(100) UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 执行所有表创建
            tables = [
                ('users', users_table),
                ('lawyer_certification_requests', lawyer_certification_table),
                ('workspace_mappings', workspace_mappings_table),
                ('demo_accounts', demo_accounts_table),
                ('lawyer_points', lawyer_points_table),
                ('lawyer_levels', lawyer_levels_table),
                ('lawyer_memberships', lawyer_memberships_table),
                ('lawyer_membership_plans', lawyer_membership_plans_table),
                ('user_credits', user_credits_table),
                ('credit_purchase_records', credit_purchase_records_table),
                ('system_config', system_config_table)
            ]

            for table_name, table_sql in tables:
                self.execute_sql(table_sql)
                logger.info(f"表 {table_name} 创建成功")

            logger.info("核心表结构创建完成")
        except Exception as e:
            logger.error(f"核心表创建失败: {e}")
            raise

    def create_business_optimization_tables(self):
        """创建业务优化相关表"""
        try:
            logger.info("开始创建业务优化表...")

            # 企业客户满意度调查表
            enterprise_satisfaction_table = """
            CREATE TABLE IF NOT EXISTS enterprise_satisfaction_surveys (
                id SERIAL PRIMARY KEY,
                enterprise_id INTEGER,
                survey_date DATE NOT NULL,
                overall_satisfaction INTEGER CHECK (overall_satisfaction BETWEEN 1 AND 10),
                service_quality INTEGER CHECK (service_quality BETWEEN 1 AND 10),
                response_time INTEGER CHECK (response_time BETWEEN 1 AND 10),
                cost_effectiveness INTEGER CHECK (cost_effectiveness BETWEEN 1 AND 10),
                recommendation_likelihood INTEGER CHECK (recommendation_likelihood BETWEEN 1 AND 10),
                feedback_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 律师推广活动表
            lawyer_promotion_table = """
            CREATE TABLE IF NOT EXISTS lawyer_promotion_campaigns (
                id SERIAL PRIMARY KEY,
                campaign_name VARCHAR(100) NOT NULL,
                campaign_type VARCHAR(50) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                target_registrations INTEGER DEFAULT 0,
                actual_registrations INTEGER DEFAULT 0,
                budget DECIMAL(10,2),
                cost_per_acquisition DECIMAL(10,2),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 律师转化跟踪表
            lawyer_conversion_table = """
            CREATE TABLE IF NOT EXISTS lawyer_conversion_tracking (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                registration_source VARCHAR(100),
                conversion_step VARCHAR(50),
                conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                campaign_id INTEGER REFERENCES lawyer_promotion_campaigns(id)
            );
            """

            # 律师活动日志表
            lawyer_activity_table = """
            CREATE TABLE IF NOT EXISTS lawyer_activity_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                activity_type VARCHAR(50) NOT NULL,
                activity_description TEXT,
                points_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 批量滥用监控表
            batch_abuse_table = """
            CREATE TABLE IF NOT EXISTS batch_abuse_monitoring (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                upload_count INTEGER DEFAULT 0,
                upload_date DATE NOT NULL,
                is_flagged BOOLEAN DEFAULT false,
                flag_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # 执行表创建
            tables = [
                ('enterprise_satisfaction_surveys', enterprise_satisfaction_table),
                ('lawyer_promotion_campaigns', lawyer_promotion_table),
                ('lawyer_conversion_tracking', lawyer_conversion_table),
                ('lawyer_activity_logs', lawyer_activity_table),
                ('batch_abuse_monitoring', batch_abuse_table)
            ]

            for table_name, table_sql in tables:
                self.execute_sql(table_sql)
                logger.info(f"表 {table_name} 创建成功")

            logger.info("业务优化表创建完成")
        except Exception as e:
            logger.error(f"业务优化表创建失败: {e}")
            raise

    def create_indexes(self):
        """创建索引"""
        try:
            logger.info("开始创建索引...")

            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                "CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);",
                "CREATE INDEX IF NOT EXISTS idx_lawyer_cert_user_id ON lawyer_certification_requests(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_lawyer_cert_status ON lawyer_certification_requests(status);",
                "CREATE INDEX IF NOT EXISTS idx_workspace_user_id ON workspace_mappings(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_demo_accounts_user_id ON demo_accounts(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_lawyer_points_user_id ON lawyer_points(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_lawyer_memberships_user_id ON lawyer_memberships(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_enterprise_survey_date ON enterprise_satisfaction_surveys(survey_date);",
                "CREATE INDEX IF NOT EXISTS idx_lawyer_activity_user_id ON lawyer_activity_logs(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_batch_abuse_user_id ON batch_abuse_monitoring(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_batch_abuse_date ON batch_abuse_monitoring(upload_date);"
            ]

            for index_sql in indexes:
                self.execute_sql(index_sql)

            logger.info("索引创建完成")
        except Exception as e:
            logger.error(f"索引创建失败: {e}")
            raise

    def insert_initial_data(self):
        """插入初始数据"""
        try:
            logger.info("开始插入初始数据...")

            # 律师等级数据
            lawyer_levels_data = """
            INSERT INTO lawyer_levels (level, name, min_points, max_points, benefits) VALUES
            (1, '见习律师', 0, 999, '{"description": "刚入门的律师", "features": ["基础案件分配"]}'),
            (2, '初级律师', 1000, 2999, '{"description": "有一定经验的律师", "features": ["基础案件分配", "优先客服支持"]}'),
            (3, '中级律师', 3000, 5999, '{"description": "经验丰富的律师", "features": ["基础案件分配", "优先客服支持", "专业培训"]}'),
            (4, '高级律师', 6000, 9999, '{"description": "资深律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件"]}'),
            (5, '专家律师', 10000, 19999, '{"description": "专业领域专家", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询"]}'),
            (6, '资深专家', 20000, 39999, '{"description": "行业资深专家", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享"]}'),
            (7, '首席律师', 40000, 79999, '{"description": "首席级别律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件"]}'),
            (8, '合伙人级', 80000, 159999, '{"description": "合伙人级别", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件", "业务决策"]}'),
            (9, '传奇律师', 160000, 319999, '{"description": "传奇级别律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件", "业务决策", "平台代言"]}'),
            (10, '至尊律师', 320000, 999999999, '{"description": "至尊级别律师", "features": ["基础案件分配", "优先客服支持", "专业培训", "高价值案件", "专家咨询", "内部分享", "战略案件", "业务决策", "平台代言", "无限特权"]}')
            ON CONFLICT (level) DO NOTHING;
            """

            # 会员套餐数据
            membership_plans_data = """
            INSERT INTO lawyer_membership_plans (name, price, duration_months, features, points_multiplier, is_active) VALUES
            ('免费会员', 0.00, 120, '{"ai_credits": 20, "case_limit": 10, "support": "basic"}', 1.0, true),
            ('专业会员', 299.00, 12, '{"ai_credits": 100, "case_limit": 50, "support": "priority", "training": true}', 2.0, true),
            ('企业会员', 999.00, 12, '{"ai_credits": 500, "case_limit": 200, "support": "vip", "training": true, "analytics": true}', 3.0, true)
            ON CONFLICT DO NOTHING;
            """

            # 系统配置数据
            system_config_data = """
            INSERT INTO system_config (config_key, config_value, description) VALUES
            ('credits_weekly_free', '1', '每周免费Credits数量'),
            ('credits_price', '50.00', 'Credits单价（元）'),
            ('batch_upload_credit_cost', '1', '批量上传消耗Credits数量'),
            ('lawyer_rejection_penalty', '100', '律师拒绝案件扣除积分'),
            ('case_completion_reward', '50', '案件完成奖励积分'),
            ('client_rating_multiplier', '10', '客户评分积分倍数'),
            ('enterprise_satisfaction_target', '95', '企业客户满意度目标（%）')
            ON CONFLICT (config_key) DO NOTHING;
            """

            # 执行数据插入
            self.execute_sql(lawyer_levels_data)
            self.execute_sql(membership_plans_data)
            self.execute_sql(system_config_data)

            logger.info("初始数据插入完成")
        except Exception as e:
            logger.error(f"初始数据插入失败: {e}")
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
            logger.info("开始PostgreSQL数据库迁移...")
            self.connect()
            self.create_migration_log_table()

            # 执行迁移
            migration_name = "postgresql_complete_migration"
            if self.is_migration_executed(migration_name):
                logger.info("迁移已执行，跳过")
                return True

            self.create_core_tables()
            self.create_business_optimization_tables()
            self.create_indexes()
            self.insert_initial_data()

            # 记录迁移成功
            self.log_migration(migration_name, 'success')

            # 验证迁移
            if not self.verify_migration():
                logger.error("迁移验证失败")
                return False

            logger.info("PostgreSQL数据库迁移成功完成")
            return True
        except Exception as e:
            logger.error(f"迁移过程发生错误: {e}")
            self.log_migration(migration_name, 'failed', str(e))
            return False
        finally:
            self.disconnect()

def main():
    """主函数"""
    print("=" * 60)
    print("Lawsker PostgreSQL数据库迁移工具")
    print("=" * 60)

    migrator = PostgreSQLMigrator()

    # 询问用户确认
    response = input("是否开始PostgreSQL数据库迁移? (y/N): ").strip().lower()
    if response != 'y':
        print("迁移已取消")
        return

    # 执行迁移
    success = migrator.run_complete_migration()

    if success:
        print("\n" + "=" * 60)
        print("✅ PostgreSQL数据库迁移成功完成！")
        print("=" * 60)
        print("📋 迁移摘要:")
        print("  - 所有必需的表已创建")
        print("  - 索引已优化")
        print("  - 初始数据已插入")
        print("  - 数据完整性验证通过")
        print("  - 迁移日志已记录")
        print("\n📁 日志文件: postgresql_migration.log")
        print("🚀 系统已准备就绪，可以启动应用程序")
    else:
        print("\n" + "=" * 60)
        print("❌ PostgreSQL数据库迁移失败！")
        print("=" * 60)
        print("请检查 postgresql_migration.log 文件获取详细错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()