-- Lawsker数据库初始化SQL脚本
-- 创建数据库和基础配置

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建数据库（如果不存在）
-- 注意：这在Docker初始化中会自动处理

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建自定义函数：更新时间戳
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建自定义函数：生成案件编号
CREATE OR REPLACE FUNCTION generate_case_number()
RETURNS TEXT AS $$
DECLARE
    prefix TEXT := 'LW';
    year_part TEXT := to_char(NOW(), 'YYYY');
    month_part TEXT := to_char(NOW(), 'MM');
    sequence_part TEXT;
    case_number TEXT;
BEGIN
    -- 获取当月案件序号
    SELECT LPAD((COUNT(*) + 1)::TEXT, 6, '0') INTO sequence_part
    FROM cases
    WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW());
    
    case_number := prefix || year_part || month_part || sequence_part;
    RETURN case_number;
END;
$$ LANGUAGE plpgsql;

-- 创建自定义函数：计算法律时效状态
CREATE OR REPLACE FUNCTION calculate_legal_status(
    debt_creation_date DATE,
    last_follow_up_date DATE DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    base_date DATE;
    expiry_date DATE;
    days_remaining INTEGER;
BEGIN
    -- 确定计算基准日期（最后跟进日期或债权形成日期）
    base_date := COALESCE(last_follow_up_date, debt_creation_date);
    
    -- 计算诉讼时效到期日期（3年）
    expiry_date := base_date + INTERVAL '3 years';
    
    -- 计算剩余天数
    days_remaining := expiry_date - CURRENT_DATE;
    
    -- 判断状态
    IF days_remaining < 0 THEN
        RETURN 'expired';
    ELSIF days_remaining <= 90 THEN
        RETURN 'expiring_soon';
    ELSE
        RETURN 'valid';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 创建索引模板（在表创建后会自动应用）
-- 这些索引会在Alembic迁移中创建

COMMIT; 