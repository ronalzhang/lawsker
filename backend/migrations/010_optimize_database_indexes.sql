-- 数据库索引优化脚本
-- 为高频查询创建复合索引，提升查询性能

-- ==================== 访问日志表索引优化 ====================

-- 访问日志按用户和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_user_time 
ON access_logs(user_id, created_at DESC) 
WHERE user_id IS NOT NULL;

-- 访问日志按IP和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_ip_time 
ON access_logs(ip_address, created_at DESC);

-- 访问日志按路径和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_path_time 
ON access_logs(request_path, created_at DESC);

-- 访问日志按状态码和时间的复合索引（用于错误分析）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_status_time 
ON access_logs(status_code, created_at DESC) 
WHERE status_code >= 400;

-- 访问日志按设备类型的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_device_type 
ON access_logs(device_type, created_at DESC);

-- 访问日志按响应时间的索引（用于性能分析）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_response_time 
ON access_logs(response_time DESC, created_at DESC) 
WHERE response_time IS NOT NULL;

-- ==================== 用户活动日志表索引优化 ====================

-- 用户活动按用户和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_logs_user_time 
ON user_activity_logs(user_id, created_at DESC);

-- 用户活动按动作类型和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_logs_action_time 
ON user_activity_logs(action, created_at DESC);

-- 用户活动按资源类型和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_logs_resource_time 
ON user_activity_logs(resource_type, created_at DESC) 
WHERE resource_type IS NOT NULL;

-- 用户活动按用户、动作和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_logs_user_action_time 
ON user_activity_logs(user_id, action, created_at DESC);

-- ==================== 用户表索引优化 ====================

-- 用户按角色和状态的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_status 
ON users(role, status) 
WHERE status = 'active';

-- 用户按邮箱的唯一索引（如果不存在）
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_unique 
ON users(email) 
WHERE email IS NOT NULL;

-- 用户按手机号的唯一索引（如果不存在）
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_phone_unique 
ON users(phone_number) 
WHERE phone_number IS NOT NULL;

-- 用户按创建时间的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at 
ON users(created_at DESC);

-- ==================== 案件表索引优化 ====================

-- 案件按状态和创建时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cases_status_created 
ON cases(status, created_at DESC) 
WHERE status IN ('pending', 'assigned', 'in_progress');

-- 案件按分配律师和状态的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cases_assigned_status 
ON cases(assigned_to_user_id, status, created_at DESC) 
WHERE assigned_to_user_id IS NOT NULL;

-- 案件按销售用户和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cases_sales_time 
ON cases(sales_user_id, created_at DESC) 
WHERE sales_user_id IS NOT NULL;

-- 案件按金额范围的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cases_amount_range 
ON cases(case_amount DESC, created_at DESC);

-- 案件按客户ID的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cases_client_id 
ON cases(client_id, created_at DESC) 
WHERE client_id IS NOT NULL;

-- ==================== 交易记录表索引优化 ====================

-- 交易按案件ID和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_case_time 
ON transactions(case_id, created_at DESC) 
WHERE case_id IS NOT NULL;

-- 交易按类型和状态的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_type_status 
ON transactions(transaction_type, status, created_at DESC);

-- 交易按金额和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_amount_time 
ON transactions(amount DESC, created_at DESC);

-- 交易按完成时间的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_completed_at 
ON transactions(completed_at DESC) 
WHERE completed_at IS NOT NULL;

-- ==================== 分账记录表索引优化 ====================

-- 分账按交易ID的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_commission_splits_transaction 
ON commission_splits(transaction_id, created_at DESC);

-- 分账按用户ID和状态的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_commission_splits_user_status 
ON commission_splits(user_id, status, created_at DESC);

-- 分账按角色和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_commission_splits_role_time 
ON commission_splits(role_at_split, created_at DESC);

-- 分账按支付时间的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_commission_splits_paid_at 
ON commission_splits(paid_at DESC) 
WHERE paid_at IS NOT NULL;

-- ==================== 文档审核任务表索引优化 ====================

-- 文档审核按律师ID和状态的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_review_tasks_lawyer_status 
ON document_review_tasks(lawyer_id, status, created_at DESC);

