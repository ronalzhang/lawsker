-- 创建告警相关表
-- 迁移文件: 011_create_alert_tables.sql

-- 创建告警记录表
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    description TEXT,
    service VARCHAR(100),
    labels JSONB,
    annotations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- 创建告警记录表索引
CREATE INDEX IF NOT EXISTS idx_alerts_alert_id ON alerts(alert_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_service ON alerts(service);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_severity_created ON alerts(severity, created_at);

-- 创建告警规则表
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    expression TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    duration VARCHAR(50),
    labels JSONB,
    annotations JSONB,
    enabled VARCHAR(10) DEFAULT 'true',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建告警规则表索引
CREATE INDEX IF NOT EXISTS idx_alert_rules_name ON alert_rules(name);
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);

-- 创建告警通知记录表
CREATE TABLE IF NOT EXISTS alert_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(255) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    recipient VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建告警通知记录表索引
CREATE INDEX IF NOT EXISTS idx_alert_notifications_alert_id ON alert_notifications(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_channel ON alert_notifications(channel);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_status ON alert_notifications(status);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_sent_at ON alert_notifications(sent_at);

-- 创建告警静默表
CREATE TABLE IF NOT EXISTS alert_silences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(255),
    matcher_labels JSONB,
    comment TEXT,
    created_by VARCHAR(255),
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建告警静默表索引
CREATE INDEX IF NOT EXISTS idx_alert_silences_alert_id ON alert_silences(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_silences_starts_at ON alert_silences(starts_at);
CREATE INDEX IF NOT EXISTS idx_alert_silences_ends_at ON alert_silences(ends_at);
CREATE INDEX IF NOT EXISTS idx_alert_silences_created_by ON alert_silences(created_by);

-- 添加表注释
COMMENT ON TABLE alerts IS '告警记录表';
COMMENT ON COLUMN alerts.id IS '主键ID';
COMMENT ON COLUMN alerts.alert_id IS '告警唯一标识';
COMMENT ON COLUMN alerts.name IS '告警名称';
COMMENT ON COLUMN alerts.severity IS '严重级别';
COMMENT ON COLUMN alerts.status IS '告警状态';
COMMENT ON COLUMN alerts.message IS '告警消息';
COMMENT ON COLUMN alerts.description IS '详细描述';
COMMENT ON COLUMN alerts.service IS '相关服务';
COMMENT ON COLUMN alerts.labels IS '标签信息';
COMMENT ON COLUMN alerts.annotations IS '注释信息';
COMMENT ON COLUMN alerts.created_at IS '创建时间';
COMMENT ON COLUMN alerts.updated_at IS '更新时间';
COMMENT ON COLUMN alerts.resolved_at IS '解决时间';

COMMENT ON TABLE alert_rules IS '告警规则表';
COMMENT ON COLUMN alert_rules.id IS '主键ID';
COMMENT ON COLUMN alert_rules.name IS '规则名称';
COMMENT ON COLUMN alert_rules.expression IS '告警表达式';
COMMENT ON COLUMN alert_rules.severity IS '严重级别';
COMMENT ON COLUMN alert_rules.duration IS '持续时间';
COMMENT ON COLUMN alert_rules.labels IS '标签';
COMMENT ON COLUMN alert_rules.annotations IS '注释';
COMMENT ON COLUMN alert_rules.enabled IS '是否启用';
COMMENT ON COLUMN alert_rules.created_at IS '创建时间';
COMMENT ON COLUMN alert_rules.updated_at IS '更新时间';

COMMENT ON TABLE alert_notifications IS '告警通知记录表';
COMMENT ON COLUMN alert_notifications.id IS '主键ID';
COMMENT ON COLUMN alert_notifications.alert_id IS '告警ID';
COMMENT ON COLUMN alert_notifications.channel IS '通知渠道';
COMMENT ON COLUMN alert_notifications.recipient IS '收件人';
COMMENT ON COLUMN alert_notifications.status IS '发送状态';
COMMENT ON COLUMN alert_notifications.error_message IS '错误信息';
COMMENT ON COLUMN alert_notifications.sent_at IS '发送时间';

COMMENT ON TABLE alert_silences IS '告警静默表';
COMMENT ON COLUMN alert_silences.id IS '主键ID';
COMMENT ON COLUMN alert_silences.alert_id IS '告警ID';
COMMENT ON COLUMN alert_silences.matcher_labels IS '匹配标签';
COMMENT ON COLUMN alert_silences.comment IS '静默原因';
COMMENT ON COLUMN alert_silences.created_by IS '创建人';
COMMENT ON COLUMN alert_silences.starts_at IS '开始时间';
COMMENT ON COLUMN alert_silences.ends_at IS '结束时间';
COMMENT ON COLUMN alert_silences.created_at IS '创建时间';

-- 插入默认告警规则
INSERT INTO alert_rules (name, expression, severity, duration, labels, annotations, enabled) VALUES
('高错误率告警', 'rate(http_requests_total{status=~"5.."}[5m]) > 0.1', 'critical', '2m', 
 '{"service": "lawsker-api"}', 
 '{"summary": "系统错误率过高", "description": "过去5分钟内错误率超过10%阈值"}', 
 'true'),

('数据库连接数过高', 'database_connections_active > 80', 'warning', '1m',
 '{"service": "lawsker-db"}',
 '{"summary": "数据库连接数过高", "description": "当前数据库连接数接近最大连接数限制"}',
 'true'),

('磁盘空间不足', '(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1', 'critical', '5m',
 '{"service": "lawsker-system"}',
 '{"summary": "磁盘空间不足", "description": "根分区可用空间低于10%"}',
 'true'),

('API响应时间过长', 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 3', 'warning', '3m',
 '{"service": "lawsker-api"}',
 '{"summary": "API响应时间过长", "description": "95%分位数响应时间超过3秒阈值"}',
 'true'),

('内存使用率过高', '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9', 'warning', '5m',
 '{"service": "lawsker-system"}',
 '{"summary": "内存使用率过高", "description": "内存使用率超过90%阈值"}',
 'true');

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为alerts表创建更新时间触发器
CREATE TRIGGER update_alerts_updated_at 
    BEFORE UPDATE ON alerts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 为alert_rules表创建更新时间触发器
CREATE TRIGGER update_alert_rules_updated_at 
    BEFORE UPDATE ON alert_rules 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();