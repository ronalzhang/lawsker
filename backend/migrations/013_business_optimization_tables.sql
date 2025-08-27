-- Lawsker业务优化数据库迁移脚本
-- 版本: 013_business_optimization_tables.sql
-- 创建时间: 2025-01-25
-- 描述: 为业务优化方案添加必要的数据表，包括统一认证系统

-- =====================================================
-- 0. 统一认证系统表
-- =====================================================

-- 扩展用户表，添加认证相关字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS workspace_id VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) DEFAULT 'pending' CHECK (account_type IN ('pending', 'user', 'lawyer', 'lawyer_pending', 'admin'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_source VARCHAR(20) DEFAULT 'web';

-- 为现有用户生成workspace_id
UPDATE users SET workspace_id = CONCAT('ws-', SUBSTRING(MD5(RANDOM()::text), 1, 12)) WHERE workspace_id IS NULL;

-- 律师认证申请表
CREATE TABLE lawyer_certification_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certificate_file_path VARCHAR(500) NOT NULL,
    certificate_file_name VARCHAR(255) NOT NULL,
    lawyer_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) NOT NULL,
    law_firm VARCHAR(200),
    practice_areas JSONB DEFAULT '[]',
    years_of_experience INTEGER DEFAULT 0,
    education_background TEXT,
    specialization_certificates JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'under_review')),
    admin_review_notes TEXT,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 工作台ID映射表（安全访问）
CREATE TABLE workspace_mappings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    workspace_id VARCHAR(50) NOT NULL UNIQUE,
    workspace_type VARCHAR(20) NOT NULL CHECK (workspace_type IN ('user', 'lawyer', 'admin')),
    is_demo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 演示账户配置表
CREATE TABLE demo_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demo_type VARCHAR(20) NOT NULL CHECK (demo_type IN ('lawyer', 'user')),
    workspace_id VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    demo_data JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 1. 会员系统表
-- =====================================================

