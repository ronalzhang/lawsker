-- Lawsker生产环境数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建数据库用户（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lawsker_user') THEN
        CREATE ROLE lawsker_user WITH LOGIN PASSWORD 'your-strong-database-password';
    END IF;
END
$$;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE lawsker_prod TO lawsker_user;
GRANT ALL ON SCHEMA public TO lawsker_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lawsker_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lawsker_user;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO lawsker_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO lawsker_user;

-- 创建性能监控函数
CREATE OR REPLACE FUNCTION pg_stat_statements_reset()
RETURNS void AS $$
BEGIN
    -- 重置统计信息
    PERFORM pg_stat_reset();
END;
$$ LANGUAGE plpgsql;

-- 创建数据库连接监控视图
CREATE OR REPLACE VIEW connection_stats AS
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database 
WHERE datname = 'lawsker_prod';

-- 创建表空间监控视图
CREATE OR REPLACE VIEW table_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- 创建索引使用统计视图
CREATE OR REPLACE VIEW index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_tup_read DESC;

-- 创建慢查询监控表
CREATE TABLE IF NOT EXISTS slow_queries (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    execution_time INTERVAL NOT NULL,
    calls INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 插入默认系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('maintenance_mode', 'false', '系统维护模式'),
('max_upload_size', '10485760', '最大上传文件大小（字节）'),
('session_timeout', '3600', '会话超时时间（秒）'),
('rate_limit_enabled', 'true', '是否启用限流'),
('backup_enabled', 'true', '是否启用自动备份'),
('log_level', 'INFO', '日志级别')
ON CONFLICT (config_key) DO NOTHING;

-- 创建数据备份记录表
CREATE TABLE IF NOT EXISTS backup_records (
    id SERIAL PRIMARY KEY,
    backup_type VARCHAR(50) NOT NULL,
    backup_path TEXT NOT NULL,
    file_size BIGINT,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 创建系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL,
    module VARCHAR(100),
    message TEXT NOT NULL,
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_system_logs_level_time ON system_logs(log_level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_module_time ON system_logs(module, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backup_records_type_time ON backup_records(backup_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_slow_queries_time ON slow_queries(execution_time DESC);

-- 设置表的自动清理策略
-- 系统日志保留30天
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM system_logs WHERE created_at < NOW() - INTERVAL '30 days';
    DELETE FROM backup_records WHERE created_at < NOW() - INTERVAL '90 days';
    DELETE FROM slow_queries WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- 创建定时清理任务（需要pg_cron扩展）
-- SELECT cron.schedule('cleanup-logs', '0 2 * * *', 'SELECT cleanup_old_logs();');

COMMIT;