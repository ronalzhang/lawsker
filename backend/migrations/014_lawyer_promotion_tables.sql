-- 律师推广系统数据表
-- 用于支持300%律师注册率提升目标

-- 律师推荐计划表
CREATE TABLE IF NOT EXISTS lawyer_referral_programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referral_code VARCHAR(50) UNIQUE NOT NULL,
    referral_url TEXT NOT NULL,
    bonus_points INTEGER DEFAULT 500,
    total_referrals INTEGER DEFAULT 0,
    successful_referrals INTEGER DEFAULT 0,
    total_bonus_earned INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 推广跟踪表
CREATE TABLE IF NOT EXISTS lawyer_promotion_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255),
    source VARCHAR(100) NOT NULL, -- 来源渠道：email, social, referral, organic等
    campaign VARCHAR(100), -- 活动名称
    referral_code VARCHAR(50), -- 推荐码
    event_type VARCHAR(50) NOT NULL, -- 事件类型：email_sent, email_opened, link_clicked, registration, certification
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    additional_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 推广活动表
CREATE TABLE IF NOT EXISTS lawyer_promotion_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_name VARCHAR(100) UNIQUE NOT NULL,
    campaign_type VARCHAR(50) NOT NULL, -- email, social, referral, paid_ads等
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_audience TEXT, -- 目标受众描述
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    budget_amount DECIMAL(10,2),
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    links_clicked INTEGER DEFAULT 0,
    registrations INTEGER DEFAULT 0,
    certifications INTEGER DEFAULT 0,
    conversion_cost DECIMAL(10,2), -- 每个转化的成本
    roi DECIMAL(5,2), -- 投资回报率
    status VARCHAR(20) DEFAULT 'active', -- active, paused, completed, cancelled
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 律师注册漏斗分析表
CREATE TABLE IF NOT EXISTS lawyer_registration_funnel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    source VARCHAR(100) NOT NULL,
    campaign VARCHAR(100),
    -- 漏斗各阶段数据
    visitors INTEGER DEFAULT 0, -- 访问者
    page_views INTEGER DEFAULT 0, -- 页面浏览
    form_starts INTEGER DEFAULT 0, -- 开始填写表单
    form_completions INTEGER DEFAULT 0, -- 完成表单
    email_verifications INTEGER DEFAULT 0, -- 邮箱验证
    identity_selections INTEGER DEFAULT 0, -- 身份选择
    lawyer_selections INTEGER DEFAULT 0, -- 选择律师身份
    cert_uploads INTEGER DEFAULT 0, -- 上传律师证
    cert_approvals INTEGER DEFAULT 0, -- 认证通过
    free_memberships INTEGER DEFAULT 0, -- 获得免费会员
    -- 转化率计算字段
    form_start_rate DECIMAL(5,2), -- 表单开始率
    form_completion_rate DECIMAL(5,2), -- 表单完成率
    email_verification_rate DECIMAL(5,2), -- 邮箱验证率
    lawyer_selection_rate DECIMAL(5,2), -- 律师身份选择率
    cert_upload_rate DECIMAL(5,2), -- 律师证上传率
    cert_approval_rate DECIMAL(5,2), -- 认证通过率
    overall_conversion_rate DECIMAL(5,2), -- 整体转化率
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 律师推广效果统计表
CREATE TABLE IF NOT EXISTS lawyer_promotion_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    -- 注册数据
    total_registrations INTEGER DEFAULT 0,
    lawyer_registrations INTEGER DEFAULT 0,
    user_registrations INTEGER DEFAULT 0,
    -- 认证数据
    cert_submissions INTEGER DEFAULT 0,
    cert_approvals INTEGER DEFAULT 0,
    cert_rejections INTEGER DEFAULT 0,
    -- 会员数据
    free_memberships_assigned INTEGER DEFAULT 0,
    professional_upgrades INTEGER DEFAULT 0,
    enterprise_upgrades INTEGER DEFAULT 0,
    -- 转化率
    lawyer_conversion_rate DECIMAL(5,2), -- 律师注册转化率
    cert_approval_rate DECIMAL(5,2), -- 认证通过率
    membership_upgrade_rate DECIMAL(5,2), -- 会员升级率
    -- 目标达成
    daily_target INTEGER DEFAULT 10, -- 每日目标律师注册数
    target_achievement_rate DECIMAL(5,2), -- 目标达成率
    cumulative_growth_rate DECIMAL(5,2), -- 累计增长率
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_referral_programs_referrer ON lawyer_referral_programs(referrer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_referral_programs_code ON lawyer_referral_programs(referral_code);
CREATE INDEX IF NOT EXISTS idx_lawyer_promotion_tracking_source ON lawyer_promotion_tracking(source, created_at);
CREATE INDEX IF NOT EXISTS idx_lawyer_promotion_tracking_campaign ON lawyer_promotion_tracking(campaign, created_at);
CREATE INDEX IF NOT EXISTS idx_lawyer_promotion_tracking_event ON lawyer_promotion_tracking(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_lawyer_promotion_campaigns_status ON lawyer_promotion_campaigns(status, created_at);
CREATE INDEX IF NOT EXISTS idx_lawyer_registration_funnel_date ON lawyer_registration_funnel(date, source);
CREATE INDEX IF NOT EXISTS idx_lawyer_promotion_stats_date ON lawyer_promotion_stats(date);

-- 创建视图：律师推广总览
CREATE OR REPLACE VIEW lawyer_promotion_overview AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) FILTER (WHERE event_type = 'email_sent') as emails_sent,
    COUNT(*) FILTER (WHERE event_type = 'email_opened') as emails_opened,
    COUNT(*) FILTER (WHERE event_type = 'link_clicked') as links_clicked,
    COUNT(*) FILTER (WHERE event_type = 'registration') as registrations,
    COUNT(*) FILTER (WHERE event_type = 'certification') as certifications,
    ROUND(
        COUNT(*) FILTER (WHERE event_type = 'email_opened')::DECIMAL / 
        NULLIF(COUNT(*) FILTER (WHERE event_type = 'email_sent'), 0) * 100, 2
    ) as open_rate,
    ROUND(
        COUNT(*) FILTER (WHERE event_type = 'link_clicked')::DECIMAL / 
        NULLIF(COUNT(*) FILTER (WHERE event_type = 'email_opened'), 0) * 100, 2
    ) as click_rate,
    ROUND(
        COUNT(*) FILTER (WHERE event_type = 'registration')::DECIMAL / 
        NULLIF(COUNT(*) FILTER (WHERE event_type = 'link_clicked'), 0) * 100, 2
    ) as conversion_rate
FROM lawyer_promotion_tracking
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- 创建视图：律师注册增长趋势
CREATE OR REPLACE VIEW lawyer_registration_growth AS
SELECT 
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) FILTER (WHERE account_type = 'lawyer') as lawyer_registrations,
    COUNT(*) as total_registrations,
    ROUND(
        COUNT(*) FILTER (WHERE account_type = 'lawyer')::DECIMAL / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as lawyer_percentage,
    -- 计算周环比增长率
    LAG(COUNT(*) FILTER (WHERE account_type = 'lawyer')) OVER (ORDER BY DATE_TRUNC('week', created_at)) as prev_week_lawyers,
    ROUND(
        (COUNT(*) FILTER (WHERE account_type = 'lawyer') - 
         LAG(COUNT(*) FILTER (WHERE account_type = 'lawyer')) OVER (ORDER BY DATE_TRUNC('week', created_at))
        )::DECIMAL / 
        NULLIF(LAG(COUNT(*) FILTER (WHERE account_type = 'lawyer')) OVER (ORDER BY DATE_TRUNC('week', created_at)), 0) * 100, 2
    ) as week_over_week_growth
FROM users
WHERE created_at >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;

-- 插入初始推广活动数据
INSERT INTO lawyer_promotion_campaigns (
    campaign_name, campaign_type, title, description, target_audience, 
    start_date, budget_amount, status, created_at
) VALUES 
(
    'lawyer_free_registration_2025', 
    'email', 
    '律师免费注册推广活动', 
    '通过邮件推广律师免费会员注册，目标实现300%增长', 
    '潜在律师用户、法律从业者、法学院学生',
    CURRENT_DATE,
    10000.00,
    'active',
    now()
),
(
    'lawyer_referral_program', 
    'referral', 
    '律师推荐计划', 
    '现有律师推荐新律师注册，双方获得积分奖励', 
    '已注册律师用户',
    CURRENT_DATE,
    5000.00,
    'active',
    now()
);

-- 插入初始统计数据（当天）
INSERT INTO lawyer_promotion_stats (
    date, daily_target, target_achievement_rate, cumulative_growth_rate
) VALUES (
    CURRENT_DATE, 
    15, -- 每日目标15个律师注册
    0.0, -- 初始达成率
    0.0  -- 初始增长率
);

-- 创建触发器函数：自动更新推广统计
CREATE OR REPLACE FUNCTION update_lawyer_promotion_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 当有新的律师注册时，更新统计数据
    IF NEW.account_type = 'lawyer' THEN
        INSERT INTO lawyer_promotion_stats (date, lawyer_registrations, total_registrations)
        VALUES (CURRENT_DATE, 1, 1)
        ON CONFLICT (date) DO UPDATE SET
            lawyer_registrations = lawyer_promotion_stats.lawyer_registrations + 1,
            total_registrations = lawyer_promotion_stats.total_registrations + 1,
            lawyer_conversion_rate = ROUND(
                (lawyer_promotion_stats.lawyer_registrations + 1)::DECIMAL / 
                (lawyer_promotion_stats.total_registrations + 1) * 100, 2
            );
    ELSE
        INSERT INTO lawyer_promotion_stats (date, total_registrations)
        VALUES (CURRENT_DATE, 1)
        ON CONFLICT (date) DO UPDATE SET
            total_registrations = lawyer_promotion_stats.total_registrations + 1,
            lawyer_conversion_rate = ROUND(
                lawyer_promotion_stats.lawyer_registrations::DECIMAL / 
                (lawyer_promotion_stats.total_registrations + 1) * 100, 2
            );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_lawyer_promotion_stats ON users;
CREATE TRIGGER trigger_update_lawyer_promotion_stats
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_lawyer_promotion_stats();

-- 添加注释
COMMENT ON TABLE lawyer_referral_programs IS '律师推荐计划表，用于跟踪律师推荐其他律师注册的情况';
COMMENT ON TABLE lawyer_promotion_tracking IS '律师推广跟踪表，记录各种推广事件和转化数据';
COMMENT ON TABLE lawyer_promotion_campaigns IS '律师推广活动表，管理各种推广活动的配置和效果';
COMMENT ON TABLE lawyer_registration_funnel IS '律师注册漏斗分析表，详细跟踪注册流程各环节的转化';
COMMENT ON TABLE lawyer_promotion_stats IS '律师推广效果统计表，汇总每日推广数据和目标达成情况';
COMMENT ON VIEW lawyer_promotion_overview IS '律师推广总览视图，提供推广活动的关键指标';
COMMENT ON VIEW lawyer_registration_growth IS '律师注册增长趋势视图，显示律师注册的增长情况';