-- 用户会员表 (支持credits系统)
CREATE TABLE user_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    membership_type VARCHAR(50) NOT NULL CHECK (membership_type IN ('basic', 'premium', 'enterprise')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    benefits JSONB NOT NULL DEFAULT '{}',
    credits_monthly INTEGER NOT NULL DEFAULT 0, -- 每月批量任务credits额度
    credits_remaining INTEGER NOT NULL DEFAULT 0, -- 剩余credits
    credits_used INTEGER NOT NULL DEFAULT 0, -- 已使用credits
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'expired', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师会员表 (整合AI工具包到会员订阅)
CREATE TABLE lawyer_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    membership_type VARCHAR(50) NOT NULL CHECK (membership_type IN ('basic', 'premium', 'enterprise')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    benefits JSONB NOT NULL DEFAULT '{}',
    daily_case_limit INTEGER NOT NULL DEFAULT 5,
    monthly_amount_limit DECIMAL(15,2) NOT NULL DEFAULT 50000,
    ai_credits_monthly INTEGER NOT NULL DEFAULT 50, -- 每月AI credits额度
    ai_credits_remaining INTEGER NOT NULL DEFAULT 50, -- 剩余AI credits
    ai_credits_used INTEGER NOT NULL DEFAULT 0, -- 已使用AI credits
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 2. 律师等级系统表
-- =====================================================

-- 律师等级配置表
CREATE TABLE lawyer_levels (
    id SERIAL PRIMARY KEY,
    level INTEGER NOT NULL UNIQUE CHECK (level BETWEEN 1 AND 10),
    name VARCHAR(50) NOT NULL,
    requirements JSONB NOT NULL DEFAULT '{}',
    benefits JSONB NOT NULL DEFAULT '{}',
    daily_case_limit INTEGER NOT NULL DEFAULT 5,
    monthly_amount_limit DECIMAL(15,2) NOT NULL DEFAULT 50000,
    priority_weight DECIMAL(3,2) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师等级详细信息表 (传奇游戏式指数级积分制)
CREATE TABLE lawyer_level_details (
    lawyer_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_level INTEGER NOT NULL DEFAULT 1 REFERENCES lawyer_levels(level),
    level_points BIGINT NOT NULL DEFAULT 0, -- 使用BIGINT支持大积分值
    experience_points BIGINT NOT NULL DEFAULT 0, -- 总经验值，不会减少
    cases_completed INTEGER NOT NULL DEFAULT 0,
    cases_won INTEGER NOT NULL DEFAULT 0,
    cases_failed INTEGER NOT NULL DEFAULT 0,
    success_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    client_rating DECIMAL(3,2) NOT NULL DEFAULT 0,
    total_revenue DECIMAL(15,2) NOT NULL DEFAULT 0,
    total_online_hours INTEGER NOT NULL DEFAULT 0, -- 在线总时长(小时)
    total_cases_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 累计接案金额
    total_ai_credits_used INTEGER NOT NULL DEFAULT 0, -- 累计AI使用量
    total_paid_amount DECIMAL(15,2) NOT NULL DEFAULT 0, -- 累计付费金额
    response_time_avg INTEGER NOT NULL DEFAULT 0, -- 平均响应时间(分钟)
    case_completion_speed DECIMAL(5,2) NOT NULL DEFAULT 0, -- 案件完成速度评分
    quality_score DECIMAL(5,2) NOT NULL DEFAULT 0, -- 工作质量评分
    upgrade_eligible BOOLEAN DEFAULT FALSE,
    downgrade_risk BOOLEAN DEFAULT FALSE, -- 降级风险标记
    next_review_date DATE,
    last_upgrade_date DATE,
    last_downgrade_date DATE,
    level_change_history JSONB DEFAULT '[]', -- 等级变化历史
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 3. 智能匹配系统表
-- =====================================================

-- 案件邀请表
CREATE TABLE case_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invitation_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    reasoning TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    responded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(case_id, lawyer_id)
);

-- 匹配历史表
CREATE TABLE matching_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    algorithm_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    matching_factors JSONB NOT NULL DEFAULT '{}',
    candidate_lawyers JSONB NOT NULL DEFAULT '[]',
    selected_lawyers JSONB NOT NULL DEFAULT '[]',
    matching_duration INTEGER, -- 毫秒
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 4. 评价系统表
-- =====================================================

-- 案件评价表
CREATE TABLE case_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    overall_rating INTEGER NOT NULL CHECK (overall_rating BETWEEN 1 AND 5),
    professionalism_rating INTEGER NOT NULL CHECK (professionalism_rating BETWEEN 1 AND 5),
    response_speed_rating INTEGER NOT NULL CHECK (response_speed_rating BETWEEN 1 AND 5),
    communication_rating INTEGER NOT NULL CHECK (communication_rating BETWEEN 1 AND 5),
    result_satisfaction_rating INTEGER NOT NULL CHECK (result_satisfaction_rating BETWEEN 1 AND 5),
    written_feedback TEXT,
    is_anonymous BOOLEAN DEFAULT FALSE,
    sentiment_score DECIMAL(3,2), -- AI分析的情感分数
    key_topics JSONB DEFAULT '[]', -- AI提取的关键词
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(case_id, reviewer_id)
);

-- =====================================================
-- 5. AI工具使用记录表 (已整合到会员订阅)
-- =====================================================

-- AI工具使用记录
CREATE TABLE ai_tool_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    membership_id UUID REFERENCES lawyer_memberships(id) ON DELETE SET NULL,
    tool_type VARCHAR(50) NOT NULL,
    credits_consumed INTEGER NOT NULL DEFAULT 1,
    input_data JSONB,
    output_data JSONB,
    processing_time INTEGER, -- 毫秒
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    case_id UUID REFERENCES cases(id) ON DELETE SET NULL, -- 关联案件
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 6. 批量处理系统表 (区分单一付费和批量credits模式)
-- =====================================================

-- 批量上传任务表
CREATE TABLE batch_upload_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(20) NOT NULL DEFAULT 'debt_collection' CHECK (task_type IN ('debt_collection', 'single_case')),
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    total_records INTEGER NOT NULL DEFAULT 0,
    processed_records INTEGER NOT NULL DEFAULT 0,
    success_records INTEGER NOT NULL DEFAULT 0,
    error_records INTEGER NOT NULL DEFAULT 0,
    credits_cost INTEGER NOT NULL DEFAULT 0, -- 消耗的credits
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_details JSONB DEFAULT '[]',
    estimated_revenue DECIMAL(15,2) DEFAULT 0, -- 预估收入
    actual_revenue DECIMAL(15,2) DEFAULT 0, -- 实际收入
    commission_rate DECIMAL(5,4) DEFAULT 0.02, -- 分账比例(默认2%)
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 7. 索引创建
-- =====================================================

-- 会员系统索引
CREATE INDEX idx_user_memberships_user_id ON user_memberships(user_id);
CREATE INDEX idx_user_memberships_type_status ON user_memberships(membership_type, payment_status);
CREATE INDEX idx_lawyer_memberships_lawyer_id ON lawyer_memberships(lawyer_id);

-- 律师等级索引
CREATE INDEX idx_lawyer_level_details_level ON lawyer_level_details(current_level);
CREATE INDEX idx_lawyer_level_details_eligible ON lawyer_level_details(upgrade_eligible) WHERE upgrade_eligible = TRUE;

-- 邀请系统索引
CREATE INDEX idx_case_invitations_case_id ON case_invitations(case_id);
CREATE INDEX idx_case_invitations_lawyer_id ON case_invitations(lawyer_id);
CREATE INDEX idx_case_invitations_status ON case_invitations(status);
CREATE INDEX idx_case_invitations_expires ON case_invitations(expires_at);

-- 评价系统索引
CREATE INDEX idx_case_reviews_case_id ON case_reviews(case_id);
CREATE INDEX idx_case_reviews_lawyer_id ON case_reviews(lawyer_id);
CREATE INDEX idx_case_reviews_rating ON case_reviews(overall_rating);

-- AI工具包索引
CREATE INDEX idx_user_ai_packages_user_id ON user_ai_packages(user_id);
CREATE INDEX idx_user_ai_packages_active ON user_ai_packages(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_ai_tool_usage_user_id ON ai_tool_usage(user_id);
CREATE INDEX idx_ai_tool_usage_created_at ON ai_tool_usage(created_at);

-- 批量处理索引
CREATE INDEX idx_batch_upload_tasks_user_id ON batch_upload_tasks(user_id);
CREATE INDEX idx_batch_upload_tasks_status ON batch_upload_tasks(status);
CREATE INDEX idx_batch_upload_tasks_type ON batch_upload_tasks(task_type);

-- 律师积分系统索引
CREATE INDEX idx_lawyer_point_transactions_lawyer_id ON lawyer_point_transactions(lawyer_id);
CREATE INDEX idx_lawyer_point_transactions_type ON lawyer_point_transactions(transaction_type);
CREATE INDEX idx_lawyer_point_transactions_created_at ON lawyer_point_transactions(created_at);
CREATE INDEX idx_lawyer_online_sessions_lawyer_id ON lawyer_online_sessions(lawyer_id);
CREATE INDEX idx_lawyer_online_sessions_date ON lawyer_online_sessions(session_start);

-- 企业服务索引
CREATE INDEX idx_enterprise_clients_company_type ON enterprise_clients(company_type);
CREATE INDEX idx_enterprise_clients_status ON enterprise_clients(status);
CREATE INDEX idx_enterprise_subscriptions_client_id ON enterprise_subscriptions(client_id);
CREATE INDEX idx_enterprise_subscriptions_status ON enterprise_subscriptions(status);

-- =====================================================
-- 8. 触发器创建
-- =====================================================

-- 自动更新updated_at字段的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表添加触发器
CREATE TRIGGER update_user_memberships_updated_at BEFORE UPDATE ON user_memberships FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lawyer_memberships_updated_at BEFORE UPDATE ON lawyer_memberships FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lawyer_level_details_updated_at BEFORE UPDATE ON lawyer_level_details FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_tool_packages_updated_at BEFORE UPDATE ON ai_tool_packages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 9. 初始数据插入
-- =====================================================

-- 插入律师等级配置数据 (与会员订阅呼应的传奇游戏式积分制)
INSERT INTO lawyer_levels (level, name, requirements, benefits, daily_case_limit, monthly_amount_limit, priority_weight) VALUES
(1, '见习律师', '{"level_points": 0, "cases_completed": 0}', '{"membership_suggestion": "free", "ai_credits": 20}', 2, 5000, 1.0),
(2, '初级律师', '{"level_points": 500, "cases_completed": 3}', '{"membership_suggestion": "free", "ai_credits": 30}', 3, 8000, 1.1),
(3, '助理律师', '{"level_points": 1500, "cases_completed": 8}', '{"membership_suggestion": "professional", "ai_credits": 50}', 5, 15000, 1.2),
(4, '执业律师', '{"level_points": 4000, "cases_completed": 20}', '{"membership_suggestion": "professional", "ai_credits": 100}', 8, 50000, 1.3),
(5, '资深律师', '{"level_points": 10000, "cases_completed": 50}', '{"membership_suggestion": "professional", "ai_credits": 200}', 12, 100000, 1.5),
(6, '专业律师', '{"level_points": 25000, "cases_completed": 120}', '{"membership_suggestion": "professional", "ai_credits": 350}', 18, 200000, 1.7),
(7, '高级律师', '{"level_points": 60000, "cases_completed": 300}', '{"membership_suggestion": "enterprise", "ai_credits": 500}', 25, 400000, 2.0),
(8, '合伙人律师', '{"level_points": 150000, "cases_completed": 700}', '{"membership_suggestion": "enterprise", "ai_credits": 800}', 35, 800000, 2.5),
(9, '高级合伙人', '{"level_points": 350000, "cases_completed": 1500}', '{"membership_suggestion": "enterprise", "ai_credits": 1200}', 50, 1500000, 3.0),
(10, '首席合伙人', '{"level_points": 800000, "cases_completed": 3000}', '{"membership_suggestion": "enterprise", "ai_credits": 2000}', 80, 3000000, 4.0);

-- 插入企业服务套餐数据 (数据导向，不承诺成功率)
INSERT INTO enterprise_service_packages (package_name, package_type, monthly_fee, case_volume_limit, features, ai_credits_included, dedicated_support, sla_response_time) VALUES
('基础企业版', 'basic', 9999.00, 500, '["batch_debt_collection", "basic_reporting", "email_support", "success_rate_tracking"]', 1000, FALSE, 48),
('专业企业版', 'professional', 29999.00, 2000, '["batch_debt_collection", "advanced_reporting", "priority_support", "custom_templates", "success_rate_tracking", "custom_reports"]', 5000, TRUE, 24),
('旗舰企业版', 'enterprise', 99999.00, 10000, '["batch_debt_collection", "real_time_reporting", "dedicated_support", "custom_integration", "white_label", "success_rate_tracking", "api_access"]', 20000, TRUE, 4),
('定制企业版', 'custom', 199999.00, 50000, '["unlimited_features", "custom_development", "dedicated_team", "on_premise_deployment", "success_rate_tracking", "api_access"]', 100000, TRUE, 2);

-- 为现有律师用户创建等级详情记录
INSERT INTO lawyer_level_details (lawyer_id, current_level, level_points, cases_completed, success_rate, client_rating)
SELECT 
    u.id,
    1, -- 默认等级1
    0, -- 默认积分0
    COALESCE(lawyer_stats.cases_completed, 0),
    COALESCE(lawyer_stats.success_rate, 0),
    COALESCE(lawyer_stats.avg_rating, 0)
FROM users u
LEFT JOIN (
    SELECT 
        assigned_to_user_id,
        COUNT(*) as cases_completed,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate,
        AVG(COALESCE(client_rating, 0)) as avg_rating
    FROM cases 
    WHERE assigned_to_user_id IS NOT NULL
    GROUP BY assigned_to_user_id
) lawyer_stats ON u.id = lawyer_stats.assigned_to_user_id
WHERE EXISTS (
    SELECT 1 FROM user_roles ur 
    JOIN roles r ON ur.role_id = r.id 
    WHERE ur.user_id = u.id AND r.name = 'Lawyer'
);

-- 为现有用户创建工作台映射
INSERT INTO workspace_mappings (user_id, workspace_id, workspace_type)
SELECT 
    u.id,
    u.workspace_id,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM user_roles ur 
            JOIN roles r ON ur.role_id = r.id 
            WHERE ur.user_id = u.id AND r.name = 'Lawyer'
        ) THEN 'lawyer'
        WHEN EXISTS (
            SELECT 1 FROM user_roles ur 
            JOIN roles r ON ur.role_id = r.id 
            WHERE ur.user_id = u.id AND r.name = 'Admin'
        ) THEN 'admin'
        ELSE 'user'
    END
FROM users u
WHERE u.workspace_id IS NOT NULL;

-- 插入演示账户数据
INSERT INTO demo_accounts (demo_type, workspace_id, display_name, demo_data) VALUES
('lawyer', 'demo-lawyer-001', '张律师（演示）', '{
    "specialties": ["合同纠纷", "债务催收", "公司法务"],
    "experience_years": 8,
    "success_rate": 92.5,
    "cases_handled": 156,
    "client_rating": 4.8,
    "demo_cases": [
        {"id": "demo-case-001", "title": "合同违约纠纷", "amount": 50000, "status": "进行中"},
        {"id": "demo-case-002", "title": "债务催收案件", "amount": 120000, "status": "已完成"}
    ]
}'),
('user', 'demo-user-001', '李先生（演示）', '{
    "company": "某科技公司",
    "cases_published": 3,
    "total_amount": 180000,
    "demo_cases": [
        {"id": "demo-case-003", "title": "劳动合同纠纷", "amount": 30000, "status": "匹配中"}
    ]
}');

-- =====================================================
-- 10. 权限和安全设置
-- =====================================================

-- 创建只读视图用于报表
CREATE VIEW lawyer_performance_summary AS
SELECT 
    u.id as lawyer_id,
    u.username,
    p.full_name,
    lld.current_level,
    ll.name as level_name,
    lld.cases_completed,
    lld.success_rate,
    lld.client_rating,
    lld.total_revenue,
    lld.upgrade_eligible
FROM users u
JOIN profiles p ON u.id = p.user_id
JOIN lawyer_level_details lld ON u.id = lld.lawyer_id
JOIN lawyer_levels ll ON lld.current_level = ll.level
WHERE EXISTS (
    SELECT 1 FROM user_roles ur 
    JOIN roles r ON ur.role_id = r.id 
    WHERE ur.user_id = u.id AND r.name = 'Lawyer'
);

-- 创建案件匹配统计视图
CREATE VIEW case_matching_stats AS
SELECT 
    c.id as case_id,
    c.case_amount,
    c.status,
    COUNT(ci.id) as invitations_sent,
    COUNT(CASE WHEN ci.status = 'accepted' THEN 1 END) as invitations_accepted,
    COUNT(CASE WHEN ci.status = 'declined' THEN 1 END) as invitations_declined,
    AVG(ci.invitation_score) as avg_match_score
FROM cases c
LEFT JOIN case_invitations ci ON c.id = ci.case_id
GROUP BY c.id, c.case_amount, c.status;

-- =====================================================
-- 律师积分计算系统表
-- =====================================================

-- 律师积分变动记录表
CREATE TABLE lawyer_point_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'case_complete', 'good_review', 'bad_review', 'online_time', 'ai_usage', 'payment'
    points_change BIGINT NOT NULL, -- 可以是正数或负数
    points_before BIGINT NOT NULL,
    points_after BIGINT NOT NULL,
    related_case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    related_review_id UUID REFERENCES case_reviews(id) ON DELETE SET NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师在线时间记录表
CREATE TABLE lawyer_online_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER, -- 会话时长(分钟)
    points_earned INTEGER DEFAULT 0, -- 本次会话获得积分
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 企业服务系统表
-- =====================================================

-- 企业客户表
CREATE TABLE enterprise_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    company_type VARCHAR(50) NOT NULL, -- 'bank', 'lending_institution', 'law_firm', 'other'
    contact_person VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    business_license VARCHAR(100),
    service_type VARCHAR(50) NOT NULL, -- 'debt_collection', 'legal_consulting', 'compliance'
    contract_start_date DATE,
    contract_end_date DATE,
    monthly_fee DECIMAL(15,2) DEFAULT 0,
    case_volume_limit INTEGER DEFAULT 1000, -- 月案件量限制
    priority_level INTEGER DEFAULT 1, -- 优先级 1-5
    assigned_account_manager UUID REFERENCES users(id), -- 客户经理
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 企业服务套餐表
CREATE TABLE enterprise_service_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_name VARCHAR(100) NOT NULL,
    package_type VARCHAR(50) NOT NULL, -- 'basic', 'professional', 'enterprise', 'custom'
    monthly_fee DECIMAL(15,2) NOT NULL,
    case_volume_limit INTEGER NOT NULL,
    features JSONB NOT NULL DEFAULT '[]',
    ai_credits_included INTEGER DEFAULT 0,
    dedicated_support BOOLEAN DEFAULT FALSE,
    sla_response_time INTEGER DEFAULT 24, -- SLA响应时间(小时)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 企业客户订阅记录表
CREATE TABLE enterprise_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES enterprise_clients(id) ON DELETE CASCADE,
    package_id UUID NOT NULL REFERENCES enterprise_service_packages(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_fee DECIMAL(15,2) NOT NULL,
    cases_used INTEGER DEFAULT 0,
    cases_limit INTEGER NOT NULL,
    auto_renewal BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 用户Credits控制系统表
-- =====================================================

-- 用户Credits表
CREATE TABLE user_credits (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    credits_weekly INTEGER NOT NULL DEFAULT 1, -- 每周分配的credits
    credits_remaining INTEGER NOT NULL DEFAULT 1, -- 剩余credits
    credits_purchased INTEGER NOT NULL DEFAULT 0, -- 购买的credits
    total_credits_used INTEGER NOT NULL DEFAULT 0, -- 累计使用的credits
    last_reset_date DATE NOT NULL DEFAULT CURRENT_DATE, -- 最后重置日期
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Credits购买记录表
CREATE TABLE credit_purchase_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credits_count INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 50.00, -- 50元/个credit
    total_amount DECIMAL(10,2) NOT NULL,
    payment_order_id UUID,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 律师拒绝案件惩罚系统表
-- =====================================================

-- 律师拒绝记录表
CREATE TABLE lawyer_case_declines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    decline_reason TEXT,
    points_penalty INTEGER NOT NULL DEFAULT 0,
    priority_impact DECIMAL(3,2) DEFAULT -0.1, -- 对派单优先级的影响
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师暂停派单记录表
CREATE TABLE lawyer_assignment_suspensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    suspension_reason VARCHAR(100) NOT NULL,
    decline_count INTEGER NOT NULL, -- 导致暂停的拒绝次数
    suspended_at TIMESTAMP WITH TIME ZONE NOT NULL,
    suspension_duration_hours INTEGER NOT NULL DEFAULT 24,
    lifted_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 催收成功率统计表 (不承诺成功率，仅统计)
-- =====================================================

-- 催收成功率统计表
CREATE TABLE collection_success_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES enterprise_clients(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_cases INTEGER NOT NULL DEFAULT 0,
    cases_with_response INTEGER NOT NULL DEFAULT 0,
    cases_with_payment INTEGER NOT NULL DEFAULT 0,
    total_debt_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    recovered_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    response_rate DECIMAL(5,4) NOT NULL DEFAULT 0, -- 响应率
    recovery_rate DECIMAL(5,4) NOT NULL DEFAULT 0, -- 回收率
    average_recovery_time INTEGER, -- 平均回收时间(天)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 新增索引
-- =====================================================

-- 认证系统索引
CREATE INDEX idx_users_workspace_id ON users(workspace_id);
CREATE INDEX idx_users_account_type ON users(account_type);
CREATE INDEX idx_users_email_verified ON users(email_verified);
CREATE INDEX idx_lawyer_certification_requests_user_id ON lawyer_certification_requests(user_id);
CREATE INDEX idx_lawyer_certification_requests_status ON lawyer_certification_requests(status);
CREATE INDEX idx_workspace_mappings_workspace_id ON workspace_mappings(workspace_id);
CREATE INDEX idx_demo_accounts_demo_type ON demo_accounts(demo_type);
CREATE INDEX idx_demo_accounts_workspace_id ON demo_accounts(workspace_id);

-- Credits系统索引
CREATE INDEX idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX idx_user_credits_reset_date ON user_credits(last_reset_date);
CREATE INDEX idx_credit_purchase_records_user_id ON credit_purchase_records(user_id);
CREATE INDEX idx_credit_purchase_records_status ON credit_purchase_records(status);

-- 律师拒绝系统索引
CREATE INDEX idx_lawyer_case_declines_lawyer_id ON lawyer_case_declines(lawyer_id);
CREATE INDEX idx_lawyer_case_declines_case_id ON lawyer_case_declines(case_id);
CREATE INDEX idx_lawyer_case_declines_created_at ON lawyer_case_declines(created_at);
CREATE INDEX idx_lawyer_assignment_suspensions_lawyer_id ON lawyer_assignment_suspensions(lawyer_id);
CREATE INDEX idx_lawyer_assignment_suspensions_active ON lawyer_assignment_suspensions(is_active) WHERE is_active = TRUE;

-- 催收统计索引
CREATE INDEX idx_collection_success_stats_client_id ON collection_success_stats(client_id);
CREATE INDEX idx_collection_success_stats_period ON collection_success_stats(period_start, period_end);

-- =====================================================
-- 初始化用户Credits数据
-- =====================================================

-- 为所有现有用户初始化Credits
INSERT INTO user_credits (user_id, credits_weekly, credits_remaining)
SELECT id, 1, 1 FROM users 
WHERE EXISTS (
    SELECT 1 FROM user_roles ur 
    JOIN roles r ON ur.role_id = r.id 
    WHERE ur.user_id = users.id AND r.name IN ('User', 'Institution')
);

-- 提交事务
COMMIT;

-- 验证数据完整性
DO $$
BEGIN
    -- 检查认证系统表
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_certification_requests') THEN
        RAISE EXCEPTION '律师认证申请表创建失败';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspace_mappings') THEN
        RAISE EXCEPTION '工作台映射表创建失败';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'demo_accounts') THEN
        RAISE EXCEPTION '演示账户表创建失败';
    END IF;
    
    -- 检查会员系统表
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_levels') THEN
        RAISE EXCEPTION '律师等级表创建失败';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_credits') THEN
        RAISE EXCEPTION '用户Credits表创建失败';
    END IF;
    
    -- 检查初始数据是否插入成功
    IF (SELECT COUNT(*) FROM lawyer_levels) != 10 THEN
        RAISE EXCEPTION '律师等级初始数据插入失败';
    END IF;
    
    IF (SELECT COUNT(*) FROM demo_accounts) != 2 THEN
        RAISE EXCEPTION '演示账户初始数据插入失败';
    END IF;
    
    -- 检查用户表扩展字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'workspace_id') THEN
        RAISE EXCEPTION '用户表workspace_id字段添加失败';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'account_type') THEN
        RAISE EXCEPTION '用户表account_type字段添加失败';
    END IF;
    
    -- 统计创建的表数量
    DECLARE
        table_count INTEGER;
    BEGIN
        SELECT COUNT(*) INTO table_count 
        FROM information_schema.tables 
        WHERE table_name IN (
            'lawyer_certification_requests', 'workspace_mappings', 'demo_accounts',
            'user_memberships', 'lawyer_memberships', 'lawyer_levels', 'lawyer_level_details',
            'case_invitations', 'matching_history', 'case_reviews', 'ai_tool_usage',
            'batch_upload_tasks', 'lawyer_point_transactions', 'lawyer_online_sessions',
            'enterprise_clients', 'enterprise_service_packages', 'enterprise_subscriptions',
            'user_credits', 'credit_purchase_records', 'lawyer_case_declines',
            'lawyer_assignment_suspensions', 'collection_success_stats'
        );
        
        RAISE NOTICE '业务优化数据库迁移完成！';
        RAISE NOTICE '新增数据表数量: %', table_count;
        RAISE NOTICE '包含功能: 统一认证系统、会员订阅、积分系统、Credits控制、企业服务';
        RAISE NOTICE '演示账户已配置: 律师演示、用户演示';
    END;
END $$;