-- 添加用户哈希字段
-- 用于生成唯一的10位哈希值作为用户工作台URL

-- 添加user_hash字段
ALTER TABLE users ADD COLUMN user_hash VARCHAR(10) UNIQUE;

-- 创建索引以提高查询性能
CREATE INDEX idx_users_user_hash ON users(user_hash);

-- 为现有用户生成哈希值（可选）
-- 注意：这个脚本不会自动为现有用户生成哈希，需要在应用层面处理 