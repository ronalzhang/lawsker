-- 创建律师会员系统所需的表
-- 只创建不存在的表

-- 律师会员表
CREATE TABLE IF NOT EXISTS lawyer_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL,
    membership_type VARCHAR(50) NOT NULL CHECK (membership_type IN ('free', 'professional', 'enterprise')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    benefits JSONB NOT NULL DEFAULT '{}',
    daily_case_limit INTEGER NOT NULL DEFAULT 5,
    monthly_amount_limit DECIMAL(15,2) NOT NULL DEFAULT 50000,
    ai_credits_monthly INTEGER NOT NULL DEFAULT 50,
    ai_credits_remaining INTEGER NOT NULL DEFAULT 50,
    ai_credits_used INTEGER NOT NULL DEFAULT 0,
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(lawyer_id)
);

-- 律师等级配置表
CREATE TABLE IF NOT EXISTS lawyer_levels (
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

-- 律师等级详细信息表
CREATE TABLE IF NOT EXISTS lawyer_level_details (
    lawyer_id UUID PRIMARY KEY,
    current_level INTEGER NOT NULL DEFAULT 1 REFERENCES lawyer_levels(level),
    level_points BIGINT NOT NULL DEFAULT 0,
    experience_points BIGINT NOT NULL DEFAULT 0,
    cases_completed INTEGER NOT NULL DEFAULT 0,
    cases_won INTEGER NOT NULL DEFAULT 0,
    cases_failed INTEGER NOT NULL DEFAULT 0,
    success_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    client_rating DECIMAL(3,2) NOT NULL DEFAULT 0,
    total_revenue DECIMAL(15,2) NOT NULL DEFAULT 0,
    total_online_hours INTEGER NOT NULL DEFAULT 0,
    total_cases_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    total_ai_credits_used INTEGER NOT NULL DEFAULT 0,
    total_paid_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    response_time_avg INTEGER NOT NULL DEFAULT 0,
    case_completion_speed DECIMAL(5,2) NOT NULL DEFAULT 0,
    quality_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    upgrade_eligible BOOLEAN DEFAULT FALSE,
    downgrade_risk BOOLEAN DEFAULT FALSE,
    next_review_date DATE,
    last_upgrade_date DATE,
    last_downgrade_date DATE,
    level_change_history JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师积分变动记录表
CREATE TABLE IF NOT EXISTS lawyer_point_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    points_change BIGINT NOT NULL,
    points_before BIGINT NOT NULL,
    points_after BIGINT NOT NULL,
    related_case_id UUID,
    related_review_id UUID,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户Credits表
CREATE TABLE IF NOT EXISTS user_credits (
    user_id UUID PRIMARY KEY,
    credits_weekly INTEGER NOT NULL DEFAULT 1,
    credits_remaining INTEGER NOT NULL DEFAULT 1,
    credits_purchased INTEGER NOT NULL DEFAULT 0,
    total_credits_used INTEGER NOT NULL DEFAULT 0,
    last_reset_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Credits购买记录表
CREATE TABLE IF NOT EXISTS credit_purchase_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    credits_count INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 50.00,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_order_id UUID,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师拒绝记录表
CREATE TABLE IF NOT EXISTS lawyer_case_declines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL,
    case_id UUID,
    decline_reason TEXT,
    points_penalty INTEGER NOT NULL DEFAULT 0,
    priority_impact DECIMAL(3,2) DEFAULT -0.1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 律师暂停派单记录表
CREATE TABLE IF NOT EXISTS lawyer_assignment_suspensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL,
    suspension_reason VARCHAR(100) NOT NULL,
    decline_count INTEGER NOT NULL,
    suspended_at TIMESTAMP WITH TIME ZONE NOT NULL,
    suspension_duration_hours INTEGER NOT NULL DEFAULT 24,
    lifted_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_memberships_lawyer_id ON lawyer_memberships(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_memberships_type_status ON lawyer_memberships(membership_type);
CREATE INDEX IF NOT EXISTS idx_lawyer_level_details_level ON lawyer_level_details(current_level);
CREATE INDEX IF NOT EXISTS idx_lawyer_point_transactions_lawyer_id ON lawyer_point_transactions(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_point_transactions_type ON lawyer_point_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_lawyer_point_transactions_created_at ON lawyer_point_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_reset_date ON user_credits(last_reset_date);

-- 插入律师等级配置数据
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
(10, '首席合伙人', '{"level_points": 800000, "cases_completed": 3000}', '{"membership_suggestion": "enterprise", "ai_credits": 2000}', 80, 3000000, 4.0)
ON CONFLICT (level) DO NOTHING;

-- 添加 tenant_id 字段到 users 表（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'tenant_id') THEN
        ALTER TABLE users ADD COLUMN tenant_id UUID;
    END IF;
END $$;