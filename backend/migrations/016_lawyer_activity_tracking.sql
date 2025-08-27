-- 律师活跃度跟踪系统数据表
-- 用于提升律师活跃度50%的目标

-- 律师活动日志表
CREATE TABLE IF NOT EXISTS lawyer_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_date DATE NOT NULL,
    activity_time TIME NOT NULL,
    context JSONB,
    ip_address INET,
    user_agent TEXT,
    session_duration INTEGER DEFAULT 0, -- 会话持续时间（秒）
    quality_score INTEGER DEFAULT 0, -- 质量得分 0-100
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 律师每日活跃度汇总表
CREATE TABLE IF NOT EXISTS lawyer_daily_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    total_activity_score INTEGER NOT NULL DEFAULT 0,
    activity_count INTEGER NOT NULL DEFAULT 0,
    activity_breakdown JSONB, -- 各类活动的计数
    first_activity_time TIMESTAMP WITH TIME ZONE,
    last_activity_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lawyer_id, activity_date)
);

-- 律师活跃度等级表
CREATE TABLE IF NOT EXISTS lawyer_activity_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_level VARCHAR(20) NOT NULL DEFAULT 'inactive',
    total_score INTEGER NOT NULL DEFAULT 0,
    active_days INTEGER NOT NULL DEFAULT 0,
    avg_daily_score DECIMAL(10,2) DEFAULT 0,
    max_daily_score INTEGER DEFAULT 0,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lawyer_id)
);

-- 律师每日任务完成表
CREATE TABLE IF NOT EXISTS lawyer_daily_task_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    completion_date DATE NOT NULL,
    points_earned INTEGER NOT NULL DEFAULT 0,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 律师活跃度里程碑表
CREATE TABLE IF NOT EXISTS lawyer_activity_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    milestone_key VARCHAR(100) NOT NULL,
    milestone_type VARCHAR(50) NOT NULL,
    threshold_value INTEGER NOT NULL,
    current_value INTEGER NOT NULL,
    reward_points INTEGER NOT NULL DEFAULT 0,
    achieved_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lawyer_id, milestone_key)
);

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_lawyer_activity_logs_lawyer_date 
ON lawyer_activity_logs(lawyer_id, activity_date DESC);

CREATE INDEX IF NOT EXISTS idx_lawyer_activity_logs_type_date 
ON lawyer_activity_logs(activity_type, activity_date DESC);

CREATE INDEX IF NOT EXISTS idx_lawyer_daily_activity_lawyer_date 
ON lawyer_daily_activity(lawyer_id, activity_date DESC);

CREATE INDEX IF NOT EXISTS idx_lawyer_daily_activity_date_score 
ON lawyer_daily_activity(activity_date DESC, total_activity_score DESC);

CREATE INDEX IF NOT EXISTS idx_lawyer_activity_levels_level_score 
ON lawyer_activity_levels(activity_level, total_score DESC);

CREATE INDEX IF NOT EXISTS idx_lawyer_daily_task_completions_lawyer_date 
ON lawyer_daily_task_completions(lawyer_id, completion_date DESC);

CREATE INDEX IF NOT EXISTS idx_lawyer_daily_task_completions_task_date 
ON lawyer_daily_task_completions(task_type, completion_date DESC);

CREATE INDEX IF NOT EXISTS idx_lawyer_activity_milestones_lawyer_date 
ON lawyer_activity_milestones(lawyer_id, achieved_date DESC);

-- 添加活跃度等级检查约束
ALTER TABLE lawyer_activity_levels 
ADD CONSTRAINT chk_activity_level 
CHECK (activity_level IN ('inactive', 'low', 'moderate', 'active', 'highly_active', 'super_active'));

-- 添加任务类型检查约束
ALTER TABLE lawyer_daily_task_completions 
ADD CONSTRAINT chk_task_type 
CHECK (task_type IN ('login', 'respond_to_case', 'complete_case', 'update_profile', 'use_ai_tool', 'online_1hour', 'client_message'));

-- 添加里程碑类型检查约束
ALTER TABLE lawyer_activity_milestones 
ADD CONSTRAINT chk_milestone_type 
CHECK (milestone_type IN ('consecutive_days', 'total_active_days', 'total_score', 'best_daily_score'));

-- 创建活跃度统计视图
CREATE OR REPLACE VIEW lawyer_activity_stats AS
SELECT 
    l.lawyer_id,
    u.username,
    p.full_name,
    lal.activity_level,
    lal.total_score,
    lal.active_days,
    lal.avg_daily_score,
    lal.max_daily_score,
    lld.current_level as lawyer_level,
    ll.name as lawyer_level_name,
    lm.membership_type,
    -- 最近7天活跃度
    COALESCE(recent.recent_score, 0) as recent_7days_score,
    COALESCE(recent.recent_days, 0) as recent_7days_active,
    -- 连续活跃天数（简化计算）
    CASE 
        WHEN lda_today.activity_date = CURRENT_DATE THEN 1
        ELSE 0 
    END as is_active_today
