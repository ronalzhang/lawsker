-- 添加加密字段的数据库迁移
-- 为敏感字段添加加密存储列

-- 修改用户资料表，添加加密字段
ALTER TABLE profiles 
ADD COLUMN full_name_encrypted TEXT,
ADD COLUMN id_card_number_encrypted TEXT;

-- 修改律师资质表，添加加密字段
ALTER TABLE lawyer_qualifications 
ADD COLUMN lawyer_name_encrypted TEXT,
ADD COLUMN id_card_number_encrypted TEXT;

-- 创建加密字段索引（用于性能优化，但不能用于搜索）
CREATE INDEX idx_profiles_encrypted_fields ON profiles(user_id) WHERE full_name_encrypted IS NOT NULL;
CREATE INDEX idx_lawyer_qualifications_encrypted_fields ON lawyer_qualifications(user_id) WHERE lawyer_name_encrypted IS NOT NULL;

-- 添加注释说明
COMMENT ON COLUMN profiles.full_name_encrypted IS '加密存储的用户姓名';
COMMENT ON COLUMN profiles.id_card_number_encrypted IS '加密存储的身份证号';
COMMENT ON COLUMN lawyer_qualifications.lawyer_name_encrypted IS '加密存储的律师姓名';
COMMENT ON COLUMN lawyer_qualifications.id_card_number_encrypted IS '加密存储的律师身份证号';

-- 创建数据迁移函数（将现有明文数据迁移到加密字段）
-- 注意：这个函数需要在应用层调用，因为需要使用加密密钥

-- 创建加密配置表
CREATE TABLE IF NOT EXISTS encryption_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_name VARCHAR(100) NOT NULL UNIQUE,
    encryption_algorithm VARCHAR(50) NOT NULL DEFAULT 'AES-256',
    key_rotation_interval INTEGER NOT NULL DEFAULT 604800, -- 7天，单位秒
    last_rotation_at TIMESTAMPTZ,
    next_rotation_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 插入字段加密配置
INSERT INTO encryption_config (field_name, encryption_algorithm, key_rotation_interval, next_rotation_at) VALUES
('full_name', 'AES-256', 604800, NOW() + INTERVAL '7 days'),
('id_card_number', 'AES-256', 604800, NOW() + INTERVAL '7 days'),
('lawyer_name', 'AES-256', 604800, NOW() + INTERVAL '7 days');

-- 创建密钥轮换日志表
CREATE TABLE IF NOT EXISTS key_rotation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_name VARCHAR(100) NOT NULL,
    rotation_type VARCHAR(50) NOT NULL, -- 'scheduled', 'emergency', 'manual'
    old_key_id VARCHAR(255),
    new_key_id VARCHAR(255),
    rotation_status VARCHAR(50) NOT NULL, -- 'started', 'completed', 'failed'
    affected_records INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id)
);

-- 创建加密审计日志表
CREATE TABLE IF NOT EXISTS encryption_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    operation VARCHAR(50) NOT NULL, -- 'encrypt', 'decrypt', 'mask'
    user_id UUID REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_encryption_config_field_name ON encryption_config(field_name);
CREATE INDEX idx_encryption_config_next_rotation ON encryption_config(next_rotation_at) WHERE is_active = TRUE;
CREATE INDEX idx_key_rotation_log_field_name ON key_rotation_log(field_name);
CREATE INDEX idx_key_rotation_log_created_at ON key_rotation_log(started_at);
CREATE INDEX idx_encryption_audit_log_table_record ON encryption_audit_log(table_name, record_id);
CREATE INDEX idx_encryption_audit_log_created_at ON encryption_audit_log(created_at);
CREATE INDEX idx_encryption_audit_log_user_id ON encryption_audit_log(user_id);

-- 添加表注释
COMMENT ON TABLE encryption_config IS '加密配置表，管理各字段的加密设置';
COMMENT ON TABLE key_rotation_log IS '密钥轮换日志表，记录密钥轮换操作';
COMMENT ON TABLE encryption_audit_log IS '加密审计日志表，记录加密解密操作';

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_encryption_config_updated_at 
    BEFORE UPDATE ON encryption_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建密钥轮换提醒视图
CREATE OR REPLACE VIEW key_rotation_reminders AS
SELECT 
    field_name,
    encryption_algorithm,
    key_rotation_interval,
    last_rotation_at,
    next_rotation_at,
    CASE 
        WHEN next_rotation_at <= NOW() THEN 'overdue'
        WHEN next_rotation_at <= NOW() + INTERVAL '1 day' THEN 'due_soon'
        ELSE 'ok'
    END as rotation_status,
    EXTRACT(EPOCH FROM (next_rotation_at - NOW())) / 3600 as hours_until_rotation
FROM encryption_config 
WHERE is_active = TRUE
ORDER BY next_rotation_at;

COMMENT ON VIEW key_rotation_reminders IS '密钥轮换提醒视图，显示需要轮换的密钥';

-- 创建加密统计视图
CREATE OR REPLACE VIEW encryption_statistics AS
SELECT 
    table_name,
    field_name,
    COUNT(*) as total_operations,
    COUNT(*) FILTER (WHERE operation = 'encrypt') as encrypt_operations,
    COUNT(*) FILTER (WHERE operation = 'decrypt') as decrypt_operations,
    COUNT(*) FILTER (WHERE operation = 'mask') as mask_operations,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_operations,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_operations,
    ROUND(
        COUNT(*) FILTER (WHERE success = TRUE) * 100.0 / COUNT(*), 2
    ) as success_rate,
    MIN(created_at) as first_operation,
    MAX(created_at) as last_operation
FROM encryption_audit_log 
GROUP BY table_name, field_name
ORDER BY total_operations DESC;

COMMENT ON VIEW encryption_statistics IS '加密操作统计视图，显示各表各字段的加密操作统计';

-- 创建安全函数：检查是否需要密钥轮换
CREATE OR REPLACE FUNCTION check_key_rotation_needed()
RETURNS TABLE(field_name VARCHAR, days_overdue INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ec.field_name,
        EXTRACT(DAY FROM (NOW() - ec.next_rotation_at))::INTEGER as days_overdue
    FROM encryption_config ec
    WHERE ec.is_active = TRUE 
    AND ec.next_rotation_at <= NOW()
    ORDER BY ec.next_rotation_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION check_key_rotation_needed() IS '检查需要进行密钥轮换的字段';

-- 创建安全函数：记录加密操作
CREATE OR REPLACE FUNCTION log_encryption_operation(
    p_table_name VARCHAR,
    p_record_id UUID,
    p_field_name VARCHAR,
    p_operation VARCHAR,
    p_user_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO encryption_audit_log (
        table_name, record_id, field_name, operation,
        user_id, ip_address, user_agent, success, error_message
    ) VALUES (
        p_table_name, p_record_id, p_field_name, p_operation,
        p_user_id, p_ip_address, p_user_agent, p_success, p_error_message
    ) RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION log_encryption_operation IS '记录加密操作到审计日志';

-- 授予必要权限（根据实际用户调整）
-- GRANT SELECT, INSERT, UPDATE ON encryption_config TO app_user;
-- GRANT SELECT, INSERT ON key_rotation_log TO app_user;
-- GRANT SELECT, INSERT ON encryption_audit_log TO app_user;
-- GRANT SELECT ON key_rotation_reminders TO app_user;
-- GRANT SELECT ON encryption_statistics TO app_user;
-- GRANT EXECUTE ON FUNCTION check_key_rotation_needed() TO app_user;
-- GRANT EXECUTE ON FUNCTION log_encryption_operation TO app_user;