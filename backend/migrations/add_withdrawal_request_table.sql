-- 添加WithdrawalRequest提现申请表
-- 执行时间: 2024-01-15

-- 创建提现状态枚举类型
DO $$ BEGIN
    CREATE TYPE withdrawal_status AS ENUM (
        'pending',
        'approved', 
        'processing',
        'completed',
        'rejected',
        'failed',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建WithdrawalRequest表
CREATE TABLE IF NOT EXISTS withdrawal_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(32) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- 金额信息
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    fee DECIMAL(15, 2) NOT NULL DEFAULT 0 CHECK (fee >= 0),
    actual_amount DECIMAL(15, 2) NOT NULL CHECK (actual_amount > 0),
    
    -- 银行信息
    bank_account VARCHAR(32) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    account_holder VARCHAR(100) NOT NULL,
    
    -- 状态和风险评估
    status withdrawal_status NOT NULL DEFAULT 'pending',
    risk_score DECIMAL(5, 2) CHECK (risk_score >= 0 AND risk_score <= 100),
    auto_approved BOOLEAN NOT NULL DEFAULT false,
    
    -- 审核信息
    admin_id UUID REFERENCES users(id) ON DELETE SET NULL,
    admin_notes TEXT,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- 元数据
    metadata JSONB DEFAULT '{}' NOT NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_user_id ON withdrawal_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_tenant_id ON withdrawal_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_status ON withdrawal_requests(status);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_created_at ON withdrawal_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_request_number ON withdrawal_requests(request_number);

-- 创建更新时间戳触发器
CREATE OR REPLACE FUNCTION update_withdrawal_requests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER withdrawal_requests_updated_at
    BEFORE UPDATE ON withdrawal_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_withdrawal_requests_updated_at();

-- 添加表注释
COMMENT ON TABLE withdrawal_requests IS '提现申请表 - 存储用户提现申请和审核记录';
COMMENT ON COLUMN withdrawal_requests.request_number IS '提现申请单号';
COMMENT ON COLUMN withdrawal_requests.amount IS '申请提现金额';
COMMENT ON COLUMN withdrawal_requests.fee IS '提现手续费';
COMMENT ON COLUMN withdrawal_requests.actual_amount IS '实际到账金额 = amount - fee';
COMMENT ON COLUMN withdrawal_requests.bank_account IS '银行账户号码';
COMMENT ON COLUMN withdrawal_requests.bank_name IS '开户银行名称';
COMMENT ON COLUMN withdrawal_requests.account_holder IS '账户持有人姓名';
COMMENT ON COLUMN withdrawal_requests.status IS '提现状态';
COMMENT ON COLUMN withdrawal_requests.risk_score IS '风险评分 0-100';
COMMENT ON COLUMN withdrawal_requests.auto_approved IS '是否自动审批通过';
COMMENT ON COLUMN withdrawal_requests.admin_id IS '审核管理员ID';
COMMENT ON COLUMN withdrawal_requests.admin_notes IS '管理员审核备注';
COMMENT ON COLUMN withdrawal_requests.processed_at IS '处理完成时间';
COMMENT ON COLUMN withdrawal_requests.metadata IS '扩展元数据';

-- 插入测试数据（可选）
INSERT INTO withdrawal_requests (
    request_number,
    user_id,
    tenant_id,
    amount,
    fee,
    actual_amount,
    bank_account,
    bank_name,
    account_holder,
    status,
    risk_score,
    auto_approved,
    metadata
) 
SELECT 
    'WD' || TO_CHAR(NOW(), 'YYYYMMDD') || LPAD((ROW_NUMBER() OVER())::TEXT, 6, '0'),
    u.id,
    u.tenant_id,
    500.00,
    5.00,
    495.00,
    '6225887712345678',
    '招商银行',
    u.full_name,
    'pending',
    25.5,
    false,
    '{"test_data": true, "created_by": "migration"}'::jsonb
FROM users u
WHERE u.role = 'lawyer'
LIMIT 3;

-- 验证表创建
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'withdrawal_requests'
ORDER BY ordinal_position; 