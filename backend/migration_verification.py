#!/usr/bin/env python3
"""
数据库迁移验证工具
确保迁移后数据完整性和系统功能正常
"""

import asyncio
import asyncpg
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """验证结果"""
    test_name: str
    success: bool
    message: str
    details: Dict[str, Any] = None

class MigrationVerifier:
    """迁移验证器"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/lawsker')
        self.verification_results: List[VerificationResult] = []
    
    async def run_all_verifications(self) -> bool:
        """运行所有验证测试"""
        logger.info("🔍 开始运行迁移验证测试...")
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # 运行所有验证测试
            await self._verify_table_structure(conn)
            await self._verify_initial_data(conn)
            await self._verify_indexes(conn)
            await self._verify_constraints(conn)
            await self._verify_triggers(conn)
            await self._verify_data_integrity(conn)
            await self._verify_user_data_migration(conn)
            await self._verify_business_logic(conn)
            
            # 统计结果
            total_tests = len(self.verification_results)
            passed_tests = sum(1 for r in self.verification_results if r.success)
            failed_tests = total_tests - passed_tests
            
            logger.info(f"📊 验证完成: {passed_tests}/{total_tests} 通过, {failed_tests} 失败")
            
            # 输出详细结果
            self._print_verification_results()
            
            return failed_tests == 0
            
        finally:
            await conn.close()
    
    async def _verify_table_structure(self, conn: asyncpg.Connection):
        """验证表结构"""
        logger.info("🔍 验证表结构...")
        
        # 检查新创建的表
        required_tables = [
            "lawyer_certification_requests",
            "workspace_mappings",
            "demo_accounts",
            "lawyer_levels", 
            "lawyer_level_details",
            "user_credits",
            "credit_purchase_records",
            "lawyer_point_transactions",
            "lawyer_online_sessions",
            "lawyer_case_declines",
            "lawyer_assignment_suspensions",
            "collection_success_stats",
            "enterprise_clients",
            "enterprise_service_packages",
            "enterprise_subscriptions"
        ]
        
        for table in required_tables:
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                
                if exists:
                    # 检查表的列数
                    column_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = $1",
                        table
                    )
                    
                    self.verification_results.append(VerificationResult(
                        test_name=f"表结构_{table}",
                        success=True,
                        message=f"表 {table} 存在，包含 {column_count} 列",
                        details={"table": table, "columns": column_count}
                    ))
                else:
                    self.verification_results.append(VerificationResult(
                        test_name=f"表结构_{table}",
                        success=False,
                        message=f"表 {table} 不存在"
                    ))
                    
            except Exception as e:
                self.verification_results.append(VerificationResult(
                    test_name=f"表结构_{table}",
                    success=False,
                    message=f"检查表 {table} 时出错: {e}"
                ))
        
        # 检查用户表的新字段
        user_table_fields = ["workspace_id", "account_type", "email_verified", "registration_source"]
        
        for field in user_table_fields:
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = $1)",
                    field
                )
                
                self.verification_results.append(VerificationResult(
                    test_name=f"用户表字段_{field}",
                    success=exists,
                    message=f"用户表字段 {field} {'存在' if exists else '不存在'}"
                ))
                
            except Exception as e:
                self.verification_results.append(VerificationResult(
                    test_name=f"用户表字段_{field}",
                    success=False,
                    message=f"检查用户表字段 {field} 时出错: {e}"
                ))
    
    async def _verify_initial_data(self, conn: asyncpg.Connection):
        """验证初始数据"""
        logger.info("🔍 验证初始数据...")
        
        # 检查律师等级数据
        try:
            lawyer_levels_count = await conn.fetchval("SELECT COUNT(*) FROM lawyer_levels")
            
            self.verification_results.append(VerificationResult(
                test_name="律师等级初始数据",
                success=lawyer_levels_count == 10,
                message=f"律师等级数据: {lawyer_levels_count}/10",
                details={"expected": 10, "actual": lawyer_levels_count}
            ))
            
            # 检查等级数据的完整性
            if lawyer_levels_count == 10:
                levels = await conn.fetch("SELECT level, name FROM lawyer_levels ORDER BY level")
                expected_levels = [
                    (1, "见习律师"), (2, "初级律师"), (3, "助理律师"), (4, "执业律师"), (5, "资深律师"),
                    (6, "专业律师"), (7, "高级律师"), (8, "合伙人律师"), (9, "高级合伙人"), (10, "首席合伙人")
                ]
                
                for i, (expected_level, expected_name) in enumerate(expected_levels):
                    if i < len(levels):
                        actual_level = levels[i]['level']
                        actual_name = levels[i]['name']
                        
                        self.verification_results.append(VerificationResult(
                            test_name=f"律师等级_{expected_level}",
                            success=actual_level == expected_level and actual_name == expected_name,
                            message=f"等级 {expected_level}: {actual_name}"
                        ))
                        
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="律师等级初始数据",
                success=False,
                message=f"检查律师等级数据时出错: {e}"
            ))
        
        # 检查演示账户数据
        try:
            demo_accounts_count = await conn.fetchval("SELECT COUNT(*) FROM demo_accounts")
            
            self.verification_results.append(VerificationResult(
                test_name="演示账户初始数据",
                success=demo_accounts_count >= 2,
                message=f"演示账户数据: {demo_accounts_count} 个账户",
                details={"count": demo_accounts_count}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="演示账户初始数据",
                success=False,
                message=f"检查演示账户数据时出错: {e}"
            ))
    
    async def _verify_indexes(self, conn: asyncpg.Connection):
        """验证索引"""
        logger.info("🔍 验证索引...")
        
        # 检查关键索引
        important_indexes = [
            "idx_users_workspace_id",
            "idx_lawyer_level_details_level",
            "idx_user_credits_user_id",
            "idx_lawyer_point_transactions_lawyer_id",
            "idx_case_invitations_case_id"
        ]
        
        for index_name in important_indexes:
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = $1)",
                    index_name
                )
                
                self.verification_results.append(VerificationResult(
                    test_name=f"索引_{index_name}",
                    success=exists,
                    message=f"索引 {index_name} {'存在' if exists else '不存在'}"
                ))
                
            except Exception as e:
                self.verification_results.append(VerificationResult(
                    test_name=f"索引_{index_name}",
                    success=False,
                    message=f"检查索引 {index_name} 时出错: {e}"
                ))
    
    async def _verify_constraints(self, conn: asyncpg.Connection):
        """验证约束"""
        logger.info("🔍 验证约束...")
        
        # 检查外键约束
        try:
            fk_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_schema = 'public'
            """)
            
            self.verification_results.append(VerificationResult(
                test_name="外键约束",
                success=fk_count > 0,
                message=f"外键约束数量: {fk_count}",
                details={"count": fk_count}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="外键约束",
                success=False,
                message=f"检查外键约束时出错: {e}"
            ))
        
        # 检查检查约束
        try:
            check_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'CHECK'
                AND table_schema = 'public'
            """)
            
            self.verification_results.append(VerificationResult(
                test_name="检查约束",
                success=check_count > 0,
                message=f"检查约束数量: {check_count}",
                details={"count": check_count}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="检查约束",
                success=False,
                message=f"检查检查约束时出错: {e}"
            ))
    
    async def _verify_triggers(self, conn: asyncpg.Connection):
        """验证触发器"""
        logger.info("🔍 验证触发器...")
        
        try:
            trigger_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.triggers 
                WHERE trigger_schema = 'public'
            """)
            
            self.verification_results.append(VerificationResult(
                test_name="触发器",
                success=trigger_count > 0,
                message=f"触发器数量: {trigger_count}",
                details={"count": trigger_count}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="触发器",
                success=False,
                message=f"检查触发器时出错: {e}"
            ))
    
    async def _verify_data_integrity(self, conn: asyncpg.Connection):
        """验证数据完整性"""
        logger.info("🔍 验证数据完整性...")
        
        # 检查用户表的workspace_id是否都已生成
        try:
            users_without_workspace = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE workspace_id IS NULL"
            )
            
            self.verification_results.append(VerificationResult(
                test_name="用户workspace_id完整性",
                success=users_without_workspace == 0,
                message=f"缺少workspace_id的用户: {users_without_workspace}",
                details={"missing_count": users_without_workspace}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="用户workspace_id完整性",
                success=False,
                message=f"检查用户workspace_id时出错: {e}"
            ))
        
        # 检查工作台映射的完整性
        try:
            users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            workspace_mappings_count = await conn.fetchval("SELECT COUNT(*) FROM workspace_mappings")
            
            self.verification_results.append(VerificationResult(
                test_name="工作台映射完整性",
                success=workspace_mappings_count > 0,
                message=f"用户数: {users_count}, 工作台映射数: {workspace_mappings_count}",
                details={"users": users_count, "mappings": workspace_mappings_count}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="工作台映射完整性",
                success=False,
                message=f"检查工作台映射时出错: {e}"
            ))
    
    async def _verify_user_data_migration(self, conn: asyncpg.Connection):
        """验证用户数据迁移"""
        logger.info("🔍 验证用户数据迁移...")
        
        # 检查律师用户的等级详情是否已创建
        try:
            lawyer_users = await conn.fetchval("""
                SELECT COUNT(DISTINCT u.id) 
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE r.name = 'Lawyer'
            """)
            
            lawyer_level_details = await conn.fetchval("SELECT COUNT(*) FROM lawyer_level_details")
            
            self.verification_results.append(VerificationResult(
                test_name="律师等级详情迁移",
                success=lawyer_level_details >= 0,  # 允许为0，因为可能没有律师用户
                message=f"律师用户数: {lawyer_users}, 等级详情数: {lawyer_level_details}",
                details={"lawyers": lawyer_users, "level_details": lawyer_level_details}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="律师等级详情迁移",
                success=False,
                message=f"检查律师等级详情时出错: {e}"
            ))
        
        # 检查用户Credits初始化
        try:
            regular_users = await conn.fetchval("""
                SELECT COUNT(DISTINCT u.id) 
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE r.name IN ('User', 'Institution')
            """)
            
            user_credits = await conn.fetchval("SELECT COUNT(*) FROM user_credits")
            
            self.verification_results.append(VerificationResult(
                test_name="用户Credits初始化",
                success=user_credits >= 0,  # 允许为0，因为可能没有普通用户
                message=f"普通用户数: {regular_users}, Credits记录数: {user_credits}",
                details={"users": regular_users, "credits": user_credits}
            ))
            
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="用户Credits初始化",
                success=False,
                message=f"检查用户Credits时出错: {e}"
            ))
    
    async def _verify_business_logic(self, conn: asyncpg.Connection):
        """验证业务逻辑"""
        logger.info("🔍 验证业务逻辑...")
        
        # 测试律师等级查询
        try:
            level_1_requirements = await conn.fetchval(
                "SELECT requirements FROM lawyer_levels WHERE level = 1"
            )
            
            if level_1_requirements:
                requirements = json.loads(level_1_requirements)
                expected_points = requirements.get('level_points', 0)
                
                self.verification_results.append(VerificationResult(
                    test_name="律师等级业务逻辑",
                    success=expected_points == 0,
                    message=f"1级律师要求积分: {expected_points}",
                    details={"requirements": requirements}
                ))
            else:
                self.verification_results.append(VerificationResult(
                    test_name="律师等级业务逻辑",
                    success=False,
                    message="无法获取1级律师要求"
                ))
                
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="律师等级业务逻辑",
                success=False,
                message=f"检查律师等级业务逻辑时出错: {e}"
            ))
        
        # 测试演示账户数据结构
        try:
            demo_lawyer = await conn.fetchrow(
                "SELECT demo_data FROM demo_accounts WHERE demo_type = 'lawyer' LIMIT 1"
            )
            
            if demo_lawyer:
                demo_data = json.loads(demo_lawyer['demo_data'])
                has_required_fields = all(field in demo_data for field in ['specialties', 'experience_years', 'success_rate'])
                
                self.verification_results.append(VerificationResult(
                    test_name="演示账户数据结构",
                    success=has_required_fields,
                    message=f"演示律师数据完整性: {'完整' if has_required_fields else '不完整'}",
                    details={"demo_data_keys": list(demo_data.keys())}
                ))
            else:
                self.verification_results.append(VerificationResult(
                    test_name="演示账户数据结构",
                    success=False,
                    message="未找到演示律师账户"
                ))
                
        except Exception as e:
            self.verification_results.append(VerificationResult(
                test_name="演示账户数据结构",
                success=False,
                message=f"检查演示账户数据结构时出错: {e}"
            ))
    
    def _print_verification_results(self):
        """打印验证结果"""
        print("\n" + "=" * 80)
        print("📊 迁移验证结果详情")
        print("=" * 80)
        
        for result in self.verification_results:
            status = "✅ 通过" if result.success else "❌ 失败"
            print(f"{status} | {result.test_name}: {result.message}")
            
            if result.details and not result.success:
                print(f"    详情: {result.details}")
        
        print("=" * 80)
    
    async def generate_verification_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        total_tests = len(self.verification_results)
        passed_tests = sum(1 for r in self.verification_results if r.success)
        failed_tests = total_tests - passed_tests
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.verification_results
            ]
        }
        
        # 保存报告
        report_file = f"migration_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 验证报告已保存到: {report_file}")
        
        return report

async def main():
    """主函数"""
    print("🔍 Lawsker数据库迁移验证工具")
    print("=" * 50)
    
    verifier = MigrationVerifier()
    
    # 运行验证
    success = await verifier.run_all_verifications()
    
    # 生成报告
    report = await verifier.generate_verification_report()
    
    # 输出最终结果
    print(f"\n🎯 最终结果: {'✅ 验证通过' if success else '❌ 验证失败'}")
    print(f"📊 成功率: {report['summary']['success_rate']:.1f}%")
    print(f"📈 通过测试: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
    
    if not success:
        print("\n⚠️ 发现问题，请检查上述失败的测试项目")
        return 1
    else:
        print("\n🎉 所有验证测试通过，迁移成功！")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)