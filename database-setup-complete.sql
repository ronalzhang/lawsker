-- Lawsker业务优化系统 - 完整数据库初始化脚本
-- 版本: 1.0.0
-- 作者: Kiro AI Assistant
-- 日期: 2025-01-27

-- 设置数据库编码和时区
SET client_encoding = 'UTF8';
SET timezone = 'Asia/Shanghai';

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 基础用户表扩展（统一认证系统）
-- ============================================================================

-- 扩展现有用户表
ALTER TABLE users ADD COLUMN IF NOT EXISTS workspace_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(50) DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 创建工作台映射表
CREATE TABLE IF NOT EXISTS workspace_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id VARCHAR(255) NOT NULL UNIQUE,
    workspace_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, workspace_id)
);

-- 创建律师证认证申请表
CREATE TABLE IF NOT EXISTS lawyer_certification_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certificate_file_path TEXT NOT NULL,
    lawyer_name VARCHAR(255) NOT NULL,
    license_number VARCHAR(100) NOT NULL UNIQUE,
    law_firm VARCHAR(255),
    practice_areas TEXT[],
    status VARCHAR(50) DEFAULT 'pending',
    admin_id UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 演示账户系统
-- ============================================================================

-- 演示账户表
CREATE TABLE IF NOT EXISTS demo_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    demo_type VARCHAR(50) NOT NULL,
    demo_data JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 演示数据隔离表
CREATE TABLE IF NOT EXISTS demo_data_isolation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    demo_account_id UUID NOT NULL REFERENCES demo_accounts(id) ON DELETE CASCADE,
    table_name VARCHAR(255) NOT NULL,
    record_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 律师等级和积分系统
-- ============================================================================-- 律师等级配置表

CREATE TABLE IF NOT EXISTS lawyer_levels (
    id SERIAL PRIMARY KEY,
    level_number INTEGER NOT NULL UNIQUE,
    level_name VARCHAR(100) NOT NULL,
    level_description TEXT,
    required_points INTEGER NOT NULL,
    level_benefits JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师等级详情表
CREATE TABLE IF NOT EXISTS lawyer_level_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_level INTEGER DEFAULT 1,
    level_points INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    level_progress DECIMAL(5,2) DEFAULT 0.00,
    last_level_up TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(lawyer_id)
);

-- 积分变动记录表
CREATE TABLE IF NOT EXISTS lawyer_point_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    points_change INTEGER NOT NULL,
    multiplier DECIMAL(3,2) DEFAULT 1.00,
    context_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师拒绝案件记录表
CREATE TABLE IF NOT EXISTS lawyer_case_declines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID,
    decline_reason TEXT,
    points_deducted INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师暂停派单记录表
CREATE TABLE IF NOT EXISTS lawyer_suspension_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suspension_type VARCHAR(50) NOT NULL,
    suspension_duration INTEGER, -- 小时
    reason TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ends_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================================
-- 律师会员系统
-- ============================================================================

-- 律师会员表
CREATE TABLE IF NOT EXISTS lawyer_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    membership_type VARCHAR(50) NOT NULL DEFAULT 'free',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    benefits JSONB NOT NULL,
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_amount DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(lawyer_id)
);

-- 会员订阅历史表
CREATE TABLE IF NOT EXISTS lawyer_membership_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    membership_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    payment_amount DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 用户Credits系统
-- ============================================================================

-- 用户Credits表
CREATE TABLE IF NOT EXISTS user_credits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credits_weekly INTEGER DEFAULT 1,
    credits_remaining INTEGER DEFAULT 1,
    credits_purchased INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Credits购买记录表
CREATE TABLE IF NOT EXISTS credit_purchase_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credits_count INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Credits使用记录表
CREATE TABLE IF NOT EXISTS credit_usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credits_used INTEGER NOT NULL,
    usage_type VARCHAR(100) NOT NULL,
    context_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 批量上传任务表
CREATE TABLE IF NOT EXISTS batch_upload_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_status VARCHAR(50) DEFAULT 'pending',
    file_count INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    credits_consumed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- 企业客户满意度系统
-- ============================================================================-- 企业客户满
意度记录表
CREATE TABLE IF NOT EXISTS enterprise_customer_satisfaction (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_type VARCHAR(100) NOT NULL,
    satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 5),
    feedback_text TEXT,
    service_quality_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 客户满意度警报表
