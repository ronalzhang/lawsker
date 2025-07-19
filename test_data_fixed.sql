-- 测试数据插入脚本（修复版本）
-- 创建时间: 2025-07-19 18:38:19
-- 说明: 此脚本创建测试用户和任务数据，使用正确的数据库字段

INSERT INTO users (id, username, email, phone_number, password_hash, status, created_at, updated_at)
VALUES ('054b44c3-a4c3-4daa-bd63-c7c15f9fe8ec', 'testuser1', 'testuser1@example.com', '13800138001', 
        '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 'active', 
        '2025-07-14 18:38:19.333680', '2025-07-14 18:38:19.333680')
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, username, email, phone_number, password_hash, status, created_at, updated_at)
VALUES ('4ff1beee-cec6-450c-a7af-40f15d7fa9ae', 'testuser2', 'testuser2@example.com', '13800138002', 
        '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 'active', 
        '2025-07-16 18:38:19.333692', '2025-07-16 18:38:19.333692')
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, username, email, phone_number, password_hash, status, created_at, updated_at)
VALUES ('8a24d6e5-759c-47e5-b8c5-2325b37d49b4', 'testlawyer1', 'testlawyer1@example.com', '13800138003', 
        '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 'active', 
        '2025-07-12 18:38:19.333696', '2025-07-12 18:38:19.333696')
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, username, email, phone_number, password_hash, status, created_at, updated_at)
VALUES ('9b478d15-c2a6-45f1-8fdc-07149e9c2f7f', 'testlawyer2', 'testlawyer2@example.com', '13800138004', 
        '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e', 'active', 
        '2025-07-15 18:38:19.333702', '2025-07-15 18:38:19.333702')
ON CONFLICT (email) DO NOTHING;

INSERT INTO task_publish_records (id, user_id, task_type, title, description, amount, urgency, status, target_info, created_at, updated_at)
VALUES ('f680749e-c66e-407b-ad41-32768e9e7eb2', '054b44c3-a4c3-4daa-bd63-c7c15f9fe8ec', 'lawyer_letter', '债权催收律师函 #001', 
        '需要向欠款人发送正式的债权催收律师函，督促其履行还款义务。债务金额约5万元，欠款时间已超过6个月。', 650, 'normal', 'published', 
        '{"target_name": "\u503a\u52a1\u4eba\u5f20\u67d0", "contact_phone": "138****5678", "contact_address": "\u5317\u4eac\u5e02\u671d\u9633\u533a\u67d0\u67d0\u8857\u9053123\u53f7", "debt_amount": 50000, "case_details": "\u8d2d\u4e70\u5546\u54c1\u540e\u62d6\u6b20\u8d27\u6b3e\uff0c\u7ecf\u591a\u6b21\u50ac\u6536\u672a\u679c"}', '2025-07-19 16:38:19.333725', '2025-07-19 16:38:19.333725')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, user_id, task_type, title, description, amount, urgency, status, target_info, created_at, updated_at)
VALUES ('ad49ba98-8465-4b69-b91e-444f0601bb70', '054b44c3-a4c3-4daa-bd63-c7c15f9fe8ec', 'debt_collection', '企业欠款催收 #002', 
        '企业间的货款纠纷，需要专业律师进行催收处理。涉及合同违约，金额较大。', 3500, 'urgent', 'published', 
        '{"target_name": "\u67d0\u8d38\u6613\u516c\u53f8", "contact_phone": "010-12345678", "contact_address": "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a\u79d1\u6280\u56ed\u533a", "debt_amount": 180000, "case_details": "B2B\u8d38\u6613\u8d27\u6b3e\u7ea0\u7eb7\uff0c\u5408\u540c\u660e\u786e\u4f46\u5bf9\u65b9\u62d6\u6b20"}', '2025-07-19 17:38:19.333734', '2025-07-19 17:38:19.333734')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, user_id, task_type, title, description, amount, urgency, status, target_info, created_at, updated_at)
VALUES ('7d08f7cf-c6bc-4ed3-881a-4552e25c1374', '4ff1beee-cec6-450c-a7af-40f15d7fa9ae', 'contract_review', '商务合同审查 #003', 
        '需要律师审查商务合作合同的条款和风险点，特别是违约责任和争议解决条款。', 1200, 'normal', 'published', 
        '{"contract_type": "\u670d\u52a1\u5916\u5305\u5408\u540c", "contract_value": 500000, "key_concerns": "\u8fdd\u7ea6\u8d23\u4efb\u3001\u77e5\u8bc6\u4ea7\u6743\u3001\u4fdd\u5bc6\u6761\u6b3e", "review_deadline": "3\u4e2a\u5de5\u4f5c\u65e5\u5185"}', '2025-07-19 18:08:19.333740', '2025-07-19 18:08:19.333740')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, user_id, task_type, title, description, amount, urgency, status, target_info, created_at, updated_at)
VALUES ('db39e0e0-84ed-424b-bdd0-b0be0eed01c9', '4ff1beee-cec6-450c-a7af-40f15d7fa9ae', 'legal_consultation', '法律咨询服务 #004', 
        '关于公司经营中的法律问题咨询和建议，涉及劳动法、公司法等多个领域。', 800, 'normal', 'published', 
        '{"consultation_type": "\u4f01\u4e1a\u6cd5\u5f8b\u987e\u95ee\u54a8\u8be2", "main_issues": "\u5458\u5de5\u5173\u7cfb\u3001\u5408\u89c4\u5ba1\u67e5\u3001\u98ce\u9669\u9632\u63a7", "company_size": "\u4e2d\u5c0f\u4f01\u4e1a\uff0850-100\u4eba\uff09", "urgency_level": "\u4e00\u822c\u54a8\u8be2"}', '2025-07-19 17:53:19.333747', '2025-07-19 17:53:19.333747')
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_publish_records (id, user_id, task_type, title, description, amount, urgency, status, target_info, created_at, updated_at)
VALUES ('e79571b4-f26c-450a-b45a-1d39e2130b61', '054b44c3-a4c3-4daa-bd63-c7c15f9fe8ec', 'lawyer_letter', '违约责任追究函 #005', 
        '合同违约后需要发送法律函件追究违约责任，要求对方承担相应的经济损失。', 950, 'urgent', 'published', 
        '{"target_name": "\u8fdd\u7ea6\u65b9\u4f01\u4e1a", "contract_number": "HT2024001", "violation_details": "\u5ef6\u671f\u4ea4\u4ed8\u5bfc\u81f4\u635f\u5931", "claim_amount": 80000, "legal_basis": "\u5408\u540c\u6cd5\u76f8\u5173\u6761\u6b3e"}', '2025-07-19 18:23:19.333753', '2025-07-19 18:23:19.333753')
ON CONFLICT (id) DO NOTHING;

-- 验证数据插入
SELECT COUNT(*) as user_count FROM users WHERE phone_number LIKE '1380013800%';
SELECT COUNT(*) as task_count FROM task_publish_records WHERE status = 'published';
SELECT id, title, amount, urgency, status, created_at FROM task_publish_records WHERE status = 'published' ORDER BY created_at DESC;

-- 测试登录凭据:
-- 用户1: 用户名 testuser1, 手机号 13800138001, 密码 test123456
-- 用户2: 用户名 testuser2, 手机号 13800138002, 密码 test123456
-- 律师1: 用户名 testlawyer1, 手机号 13800138003, 密码 test123456
-- 律师2: 用户名 testlawyer2, 手机号 13800138004, 密码 test123456
