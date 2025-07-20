#!/usr/bin/env python3
"""
将案件数据转换为任务数据脚本
这样律师就可以在接单平台看到并抢单
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from app.core.database import AsyncSessionLocal
from app.models.case import Case
from app.models.statistics import TaskPublishRecord


async def convert_cases_to_tasks():
    """将案件转换为可抢单任务"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始转换案件为可抢单任务...")
            
            # 查询未分配律师或状态为PENDING的案件
            cases_query = select(Case).where(
                or_(
                    Case.assigned_to_user_id.is_(None),
                    Case.status == "PENDING"
                )
            ).limit(50)  # 一次最多转换50个
            
            cases_result = await session.execute(cases_query)
            cases = cases_result.scalars().all()
            
            print(f"📋 找到 {len(cases)} 个待转换案件")
            
            converted_count = 0
            
            for case in cases:
                # 检查是否已经转换过
                existing_task = await session.scalar(
                    select(TaskPublishRecord).where(
                        TaskPublishRecord.source_case_id == case.id
                    )
                )
                
                if existing_task:
                    print(f"⚠️  案件 {case.case_number} 已转换过，跳过")
                    continue
                
                # 解析债务人信息
                debtor_info = {}
                if case.debtor_info:
                    if isinstance(case.debtor_info, str):
                        try:
                            debtor_info = json.loads(case.debtor_info)
                        except:
                            debtor_info = {"raw": case.debtor_info}
                    else:
                        debtor_info = case.debtor_info
                
                # 根据案件信息推断任务类型
                task_type = "debt_collection"  # 默认债务催收
                if case.description:
                    desc_lower = case.description.lower()
                    if "合同" in desc_lower:
                        task_type = "contract_review"
                    elif "咨询" in desc_lower:
                        task_type = "legal_consultation"
                    elif "律师函" in desc_lower:
                        task_type = "lawyer_letter"
                
                # 生成任务标题
                debtor_name = debtor_info.get("name", "未知债务人")
                case_amount = float(case.case_amount) if case.case_amount else 0
                
                if case_amount > 0:
                    title = f"{debtor_name}债务催收案 - ¥{case_amount:,.0f}"
                    budget = min(max(case_amount * 0.02, 500), 5000)  # 2%佣金，最低500，最高5000
                else:
                    title = f"{debtor_name}法律服务案"
                    budget = 800  # 默认预算
                
                # 生成详细描述
                description = f"""案件编号：{case.case_number}
债务人：{debtor_name}
联系方式：{debtor_info.get('phone', '待提供')}
地址：{debtor_info.get('address', '待提供')}
案件金额：¥{case_amount:,.2f}

案件描述：
{case.description or '详细信息请与委托人沟通'}

要求：
1. 专业处理债务催收事务
2. 按法律程序发送催收函件
3. 及时反馈处理进度
4. 确保符合相关法律法规""".strip()
                
                # 设置紧急程度
                urgency = "normal"
                if case.legal_status == "EXPIRING_SOON":
                    urgency = "urgent"
                elif case_amount and case_amount > 100000:
                    urgency = "high"
                
                # 创建任务记录
                task_record = TaskPublishRecord(
                    user_id=None,  # 系统生成的任务，暂时不分配用户
                    task_type=task_type,
                    title=title,
                    description=description,
                    target_info={
                        "debtor_info": debtor_info,
                        "case_number": case.case_number,
                        "source": "case_conversion",
                        "original_case_id": str(case.id)
                    },
                    amount=Decimal(str(budget)),
                    urgency=urgency,
                    status="published",  # 立即可抢单
                    source_case_id=case.id,  # 关联原案件ID
                    created_at=case.created_at or datetime.now()
                )
                
                session.add(task_record)
                converted_count += 1
                
                print(f"✅ 转换案件: {case.case_number} -> 任务: {title}")
            
            await session.commit()
            
            # 查询转换后的总任务数
            total_tasks = await session.scalar(
                select(func.count(TaskPublishRecord.id)).where(
                    and_(
                        TaskPublishRecord.status == "published",
                        TaskPublishRecord.assigned_to.is_(None)
                    )
                )
            )
            
            print(f"\n🎉 转换完成!")
            print(f"   - 新转换: {converted_count} 个案件")
            print(f"   - 总可抢单任务: {total_tasks} 个")
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            await session.rollback()
            raise


async def main():
    """主函数"""
    try:
        await convert_cases_to_tasks()
        print("✅ 案件转换任务完成")
    except Exception as e:
        print(f"💥 转换失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())