-- 文档审核按案件ID的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_review_tasks_case 
ON document_review_tasks(case_id, created_at DESC) 
WHERE case_id IS NOT NULL;

-- 文档审核按优先级和截止时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_review_tasks_priority_deadline 
ON document_review_tasks(priority DESC, deadline ASC) 
WHERE deadline IS NOT NULL;

-- 文档审核按文档类型和状态的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_review_tasks_type_status 
ON document_review_tasks(document_type, status, created_at DESC);

-- ==================== 支付订单表索引优化 ====================

-- 支付订单按案件ID的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payment_orders_case 
ON payment_orders(case_id, created_at DESC) 
WHERE case_id IS NOT NULL;

-- 支付订单按状态和时间的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payment_orders_status_time 
ON payment_orders(status, created_at DESC);

-- 支付订单按过期时间的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payment_orders_expired_at 
ON payment_orders(expired_at ASC) 
WHERE expired_at IS NOT NULL;

-- 支付订单按支付时间的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payment_orders_paid_at 
ON payment_orders(paid_at DESC) 
WHERE paid_at IS NOT NULL;

-- ==================== 系统配置表索引优化 ====================

-- 系统配置按类别和键的复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_configs_category_key 
ON system_configs(category, key);

-- 系统配置按租户ID的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_configs_tenant 
ON system_configs(tenant_id, category) 
WHERE tenant_id IS NOT NULL;

-- 系统配置按更新时间的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_configs_updated_at 
ON system_configs(updated_at DESC);

-- ==================== 钱包表索引优化 ====================

-- 钱包按用户ID的唯一索引（如果不存在）
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_wallets_user_id_unique 
ON wallets(user_id);

-- 钱包按余额的索引（用于统计）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_wallets_balance 
ON wallets(balance DESC) 
WHERE balance > 0;

-- 钱包按最后分账时间的索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_wallets_last_commission_at 
ON wallets(last_commission_at DESC) 
WHERE last_commission_at IS NOT NULL;

-- ==================== 每日统计表索引优化 ====================

-- 每日统计按日期的唯一索引（如果不存在）
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_statistics_date_unique 
ON daily_statistics(stat_date DESC);

-- ==================== 清理无用索引 ====================

-- 检查并删除重复或无用的索引
-- 注意：在生产环境中执行前请仔细检查

-- 删除可能重复的简单索引（如果复合索引已覆盖）
-- DROP INDEX CONCURRENTLY IF EXISTS idx_access_logs_user_id;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_access_logs_ip;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_access_logs_created_at;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_access_logs_path;

-- ==================== 索引使用情况分析 ====================

-- 创建视图来监控索引使用情况
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MEDIUM_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_level
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- 创建视图来监控表的扫描情况
CREATE OR REPLACE VIEW table_scan_stats AS
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    CASE 
        WHEN seq_scan > idx_scan THEN 'NEEDS_INDEX'
        WHEN seq_scan = 0 AND idx_scan > 0 THEN 'WELL_INDEXED'
        ELSE 'MIXED_ACCESS'
    END as index_effectiveness
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY seq_scan DESC;

-- ==================== 索引维护建议 ====================

-- 创建函数来分析慢查询
CREATE OR REPLACE FUNCTION analyze_slow_queries()
RETURNS TABLE(
    query_text text,
    calls bigint,
    total_time double precision,
    mean_time double precision,
    rows bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pg_stat_statements.query,
        pg_stat_statements.calls,
        pg_stat_statements.total_exec_time,
        pg_stat_statements.mean_exec_time,
        pg_stat_statements.rows
    FROM pg_stat_statements
    WHERE pg_stat_statements.mean_exec_time > 100  -- 超过100ms的查询
    ORDER BY pg_stat_statements.mean_exec_time DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- 注释：使用以下查询来监控索引效果
-- SELECT * FROM index_usage_stats WHERE usage_level = 'UNUSED';
-- SELECT * FROM table_scan_stats WHERE index_effectiveness = 'NEEDS_INDEX';
-- SELECT * FROM analyze_slow_queries();

-- 完成索引优化
-- 建议定期运行 ANALYZE 命令更新统计信息
-- ANALYZE;