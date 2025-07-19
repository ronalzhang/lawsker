-- 测试数据插入脚本
-- 创建时间: 2025-07-19 18:34:35
-- 说明: 此脚本创建测试用户和任务数据，用于验证系统功能

INSERT INTO users (id, phone, email, password_hash, role, full_name, status, created_at, updated_at)
VALUES ('4dec2626-9126-45b9-a101-3c03bff2ab5d', '13800138001', 'testuser1@example.com', '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 
        'user', '张三', 'active', 
        '2025-07-14 18:34:35.381141', '2025-07-14 18:34:35.381141')
ON CONFLICT (phone) DO NOTHING;

INSERT INTO users (id, phone, email, password_hash, role, full_name, status, created_at, updated_at)
VALUES ('cb813910-9bfe-4a08-9416-77ea59be71aa', '13800138002', 'testuser2@example.com', '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 
        'user', '李四', 'active', 
        '2025-07-16 18:34:35.381153', '2025-07-16 18:34:35.381153')
ON CONFLICT (phone) DO NOTHING;

INSERT INTO users (id, phone, email, password_hash, role, full_name, status, created_at, updated_at)
VALUES ('c1463b1e-5ddf-439b-9eee-80fcf24fffd6', '13800138003', 'testlawyer1@example.com', '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 
        'lawyer', '王律师', 'active', 
        '2025-07-12 18:34:35.381157', '2025-07-12 18:34:35.381157')
ON CONFLICT (phone) DO NOTHING;

INSERT INTO users (id, phone, email, password_hash, role, full_name, status, created_at, updated_at)
VALUES ('72d80e6f-1bfb-40f6-9423-3ce1aa416d83', '13800138004', 'testlawyer2@example.com', '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 
        'lawyer', '赵律师', 'active', 
        '2025-07-15 18:34:35.381163', '2025-07-15 18:34:35.381163')
ON CONFLICT (phone) DO NOTHING;

INSERT INTO task_publish_records (id, publisher_id, task_type, title, description, budget, urgency, status, target_info, created_at, updated_at)
VALUES ('9c5fcd6f-88d6-49af-8e8c-ab8acef436e7', '4dec2626-9126-45b9-a101-3c03bff2ab5d', 'lawyer_letter', '债权催收律师函 #001', 
        '需要向欠款人发送正式的债权催收律师函，督促其履行还款义务。债务金额约5万元，欠款时间已超过6个月。', 650, 'normal', 'published', 
        '{"target_name": "\u503a\u52a1\u4eba\u5f20\u67d0", "contact_phone": "138****5678", "contact_address": "\u5317\u4eac\u5e02\u671d\u9633\u533a\u67d0\u67d0\u8857\u9053123\u53f7", "debt_amount": 50000, "case_details": "\u8d2d\u4e70\u5546\u54c1\u540e\u62d6\u6b20\u8d27\u6b3e\uff0c\u7ecf\u591a\u6b21\u50ac\u6536\u672a\u679c"}', '2025-07-19 16:34:35.381189', '2025-07-19 16:34:35.381189')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, publisher_id, task_type, title, description, budget, urgency, status, target_info, created_at, updated_at)
VALUES ('8b544b87-9112-41fe-ba5c-bce60d5dcbcc', '4dec2626-9126-45b9-a101-3c03bff2ab5d', 'debt_collection', '企业欠款催收 #002', 
        '企业间的货款纠纷，需要专业律师进行催收处理。涉及合同违约，金额较大。', 3500, 'urgent', 'published', 
        '{"target_name": "\u67d0\u8d38\u6613\u516c\u53f8", "contact_phone": "010-12345678", "contact_address": "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a\u79d1\u6280\u56ed\u533a", "debt_amount": 180000, "case_details": "B2B\u8d38\u6613\u8d27\u6b3e\u7ea0\u7eb7\uff0c\u5408\u540c\u660e\u786e\u4f46\u5bf9\u65b9\u62d6\u6b20"}', '2025-07-19 17:34:35.381197', '2025-07-19 17:34:35.381197')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, publisher_id, task_type, title, description, budget, urgency, status, target_info, created_at, updated_at)
VALUES ('a0050b2b-4b1a-4585-a206-0b634a178dd4', 'cb813910-9bfe-4a08-9416-77ea59be71aa', 'contract_review', '商务合同审查 #003', 
        '需要律师审查商务合作合同的条款和风险点，特别是违约责任和争议解决条款。', 1200, 'normal', 'published', 
        '{"contract_type": "\u670d\u52a1\u5916\u5305\u5408\u540c", "contract_value": 500000, "key_concerns": "\u8fdd\u7ea6\u8d23\u4efb\u3001\u77e5\u8bc6\u4ea7\u6743\u3001\u4fdd\u5bc6\u6761\u6b3e", "review_deadline": "3\u4e2a\u5de5\u4f5c\u65e5\u5185"}', '2025-07-19 18:04:35.381204', '2025-07-19 18:04:35.381204')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, publisher_id, task_type, title, description, budget, urgency, status, target_info, created_at, updated_at)
VALUES ('4be09ee8-d00b-4bcd-8b97-e55411cc45a5', 'cb813910-9bfe-4a08-9416-77ea59be71aa', 'legal_consultation', '法律咨询服务 #004', 
        '关于公司经营中的法律问题咨询和建议，涉及劳动法、公司法等多个领域。', 800, 'normal', 'published', 
        '{"consultation_type": "\u4f01\u4e1a\u6cd5\u5f8b\u987e\u95ee\u54a8\u8be2", "main_issues": "\u5458\u5de5\u5173\u7cfb\u3001\u5408\u89c4\u5ba1\u67e5\u3001\u98ce\u9669\u9632\u63a7", "company_size": "\u4e2d\u5c0f\u4f01\u4e1a\uff0850-100\u4eba\uff09", "urgency_level": "\u4e00\u822c\u54a8\u8be2"}', '2025-07-19 17:49:35.381211', '2025-07-19 17:49:35.381211')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, publisher_id, task_type, title, description, budget, urgency, status, target_info, created_at, updated_at)
VALUES ('42d5553a-4163-4ed6-94b9-063606ee0907', '4dec2626-9126-45b9-a101-3c03bff2ab5d', 'lawyer_letter', '违约责任追究函 #005', 
        '合同违约后需要发送法律函件追究违约责任，要求对方承担相应的经济损失。', 950, 'urgent', 'published', 
        '{"target_name": "\u8fdd\u7ea6\u65b9\u4f01\u4e1a", "contract_number": "HT2024001", "violation_details": "\u5ef6\u671f\u4ea4\u4ed8\u5bfc\u81f4\u635f\u5931", "claim_amount": 80000, "legal_basis": "\u5408\u540c\u6cd5\u76f8\u5173\u6761\u6b3e"}', '2025-07-19 18:19:35.381218', '2025-07-19 18:19:35.381218')
ON CONFLICT (id) DO NOTHING;

-- 验证数据插入
SELECT COUNT(*) as user_count FROM users WHERE phone LIKE '1380013800%';
SELECT COUNT(*) as task_count FROM task_publish_records WHERE status = 'published';
SELECT id, title, budget, urgency, status, created_at FROM task_publish_records WHERE status = 'published' ORDER BY created_at DESC;

-- 测试登录凭据:
-- 用户1: 手机号 13800138001, 密码 test123456
-- 用户2: 手机号 13800138002, 密码 test123456
-- 律师1: 手机号 13800138003, 密码 test123456
-- 律师2: 手机号 13800138004, 密码 test123456
