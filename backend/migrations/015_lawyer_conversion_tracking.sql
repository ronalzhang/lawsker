-- 律师会员转化跟踪表
-- 用于实现20%付费会员转化率目标

-- 律师转化事件表
CREATE TABLE IF NOT EXISTS lawyer_conversion_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_context JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    session_id VARCHAR(255),
    user_agent TEXT,
    referrer TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_lawyer_conversion_events_lawyer_id 
        FOREIGN KEY (lawyer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_events_lawyer_id 
    ON lawyer_conversion_events(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_events_event_type 
    ON lawyer_conversion_events(event_type);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_events_timestamp 
    ON lawyer_conversion_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_events_session_id 
    ON lawyer_conversion_events(session_id);

-- 律师转化漏斗统计表（用于缓存计算结果）
CREATE TABLE IF NOT EXISTS lawyer_conversion_funnel_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    total_free_lawyers INTEGER NOT NULL DEFAULT 0,
    viewed_membership_page INTEGER NOT NULL DEFAULT 0,
    clicked_upgrade_button INTEGER NOT NULL DEFAULT 0,
    initiated_payment INTEGER NOT NULL DEFAULT 0,
    completed_payment INTEGER NOT NULL DEFAULT 0,
    conversion_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    UNIQUE(date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_funnel_stats_date 
    ON lawyer_conversion_funnel_stats(date DESC);

-- 律师个性化推荐记录表
CREATE TABLE IF NOT EXISTS lawyer_upgrade_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL,
    recommendation_type VARCHAR(100) NOT NULL,
    recommended_tier VARCHAR(50) NOT NULL,
    recommendation_data JSONB NOT NULL,
    shown_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    clicked BOOLEAN DEFAULT FALSE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    converted BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_lawyer_upgrade_recommendations_lawyer_id 
        FOREIGN KEY (lawyer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_upgrade_recommendations_lawyer_id 
    ON lawyer_upgrade_recommendations(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_upgrade_recommendations_shown_at 
    ON lawyer_upgrade_recommendations(shown_at DESC);
CREATE INDEX IF NOT EXISTS idx_lawyer_upgrade_recommendations_type 
    ON lawyer_upgrade_recommendations(recommendation_type);

-- A/B测试记录表
CREATE TABLE IF NOT EXISTS lawyer_conversion_ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id VARCHAR(100) NOT NULL,
    lawyer_id UUID NOT NULL,
    variant_id VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    converted BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMP WITH TIME ZONE,
    conversion_value DECIMAL(10,2),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_lawyer_conversion_ab_tests_lawyer_id 
        FOREIGN KEY (lawyer_id) REFERENCES users(id) ON DELETE CASCADE,
    
    UNIQUE(test_id, lawyer_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_ab_tests_test_id 
    ON lawyer_conversion_ab_tests(test_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_ab_tests_lawyer_id 
    ON lawyer_conversion_ab_tests(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_ab_tests_variant_id 
    ON lawyer_conversion_ab_tests(variant_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_ab_tests_assigned_at 
    ON lawyer_conversion_ab_tests(assigned_at DESC);

-- 转化率优化活动表
CREATE TABLE IF NOT EXISTS lawyer_conversion_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(100) NOT NULL, -- 'email', 'discount', 'notification', etc.
    target_audience JSONB, -- 目标受众条件
    campaign_config JSONB NOT NULL, -- 活动配置
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'planned', -- 'planned', 'active', 'paused', 'completed'
    target_lawyers INTEGER,
    reached_lawyers INTEGER DEFAULT 0,
    converted_lawyers INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,2) DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_campaigns_status 
    ON lawyer_conversion_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_campaigns_type 
    ON lawyer_conversion_campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_lawyer_conversion_campaigns_start_date 
    ON lawyer_conversion_campaigns(start_date DESC);

-- 活动参与记录表
CREATE TABLE IF NOT EXISTS lawyer_campaign_participations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL,
    lawyer_id UUID NOT NULL,
    participated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    action_taken VARCHAR(100), -- 'email_opened', 'link_clicked', 'upgraded', etc.
    action_at TIMESTAMP WITH TIME ZONE,
    converted BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMP WITH TIME ZONE,
    conversion_value DECIMAL(10,2),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_lawyer_campaign_participations_campaign_id 
        FOREIGN KEY (campaign_id) REFERENCES lawyer_conversion_campaigns(id) ON DELETE CASCADE,
    CONSTRAINT fk_lawyer_campaign_participations_lawyer_id 
        FOREIGN KEY (lawyer_id) REFERENCES users(id) ON DELETE CASCADE,
    
    UNIQUE(campaign_id, lawyer_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_campaign_participations_campaign_id 
    ON lawyer_campaign_participations(campaign_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_campaign_participations_lawyer_id 
    ON lawyer_campaign_participations(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_campaign_participations_participated_at 
    ON lawyer_campaign_participations(participated_at DESC);

-- 插入常见的转化事件类型
INSERT INTO lawyer_conversion_events (lawyer_id, event_type, event_context, timestamp) VALUES
('00000000-0000-0000-0000-000000000000', 'membership_page_view', '{"page": "membership", "source": "navigation"}', now() - INTERVAL '1 day'),
('00000000-0000-0000-0000-000000000000', 'upgrade_button_click', '{"tier": "professional", "source": "recommendation"}', now() - INTERVAL '1 day'),
('00000000-0000-0000-0000-000000000000', 'payment_initiated', '{"tier": "professional", "amount": 899}', now() - INTERVAL '1 day'),
('00000000-0000-0000-0000-000000000000', 'payment_completed', '{"tier": "professional", "amount": 899, "payment_method": "wechat"}', now() - INTERVAL '1 day')
ON CONFLICT DO NOTHING;

-- 创建视图：律师转化率统计
CREATE OR REPLACE VIEW lawyer_conversion_rate_stats AS
SELECT 
    DATE(lm.created_at) as date,
    COUNT(DISTINCT lm.lawyer_id) as total_lawyers,
    COUNT(DISTINCT CASE WHEN lm.membership_type != 'free' THEN lm.lawyer_id END) as paid_lawyers,
    COUNT(DISTINCT CASE WHEN lm.membership_type = 'free' THEN lm.lawyer_id END) as free_lawyers,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT lm.lawyer_id) > 0 
            THEN COUNT(DISTINCT CASE WHEN lm.membership_type != 'free' THEN lm.lawyer_id END) * 100.0 / COUNT(DISTINCT lm.lawyer_id)
            ELSE 0 
        END, 2
    ) as conversion_rate
FROM lawyer_memberships lm
WHERE lm.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(lm.created_at)
ORDER BY date DESC;

-- 创建视图：转化漏斗统计
CREATE OR REPLACE VIEW lawyer_conversion_funnel_view AS
WITH funnel_data AS (
    SELECT 
        COUNT(DISTINCT lm.lawyer_id) as total_free_lawyers,
        COUNT(DISTINCT CASE WHEN lce.event_type = 'membership_page_view' THEN lce.lawyer_id END) as viewed_membership,
        COUNT(DISTINCT CASE WHEN lce.event_type = 'upgrade_button_click' THEN lce.lawyer_id END) as clicked_upgrade,
        COUNT(DISTINCT CASE WHEN lce.event_type = 'payment_initiated' THEN lce.lawyer_id END) as initiated_payment,
        COUNT(DISTINCT CASE WHEN lce.event_type = 'payment_completed' THEN lce.lawyer_id END) as completed_payment
    FROM lawyer_memberships lm
    LEFT JOIN lawyer_conversion_events lce ON lm.lawyer_id = lce.lawyer_id 
        AND lce.timestamp >= CURRENT_DATE - INTERVAL '30 days'
    WHERE lm.membership_type = 'free'
        AND lm.created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    *,
    CASE WHEN total_free_lawyers > 0 THEN ROUND(viewed_membership * 100.0 / total_free_lawyers, 2) ELSE 0 END as view_rate,
    CASE WHEN viewed_membership > 0 THEN ROUND(clicked_upgrade * 100.0 / viewed_membership, 2) ELSE 0 END as click_rate,
    CASE WHEN clicked_upgrade > 0 THEN ROUND(initiated_payment * 100.0 / clicked_upgrade, 2) ELSE 0 END as initiation_rate,
    CASE WHEN initiated_payment > 0 THEN ROUND(completed_payment * 100.0 / initiated_payment, 2) ELSE 0 END as completion_rate,
    CASE WHEN total_free_lawyers > 0 THEN ROUND(completed_payment * 100.0 / total_free_lawyers, 2) ELSE 0 END as overall_rate
FROM funnel_data;

-- 创建函数：计算律师转化率
CREATE OR REPLACE FUNCTION calculate_lawyer_conversion_rate(days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    period_days INTEGER,
    total_lawyers BIGINT,
    paid_lawyers BIGINT,
    free_lawyers BIGINT,
    conversion_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        days_back as period_days,
        COUNT(DISTINCT lm.lawyer_id) as total_lawyers,
        COUNT(DISTINCT CASE WHEN lm.membership_type != 'free' THEN lm.lawyer_id END) as paid_lawyers,
        COUNT(DISTINCT CASE WHEN lm.membership_type = 'free' THEN lm.lawyer_id END) as free_lawyers,
        ROUND(
            CASE 
                WHEN COUNT(DISTINCT lm.lawyer_id) > 0 
                THEN COUNT(DISTINCT CASE WHEN lm.membership_type != 'free' THEN lm.lawyer_id END) * 100.0 / COUNT(DISTINCT lm.lawyer_id)
                ELSE 0 
            END, 2
        ) as conversion_rate
    FROM lawyer_memberships lm
    WHERE lm.created_at >= CURRENT_DATE - INTERVAL '1 day' * days_back;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器：自动更新转化漏斗统计
CREATE OR REPLACE FUNCTION update_conversion_funnel_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 当有新的转化事件时，更新当日的漏斗统计
    INSERT INTO lawyer_conversion_funnel_stats (
        date,
        total_free_lawyers,
        viewed_membership_page,
        clicked_upgrade_button,
        initiated_payment,
        completed_payment,
        conversion_rate
    )
    SELECT 
        CURRENT_DATE,
        (SELECT COUNT(DISTINCT lawyer_id) FROM lawyer_memberships WHERE membership_type = 'free'),
        COUNT(DISTINCT CASE WHEN event_type = 'membership_page_view' THEN lawyer_id END),
        COUNT(DISTINCT CASE WHEN event_type = 'upgrade_button_click' THEN lawyer_id END),
        COUNT(DISTINCT CASE WHEN event_type = 'payment_initiated' THEN lawyer_id END),
        COUNT(DISTINCT CASE WHEN event_type = 'payment_completed' THEN lawyer_id END),
        (SELECT conversion_rate FROM calculate_lawyer_conversion_rate(1))
    FROM lawyer_conversion_events
    WHERE DATE(timestamp) = CURRENT_DATE
    ON CONFLICT (date) DO UPDATE SET
        viewed_membership_page = EXCLUDED.viewed_membership_page,
        clicked_upgrade_button = EXCLUDED.clicked_upgrade_button,
        initiated_payment = EXCLUDED.initiated_payment,
        completed_payment = EXCLUDED.completed_payment,
        conversion_rate = EXCLUDED.conversion_rate,
        updated_at = now();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_conversion_funnel_stats ON lawyer_conversion_events;
CREATE TRIGGER trigger_update_conversion_funnel_stats
    AFTER INSERT ON lawyer_conversion_events
    FOR EACH ROW
    EXECUTE FUNCTION update_conversion_funnel_stats();

-- 添加注释
COMMENT ON TABLE lawyer_conversion_events IS '律师转化事件跟踪表，记录所有与会员转化相关的用户行为';
COMMENT ON TABLE lawyer_conversion_funnel_stats IS '律师转化漏斗统计表，缓存每日的转化漏斗数据';
COMMENT ON TABLE lawyer_upgrade_recommendations IS '律师升级推荐记录表，跟踪个性化推荐的效果';
COMMENT ON TABLE lawyer_conversion_ab_tests IS 'A/B测试记录表，用于测试不同转化策略的效果';
COMMENT ON TABLE lawyer_conversion_campaigns IS '转化率优化活动表，管理各种转化优化活动';
COMMENT ON TABLE lawyer_campaign_participations IS '活动参与记录表，跟踪律师参与转化活动的情况';

COMMENT ON VIEW lawyer_conversion_rate_stats IS '律师转化率统计视图，提供每日转化率数据';
COMMENT ON VIEW lawyer_conversion_funnel_view IS '转化漏斗统计视图，提供实时的转化漏斗数据';

COMMENT ON FUNCTION calculate_lawyer_conversion_rate IS '计算指定天数内的律师转化率';
COMMENT ON FUNCTION update_conversion_funnel_stats IS '自动更新转化漏斗统计数据的触发器函数';