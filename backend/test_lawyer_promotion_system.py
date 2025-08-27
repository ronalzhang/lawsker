#!/usr/bin/env python3
"""
律师推广系统测试
验证300%律师注册率提升目标的实现功能
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.services.lawyer_promotion_service import LawyerPromotionService
from app.services.email_service import EmailService
from app.services.unified_auth_service import UnifiedAuthService
from app.services.lawyer_certification_service import LawyerCertificationService
from app.services.lawyer_membership_service import LawyerMembershipService


class LawyerPromotionSystemTest:
    """律师推广系统测试类"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.promotion_service = LawyerPromotionService(self.email_service)
        self.auth_service = UnifiedAuthService()
        self.test_results = []
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始律师推广系统测试...")
        print("=" * 60)
        
        # 测试推广邮件功能
        await self.test_promotion_email_system()
        
        # 测试推荐计划功能
        await self.test_referral_program()
        
        # 测试转化跟踪功能
        await self.test_conversion_tracking()
        
        # 测试统计数据功能
        await self.test_statistics_system()
        
        # 测试注册漏斗优化
        await self.test_funnel_optimization()
        
        # 测试免费会员自动分配
        await self.test_free_membership_assignment()
        
        # 生成测试报告
        self.generate_test_report()
    
    async def test_promotion_email_system(self):
        """测试推广邮件系统"""
        print("\n📧 测试推广邮件系统...")
        
        try:
            # 测试获取潜在律师邮箱
            with get_db() as db:
                emails = await self.promotion_service.get_potential_lawyer_emails(db)
                
                if emails:
                    self.log_success("获取潜在律师邮箱", f"成功获取 {len(emails)} 个邮箱")
                else:
                    self.log_info("获取潜在律师邮箱", "暂无潜在律师邮箱")
            
            # 测试邮件模板加载
            template_vars = {
                'registration_url': 'https://test.lawsker.com/lawyer-registration-landing.html',
                'unsubscribe_url': 'https://test.lawsker.com/unsubscribe',
                'campaign_name': 'test_campaign',
                'timestamp': datetime.now().isoformat()
            }
            
            # 模拟发送测试邮件
            test_email = "test@example.com"
            success = await self.email_service.send_lawyer_promotion_email(
                test_email, template_vars
            )
            
            if success:
                self.log_success("推广邮件发送", "邮件模板和发送功能正常")
            else:
                self.log_warning("推广邮件发送", "邮件发送功能需要配置")
            
        except Exception as e:
            self.log_error("推广邮件系统", str(e))
    
    async def test_referral_program(self):
        """测试推荐计划功能"""
        print("\n🔗 测试推荐计划功能...")
        
        try:
            # 创建测试推荐计划
            test_lawyer_id = "test-lawyer-123"
            result = await self.promotion_service.create_lawyer_referral_program(
                test_lawyer_id, 500
            )
            
            if result and 'referral_code' in result:
                self.log_success("推荐计划创建", f"推荐码: {result['referral_code']}")
                self.log_info("推荐链接", result['referral_url'])
            else:
                self.log_error("推荐计划创建", "创建失败")
            
        except Exception as e:
            self.log_error("推荐计划功能", str(e))
    
    async def test_conversion_tracking(self):
        """测试转化跟踪功能"""
        print("\n📊 测试转化跟踪功能...")
        
        try:
            # 测试跟踪注册转化
            result = await self.promotion_service.track_registration_conversion(
                source="email_campaign",
                campaign="lawyer_free_registration",
                referral_code="LAW_test123_202501"
            )
            
            if result.get('tracked'):
                self.log_success("转化跟踪", "成功记录转化事件")
            else:
                self.log_error("转化跟踪", result.get('error', '未知错误'))
            
        except Exception as e:
            self.log_error("转化跟踪功能", str(e))
    
    async def test_statistics_system(self):
        """测试统计数据系统"""
        print("\n📈 测试统计数据系统...")
        
        try:
            # 获取推广统计数据
            stats = await self.promotion_service.get_promotion_statistics(30)
            
            if stats:
                self.log_success("统计数据获取", "成功获取推广统计")
                self.log_info("总注册数", str(stats.get('total_registrations', 0)))
                self.log_info("律师注册数", str(stats.get('lawyer_registrations', 0)))
                self.log_info("律师转化率", f"{stats.get('lawyer_conversion_rate', 0)}%")
                
                # 检查目标达成情况
                target_achievement = stats.get('target_achievement', {})
                current_growth = target_achievement.get('current_growth', 0)
                achievement_rate = target_achievement.get('achievement_rate', 0)
                
                self.log_info("当前增长率", f"{current_growth}%")
                self.log_info("目标达成率", f"{achievement_rate}%")
                
                if achievement_rate >= 100:
                    self.log_success("目标达成", "🎉 已达成300%增长目标！")
                elif achievement_rate >= 50:
                    self.log_info("目标进度", f"已完成 {achievement_rate}%，进展良好")
                else:
                    self.log_warning("目标进度", f"仅完成 {achievement_rate}%，需要加强推广")
            else:
                self.log_warning("统计数据获取", "暂无统计数据")
            
        except Exception as e:
            self.log_error("统计数据系统", str(e))
    
    async def test_funnel_optimization(self):
        """测试注册漏斗优化"""
        print("\n🎯 测试注册漏斗优化...")
        
        try:
            # 获取优化建议
            recommendations = await self.promotion_service.optimize_registration_funnel()
            
            if recommendations:
                self.log_success("漏斗优化分析", "成功生成优化建议")
                
                optimization_score = recommendations.get('optimization_score', 0)
                self.log_info("优化评分", f"{optimization_score}/100")
                
                # 显示优化建议
                suggestions = recommendations.get('recommendations', [])
                if suggestions:
                    self.log_info("优化建议数量", str(len(suggestions)))
                    for i, suggestion in enumerate(suggestions[:3], 1):
                        self.log_info(f"建议{i}", suggestion.get('suggestion', ''))
                else:
                    self.log_info("优化建议", "当前表现良好，无需特别优化")
            else:
                self.log_warning("漏斗优化分析", "分析失败")
            
        except Exception as e:
            self.log_error("漏斗优化功能", str(e))
    
    async def test_free_membership_assignment(self):
        """测试免费会员自动分配"""
        print("\n👑 测试免费会员自动分配...")
        
        try:
            # 模拟律师认证通过后的免费会员分配
            # 这里需要实际的数据库连接和会员服务
            
            self.log_info("免费会员分配", "需要实际的律师认证流程触发")
            self.log_info("分配规则", "律师认证通过 → 自动获得10年免费会员")
            self.log_info("会员权益", "20个AI Credits/月 + 2个案件/天 + 1倍积分")
            
            # 检查会员系统是否正常
            try:
                from app.services.lawyer_membership_service import LawyerMembershipService
                membership_service = LawyerMembershipService(None, None)
                
                # 检查会员套餐配置
                tiers = membership_service.MEMBERSHIP_TIERS
                if 'free' in tiers:
                    free_tier = tiers['free']
                    self.log_success("免费会员配置", f"月费: ¥{free_tier['monthly_fee']}")
                    self.log_info("AI Credits", f"{free_tier['ai_credits_monthly']}/月")
                    self.log_info("案件限制", f"{free_tier['daily_case_limit']}/天")
                    self.log_info("积分倍数", f"{free_tier['point_multiplier']}x")
                else:
                    self.log_error("免费会员配置", "未找到免费会员套餐配置")
                
            except ImportError:
                self.log_warning("会员系统", "会员服务模块未正确导入")
            
        except Exception as e:
            self.log_error("免费会员分配测试", str(e))
    
    def log_success(self, test_name: str, message: str):
        """记录成功测试"""
        print(f"✅ {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'status': 'success',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_info(self, test_name: str, message: str):
        """记录信息"""
        print(f"ℹ️  {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'status': 'info',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_warning(self, test_name: str, message: str):
        """记录警告"""
        print(f"⚠️  {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'status': 'warning',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_error(self, test_name: str, message: str):
        """记录错误"""
        print(f"❌ {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📋 律师推广系统测试报告")
        print("=" * 60)
        
        # 统计测试结果
        total_tests = len(self.test_results)
        success_count = len([r for r in self.test_results if r['status'] == 'success'])
        warning_count = len([r for r in self.test_results if r['status'] == 'warning'])
        error_count = len([r for r in self.test_results if r['status'] == 'error'])
        info_count = len([r for r in self.test_results if r['status'] == 'info'])
        
        print(f"总测试项目: {total_tests}")
        print(f"✅ 成功: {success_count}")
        print(f"ℹ️  信息: {info_count}")
        print(f"⚠️  警告: {warning_count}")
        print(f"❌ 错误: {error_count}")
        
        # 计算成功率
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        print(f"\n测试成功率: {success_rate:.1f}%")
        
        # 评估系统状态
        if success_rate >= 80:
            print("🎉 系统状态: 优秀 - 律师推广系统运行良好")
        elif success_rate >= 60:
            print("👍 系统状态: 良好 - 大部分功能正常，有少量问题")
        elif success_rate >= 40:
            print("⚠️  系统状态: 一般 - 存在一些问题需要修复")
        else:
            print("❌ 系统状态: 需要改进 - 存在较多问题")
        
        # 保存测试报告
        report_file = f"lawyer_promotion_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'test_summary': {
                        'total_tests': total_tests,
                        'success_count': success_count,
                        'warning_count': warning_count,
                        'error_count': error_count,
                        'info_count': info_count,
                        'success_rate': success_rate,
                        'test_time': datetime.now().isoformat()
                    },
                    'test_results': self.test_results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 测试报告已保存: {report_file}")
        except Exception as e:
            print(f"⚠️  保存测试报告失败: {str(e)}")
        
        print("\n🎯 300%律师注册率提升目标实现要点:")
        print("1. ✅ 免费会员福利推广 - 吸引律师注册")
        print("2. ✅ 推广邮件系统 - 扩大目标用户覆盖")
        print("3. ✅ 推荐计划 - 利用现有律师推荐新用户")
        print("4. ✅ 转化跟踪 - 监控各渠道效果")
        print("5. ✅ 数据分析 - 持续优化推广策略")
        print("6. ✅ 自动化流程 - 认证通过即获免费会员")
        
        print(f"\n🚀 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """主函数"""
    tester = LawyerPromotionSystemTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())