FROM (
    SELECT DISTINCT lawyer_id FROM lawyer_daily_activity
) l
JOIN users u ON l.lawyer_id = u.id
LEFT JOIN profiles p ON u.id = p.user_id
LEFT JOIN lawyer_activity_levels lal ON l.lawyer_id = lal.lawyer_id
LEFT JOIN lawyer_level_details lld ON l.lawyer_id = lld.lawyer_id
LEFT JOIN lawyer_levels ll ON lld.current_level = ll.level
LEFT JOIN lawyer_memberships lm ON l.lawyer_id = lm.lawyer_id
LEFT JOIN lawyer_daily_activity lda_today ON l.lawyer_id = lda_today.lawyer_id 
    AND lda_today.activity_date = CURRENT_DATE
LEFT JOIN (
    SELECT 
        lawyer_id,
        SUM(total_activity_score) as recent_score,
        COUNT(*) as recent_days
    FROM lawyer_daily_activity 
    WHERE activity_date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY lawyer_id
) recent ON l.lawyer_id = recent.lawyer_id;

-- 创建活跃度排行榜视图
CREATE OR REPLACE VIEW lawyer_activity_leaderboard AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY lal.total_score DESC, lal.active_days DESC) as rank,
    l.lawyer_id,
    u.username,
    p.full_name,
    lal.activity_level,
    lal.total_score,
    lal.active_days,
    lal.avg_daily_score,
    lld.current_level as lawyer_level,
    ll.name as lawyer_level_name,
    lm.membership_type,
    -- 活跃度等级颜色
    CASE lal.activity_level
        WHEN 'inactive' THEN '#ef4444'
        WHEN 'low' THEN '#f97316'
        WHEN 'moderate' THEN '#eab308'
        WHEN 'active' THEN '#22c55e'
        WHEN 'highly_active' THEN '#3b82f6'
        WHEN 'super_active' THEN '#8b5cf6'
        ELSE '#6b7280'
    END as level_color
FROM lawyer_activity_levels lal
JOIN users u ON lal.lawyer_id = u.id
LEFT JOIN profiles p ON u.id = p.user_id
LEFT JOIN lawyer_level_details lld ON lal.lawyer_id = lld.lawyer_id
LEFT JOIN lawyer_levels ll ON lld.current_level = ll.level
LEFT JOIN lawyer_memberships lm ON lal.lawyer_id = lm.lawyer_id
WHERE lal.total_score > 0
ORDER BY lal.total_score DESC, lal.active_days DESC;

-- 插入活跃度等级配置数据
INSERT INTO system_configs (config_key, config_value, description, config_type) VALUES
('activity_levels', '{
    "inactive": {"min_score": 0, "max_score": 100, "name": "不活跃", "color": "#ef4444"},
    "low": {"min_score": 101, "max_score": 300, "name": "低活跃", "color": "#f97316"},
    "moderate": {"min_score": 301, "max_score": 600, "name": "中等活跃", "color": "#eab308"},
    "active": {"min_score": 601, "max_score": 900, "name": "活跃", "color": "#22c55e"},
    "highly_active": {"min_score": 901, "max_score": 1500, "name": "高度活跃", "color": "#3b82f6"},
    "super_active": {"min_score": 1501, "max_score": 999999, "name": "超级活跃", "color": "#8b5cf6"}
}', '律师活跃度等级配置', 'json')
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO system_configs (config_key, config_value, description, config_type) VALUES
('daily_activity_tasks', '{
    "login": {"points": 10, "description": "每日登录", "max_per_day": 1},
    "respond_to_case": {"points": 25, "description": "响应案件", "max_per_day": 5},
    "complete_case": {"points": 50, "description": "完成案件", "max_per_day": 3},
    "update_profile": {"points": 15, "description": "更新个人资料", "max_per_day": 1},
    "use_ai_tool": {"points": 8, "description": "使用AI工具", "max_per_day": 10},
    "online_1hour": {"points": 12, "description": "在线1小时", "max_per_day": 8},
    "client_message": {"points": 5, "description": "回复客户消息", "max_per_day": 20}
}', '每日活跃度任务配置', 'json')
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO system_configs (config_key, config_value, description, config_type) VALUES
('activity_milestones', '{
    "consecutive_days_7": {"threshold": 7, "reward_points": 500, "title": "连续活跃一周"},
    "consecutive_days_30": {"threshold": 30, "reward_points": 2000, "title": "连续活跃一月"},
    "total_active_days_100": {"threshold": 100, "reward_points": 3000, "title": "累计活跃100天"},
    "total_score_10000": {"threshold": 10000, "reward_points": 1500, "title": "累计活跃度10000分"},
    "best_daily_score_500": {"threshold": 500, "reward_points": 800, "title": "单日活跃度500分"}
}', '活跃度里程碑配置', 'json')
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- 创建活跃度统计函数
CREATE OR REPLACE FUNCTION calculate_lawyer_activity_level(p_lawyer_id UUID)
RETURNS TABLE(
    activity_level VARCHAR(20),
    total_score INTEGER,
    active_days INTEGER,
    avg_daily_score DECIMAL(10,2)
) AS $$
DECLARE
    v_total_score INTEGER;
    v_active_days INTEGER;
    v_avg_score DECIMAL(10,2);
    v_level VARCHAR(20);
