-- 企业客户满意度系统数据表
-- 用于跟踪和提升企业客户满意度至95%

-- 企业客户满意度记录表
CREATE TABLE IF NOT EXISTS enterprise_customer_satisfaction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    service_type VARCHAR(100) NOT NULL, -- data_analysis, legal_consultation, document_review
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
    alert_type VARCHAR(50) NOT NULL, -- low_satisfaction, declining_trend, critical_feedback
    alert_message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, resolved, dismissed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID
);

-- 客户满意度改进措施表
CREATE TABLE IF NOT EXISTS customer_satisfaction_improvements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    improvement_type VARCHAR(100) NOT NULL, -- service_training, process_optimization, communication_enhancement
    description TEXT NOT NULL,
    expected_impact TEXT,
    implementation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completion_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'planned', -- planned, in_progress, completed, cancelled
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
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, overdue
    completion_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 客户满意度趋势分析表（用于缓存计算结果）
CREATE TABLE IF NOT EXISTS customer_satisfaction_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    service_type VARCHAR(100),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    avg_satisfaction_score DECIMAL(3,2),
    total_responses INTEGER DEFAULT 0,
    satisfaction_rate DECIMAL(5,2), -- 满意度百分比
    trend_direction VARCHAR(20), -- improving, declining, stable
    trend_strength DECIMAL(3,2), -- 趋势强度
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(customer_id, service_type, period_start, period_end)
);

-- 企业客户服务质量指标表
CREATE TABLE IF NOT EXISTS enterprise_service_quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL, -- response_time, accuracy_rate, completion_rate
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(20), -- hours, percentage, count
    measurement_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_enterprise_satisfaction_customer_service 
ON enterprise_customer_satisfaction(customer_id, service_type);

