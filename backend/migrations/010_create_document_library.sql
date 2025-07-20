-- 创建文书库表
-- 用于存储生成的法律文书，实现文书复用和管理

-- 文书库主表
CREATE TABLE IF NOT EXISTS document_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    document_type VARCHAR(50) NOT NULL, -- 文书类型：lawyer_letter, debt_collection, contract_review, legal_consultation, general_legal
    document_title VARCHAR(200) NOT NULL, -- 文书标题
    document_content TEXT NOT NULL, -- 文书内容
    template_tags TEXT[], -- 模板标签，用于匹配相似案件
    case_keywords TEXT[], -- 案件关键词
    case_type VARCHAR(100), -- 案件类型
    debtor_amount_range VARCHAR(50), -- 债务金额范围
    overdue_days_range VARCHAR(50), -- 逾期天数范围
    
    -- 使用统计
    usage_count INTEGER DEFAULT 0, -- 使用次数
    success_rate DECIMAL(5,2) DEFAULT 0, -- 成功率（基于完成率）
    last_used_at TIMESTAMP WITH TIME ZONE, -- 最后使用时间
    
    -- 质量评分
    ai_quality_score INTEGER DEFAULT 0, -- AI质量评分(0-100)
    lawyer_rating INTEGER DEFAULT 0, -- 律师评分(1-5星)
    client_feedback INTEGER DEFAULT 0, -- 客户反馈(1-5星)
    
    -- 元数据
    created_by UUID REFERENCES users(id), -- 创建者（可能是AI或律师）
    source_case_id UUID REFERENCES cases(id), -- 源案件ID
    generation_method VARCHAR(20) DEFAULT 'ai', -- 生成方式：ai, manual, template
    is_template BOOLEAN DEFAULT false, -- 是否为模板
    is_active BOOLEAN DEFAULT true, -- 是否启用
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 文书使用记录表
CREATE TABLE IF NOT EXISTS document_usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES document_library(id),
    case_id UUID REFERENCES cases(id),
    task_id UUID, -- 任务ID（如果有的话）
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 使用信息
    usage_type VARCHAR(20) NOT NULL, -- 使用类型：direct_use, modified_use, regenerated
    modifications_made TEXT, -- 所做的修改描述
    final_content TEXT, -- 最终使用的内容
    
    -- 效果反馈
    was_successful BOOLEAN, -- 是否成功（发送后的效果）
    client_response VARCHAR(500), -- 客户回复
    completion_time INTERVAL, -- 完成用时
    
    -- 时间戳
    used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_document_library_type ON document_library(document_type);
CREATE INDEX IF NOT EXISTS idx_document_library_tags ON document_library USING GIN(template_tags);
CREATE INDEX IF NOT EXISTS idx_document_library_keywords ON document_library USING GIN(case_keywords);
CREATE INDEX IF NOT EXISTS idx_document_library_usage ON document_library(usage_count DESC, success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_document_library_active ON document_library(is_active, document_type);
CREATE INDEX IF NOT EXISTS idx_document_usage_history_document ON document_usage_history(document_id);
CREATE INDEX IF NOT EXISTS idx_document_usage_history_case ON document_usage_history(case_id);

-- 更新时间戳触发器
CREATE OR REPLACE FUNCTION update_document_library_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_library_updated_at
    BEFORE UPDATE ON document_library
    FOR EACH ROW
    EXECUTE FUNCTION update_document_library_updated_at();

-- 自动更新使用统计的触发器
CREATE OR REPLACE FUNCTION update_document_usage_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 增加使用次数
    UPDATE document_library 
    SET usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE id = NEW.document_id;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_usage_stats
    AFTER INSERT ON document_usage_history
    FOR EACH ROW
    EXECUTE FUNCTION update_document_usage_stats();

-- 计算成功率的函数（定期调用）
CREATE OR REPLACE FUNCTION calculate_document_success_rates()
RETURNS void AS $$
BEGIN
    UPDATE document_library 
    SET success_rate = (
        SELECT COALESCE(
            (COUNT(CASE WHEN was_successful = true THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)),
            0
        )
        FROM document_usage_history 
        WHERE document_id = document_library.id 
        AND was_successful IS NOT NULL
    )
    WHERE usage_count > 0;
END;
$$ language 'plpgsql';

-- 插入一些初始模板数据
INSERT INTO document_library (
    tenant_id, document_type, document_title, document_content, 
    template_tags, case_keywords, is_template, generation_method,
    ai_quality_score, created_at
) VALUES 
(
    (SELECT id FROM tenants LIMIT 1),
    'lawyer_letter',
    '债务催收律师函模板',
    '律师函

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
[日期]',
    ARRAY['债务催收', '律师函', '还款通知'],
    ARRAY['债务', '催收', '律师函', '还款'],
    true,
    'template',
    95,
    CURRENT_TIMESTAMP
),
(
    (SELECT id FROM tenants LIMIT 1),
    'debt_collection',
    '债务清收通知书模板',
    '债务清收通知书

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
[日期]',
    ARRAY['债务清收', '催收通知', '还款提醒'],
    ARRAY['债务', '清收', '逾期', '还款'],
    true,
    'template',
    90,
    CURRENT_TIMESTAMP
);

COMMENT ON TABLE document_library IS '法律文书库 - 存储可复用的法律文书模板和生成内容';
COMMENT ON TABLE document_usage_history IS '文书使用历史 - 记录文书的使用情况和效果反馈';