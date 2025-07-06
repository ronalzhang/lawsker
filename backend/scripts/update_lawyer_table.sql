-- 更新律师认证表结构
-- 添加律师证AI识别相关字段

-- 检查并添加律师基本信息字段
DO $$
BEGIN
    -- 律师姓名
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'lawyer_name') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN lawyer_name VARCHAR(100) NOT NULL DEFAULT '';
    END IF;
    
    -- 性别
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'gender') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN gender VARCHAR(10);
    END IF;
    
    -- 身份证号
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'id_card_number') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN id_card_number VARCHAR(18);
    END IF;
    
    -- 律师证图片URL
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'license_image_url') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN license_image_url VARCHAR(500);
    END IF;
    
    -- 律师证图片元数据
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'license_image_metadata') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN license_image_metadata JSONB;
    END IF;
    
    -- AI验证分数
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'ai_verification_score') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN ai_verification_score INTEGER DEFAULT 0 NOT NULL;
    END IF;
    
    -- AI提取结果
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'ai_extraction_result') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN ai_extraction_result JSONB;
    END IF;
    
    -- 执业年限
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'years_of_practice') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN years_of_practice INTEGER DEFAULT 0;
    END IF;
    
    -- 认证状态
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'qualification_status') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN qualification_status VARCHAR(20) DEFAULT 'pending';
    END IF;
    
    -- 发证机关
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'license_authority') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN license_authority VARCHAR(100);
    END IF;
    
    -- 发证日期
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'license_issued_date') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN license_issued_date DATE;
    END IF;
    
    -- 到期日期
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'license_expiry_date') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN license_expiry_date DATE;
    END IF;
    
    -- 律师事务所名称
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'law_firm_name') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN law_firm_name VARCHAR(200);
    END IF;
    
    -- 执业领域
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'practice_areas') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN practice_areas TEXT[];
    END IF;
    
    -- 专业特长
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'specializations') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN specializations TEXT[];
    END IF;
    
    -- 学历背景
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'education_background') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN education_background VARCHAR(100);
    END IF;
    
    -- 联系电话
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'contact_phone') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN contact_phone VARCHAR(20);
    END IF;
    
    -- 联系邮箱
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'contact_email') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN contact_email VARCHAR(100);
    END IF;
    
    -- 创建时间
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'created_at') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- 更新时间
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'updated_at') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- 审核时间
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'reviewed_at') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN reviewed_at TIMESTAMP;
    END IF;
    
    -- 审核人员
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'reviewed_by') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN reviewed_by UUID;
    END IF;
    
    -- 审核备注
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_qualifications' AND column_name = 'review_notes') THEN
        ALTER TABLE lawyer_qualifications ADD COLUMN review_notes TEXT;
    END IF;
    
    RAISE NOTICE '律师认证表结构更新完成';
END $$;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_lawyer_qualifications_id_card ON lawyer_qualifications(id_card_number);
CREATE INDEX IF NOT EXISTS idx_lawyer_qualifications_name ON lawyer_qualifications(lawyer_name);
CREATE INDEX IF NOT EXISTS idx_lawyer_qualifications_license ON lawyer_qualifications(license_number);
CREATE INDEX IF NOT EXISTS idx_lawyer_qualifications_status ON lawyer_qualifications(qualification_status);
CREATE INDEX IF NOT EXISTS idx_lawyer_qualifications_firm ON lawyer_qualifications(law_firm_name);
CREATE INDEX IF NOT EXISTS idx_lawyer_qualifications_created ON lawyer_qualifications(created_at);

-- 更新现有记录的默认值
UPDATE lawyer_qualifications SET 
    qualification_status = 'pending' 
WHERE qualification_status IS NULL;

UPDATE lawyer_qualifications SET 
    ai_verification_score = 0 
WHERE ai_verification_score IS NULL;

UPDATE lawyer_qualifications SET 
    years_of_practice = 0 
WHERE years_of_practice IS NULL;

-- 添加约束
ALTER TABLE lawyer_qualifications 
ADD CONSTRAINT chk_qualification_status 
CHECK (qualification_status IN ('pending', 'submitted', 'under_review', 'approved', 'rejected', 'expired'));

ALTER TABLE lawyer_qualifications 
ADD CONSTRAINT chk_ai_verification_score 
CHECK (ai_verification_score >= 0 AND ai_verification_score <= 100);

ALTER TABLE lawyer_qualifications 
ADD CONSTRAINT chk_years_of_practice 
CHECK (years_of_practice >= 0 AND years_of_practice <= 100);

-- 添加注释
COMMENT ON TABLE lawyer_qualifications IS '律师资质认证表';
COMMENT ON COLUMN lawyer_qualifications.lawyer_name IS '律师姓名';
COMMENT ON COLUMN lawyer_qualifications.gender IS '性别';
COMMENT ON COLUMN lawyer_qualifications.id_card_number IS '身份证号';
COMMENT ON COLUMN lawyer_qualifications.license_number IS '执业证书编号';
COMMENT ON COLUMN lawyer_qualifications.license_authority IS '发证机关';
COMMENT ON COLUMN lawyer_qualifications.license_issued_date IS '发证日期';
COMMENT ON COLUMN lawyer_qualifications.license_expiry_date IS '到期日期';
COMMENT ON COLUMN lawyer_qualifications.law_firm_name IS '律师事务所名称';
COMMENT ON COLUMN lawyer_qualifications.years_of_practice IS '执业年限';
COMMENT ON COLUMN lawyer_qualifications.practice_areas IS '执业领域';
COMMENT ON COLUMN lawyer_qualifications.specializations IS '专业特长';
COMMENT ON COLUMN lawyer_qualifications.education_background IS '学历背景';
COMMENT ON COLUMN lawyer_qualifications.contact_phone IS '联系电话';
COMMENT ON COLUMN lawyer_qualifications.contact_email IS '联系邮箱';
COMMENT ON COLUMN lawyer_qualifications.license_image_url IS '律师证图片URL';
COMMENT ON COLUMN lawyer_qualifications.license_image_metadata IS '律师证图片元数据';
COMMENT ON COLUMN lawyer_qualifications.ai_verification_score IS 'AI验证分数(0-100)';
COMMENT ON COLUMN lawyer_qualifications.ai_extraction_result IS 'AI提取结果';
COMMENT ON COLUMN lawyer_qualifications.qualification_status IS '认证状态';
COMMENT ON COLUMN lawyer_qualifications.created_at IS '创建时间';
COMMENT ON COLUMN lawyer_qualifications.updated_at IS '更新时间';
COMMENT ON COLUMN lawyer_qualifications.reviewed_at IS '审核时间';
COMMENT ON COLUMN lawyer_qualifications.reviewed_by IS '审核人员';
COMMENT ON COLUMN lawyer_qualifications.review_notes IS '审核备注';

COMMIT; 