BEGIN
    -- 计算最近30天的活跃度
    SELECT 
        COALESCE(SUM(lda.total_activity_score), 0),
        COUNT(DISTINCT lda.activity_date),
        COALESCE(AVG(lda.total_activity_score), 0)
    INTO v_total_score, v_active_days, v_avg_score
    FROM lawyer_daily_activity lda
    WHERE lda.lawyer_id = p_lawyer_id 
    AND lda.activity_date >= CURRENT_DATE - INTERVAL '30 days';
    
    -- 确定活跃度等级
    IF v_total_score <= 100 THEN
        v_level := 'inactive';
    ELSIF v_total_score <= 300 THEN
        v_level := 'low';
    ELSIF v_total_score <= 600 THEN
        v_level := 'moderate';
    ELSIF v_total_score <= 900 THEN
        v_level := 'active';
    ELSIF v_total_score <= 1500 THEN
        v_level := 'highly_active';
    ELSE
        v_level := 'super_active';
    END IF;
    
    RETURN QUERY SELECT v_level, v_total_score, v_active_days, v_avg_score;
END;
$$ LANGUAGE plpgsql;

-- 创建连续活跃天数计算函数
CREATE OR REPLACE FUNCTION get_consecutive_activity_days(p_lawyer_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_consecutive_days INTEGER := 0;
    v_current_date DATE := CURRENT_DATE;
    v_activity_exists BOOLEAN;
BEGIN
    LOOP
        -- 检查当前日期是否有活动
        SELECT EXISTS(
            SELECT 1 FROM lawyer_daily_activity 
            WHERE lawyer_id = p_lawyer_id 
            AND activity_date = v_current_date
        ) INTO v_activity_exists;
        
        IF v_activity_exists THEN
            v_consecutive_days := v_consecutive_days + 1;
            v_current_date := v_current_date - INTERVAL '1 day';
        ELSE
            EXIT;
        END IF;
        
        -- 防止无限循环，最多检查100天
        IF v_consecutive_days >= 100 THEN
            EXIT;
        END IF;
    END LOOP;
    
    RETURN v_consecutive_days;
END;
$$ LANGUAGE plpgsql;

-- 创建活跃度更新触发器
CREATE OR REPLACE FUNCTION update_lawyer_activity_level()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新律师活跃度等级
    INSERT INTO lawyer_activity_levels (
        lawyer_id, activity_level, total_score, active_days, 
        avg_daily_score, max_daily_score, calculation_date
    )
    SELECT 
        NEW.lawyer_id,
        cal.activity_level,
        cal.total_score,
        cal.active_days,
        cal.avg_daily_score,
        (SELECT MAX(total_activity_score) FROM lawyer_daily_activity 
         WHERE lawyer_id = NEW.lawyer_id 
         AND activity_date >= CURRENT_DATE - INTERVAL '30 days'),
        CURRENT_DATE
    FROM calculate_lawyer_activity_level(NEW.lawyer_id) cal
    ON CONFLICT (lawyer_id) DO UPDATE SET
        activity_level = EXCLUDED.activity_level,
        total_score = EXCLUDED.total_score,
        active_days = EXCLUDED.active_days,
        avg_daily_score = EXCLUDED.avg_daily_score,
        max_daily_score = EXCLUDED.max_daily_score,
        calculation_date = EXCLUDED.calculation_date,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_activity_level ON lawyer_daily_activity;
CREATE TRIGGER trigger_update_activity_level
    AFTER INSERT OR UPDATE ON lawyer_daily_activity
    FOR EACH ROW
    EXECUTE FUNCTION update_lawyer_activity_level();

-- 添加注释
COMMENT ON TABLE lawyer_activity_logs IS '律师活动日志表，记录所有律师活动';
COMMENT ON TABLE lawyer_daily_activity IS '律师每日活跃度汇总表';
COMMENT ON TABLE lawyer_activity_levels IS '律师活跃度等级表';
COMMENT ON TABLE lawyer_daily_task_completions IS '律师每日任务完成表';
COMMENT ON TABLE lawyer_activity_milestones IS '律师活跃度里程碑表';

COMMENT ON COLUMN lawyer_activity_logs.activity_type IS '活动类型：daily_login, case_response, case_completion等';
COMMENT ON COLUMN lawyer_activity_logs.quality_score IS '活动质量得分，0-100分';
COMMENT ON COLUMN lawyer_daily_activity.activity_breakdown IS 'JSON格式的各类活动计数';
COMMENT ON COLUMN lawyer_activity_levels.activity_level IS '活跃度等级：inactive, low, moderate, active, highly_active, super_active';
COMMENT ON COLUMN lawyer_daily_task_completions.task_type IS '任务类型：login, respond_to_case, complete_case等';
COMMENT ON COLUMN lawyer_activity_milestones.milestone_type IS '里程碑类型：consecutive_days, total_active_days, total_score等';