#!/usr/bin/env python3
"""
用户Credits支付系统测试脚本
验证Credits管理、批量上传控制、防滥用机制
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from uuid import uuid4, UUID
from decimal import Decimal

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.user_credits_service import UserCreditsService, InsufficientCreditsError
from app.services.config_service import SystemConfigService
from app.core.config import settings

# 测试配置
TEST_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class CreditsSystemTester:
    """Credits系统测试类"""
    
    def __init__(self):
        self.credits_service = UserCreditsService()
        self.test_user_id = UUID(str(uuid4()))
        
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("用户Credits支付系统测试")
        print("=" * 60)
        
        db = SessionLocal()
        
        try:
            # 创建测试用户
            await self.create_test_user(db)
            
            # 测试用例
            test_cases = [
                ("1. Credits初始化测试", self.test_credits_initialization),
                ("2. Credits余额查询测试", self.test_get_credits_balance),
                ("3. 批量上传Credits消耗测试", self.test_batch_upload_consumption),
                ("4. Credits不足处理测试", self.test_insufficient_credits),
                ("5. Credits购买测试", self.test_credits_purchase),
                ("6. 每周重置测试", self.test_weekly_reset),
                ("7. Credits使用历史测试", self.test_usage_history),
                ("8. 防滥用机制测试", self.test_abuse_prevention),
                ("9. 批量重置测试", self.test_batch_reset),
                ("10. 边界条件测试", self.test_edge_cases)
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in test_cases:
                print(f"\n{test_name}")
                print("-" * 40)
                
                try:
                    await test_func(db)
                    print("✅ 测试通过")
                    passed += 1
                except Exception as e:
                    print(f"❌ 测试失败: {str(e)}")
                    failed += 1
            
            # 测试总结
            print("\n" + "=" * 60)
            print("测试总结")
            print("=" * 60)
            print(f"总测试数: {len(test_cases)}")
            print(f"通过: {passed}")
            print(f"失败: {failed}")
            print(f"成功率: {(passed / len(test_cases) * 100):.1f}%")
            
            if failed == 0:
                print("\n🎉 所有测试通过！Credits系统运行正常")
            else:
                print(f"\n⚠️  有 {failed} 个测试失败，请检查系统配置")
                
        finally:
            # 清理测试数据
            await self.cleanup_test_data(db)
            db.close()
    
    async def create_test_user(self, db):
        """创建测试用户"""
        try:
            # 插入测试用户到users表
            insert_user_query = text("""
                INSERT INTO users (id, username, email, password_hash, created_at)
                VALUES (:user_id, :username, :email, :password_hash, NOW())
                ON CONFLICT (id) DO NOTHING
            """)
            
            db.execute(insert_user_query, {
                "user_id": str(self.test_user_id),
                "username": f"test_user_{self.test_user_id.hex[:8]}",
                "email": f"test_{self.test_user_id.hex[:8]}@example.com",
                "password_hash": "test_hash"
            })
            
            db.commit()
            print(f"✅ 测试用户创建成功: {self.test_user_id}")
            
        except Exception as e:
            print(f"⚠️  创建测试用户失败: {str(e)}")
    
    async def test_credits_initialization(self, db):
        """测试Credits初始化"""
        result = await self.credits_service.initialize_user_credits(self.test_user_id, db)
        
        assert result["status"] in ["initialized", "already_initialized"]
        assert result["user_id"] == str(self.test_user_id)
        
        print(f"初始化结果: {result['status']}")
        print(f"初始Credits: {result.get('credits_remaining', 'N/A')}")
    
    async def test_get_credits_balance(self, db):
        """测试Credits余额查询"""
        credits_info = await self.credits_service.get_user_credits(self.test_user_id, db)
        
        assert "credits_remaining" in credits_info
        assert "credits_weekly" in credits_info
        assert "next_reset_date" in credits_info
        
        print(f"当前余额: {credits_info['credits_remaining']}")
        print(f"每周配额: {credits_info['credits_weekly']}")
        print(f"下次重置: {credits_info['next_reset_date']}")
    
    async def test_batch_upload_consumption(self, db):
        """测试批量上传Credits消耗"""
        # 先确保有Credits
        await self.credits_service.initialize_user_credits(self.test_user_id, db)
        
        # 获取消耗前余额
        before_credits = await self.credits_service.get_user_credits(self.test_user_id, db)
        
        # 消耗Credits
        result = await self.credits_service.consume_credits_for_batch_upload(self.test_user_id, db)
        
        # 获取消耗后余额
        after_credits = await self.credits_service.get_user_credits(self.test_user_id, db)
        
        assert result["status"] == "success"
        assert result["credits_consumed"] == 1
        assert after_credits["credits_remaining"] == before_credits["credits_remaining"] - 1
        
        print(f"消耗前: {before_credits['credits_remaining']}")
        print(f"消耗后: {after_credits['credits_remaining']}")
        print(f"消耗数量: {result['credits_consumed']}")
    
    async def test_insufficient_credits(self, db):
        """测试Credits不足处理"""
        # 先消耗所有Credits
        credits_info = await self.credits_service.get_user_credits(self.test_user_id, db)
        
        # 消耗到0
        for _ in range(credits_info["credits_remaining"]):
            try:
                await self.credits_service.consume_credits_for_batch_upload(self.test_user_id, db)
            except InsufficientCreditsError:
                break
        
        # 尝试再次消耗，应该抛出异常
        try:
            await self.credits_service.consume_credits_for_batch_upload(self.test_user_id, db)
            assert False, "应该抛出InsufficientCreditsError异常"
        except InsufficientCreditsError as e:
            print(f"正确捕获异常: {e.message}")
            print(f"当前Credits: {e.current_credits}")
            print(f"需要Credits: {e.required_credits}")
    
    async def test_credits_purchase(self, db):
        """测试Credits购买流程"""
        # 获取购买前余额
        before_credits = await self.credits_service.get_user_credits(self.test_user_id, db)
        
        # 创建购买订单
        purchase_result = await self.credits_service.purchase_credits(self.test_user_id, 5, db)
        
        assert purchase_result["status"] == "pending_payment"
        assert purchase_result["credits_count"] == 5
        assert purchase_result["total_amount"] == 250.0  # 5 * 50
        
        # 模拟支付成功，确认购买
        purchase_id = purchase_result["purchase_id"]
        confirm_result = await self.credits_service.confirm_credits_purchase(purchase_id, db)
        
        assert confirm_result["status"] == "confirmed"
        assert confirm_result["credits_added"] == 5
        
        # 验证余额增加
        after_credits = await self.credits_service.get_user_credits(self.test_user_id, db)
        assert after_credits["credits_remaining"] == before_credits["credits_remaining"] + 5
        
        print(f"购买前余额: {before_credits['credits_remaining']}")
        print(f"购买数量: 5")
        print(f"购买后余额: {after_credits['credits_remaining']}")
        print(f"购买金额: ¥{purchase_result['total_amount']}")
        
        # 测试批量控制功能
        print("测试批量控制功能...")
        batch_control_result = await self.credits_service.consume_credits_for_batch_upload(self.test_user_id, db)
        assert batch_control_result["status"] == "success"
        print(f"批量控制测试通过: {batch_control_result['credits_consumed']}个Credits消耗")
    
    async def test_weekly_reset(self, db):
        """测试每周重置"""
        # 模拟上周的重置日期
        last_week = date.today() - timedelta(days=7)
        
        # 更新最后重置日期为上周
        update_query = text("""
            UPDATE user_credits 
            SET last_reset_date = :last_week
            WHERE user_id = :user_id
        """)
        
        db.execute(update_query, {
            "user_id": str(self.test_user_id),
            "last_week": last_week
        })
        db.commit()
        
        # 检查重置
        credits_info = await self.credits_service.get_user_credits(self.test_user_id, db)
        
        # 验证重置日期已更新
        reset_date = datetime.strptime(credits_info["last_reset_date"], "%Y-%m-%d").date()
        assert reset_date >= date.today()
        
        print(f"重置前日期: {last_week}")
        print(f"重置后日期: {reset_date}")
        print(f"当前余额: {credits_info['credits_remaining']}")
    
    async def test_usage_history(self, db):
        """测试Credits使用历史"""
        history = await self.credits_service.get_credits_usage_history(self.test_user_id, 1, 10, db)
        
        assert "items" in history
        assert "total" in history
        assert "page" in history
        
        print(f"历史记录数: {history['total']}")
        print(f"当前页记录: {len(history['items'])}")
    
    async def test_abuse_prevention(self, db):
        """测试防滥用机制"""
        # 确保有足够Credits
        await self.credits_service.purchase_credits(self.test_user_id, 10, db)
        purchase_records = await self.get_pending_purchases(db)
        
        for record in purchase_records:
            await self.credits_service.confirm_credits_purchase(record[0], db)
        
        # 快速连续消耗Credits，测试防滥用
        consumption_count = 0
        max_attempts = 15
        
        for i in range(max_attempts):
            try:
                await self.credits_service.consume_credits_for_batch_upload(self.test_user_id, db)
                consumption_count += 1
            except InsufficientCreditsError:
                break
        
        print(f"成功消耗次数: {consumption_count}")
        print(f"最大尝试次数: {max_attempts}")
        
        # 验证不能无限消耗
        assert consumption_count < max_attempts
    
    async def test_batch_reset(self, db):
        """测试批量重置"""
        # 创建多个测试用户
        test_users = [UUID(str(uuid4())) for _ in range(3)]
        
        for user_id in test_users:
            await self.create_additional_test_user(user_id, db)
            await self.credits_service.initialize_user_credits(user_id, db)
        
        # 执行批量重置
        reset_result = await self.credits_service.weekly_credits_reset_batch(db)
        
        assert "reset_count" in reset_result
        assert "total_users" in reset_result
        
        print(f"重置用户数: {reset_result['reset_count']}")
        print(f"总用户数: {reset_result['total_users']}")
        
        # 清理额外的测试用户
        for user_id in test_users:
            await self.cleanup_test_user(user_id, db)
    
    async def test_edge_cases(self, db):
        """测试边界条件"""
        # 测试购买0个Credits
        try:
            await self.credits_service.purchase_credits(self.test_user_id, 0, db)
            assert False, "应该抛出异常"
        except Exception as e:
            print(f"正确处理0个Credits购买: {str(e)}")
        
        # 测试购买超过限制的Credits
        try:
            await self.credits_service.purchase_credits(self.test_user_id, 101, db)
            assert False, "应该抛出异常"
        except Exception as e:
            print(f"正确处理超限购买: {str(e)}")
        
        # 测试不存在的购买记录确认
        try:
            fake_purchase_id = str(uuid4())
            await self.credits_service.confirm_credits_purchase(fake_purchase_id, db)
            assert False, "应该抛出异常"
        except Exception as e:
            print(f"正确处理不存在的购买记录: {str(e)}")
    
    async def get_pending_purchases(self, db):
        """获取待确认的购买记录"""
        query = text("""
            SELECT id FROM credit_purchase_records 
            WHERE user_id = :user_id AND status = 'pending'
        """)
        
        return db.execute(query, {"user_id": str(self.test_user_id)}).fetchall()
    
    async def create_additional_test_user(self, user_id: UUID, db):
        """创建额外的测试用户"""
        try:
            insert_user_query = text("""
                INSERT INTO users (id, username, email, password_hash, created_at)
                VALUES (:user_id, :username, :email, :password_hash, NOW())
                ON CONFLICT (id) DO NOTHING
            """)
            
            db.execute(insert_user_query, {
                "user_id": str(user_id),
                "username": f"test_user_{user_id.hex[:8]}",
                "email": f"test_{user_id.hex[:8]}@example.com",
                "password_hash": "test_hash"
            })
            
            db.commit()
            
        except Exception as e:
            print(f"创建额外测试用户失败: {str(e)}")
    
    async def cleanup_test_user(self, user_id: UUID, db):
        """清理单个测试用户"""
        try:
            # 删除Credits相关记录
            cleanup_queries = [
                "DELETE FROM credit_purchase_records WHERE user_id = :user_id",
                "DELETE FROM user_credits WHERE user_id = :user_id",
                "DELETE FROM users WHERE id = :user_id"
            ]
            
            for query in cleanup_queries:
                db.execute(text(query), {"user_id": str(user_id)})
            
            db.commit()
            
        except Exception as e:
            print(f"清理测试用户失败: {str(e)}")
    
    async def cleanup_test_data(self, db):
        """清理测试数据"""
        try:
            # 删除测试用户的所有相关数据
            cleanup_queries = [
                "DELETE FROM credit_purchase_records WHERE user_id = :user_id",
                "DELETE FROM user_credits WHERE user_id = :user_id",
                "DELETE FROM users WHERE id = :user_id"
            ]
            
            for query in cleanup_queries:
                db.execute(text(query), {"user_id": str(self.test_user_id)})
            
            db.commit()
            print("✅ 测试数据清理完成")
            
        except Exception as e:
            print(f"⚠️  清理测试数据失败: {str(e)}")


async def main():
    """主函数"""
    tester = CreditsSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())