CREATE INDEX IF NOT EXISTS idx_enterprise_satisfaction_created_at 
ON enterprise_customer_satisfaction(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_enterprise_satisfaction_score 
ON enterprise_customer_satisfaction(satisfaction_score);

CREATE INDEX IF NOT EXISTS idx_satisfaction_alerts_customer 
ON customer_satisfaction_alerts(customer_id, status);

CREATE INDEX IF NOT EXISTS idx_satisfaction_alerts_created 
ON customer_satisfaction_alerts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_satisfaction_improvements_customer 
ON customer_satisfaction_improvements(customer_id, status);

CREATE INDEX IF NOT EXISTS idx_improvement_tasks_customer 
ON customer_improvement_tasks(customer_id, status);

CREATE INDEX IF NOT EXISTS idx_improvement_tasks_due_date 
ON customer_improvement_tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_satisfaction_trends_customer 
ON customer_satisfaction_trends(customer_id, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_service_quality_metrics_customer 
ON enterprise_service_quality_metrics(customer_id, service_type, measurement_date);

-- 创建触发器以自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_enterprise_satisfaction_updated_at 
    BEFORE UPDATE ON enterprise_customer_satisfaction 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_satisfaction_improvements_updated_at 
    BEFORE UPDATE ON customer_satisfaction_improvements 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入初始配置数据
INSERT INTO enterprise_service_quality_metrics (customer_id, service_type, metric_name, metric_value, metric_unit)
VALUES 
    ('00000000-0000-0000-0000-000000000000', 'data_analysis', 'target_satisfaction_rate', 95.0, 'percentage'),
    ('00000000-0000-0000-0000-000000000000', 'legal_consultation', 'target_satisfaction_rate', 95.0, 'percentage'),
    ('00000000-0000-0000-0000-000000000000', 'document_review', 'target_satisfaction_rate', 95.0, 'percentage')
ON CONFLICT DO NOTHING;

-- 创建视图以便于查询满意度统计
CREATE OR REPLACE VIEW customer_satisfaction_summary AS
SELECT 
    customer_id,
    service_type,
    COUNT(*) as total_responses,
    AVG(satisfaction_score) as avg_satisfaction,
    COUNT(CASE WHEN satisfaction_score >= 4.0 THEN 1 END) as satisfied_count,
    COUNT(CASE WHEN satisfaction_score >= 4.5 THEN 1 END) as highly_satisfied_count,
    COUNT(CASE WHEN satisfaction_score < 3.0 THEN 1 END) as dissatisfied_count,
    ROUND((COUNT(CASE WHEN satisfaction_score >= 4.0 THEN 1 END) * 100.0 / COUNT(*)), 2) as satisfaction_rate,
    MIN(created_at) as first_feedback_date,
    MAX(created_at) as last_feedback_date
FROM enterprise_customer_satisfaction
GROUP BY customer_id, service_type;

-- 创建函数以计算满意度趋势
CREATE OR REPLACE FUNCTION calculate_satisfaction_trend(
    p_customer_id UUID,
    p_service_type VARCHAR DEFAULT NULL,
    p_months INTEGER DEFAULT 6
)
RETURNS TABLE (
    period_month DATE,
    avg_score DECIMAL(3,2),
    response_count INTEGER,
    satisfaction_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE_TRUNC('month', ecs.created_at)::DATE as period_month,
        ROUND(AVG(ecs.satisfaction_score), 2) as avg_score,
        COUNT(*)::INTEGER as response_count,
        ROUND((COUNT(CASE WHEN ecs.satisfaction_score >= 4.0 THEN 1 END) * 100.0 / COUNT(*)), 2) as satisfaction_rate
    FROM enterprise_customer_satisfaction ecs
    WHERE ecs.customer_id = p_customer_id
    AND (p_service_type IS NULL OR ecs.service_type = p_service_type)
    AND ecs.created_at >= (CURRENT_DATE - INTERVAL '1 month' * p_months)
    GROUP BY DATE_TRUNC('month', ecs.created_at)
    ORDER BY period_month DESC;
END;
$$ LANGUAGE plpgsql;

-- 创建函数以生成满意度改进建议
CREATE OR REPLACE FUNCTION generate_improvement_suggestions(
    p_customer_id UUID,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    suggestion_type VARCHAR,
    priority VARCHAR,
    description TEXT,
    current_score DECIMAL(3,2),
    target_score DECIMAL(3,2)
) AS $$
DECLARE
    avg_score DECIMAL(3,2);
    dissatisfaction_rate DECIMAL(5,2);
BEGIN
    -- 计算平均满意度
    SELECT AVG(satisfaction_score) INTO avg_score
    FROM enterprise_customer_satisfaction
    WHERE customer_id = p_customer_id
    AND created_at >= (CURRENT_DATE - INTERVAL '1 day' * p_days);
    
    -- 计算不满意率
    SELECT (COUNT(CASE WHEN satisfaction_score < 3.0 THEN 1 END) * 100.0 / COUNT(*))
    INTO dissatisfaction_rate
    FROM enterprise_customer_satisfaction
    WHERE customer_id = p_customer_id
    AND created_at >= (CURRENT_DATE - INTERVAL '1 day' * p_days);
    
    -- 生成建议
    IF avg_score < 3.5 THEN
        RETURN QUERY SELECT 
            'urgent_improvement'::VARCHAR,
            'high'::VARCHAR,
            '客户满意度较低，需要立即采取改进措施'::TEXT,
            avg_score,
            4.5::DECIMAL(3,2);
    END IF;
    
    IF dissatisfaction_rate > 15.0 THEN
        RETURN QUERY SELECT 
            'reduce_dissatisfaction'::VARCHAR,
            'high'::VARCHAR,
            '不满意率较高，需要重点关注客户反馈'::TEXT,
            avg_score,
            4.0::DECIMAL(3,2);
    END IF;
    
    IF avg_score < 4.5 THEN
        RETURN QUERY SELECT 
            'enhance_service'::VARCHAR,
            'medium'::VARCHAR,
            '提升服务质量以达到高满意度标准'::TEXT,
            avg_score,
            4.5::DECIMAL(3,2);
    END IF;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- 添加注释
COMMENT ON TABLE enterprise_customer_satisfaction IS '企业客户满意度记录表 - 用于跟踪客户对各项服务的满意度评分';
COMMENT ON TABLE customer_satisfaction_alerts IS '客户满意度警报表 - 当满意度低于阈值时自动生成警报';
COMMENT ON TABLE customer_satisfaction_improvements IS '客户满意度改进措施表 - 记录针对客户的具体改进行动';
COMMENT ON TABLE customer_improvement_tasks IS '客户改进跟踪任务表 - 跟踪改进措施的执行进度';
COMMENT ON TABLE customer_satisfaction_trends IS '客户满意度趋势分析表 - 缓存趋势分析结果';
COMMENT ON TABLE enterprise_service_quality_metrics IS '企业服务质量指标表 - 记录各项服务质量指标';

COMMENT ON VIEW customer_satisfaction_summary IS '客户满意度汇总视图 - 提供按客户和服务类型的满意度统计';

COMMENT ON FUNCTION calculate_satisfaction_trend IS '计算客户满意度趋势 - 返回指定时间段内的满意度变化趋势';
COMMENT ON FUNCTION generate_improvement_suggestions IS '生成满意度改进建议 - 基于当前满意度水平提供改进建议';