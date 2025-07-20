#!/usr/bin/env python3
"""
创建文书库表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def create_document_library():
    """创建文书库表"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建文书库表...")
            
            # 创建文书库主表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS document_library (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id),
                    document_type VARCHAR(50) NOT NULL,
                    document_title VARCHAR(200) NOT NULL,
                    document_content TEXT NOT NULL,
                    template_tags TEXT[],
                    case_keywords TEXT[],
                    case_type VARCHAR(100),
                    debtor_amount_range VARCHAR(50),
                    overdue_days_range VARCHAR(50),
                    
                    usage_count INTEGER DEFAULT 0,
                    success_rate DECIMAL(5,2) DEFAULT 0,
                    last_used_at TIMESTAMP WITH TIME ZONE,
                    
                    ai_quality_score INTEGER DEFAULT 0,
                    lawyer_rating INTEGER DEFAULT 0,
                    client_feedback INTEGER DEFAULT 0,
                    
                    created_by UUID REFERENCES users(id),
                    source_case_id UUID REFERENCES cases(id),
                    generation_method VARCHAR(20) DEFAULT 'ai',
                    is_template BOOLEAN DEFAULT false,
                    is_active BOOLEAN DEFAULT true,
                    
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建文书使用记录表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS document_usage_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    document_id UUID NOT NULL REFERENCES document_library(id),
                    case_id UUID REFERENCES cases(id),
                    task_id UUID,
                    user_id UUID NOT NULL REFERENCES users(id),
                    
                    usage_type VARCHAR(20) NOT NULL,
                    modifications_made TEXT,
                    final_content TEXT,
                    
                    was_successful BOOLEAN,
                    client_response VARCHAR(500),
                    completion_time INTERVAL,
                    
                    used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP WITH TIME ZONE
                )
            """))
            
            # 创建索引
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_document_library_type ON document_library(document_type)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_document_library_usage ON document_library(usage_count DESC, success_rate DESC)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_document_library_active ON document_library(is_active, document_type)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_document_usage_history_document ON document_usage_history(document_id)"))
            
            await session.commit()
            print("✅ 文书库表创建成功")
            
            # 插入初始模板数据
            print("📝 插入初始模板数据...")
            
            # 获取租户ID
            tenant_result = await session.execute(text("SELECT id FROM tenants LIMIT 1"))
            tenant_id = tenant_result.scalar()
            
            if tenant_id:
                # 插入律师函模板
                await session.execute(text("""
                    INSERT INTO document_library (
                        tenant_id, document_type, document_title, document_content, 
                        template_tags, case_keywords, is_template, generation_method,
                        ai_quality_score, created_at
                    ) VALUES (
                        :tenant_id, :doc_type, :title, :content, :tags, :keywords, 
                        :is_template, :method, :score, CURRENT_TIMESTAMP
                    )
                """), {
                    'tenant_id': tenant_id,
                    'doc_type': 'lawyer_letter',
                    'title': '债务催收律师函模板',
                    'content': '''律师函

致：[债务人姓名]

您好！

本律师受[委托人]委托，就您拖欠[委托人]款项一事向您发出此函。

根据[委托人]提供的材料显示：
1. 您于[借款日期]向[委托人]借款人民币[金额]元
2. 约定还款期限为[还款期限]
3. 截至目前，您仍欠款[欠款金额]元未归还
4. 逾期时间已达[逾期天数]天

根据《中华人民共和国民法典》相关规定，您应当按约履行还款义务。现特此函告：

请您在收到本函后[期限]日内，将所欠款项[金额]元归还给[委托人]。

如您在规定期限内仍不履行还款义务，本律师将建议[委托人]通过法律途径解决，由此产生的一切法律后果及费用损失，均由您承担。

特此函告！

[律师姓名]
[律师事务所]
[日期]''',
                    'tags': ['债务催收', '律师函', '还款通知'],
                    'keywords': ['债务', '催收', '律师函', '还款'],
                    'is_template': True,
                    'method': 'template',
                    'score': 95
                })
                
                # 插入债务清收通知书模板
                await session.execute(text("""
                    INSERT INTO document_library (
                        tenant_id, document_type, document_title, document_content, 
                        template_tags, case_keywords, is_template, generation_method,
                        ai_quality_score, created_at
                    ) VALUES (
                        :tenant_id, :doc_type, :title, :content, :tags, :keywords, 
                        :is_template, :method, :score, CURRENT_TIMESTAMP
                    )
                """), {
                    'tenant_id': tenant_id,
                    'doc_type': 'debt_collection',
                    'title': '债务清收通知书模板',
                    'content': '''债务清收通知书

[债务人姓名]：

经查，您于[日期]通过[平台/机构]申请借款人民币[金额]元，约定还款期限为[期限]。截至[当前日期]，您尚欠本金[本金金额]元及相应利息费用，逾期[天数]天。

根据借款合同约定及相关法律法规，现通知如下：

一、债务情况
借款本金：[金额]元
逾期利息：[利息]元
逾期费用：[费用]元
合计应还：[总金额]元

二、还款要求
请您务必在[日期]前将上述款项一次性归还至指定账户。

三、法律后果
如您继续拖欠不还，我方将：
1. 上报征信系统，影响您的信用记录
2. 委托专业催收机构进行催收
3. 通过司法途径追讨债务

请您务必重视此事，及时履行还款义务。

联系电话：[电话]
[机构名称]
[日期]''',
                    'tags': ['债务清收', '催收通知', '还款提醒'],
                    'keywords': ['债务', '清收', '逾期', '还款'],
                    'is_template': True,
                    'method': 'template',
                    'score': 90
                })
                
                await session.commit()
                print("✅ 初始模板数据插入成功")
            
            print("\n🎉 文书库系统创建完成！")
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await create_document_library()
        print("✅ 文书库系统创建完成")
    except Exception as e:
        print(f"💥 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())