CREATE TABLE IF NOT EXISTS customer_satisfaction_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    alert_message TEXT NOT NULL,
    satisfaction_score INTEGER,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- 客户满意度改进措施表
CREATE TABLE IF NOT EXISTS customer_satisfaction_improvements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    improvement_type VARCHAR(100) NOT NULL,
    improvement_description TEXT NOT NULL,
    priority_level VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'planned',
    expected_impact TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    implemented_at TIMESTAMP WITH TIME ZONE
);

-- 客户改进任务表
CREATE TABLE IF NOT EXISTS customer_improvement_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    improvement_id UUID NOT NULL REFERENCES customer_satisfaction_improvements(id) ON DELETE CASCADE,
    task_description TEXT NOT NULL,
    assigned_to VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    due_date DATE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 律师推广营销系统
-- ============================================================================

-- 律师推荐计划表
CREATE TABLE IF NOT EXISTS lawyer_referral_programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referral_code VARCHAR(50) NOT NULL UNIQUE,
    referral_count INTEGER DEFAULT 0,
    total_rewards INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师推广跟踪表
CREATE TABLE IF NOT EXISTS lawyer_promotion_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id VARCHAR(100),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    source_channel VARCHAR(100) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    conversion_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师推广活动表
CREATE TABLE IF NOT EXISTS lawyer_promotion_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(100) NOT NULL,
    target_audience JSONB,
    campaign_config JSONB,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师注册漏斗分析表
CREATE TABLE IF NOT EXISTS lawyer_registration_funnel (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255),
    step_name VARCHAR(100) NOT NULL,
    step_data JSONB,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师推广效果统计表
CREATE TABLE IF NOT EXISTS lawyer_promotion_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stat_date DATE NOT NULL,
    campaign_id VARCHAR(100),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(stat_date, campaign_id, metric_name)
);

-- ============================================================================
-- 索引创建
-- ============================================================================

-- 用户相关索引
CREATE INDEX IF NOT EXISTS idx_users_workspace_id ON users(workspace_id);
CREATE INDEX IF NOT EXISTS idx_users_account_type ON users(account_type);
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);

-- 律师认证索引
CREATE INDEX IF NOT EXISTS idx_lawyer_cert_user_id ON lawyer_certification_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_cert_status ON lawyer_certification_requests(status);

