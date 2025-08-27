-- 企业客户满意度系统核心表
-- 专注于满意度跟踪和95%目标达成

-- 企业客户满意度记录表
CREATE TABLE IF NOT EXISTS enterprise_customer_satisfaction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    satisfaction_score DECIMAL(3,2) NOT NULL CHECK (satisfaction_score >= 1.0 AND satisfaction_score <= 5.0),
    feedback_text TEXT,
    service_quality_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 客户满意度警报表
CREATE TABLE IF NOT EXISTS customer_satisfaction_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    avg_satisfaction_score DECIMAL(3,2) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID
);

-- 客户满意度改进措施表
CREATE TABLE IF NOT EXISTS customer_satisfaction_improvements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    improvement_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    expected_impact TEXT,
    implementation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completion_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'planned',
    assigned_to VARCHAR(100),
    results TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 客户改进跟踪任务表
CREATE TABLE IF NOT EXISTS customer_improvement_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    improvement_id UUID REFERENCES customer_satisfaction_improvements(id),
    task_type VARCHAR(100) NOT NULL,
    task_description TEXT NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    assigned_to VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    completion_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_enterprise_satisfaction_customer_service 
ON enterprise_customer_satisfaction(customer_id, service_type);

CREATE INDEX IF NOT EXISTS idx_enterprise_satisfaction_created_at 
ON enterprise_customer_satisfaction(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_satisfaction_alerts_customer 
ON customer_satisfaction_alerts(customer_id, status);

CREATE INDEX IF NOT EXISTS idx_satisfaction_improvements_customer 
ON customer_satisfaction_improvements(customer_id, status);

-- 插入测试数据以验证95%满意度目标
INSERT INTO enterprise_customer_satisfaction (customer_id, service_type, satisfaction_score, feedback_text, service_quality_metrics)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 'data_analysis', 4.8, '数据分析非常准确，服务质量优秀', '{"response_time": 1.5, "accuracy_rate": 98.0}'),
    ('11111111-1111-1111-1111-111111111111', 'legal_consultation', 4.6, '法律建议专业，解答详细', '{"response_time": 2.0, "completeness": 95.0}'),
    ('22222222-2222-2222-2222-222222222222', 'document_review', 4.9, '文档审查细致，发现了重要问题', '{"accuracy_rate": 99.0, "thoroughness": 97.0}'),
    ('22222222-2222-2222-2222-222222222222', 'data_analysis', 4.7, '数据报告清晰易懂', '{"response_time": 1.8, "clarity": 96.0}'),
    ('33333333-3333-3333-3333-333333333333', 'legal_consultation', 4.5, '律师专业水平高', '{"expertise": 94.0, "communication": 92.0}')
ON CONFLICT DO NOTHING;

-- 创建满意度汇总视图
CREATE OR REPLACE VIEW customer_satisfaction_summary AS
SELECT 
    customer_id,
    service_type,
    COUNT(*) as total_responses,
    AVG(satisfaction_score) as avg_satisfaction,
    COUNT(CASE WHEN satisfaction_score >= 4.0 THEN 1 END) as satisfied_count,
    ROUND((COUNT(CASE WHEN satisfaction_score >= 4.0 THEN 1 END) * 100.0 / COUNT(*)), 2) as satisfaction_rate,
    MAX(created_at) as last_feedback_date
FROM enterprise_customer_satisfaction
GROUP BY customer_id, service_type;

COMMENT ON TABLE enterprise_customer_satisfaction IS '企业客户满意度记录表 - 目标95%满意度';
COMMENT ON TABLE customer_satisfaction_alerts IS '客户满意度警报表 - 低满意度自动警报';
COMMENT ON TABLE customer_satisfaction_improvements IS '客户满意度改进措施表 - 提升至95%的具体行动';
COMMENT ON VIEW customer_satisfaction_summary IS '客户满意度汇总视图 - 快速查看满意度统计';