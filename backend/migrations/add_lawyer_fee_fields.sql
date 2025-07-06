-- 添加预期律师费和分期方案相关字段
-- 执行时间：2024-12-XX

-- 1. 在cases表中添加预期律师费相关字段
ALTER TABLE cases ADD COLUMN IF NOT EXISTS expected_lawyer_fee DECIMAL(10,2) DEFAULT 0.00 COMMENT '预期律师费金额';
ALTER TABLE cases ADD COLUMN IF NOT EXISTS installment_plan TEXT COMMENT 'AI生成的分期方案详情';
ALTER TABLE cases ADD COLUMN IF NOT EXISTS payment_terms TEXT COMMENT '具体的还款条款';
ALTER TABLE cases ADD COLUMN IF NOT EXISTS fee_negotiable BOOLEAN DEFAULT TRUE COMMENT '律师费是否可协商';

-- 2. 在lawyer_letter_orders表中添加分期方案字段
ALTER TABLE lawyer_letter_orders ADD COLUMN IF NOT EXISTS installment_options JSON COMMENT '分期还款选项JSON格式';
ALTER TABLE lawyer_letter_orders ADD COLUMN IF NOT EXISTS selected_installment_plan VARCHAR(50) COMMENT '债务人选择的分期方案';
ALTER TABLE lawyer_letter_orders ADD COLUMN IF NOT EXISTS letter_effectiveness ENUM('pending', 'responded', 'paid_partial', 'paid_full', 'ignored') DEFAULT 'pending' COMMENT '律师函效果追踪';

-- 3. 创建律师函效果追踪表
CREATE TABLE IF NOT EXISTS lawyer_letter_effectiveness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    letter_order_id UUID NOT NULL REFERENCES lawyer_letter_orders(id) ON DELETE CASCADE,
    response_date TIMESTAMP,
    response_type ENUM('call', 'email', 'payment', 'negotiation', 'ignore') COMMENT '回应类型',
    payment_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '实际支付金额',
    installment_selected VARCHAR(50) COMMENT '选择的分期方案',
    notes TEXT COMMENT '效果追踪备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. 创建律师费市场价格参考表
CREATE TABLE IF NOT EXISTS lawyer_fee_market_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_type VARCHAR(100) NOT NULL COMMENT '案件类型',
    debt_amount_min DECIMAL(10,2) NOT NULL COMMENT '债务金额下限',
    debt_amount_max DECIMAL(10,2) NOT NULL COMMENT '债务金额上限',
    suggested_fee_min DECIMAL(10,2) NOT NULL COMMENT '建议律师费下限',
    suggested_fee_max DECIMAL(10,2) NOT NULL COMMENT '建议律师费上限',
    region VARCHAR(50) DEFAULT 'national' COMMENT '适用地区',
    effective_date DATE DEFAULT CURRENT_DATE COMMENT '生效日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. 插入律师费市场价格参考数据
INSERT INTO lawyer_fee_market_rates (case_type, debt_amount_min, debt_amount_max, suggested_fee_min, suggested_fee_max, region) VALUES
('债务催收', 0, 10000, 300, 800, 'national'),
('债务催收', 10000, 50000, 800, 2000, 'national'),
('债务催收', 50000, 200000, 2000, 5000, 'national'),
('债务催收', 200000, 1000000, 5000, 15000, 'national'),
('律师函', 0, 50000, 200, 500, 'national'),
('律师函', 50000, 200000, 500, 1200, 'national'),
('合同审查', 0, 100000, 500, 1500, 'national'),
('法律咨询', 0, 999999999, 300, 1000, 'national');

-- 6. 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_cases_expected_lawyer_fee ON cases(expected_lawyer_fee);
CREATE INDEX IF NOT EXISTS idx_lawyer_letter_orders_effectiveness ON lawyer_letter_orders(letter_effectiveness);
CREATE INDEX IF NOT EXISTS idx_lawyer_fee_market_rates_case_type ON lawyer_fee_market_rates(case_type);
CREATE INDEX IF NOT EXISTS idx_lawyer_fee_market_rates_amount ON lawyer_fee_market_rates(debt_amount_min, debt_amount_max);

-- 7. 添加触发器自动更新时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_lawyer_letter_effectiveness_updated_at 
    BEFORE UPDATE ON lawyer_letter_effectiveness 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lawyer_fee_market_rates_updated_at 
    BEFORE UPDATE ON lawyer_fee_market_rates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 