-- Lawsker统一认证系统数据库迁移脚本
-- 版本: 013_auth_system_tables.sql
-- 创建时间: 2025-01-25
-- 描述: 为统一认证系统添加必要的数据表和字段

-- =====================================================
-- 0. 统一认证系统表
-- =====================================================

-- 扩展用户表，添加认证相关字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS workspace_id VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) DEFAULT 'pending' CHECK (account_type IN ('pending', 'user', 'lawyer', 'lawyer_pending', 'admin'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_source VARCHAR(20) DEFAULT 'web';

-- 为现有用户生成workspace_id
UPDATE users SET workspace_id = CONCAT('ws-', SUBSTRING(MD5(RANDOM()::text), 1, 12)) WHERE workspace_id IS NULL;

-- 律师认证申请表
CREATE TABLE IF NOT EXISTS lawyer_certification_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certificate_file_path VARCHAR(500) NOT NULL,
    certificate_file_name VARCHAR(255) NOT NULL,
    lawyer_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) NOT NULL,
    law_firm VARCHAR(200),
    practice_areas JSONB DEFAULT '[]',
    years_of_experience INTEGER DEFAULT 0,
    education_background TEXT,
    specialization_certificates JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'under_review')),
    admin_review_notes TEXT,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 工作台ID映射表（安全访问）
CREATE TABLE IF NOT EXISTS workspace_mappings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    workspace_id VARCHAR(50) NOT NULL UNIQUE,
    workspace_type VARCHAR(20) NOT NULL CHECK (workspace_type IN ('user', 'lawyer', 'admin')),
    is_demo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 演示账户配置表
CREATE TABLE IF NOT EXISTS demo_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demo_type VARCHAR(20) NOT NULL CHECK (demo_type IN ('lawyer', 'user')),
    workspace_id VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    demo_data JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 索引创建
-- =====================================================

-- 认证系统索引
CREATE INDEX IF NOT EXISTS idx_users_workspace_id ON users(workspace_id);
CREATE INDEX IF NOT EXISTS idx_users_account_type ON users(account_type);
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);
CREATE INDEX IF NOT EXISTS idx_lawyer_certification_requests_user_id ON lawyer_certification_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_certification_requests_status ON lawyer_certification_requests(status);
CREATE INDEX IF NOT EXISTS idx_workspace_mappings_workspace_id ON workspace_mappings(workspace_id);
CREATE INDEX IF NOT EXISTS idx_demo_accounts_demo_type ON demo_accounts(demo_type);
CREATE INDEX IF NOT EXISTS idx_demo_accounts_workspace_id ON demo_accounts(workspace_id);

-- =====================================================
-- 触发器创建
-- =====================================================

-- 自动更新updated_at字段的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表添加触发器
DROP TRIGGER IF EXISTS update_lawyer_certification_requests_updated_at ON lawyer_certification_requests;
CREATE TRIGGER update_lawyer_certification_requests_updated_at 
    BEFORE UPDATE ON lawyer_certification_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 初始数据插入
-- =====================================================

-- 为现有用户创建工作台映射
INSERT INTO workspace_mappings (user_id, workspace_id, workspace_type)
SELECT 
    u.id,
    u.workspace_id,
    'user' -- 默认为普通用户，后续可以通过管理界面调整
FROM users u
WHERE u.workspace_id IS NOT NULL
ON CONFLICT (user_id) DO NOTHING;

-- 插入演示账户数据
INSERT INTO demo_accounts (demo_type, workspace_id, display_name, demo_data) VALUES
('lawyer', 'demo-lawyer-001', '张律师（演示）', '{
    "specialties": ["合同纠纷", "债务催收", "公司法务"],
    "experience_years": 8,
    "success_rate": 92.5,
    "cases_handled": 156,
    "client_rating": 4.8,
    "demo_cases": [
        {"id": "demo-case-001", "title": "合同违约纠纷", "amount": 50000, "status": "进行中"},
        {"id": "demo-case-002", "title": "债务催收案件", "amount": 120000, "status": "已完成"}
    ]
}'),
('user', 'demo-user-001', '李先生（演示）', '{
    "company": "某科技公司",
    "cases_published": 3,
    "total_amount": 180000,
    "demo_cases": [
        {"id": "demo-case-003", "title": "劳动合同纠纷", "amount": 30000, "status": "匹配中"}
    ]
}')
ON CONFLICT (workspace_id) DO NOTHING;

-- 提交事务
COMMIT;