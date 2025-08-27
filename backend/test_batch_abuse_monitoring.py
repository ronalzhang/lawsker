#!/usr/bin/env python3
"""
批量任务滥用监控系统测试脚本
验证90%滥用减少目标的实现
"""

import asyncio
import sys
import os
from datetime import date, timedelta
from uuid import uuid4, UUID
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.batch_abuse_monitor import BatchAbuseMonitor, AbuseLevel
from app.services.user_credits_service import UserCreditsService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = "postgresql://lawsker_user:lawsker_password@localhost:5432/lawsker_db"

class BatchAbuseMonitoringTest:
    """批量滥用监控系统测试类"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.abuse_monitor = BatchAbuseMonitor()
        
    def get_db(self):
        """获取数据库会话"""
        db = self.SessionLocal()
        try:
            return db
        finally:
            pass  # 不在这里关闭，由调用者负责
    
    async def test_abuse_detection(self):
        """测试滥用检测功能"""
        print("\n=== 测试滥用检测功能 ===")
        
        db = self.get_db()
        try:
            # 创建测试用户
            test_user_id = await self.create_test_user(db)
            
            # 创建测试数据
            await self.create_test_batch_uploads(test_user_id, db)
            
            # 执行滥用检测
            patterns = await self.abuse_monitor.detect_abuse_patterns(test_user_id, db)
            
            print(f"检测到 {len(patterns)} 个滥用模式:")
            for pattern in patterns:
                print(f"  - 类型: {pattern.pattern_type}")
                print(f"    严重程度: {pattern.severity.value}")
                print(f"    描述: {pattern.description}")
                print(f"    置信度: {pattern.confidence_score}")
                print()
            
            return len(patterns) > 0
            
        finally:
            db.close()
    
    async def test_abuse_metrics_calculation(self):
        """测试滥用指标计算"""
        print("\n=== 测试滥用指标计算 ===")
        
        db = self.get_db()
        try:
            # 计算最近30天的滥用指标
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            metrics = await self.abuse_monitor.calculate_abuse_metrics(start_date, end_date, db)
            
            print(f"时间范围: {metrics.period_start} 到 {metrics.period_end}")
            print(f"总批量上传数: {metrics.total_batch_uploads}")
            print(f"滥用上传数: {metrics.abusive_uploads}")
            print(f"滥用率: {metrics.abuse_rate:.2%}")
            print(f"Credits阻止滥用: {metrics.credits_prevented_abuse}")
            print(f"估算成本节省: ¥{metrics.estimated_cost_savings}")
            
            return metrics.abuse_rate < 0.25  # 期望滥用率低于25%
            
        finally:
            db.close()
    
    async def test_90_percent_reduction_progress(self):
        """测试90%减少目标进度"""
        print("\n=== 测试90%减少目标进度 ===")
        
        db = self.get_db()
        try:
            progress = await self.abuse_monitor.get_abuse_reduction_progress(db)
            
            print(f"目标减少率: {progress['target_reduction']:.0%}")
            print(f"实际减少率: {progress['actual_reduction']:.2%}")
            print(f"目标达成率: {progress['target_achievement_rate']:.2%}")
            print(f"目标是否达成: {'是' if progress['target_achieved'] else '否'}")
            
            print("\n实施前数据:")
            before = progress['before_period']
            print(f"  时间: {before['start_date']} 到 {before['end_date']}")
            print(f"  总上传: {before['total_uploads']}")
            print(f"  滥用上传: {before['abusive_uploads']}")
            print(f"  滥用率: {before['abuse_rate']:.2%}")
            
            print("\n实施后数据:")
            after = progress['after_period']
            print(f"  时间: {after['start_date']} 到 {after['end_date']}")
            print(f"  总上传: {after['total_uploads']}")
            print(f"  滥用上传: {after['abusive_uploads']}")
            print(f"  滥用率: {after['abuse_rate']:.2%}")
            
            print("\nCredits影响:")
            credits = progress['credits_impact']
            print(f"  阻止滥用: {credits['prevented_abuse']}")
            print(f"  成本节省: ¥{credits['cost_savings']}")
            
            print("\n改进建议:")
            for rec in progress['recommendations']:
                print(f"  - {rec}")
            
            return progress['target_achievement_rate'] >= 0.5  # 至少达成50%
            
        finally:
            db.close()
    
    async def test_credits_effectiveness(self):
        """测试Credits系统防滥用效果"""
        print("\n=== 测试Credits系统防滥用效果 ===")
        
        db = self.get_db()
        try:
            # 获取Credits系统统计
            stats_query = text("""
                SELECT 
                    COUNT(DISTINCT uc.user_id) as total_users,
                    SUM(uc.credits_purchased) as total_purchased,
                    SUM(uc.total_credits_used) as total_used,
                    COUNT(CASE WHEN uc.credits_remaining = 0 THEN 1 END) as zero_credits_users
                FROM user_credits uc
            """)
            
            result = db.execute(stats_query).fetchone()
            
            if result:
                total_users, total_purchased, total_used, zero_credits_users = result
                
                print(f"Credits系统用户数: {total_users}")
                print(f"总购买Credits: {total_purchased}")
                print(f"总使用Credits: {total_used}")
                print(f"Credits耗尽用户数: {zero_credits_users}")
                
                if total_users > 0:
                    usage_rate = (total_used / max(1, total_purchased + total_users)) * 100
                    zero_rate = (zero_credits_users / total_users) * 100
                    
                    print(f"Credits使用率: {usage_rate:.2f}%")
                    print(f"Credits耗尽率: {zero_rate:.2f}%")
                    
                    # 估算防滥用效果
                    estimated_prevented = int(zero_credits_users * 0.25)  # 假设25%会滥用
                    print(f"估算阻止滥用: {estimated_prevented} 次")
                    
                    return zero_rate > 10  # 期望至少10%的用户Credits耗尽（说明系统在起作用）
            
            return False
            
        finally:
            db.close()
    
    async def create_test_user(self, db):
        """创建测试用户"""
        user_id = str(uuid4())
        
        # 插入测试用户
        insert_user_query = text("""
            INSERT INTO users (id, username, email, password_hash, full_name)
            VALUES (:id, :username, :email, :password, :full_name)
            ON CONFLICT (id) DO NOTHING
        """)
        
        db.execute(insert_user_query, {
            "id": user_id,
            "username": f"test_user_{user_id[:8]}",
            "email": f"test_{user_id[:8]}@example.com",
            "password": "hashed_password",
            "full_name": "测试用户"
        })
        
        # 初始化Credits
        insert_credits_query = text("""
            INSERT INTO user_credits (user_id, credits_weekly, credits_remaining)
            VALUES (:user_id, 1, 0)
            ON CONFLICT (user_id) DO NOTHING
        """)
        
        db.execute(insert_credits_query, {"user_id": user_id})
        
        db.commit()
        return UUID(user_id)
    
    async def create_test_batch_uploads(self, user_id: UUID, db):
        """创建测试批量上传数据"""
        # 创建多个批量上传记录，模拟滥用行为
        test_uploads = [
            # 频率滥用 - 短时间内多次上传
            {"file_name": "test1.csv", "file_size": 1024, "hours_ago": 1},
            {"file_name": "test2.csv", "file_size": 1024, "hours_ago": 1},
            {"file_name": "test3.csv", "file_size": 1024, "hours_ago": 1},
            {"file_name": "test4.csv", "file_size": 1024, "hours_ago": 2},
            {"file_name": "test5.csv", "file_size": 1024, "hours_ago": 2},
            
            # 质量滥用 - 小文件
            {"file_name": "empty.csv", "file_size": 100, "hours_ago": 3},
            {"file_name": "tiny.csv", "file_size": 200, "hours_ago": 4},
            
            # 重复内容滥用
            {"file_name": "duplicate.csv", "file_size": 2048, "hours_ago": 5},
            {"file_name": "duplicate.csv", "file_size": 2048, "hours_ago": 6},
            
            # 可疑文件名
            {"file_name": "spam_test.csv", "file_size": 1024, "hours_ago": 7},
            {"file_name": "fake_data.csv", "file_size": 1024, "hours_ago": 8},
        ]
        
        for upload in test_uploads:
            insert_query = text("""
                INSERT INTO batch_upload_tasks (
                    id, user_id, task_type, file_name, file_size,
                    total_records, processed_records, success_records, error_records,
                    credits_cost, status, created_at
                ) VALUES (
                    :id, :user_id, 'debt_collection', :file_name, :file_size,
                    10, 10, :success_records, :error_records,
                    1, 'completed', NOW() - INTERVAL ':hours_ago hours'
                )
            """)
            
            # 小文件通常有更多错误
            success_records = 2 if upload["file_size"] < 500 else 8
            error_records = 8 if upload["file_size"] < 500 else 2
            
            db.execute(insert_query, {
                "id": str(uuid4()),
                "user_id": str(user_id),
                "file_name": upload["file_name"],
                "file_size": upload["file_size"],
                "success_records": success_records,
                "error_records": error_records,
                "hours_ago": upload["hours_ago"]
            })
        
        db.commit()
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始批量任务滥用监控系统测试...")
        
        tests = [
            ("滥用检测功能", self.test_abuse_detection),
            ("滥用指标计算", self.test_abuse_metrics_calculation),
            ("90%减少目标进度", self.test_90_percent_reduction_progress),
            ("Credits防滥用效果", self.test_credits_effectiveness),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result, None))
                print(f"✅ {test_name}: {'通过' if result else '失败'}")
            except Exception as e:
                results.append((test_name, False, str(e)))
                print(f"❌ {test_name}: 异常 - {str(e)}")
        
        # 输出测试总结
        print("\n" + "="*50)
        print("测试总结:")
        print("="*50)
        
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        
        for test_name, result, error in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status} {test_name}")
            if error:
                print(f"    错误: {error}")
        
        print(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！批量任务滥用监控系统运行正常。")
            print("📊 90%滥用减少目标的监控和分析功能已就绪。")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败，请检查系统配置。")
        
        return passed == total


async def main():
    """主函数"""
    test_runner = BatchAbuseMonitoringTest()
    
    try:
        success = await test_runner.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"测试运行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())