-- 积分系统索引
CREATE INDEX IF NOT EXISTS idx_lawyer_level_details_lawyer_id ON lawyer_level_details(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_point_trans_lawyer_id ON lawyer_point_transactions(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_point_trans_created ON lawyer_point_transactions(created_at);

-- Credits系统索引
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_purchase_user_id ON credit_purchase_records(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_usage_user_id ON credit_usage_records(user_id);

-- 满意度系统索引
CREATE INDEX IF NOT EXISTS idx_satisfaction_customer_id ON enterprise_customer_satisfaction(customer_id);
CREATE INDEX IF NOT EXISTS idx_satisfaction_created ON enterprise_customer_satisfaction(created_at);
CREATE INDEX IF NOT EXISTS idx_satisfaction_score ON enterprise_customer_satisfaction(satisfaction_score);

-- 推广系统索引
CREATE INDEX IF NOT EXISTS idx_promotion_tracking_created ON lawyer_promotion_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_promotion_stats_date ON lawyer_promotion_stats(stat_date);

-- ============================================================================
-- 视图创建
-- ============================================================================-- 客户满意度
汇总视图
CREATE OR REPLACE VIEW customer_satisfaction_summary AS
SELECT 
    customer_id,
    COUNT(*) as total_responses,
    AVG(satisfaction_score) as avg_satisfaction,
    COUNT(CASE WHEN satisfaction_score >= 4 THEN 1 END) as satisfied_count,
    COUNT(CASE WHEN satisfaction_score >= 4.5 THEN 1 END) as highly_satisfied_count,
    COUNT(CASE WHEN satisfaction_score < 3 THEN 1 END) as unsatisfied_count,
    MAX(created_at) as last_feedback_date
FROM enterprise_customer_satisfaction
GROUP BY customer_id;

-- 律师推广总览视图
CREATE OR REPLACE VIEW lawyer_promotion_overview AS
SELECT 
    DATE(created_at) as promotion_date,
    source_channel,
    COUNT(*) as total_actions,
    COUNT(CASE WHEN action_type = 'registration' THEN 1 END) as registrations,
    COUNT(CASE WHEN action_type = 'conversion' THEN 1 END) as conversions
FROM lawyer_promotion_tracking
GROUP BY DATE(created_at), source_channel;

-- 律师注册增长趋势视图
CREATE OR REPLACE VIEW lawyer_registration_growth AS
SELECT 
    DATE(created_at) as registration_date,
    COUNT(*) as daily_registrations,
    SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) as cumulative_registrations
FROM users
WHERE account_type = 'lawyer'
GROUP BY DATE(created_at)
ORDER BY registration_date;

-- ============================================================================
-- 触发器函数
-- ============================================================================

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表创建更新时间戳触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_lawyer_cert_updated_at ON lawyer_certification_requests;
CREATE TRIGGER update_lawyer_cert_updated_at 
    BEFORE UPDATE ON lawyer_certification_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_lawyer_level_updated_at ON lawyer_level_details;
CREATE TRIGGER update_lawyer_level_updated_at 
    BEFORE UPDATE ON lawyer_level_details 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_credits_updated_at ON user_credits;
CREATE TRIGGER update_user_credits_updated_at 
    BEFORE UPDATE ON user_credits 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_lawyer_membership_updated_at ON lawyer_memberships;
CREATE TRIGGER update_lawyer_membership_updated_at 
    BEFORE UPDATE ON lawyer_memberships 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 初始数据插入
-- ============================================================================

-- 插入律师等级配置数据
INSERT INTO lawyer_levels (level_number, level_name, level_description, required_points, level_benefits) VALUES
(1, '见习律师', '刚开始执业的律师', 0, '{"daily_cases": 2, "ai_credits": 20, "priority": "low"}'),
(2, '初级律师', '有一定经验的律师', 1000, '{"daily_cases": 3, "ai_credits": 30, "priority": "low"}'),
(3, '中级律师', '经验丰富的律师', 3000, '{"daily_cases": 5, "ai_credits": 50, "priority": "medium"}'),
(4, '高级律师', '资深执业律师', 6000, '{"daily_cases": 8, "ai_credits": 80, "priority": "medium"}'),
(5, '专家律师', '专业领域专家', 10000, '{"daily_cases": 12, "ai_credits": 120, "priority": "high"}'),
(6, '资深律师', '行业资深专家', 15000, '{"daily_cases": 15, "ai_credits": 150, "priority": "high"}'),
(7, '首席律师', '律所首席律师', 25000, '{"daily_cases": 20, "ai_credits": 200, "priority": "highest"}'),
(8, '合伙人律师', '律所合伙人', 40000, '{"daily_cases": 30, "ai_credits": 300, "priority": "highest"}'),
(9, '高级合伙人', '资深合伙人', 60000, '{"daily_cases": 50, "ai_credits": 500, "priority": "vip"}'),
(10, '首席合伙人', '律所首席合伙人', 100000, '{"daily_cases": -1, "ai_credits": 1000, "priority": "vip"}')
ON CONFLICT (level_number) DO NOTHING;

-- ============================================================================
-- 权限设置
-- ============================================================================

-- 为lawsker_user用户授权
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lawsker_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lawsker_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO lawsker_user;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO lawsker_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO lawsker_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO lawsker_user;

-- ============================================================================
-- 完成信息
-- ============================================================================

-- 插入系统初始化记录
INSERT INTO system_info (key, value, created_at) VALUES 
('database_version', '1.0.0', NOW()),
('optimization_system_installed', 'true', NOW()),
('installation_date', NOW()::text, NOW())
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    updated_at = NOW();

-- 显示完成信息
DO $$
BEGIN
    RAISE NOTICE '=== Lawsker业务优化系统数据库初始化完成 ===';
    RAISE NOTICE '版本: 1.0.0';
    RAISE NOTICE '完成时间: %', NOW();
    RAISE NOTICE '创建的表数量: 20+';
    RAISE NOTICE '创建的索引数量: 15+';
    RAISE NOTICE '创建的视图数量: 3';
    RAISE NOTICE '创建的触发器数量: 5';
    RAISE NOTICE '律师等级配置: 10级';
    RAISE NOTICE '=== 数据库已就绪，可以启动应用服务 ===';
END $$;