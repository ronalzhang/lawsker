-- 管理后台分析统计表创建脚本
-- 版本: 009
-- 创建时间: 2024-01-15
-- 描述: 为管理后台的数据分析功能添加所需的数据库表

-- ===================================
-- 访问统计分析表
-- ===================================

-- 访问日志记录表
CREATE TABLE IF NOT EXISTS access_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(64),
    ip_address INET NOT NULL,
    user_agent TEXT,
    referer TEXT,
    request_path VARCHAR(500) NOT NULL,
    request_method VARCHAR(10) DEFAULT 'GET',
    status_code INTEGER DEFAULT 200,
    response_time INTEGER, -- 响应时间(毫秒)
    device_type VARCHAR(20), -- mobile/desktop/tablet
    browser VARCHAR(50),
    os VARCHAR(50),
    country VARCHAR(50),
    region VARCHAR(50),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_ip ON access_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_path ON access_logs(request_path);

-- 日统计汇总表
CREATE TABLE IF NOT EXISTS daily_statistics (
    id SERIAL PRIMARY KEY,
    stat_date DATE UNIQUE NOT NULL,
    total_pv INTEGER DEFAULT 0,
    total_uv INTEGER DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    new_lawyers INTEGER DEFAULT 0,
    new_cases INTEGER DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    mobile_visits INTEGER DEFAULT 0,
    desktop_visits INTEGER DEFAULT 0,
    avg_response_time INTEGER DEFAULT 0,
    bounce_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_daily_statistics_date ON daily_statistics(stat_date);

-- IP访问统计表
CREATE TABLE IF NOT EXISTS ip_statistics (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL UNIQUE,
    first_visit TIMESTAMP NOT NULL,
    last_visit TIMESTAMP NOT NULL,
    visit_count INTEGER DEFAULT 1,
    total_page_views INTEGER DEFAULT 1,
    country VARCHAR(50),
    region VARCHAR(50),
    city VARCHAR(100),
    is_suspicious BOOLEAN DEFAULT FALSE,
    risk_score INTEGER DEFAULT 0, -- 0-100风险评分
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ip_statistics_country ON ip_statistics(country);
CREATE INDEX IF NOT EXISTS idx_ip_statistics_suspicious ON ip_statistics(is_suspicious);

-- 页面访问分析表
CREATE TABLE IF NOT EXISTS page_analytics (
    id SERIAL PRIMARY KEY,
    page_path VARCHAR(500) NOT NULL,
    page_title VARCHAR(200),
    visit_count INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_duration DECIMAL(8,2) DEFAULT 0, -- 平均停留时间(秒)
    bounce_count INTEGER DEFAULT 0,
    stat_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_page_analytics_path_date ON page_analytics(page_path, stat_date);

-- ===================================
-- 业绩排行分析表
-- ===================================

-- 律师业绩统计表
CREATE TABLE IF NOT EXISTS lawyer_performance_stats (
    id SERIAL PRIMARY KEY,
    lawyer_id INTEGER NOT NULL REFERENCES users(id),
    stat_period VARCHAR(20) NOT NULL, -- daily, weekly, monthly, yearly
    stat_date DATE NOT NULL,
    cases_handled INTEGER DEFAULT 0,
    cases_completed INTEGER DEFAULT 0,
    cases_success INTEGER DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    avg_case_duration DECIMAL(8,2) DEFAULT 0, -- 平均案件处理天数
    client_satisfaction DECIMAL(3,2) DEFAULT 0, -- 客户满意度(0-5)
    response_rate DECIMAL(5,2) DEFAULT 0, -- 响应率百分比
    completion_rate DECIMAL(5,2) DEFAULT 0, -- 完成率百分比
    ai_usage_count INTEGER DEFAULT 0, -- AI工具使用次数
    ranking_score DECIMAL(10,2) DEFAULT 0, -- 综合排名分数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_lawyer_performance_unique ON lawyer_performance_stats(lawyer_id, stat_period, stat_date);
CREATE INDEX IF NOT EXISTS idx_lawyer_performance_period ON lawyer_performance_stats(stat_period, stat_date);
CREATE INDEX IF NOT EXISTS idx_lawyer_performance_ranking ON lawyer_performance_stats(ranking_score DESC);

-- 用户业绩统计表
CREATE TABLE IF NOT EXISTS user_performance_stats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    stat_period VARCHAR(20) NOT NULL, -- daily, weekly, monthly, yearly
    stat_date DATE NOT NULL,
    tasks_published INTEGER DEFAULT 0,
    total_consumption DECIMAL(15,2) DEFAULT 0,
    referral_count INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1, -- 用户等级 1-10
    level_points INTEGER DEFAULT 0,
    active_days INTEGER DEFAULT 0,
    avg_task_value DECIMAL(10,2) DEFAULT 0,
    return_rate DECIMAL(5,2) DEFAULT 0, -- 复购率
    ranking_score DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_performance_unique ON user_performance_stats(user_id, stat_period, stat_date);
CREATE INDEX IF NOT EXISTS idx_user_performance_period ON user_performance_stats(stat_period, stat_date);
CREATE INDEX IF NOT EXISTS idx_user_performance_level ON user_performance_stats(current_level);
CREATE INDEX IF NOT EXISTS idx_user_performance_ranking ON user_performance_stats(ranking_score DESC);

-- 排行榜快照表
CREATE TABLE IF NOT EXISTS ranking_snapshots (
    id SERIAL PRIMARY KEY,
    ranking_type VARCHAR(50) NOT NULL, -- lawyer_cases, lawyer_revenue, user_consumption, etc.
    ranking_period VARCHAR(20) NOT NULL, -- monthly, quarterly, yearly
    snapshot_date DATE NOT NULL,
    ranking_data JSON NOT NULL, -- 存储排行榜数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ranking_snapshots_type ON ranking_snapshots(ranking_type, ranking_period, snapshot_date);

-- ===================================
-- 系统监控运维表
-- ===================================

-- 系统监控指标表
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL, -- cpu, memory, disk, network, etc.
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(20), -- %, MB, GB, ms, etc.
    host_name VARCHAR(100),
    service_name VARCHAR(50),
    threshold_warning DECIMAL(10,4),
    threshold_critical DECIMAL(10,4),
    is_alert BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_metrics_time ON system_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_alert ON system_metrics(is_alert, created_at);

-- 系统运行日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL, -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_source VARCHAR(50) NOT NULL, -- backend, frontend, database, etc.
    log_category VARCHAR(50), -- auth, payment, ai, etc.
    log_message TEXT NOT NULL,
    log_details JSON,
    user_id INTEGER REFERENCES users(id),
    ip_address INET,
    request_id VARCHAR(64),
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_system_logs_source ON system_logs(log_source);
CREATE INDEX IF NOT EXISTS idx_system_logs_time ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id);

-- 数据备份记录表
CREATE TABLE IF NOT EXISTS backup_records (
    id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20) NOT NULL, -- full, incremental, manual
    backup_status VARCHAR(20) NOT NULL, -- running, completed, failed
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT, -- 字节
    file_path VARCHAR(500),
    backup_duration INTEGER, -- 备份耗时(秒)
    error_message TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_backup_records_status ON backup_records(backup_status);
CREATE INDEX IF NOT EXISTS idx_backup_records_time ON backup_records(created_at);

-- 系统预警记录表
CREATE TABLE IF NOT EXISTS alert_records (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL, -- performance, security, business, etc.
    alert_level VARCHAR(20) NOT NULL, -- info, warning, critical
    alert_title VARCHAR(200) NOT NULL,
    alert_message TEXT NOT NULL,
    alert_source VARCHAR(50), -- 触发来源
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_records_type ON alert_records(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_records_level ON alert_records(alert_level);
CREATE INDEX IF NOT EXISTS idx_alert_records_resolved ON alert_records(is_resolved);

-- ===================================
-- 统计汇总表
-- ===================================

-- 多维度统计汇总表
CREATE TABLE IF NOT EXISTS statistics_summary (
    id SERIAL PRIMARY KEY,
    summary_type VARCHAR(50) NOT NULL, -- dashboard, users, lawyers, revenue, etc.
    summary_period VARCHAR(20) NOT NULL, -- hourly, daily, weekly, monthly
    summary_date TIMESTAMP NOT NULL,
    summary_data JSON NOT NULL, -- 存储汇总数据的JSON
    cache_key VARCHAR(100), -- 缓存键
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_statistics_summary_unique ON statistics_summary(summary_type, summary_period, summary_date);
CREATE INDEX IF NOT EXISTS idx_statistics_summary_type ON statistics_summary(summary_type);
CREATE INDEX IF NOT EXISTS idx_statistics_summary_expires ON statistics_summary(expires_at);

-- 仪表盘数据缓存表
CREATE TABLE IF NOT EXISTS dashboard_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(100) NOT NULL UNIQUE,
    cache_data JSON NOT NULL,
    cache_type VARCHAR(50) NOT NULL, -- overview, charts, rankings, etc.
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dashboard_cache_type ON dashboard_cache(cache_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_cache_expires ON dashboard_cache(expires_at);

-- 定时报表配置表
CREATE TABLE IF NOT EXISTS report_schedules (
    id SERIAL PRIMARY KEY,
    report_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- daily, weekly, monthly
    schedule_cron VARCHAR(50) NOT NULL, -- cron表达式
    recipients JSON, -- 接收人列表
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_report_schedules_active ON report_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run ON report_schedules(next_run_at);

-- ===================================
-- 数据初始化和示例数据
-- ===================================

-- 插入一些初始系统监控指标示例
INSERT INTO system_metrics (metric_type, metric_name, metric_value, metric_unit, host_name, service_name) VALUES
('cpu', 'cpu_usage', 15.5, '%', 'lawsker-server', 'system'),
('memory', 'memory_usage', 48.2, '%', 'lawsker-server', 'system'),
('disk', 'disk_usage', 32.1, '%', 'lawsker-server', 'system'),
('network', 'active_connections', 23, 'count', 'lawsker-server', 'nginx')
ON CONFLICT DO NOTHING;

-- 插入今日统计数据示例
INSERT INTO daily_statistics (stat_date, total_pv, total_uv, unique_ips, new_users, new_lawyers, total_revenue) VALUES
(CURRENT_DATE, 15672, 4523, 3891, 45, 3, 25630.00)
ON CONFLICT (stat_date) DO UPDATE SET
total_pv = EXCLUDED.total_pv,
total_uv = EXCLUDED.total_uv,
unique_ips = EXCLUDED.unique_ips,
updated_at = CURRENT_TIMESTAMP;

-- 创建触发器用于自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_daily_statistics_updated_at BEFORE UPDATE ON daily_statistics FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_ip_statistics_updated_at BEFORE UPDATE ON ip_statistics FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_page_analytics_updated_at BEFORE UPDATE ON page_analytics FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_lawyer_performance_stats_updated_at BEFORE UPDATE ON lawyer_performance_stats FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_user_performance_stats_updated_at BEFORE UPDATE ON user_performance_stats FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_statistics_summary_updated_at BEFORE UPDATE ON statistics_summary FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_dashboard_cache_updated_at BEFORE UPDATE ON dashboard_cache FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_report_schedules_updated_at BEFORE UPDATE ON report_schedules FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 迁移完成日志
INSERT INTO system_logs (log_level, log_source, log_category, log_message) VALUES
('INFO', 'database', 'migration', '管理后台分析统计表创建完成 - 009_add_admin_analytics_tables.sql'); 