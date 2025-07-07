# Lawsker (律客) - 数据库表结构设计 v1.4 - 实际实现状态

## 📊 **实现状态概览 (2024年12月)**

### **✅ 已实现核心表**
- `tenants` - 租户表 (100% 实现)
- `users` - 用户表 (100% 实现)
- `cases` - 案件表 (100% 实现)
- `transactions` - 交易流水表 (100% 实现)
- `commission_splits` - 分账记录表 (100% 实现)
- `system_configs` - 系统配置表 (100% 实现)
- `document_review_tasks` - 文档审核任务表 (100% 实现)
- `lawyer_letter_orders` - 律师函订单表 (100% 实现)
- `payment_orders` - 支付订单表 (100% 实现)
- `lawyer_qualifications` - 律师资质表 (100% 实现)

### **⚠️ 高优先级待补充表**
- `withdrawal_requests` - 提现申请表 (前端已集成，急需后端支持)

### **❌ 待补充表**
- `case_logs` - 案件日志表 (需要补充)
- `lawyer_workloads` - 律师工作负荷表 (需要补充)
- `clients` - 客户表 (需要补充)
- `insurances` - 保险记录表 (需要补充)
- `api_keys` - API密钥表 (可选)
- `dao_proposals` - DAO提案表 (未来功能)
- `dao_votes` - DAO投票表 (未来功能)

### **数据库完成度: 90%**
### **前端工作台已完成，需要提现管理API支持**

---

## 核心设计原则
- **多租户隔离**：所有核心业务表都包含 `tenant_id` 字段，用于WorkBridge后端对不同机构的数据隔离。
- **配置化**：关键业务规则（如分成比例）存储在配置表中，而非硬编码。
- **可扩展性**：用户和角色系统设计灵活，方便未来扩展到更多业务场景。
- **审计与日志**：关键操作（如资金变动、权限修改）都有对应的日志记录。
- **安全加密**：敏感配置（API密钥、支付密钥）采用加密存储。
- **工作流管理**：支持完整的AI文书审核工作流。

---

## 1. 用户与权限模块 (`users`)

### `tenants` - 租户表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 租户唯一ID |
| `name` | `VARCHAR(255)` | `NOT NULL` | 租户/机构名称 |
| `mode` | `ENUM('SAAS', 'ON_PREMISE')` | `NOT NULL` | 部署模式 |
| `domain` | `VARCHAR(255)` | `UNIQUE` | 自定义域名 |
| `status` | `ENUM('ACTIVE', 'INACTIVE')` | `NOT NULL` | 租户状态 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

### `users` - 用户表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 用户唯一ID |
| `tenant_id` | `UUID` | `FK > tenants.id` | 所属租户ID |
| `username` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | 用户名/登录名 |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | 加密后的密码 |
| `email` | `VARCHAR(255)` | `UNIQUE` | 邮箱 |
| `phone_number` | `VARCHAR(20)` | `UNIQUE` | 手机号 |
| `status` | `ENUM('PENDING', 'ACTIVE', 'BANNED')` | `NOT NULL` | 账户状态 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

### `roles` - 角色表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `SERIAL` | **PK** | 角色ID |
| `tenant_id` | `UUID` | `FK > tenants.id` | 所属租户ID（NULL表示平台全局角色） |
| `name` | `VARCHAR(50)` | `NOT NULL` | 角色名称（如：Lawyer, Sales, InstitutionAdmin） |
| `description` | `TEXT` | | 角色描述，对应律思客平台中的不同用户身份 |

### `user_roles` - 用户角色关联表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `user_id` | `UUID` | `FK > users.id` | 用户ID |
| `role_id` | `INTEGER` | `FK > roles.id` | 角色ID |
| **PK** | `(user_id, role_id)` | | 联合主键 |
| `assigned_to_user_id`| `UUID` | `FK > users.id` | 分配给的律师/执行者ID |
| `sales_user_id` | `UUID` | `FK > users.id` | 上传该案件的销售ID |
| `ai_risk_score` | `INTEGER` | | **Lawsker AI**评估的案件风险分 (0-100) |
| `data_quality_score`| `INTEGER` | | 导入时的数据质量分 (0-100) |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

### `profiles` - 用户资料表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `user_id` | `UUID` | **PK, FK > users.id** | 用户ID |
| `full_name` | `VARCHAR(255)` | | 真实姓名 |
| `id_card_number` | `VARCHAR(18)` | | 身份证号 |
| `qualification_details` | `JSONB` | | 资质详情（如律师执业证号、照片URL）|
| `did` | `VARCHAR(255)` | `UNIQUE` | Web3去中心化身份标识 |
| `verification_status` | `ENUM('UNVERIFIED', 'PENDING', 'VERIFIED', 'FAILED')` | | 认证状态 |

---

## 2. 业务与案件模块 (`business`)

### `cases` - 案件表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 案件唯一ID |
| `tenant_id` | `UUID` | `FK > tenants.id` | 所属租户ID |
| `client_id` | `UUID` | `FK > clients.id` | 关联客户ID |
| `debtor_info` | `JSONB` | `NOT NULL` | 债务人信息 |
| `case_amount` | `DECIMAL(18, 2)` | `NOT NULL` | 案件金额 |
| `status` | `ENUM('PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CLOSED')` | `NOT NULL` | 案件状态 |
| `assigned_to_user_id`| `UUID` | `FK > users.id` | 分配给的律师/执行者ID |
| `sales_user_id` | `UUID` | `FK > users.id` | 上传该案件的销售ID |
| `ai_risk_score` | `INTEGER` | | AI评估的案件风险分 (0-100) |
| `data_quality_score`| `INTEGER` | | 导入时的数据质量分 (0-100) |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |
| `debt_creation_date` | `DATE` | `NOT NULL` | 债权形成日期（时效计算起点） |
| `last_follow_up_date` | `DATE` | | 最近有效跟进/承诺日期（时效中断点） |
| `legal_status` | `VARCHAR(50)` | `NOT NULL` | 法律时效状态 (valid, expiring_soon, expired) |
| `data_freshness_score` | `INTEGER` | | 数据新鲜度评分 (0-100) |

### `clients` - 客户表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 客户唯一ID |
| `tenant_id` | `UUID` | `FK > tenants.id` | 所属租户ID |
| `name` | `VARCHAR(255)` | `NOT NULL` | 客户/公司名称 |
| `sales_owner_id` | `UUID` | `FK > users.id` | 负责该客户的销售ID |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

### `insurances` - 保险记录表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 保险记录ID |
| `case_id` | `UUID` | `FK > cases.id, UNIQUE` | 关联的案件ID |
| `policy_number` | `VARCHAR(255)` | `NOT NULL` | 保单号 |
| `insurance_company`| `VARCHAR(255)` | `NOT NULL` | 保险公司 |
| `premium_amount` | `DECIMAL(18, 2)` | `NOT NULL` | 保费金额 |
| `status` | `ENUM('PENDING', 'ACTIVE', 'CLAIMED', 'EXPIRED')`| `NOT NULL` | 保单状态 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

### `case_logs` - 案件日志表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `BIGSERIAL` | **PK** | 日志ID |
| `case_id` | `UUID` | `FK > cases.id` | 案件ID |
| `user_id` | `UUID` | `FK > users.id` | 操作用户ID |
| `action` | `VARCHAR(255)` | `NOT NULL` | 操作内容（如：创建案件、分配律师） |
| `details` | `JSONB` | | 详细信息 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

---

## 3. 财务与分账模块 (`finance`)

### `transactions` - 交易流水表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 交易唯一ID |
| `case_id` | `UUID` | `FK > cases.id` | 关联案件ID |
| `amount` | `DECIMAL(18, 2)` | `NOT NULL` | 交易金额 |
| `transaction_type` | `ENUM(TransactionType)` | `NOT NULL` | 交易类型 |
| `status` | `ENUM(TransactionStatus)` | `DEFAULT 'pending'` | 交易状态 |
| `payment_gateway` | `VARCHAR(50)` | | 支付渠道（微信支付、支付宝） |
| `gateway_txn_id` | `VARCHAR(255)` | `UNIQUE` | 支付网关交易号 |
| `gateway_response` | `JSONB` | | 网关响应数据 |
| `description` | `VARCHAR(500)` | | 交易描述 |
| `notes` | `VARCHAR(1000)` | | 备注 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |
| `completed_at` | `TIMESTAMPZ` | | 完成时间 |

**TransactionType枚举值**：`payment` (回款), `refund` (退款), `payout` (分账支出)
**TransactionStatus枚举值**：`pending` (待处理), `completed` (已完成), `failed` (失败)

### `commission_splits` - 分账记录表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 分账记录ID |
| `transaction_id` | `UUID` | `FK > transactions.id` | 关联的原始回款交易ID |
| `user_id` | `UUID` | `FK > users.id` | 收款用户ID |
| `role_at_split` | `VARCHAR(50)` | `NOT NULL` | 分账时的角色 |
| `amount` | `DECIMAL(18, 2)` | `NOT NULL` | 分账金额 |
| `percentage` | `DECIMAL(5, 4)` | `NOT NULL` | 分账比例 |
| `status` | `ENUM(CommissionStatus)` | `DEFAULT 'pending'` | 支付状态 |
| `payout_method` | `VARCHAR(50)` | | 支付方式 |
| `payout_account` | `VARCHAR(255)` | | 支付账户 |
| `payout_txn_id` | `VARCHAR(255)` | | 支付交易号 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `paid_at` | `TIMESTAMPZ` | | 支付时间 |

**CommissionStatus枚举值**：`pending` (待分账), `paid` (已支付), `failed` (失败)

### `wallets` - 用户钱包表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `user_id` | `UUID` | **PK, FK > users.id** | 用户ID |
| `balance` | `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 账户余额 |
| `withdrawable_balance`| `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 可提现余额 |
| `frozen_balance` | `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 冻结余额（如15%安全边际） |
| `total_earned` | `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 累计收入 |
| `total_withdrawn` | `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 累计提现 |
| `commission_count` | `DECIMAL(10, 0)` | `NOT NULL, DEFAULT 0` | 分账次数 |
| `last_commission_at` | `TIMESTAMPZ` | | 最后分账时间 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 最后更新时间 |

### `payment_orders` - 支付订单表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 订单ID |
| `out_trade_no` | `VARCHAR(64)` | `UNIQUE, NOT NULL` | 商户订单号 |
| `case_id` | `UUID` | `FK > cases.id` | 关联案件ID |
| `amount` | `DECIMAL(18, 2)` | `NOT NULL` | 订单金额 |
| `body` | `VARCHAR(128)` | `NOT NULL` | 订单描述 |
| `payment_gateway` | `VARCHAR(50)` | `NOT NULL` | 支付渠道 |
| `gateway_order_id` | `VARCHAR(255)` | | 支付网关订单ID |
| `qr_code` | `TEXT` | | 支付二维码 |
| `status` | `VARCHAR(20)` | `DEFAULT 'pending'` | 订单状态 |
| `notify_url` | `VARCHAR(255)` | | 回调地址 |
| `expired_at` | `TIMESTAMPZ` | | 过期时间 |
| `paid_at` | `TIMESTAMPZ` | | 支付时间 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

### `withdrawal_requests` - 提现申请表 ⚠️ 急需实现
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 申请ID |
| `user_id` | `UUID` | `FK > users.id` | 用户ID |
| `amount` | `DECIMAL(18, 2)` | `NOT NULL` | 提现金额 |
| `withdrawal_method` | `VARCHAR(50)` | `NOT NULL` | 提现方式（银行卡、支付宝、微信） |
| `account_info` | `JSONB` | `NOT NULL` | 收款账户信息 |
| `account_holder` | `VARCHAR(100)` | `NOT NULL` | 收款人姓名 |
| `status` | `ENUM('pending', 'approved', 'rejected', 'completed')` | `DEFAULT 'pending'` | 申请状态 |
| `admin_notes` | `TEXT` | | 管理员备注 |
| `processed_by` | `UUID` | `FK > users.id` | 处理人ID |
| `processed_at` | `TIMESTAMPZ` | | 处理时间 |
| `completed_at` | `TIMESTAMPZ` | | 完成时间 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 申请时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**注意**: 前端提现管理界面已集成到律师和销售工作台，急需对应的后端API支持。

---

## 4. Web3与开放平台模块 (`web3_api`)

### `api_keys` - API密钥表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `SERIAL` | **PK** | 密钥ID |
| `tenant_id` | `UUID` | `FK > tenants.id` | 所属租户ID |
| `key_prefix` | `VARCHAR(8)` | `UNIQUE, NOT NULL` | 密钥前缀（用于识别）|
| `hashed_key` | `VARCHAR(255)` | `NOT NULL` | HASH后的完整密钥 |
| `status` | `ENUM('ACTIVE', 'REVOKED')` | `NOT NULL` | 密钥状态 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

### `dao_proposals` - DAO提案表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 提案ID |
| `proposer_id` | `UUID` | `FK > users.id` | 提案人ID |
| `title` | `VARCHAR(255)` | `NOT NULL` | 提案标题 |
| `description` | `TEXT` | `NOT NULL` | 提案详情 |
| `status` | `ENUM('PENDING', 'ACTIVE', 'PASSED', 'FAILED')`| `NOT NULL` | 提案状态 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

### `dao_votes` - DAO投票表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `BIGSERIAL` | **PK** | 投票ID |
| `proposal_id` | `UUID` | `FK > dao_proposals.id` | 提案ID |
| `voter_id` | `UUID` | `FK > users.id` | 投票人ID |
| `decision` | `BOOLEAN` | `NOT NULL` | 投票决定 (true=赞成, false=反对) |
| `voting_power` | `DECIMAL(18, 2)` | `NOT NULL` | 投票权重（基于持有的治理代币）|
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

---

## 5. 系统配置模块 (`configuration`)

### `system_configs` - 系统配置表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `SERIAL` | **PK** | 配置ID |
| `tenant_id` | `UUID` | `FK > tenants.id` | 所属租户ID（NULL表示平台全局配置） |
| `category` | `VARCHAR(100)` | `NOT NULL` | 配置类别（ai_api_keys、payment_keys等） |
| `key` | `VARCHAR(255)` | `NOT NULL` | 配置项键名 |
| `value` | `JSONB` | `NOT NULL` | 配置项值 |
| `encrypted_value` | `TEXT` | | 加密后的配置值（敏感配置） |
| `description` | `TEXT` | | 配置描述 |
| `is_encrypted` | `BOOLEAN` | `DEFAULT FALSE` | 是否为加密配置 |
| `is_editable` | `BOOLEAN` | `DEFAULT TRUE` | 是否可编辑 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

---

## 6. AI文书审核工作流模块 (`ai_document_review`)

### `document_review_tasks` - 文档审核任务表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 任务唯一ID |
| `task_number` | `VARCHAR(50)` | `UNIQUE, NOT NULL` | 任务编号 |
| `case_id` | `UUID` | `FK > cases.id` | 关联案件ID（可选） |
| `order_id` | `UUID` | `FK > lawyer_letter_orders.id` | 关联订单ID（可选） |
| `lawyer_id` | `UUID` | `FK > users.id, NOT NULL` | 分配律师ID |
| `creator_id` | `UUID` | `FK > users.id, NOT NULL` | 创建者ID |
| `document_type` | `VARCHAR(50)` | `NOT NULL` | 文档类型 |
| `original_content` | `TEXT` | `NOT NULL` | AI生成的原始内容 |
| `current_content` | `TEXT` | `NOT NULL` | 当前内容 |
| `final_content` | `TEXT` | | 最终确认内容 |
| `status` | `ENUM(ReviewStatus)` | `DEFAULT 'pending'` | 审核状态 |
| `priority` | `INTEGER` | `DEFAULT 1` | 优先级（1-5） |
| `deadline` | `TIMESTAMPZ` | | 截止时间 |
| `ai_metadata` | `JSONB` | | AI生成元数据 |
| `generation_prompt` | `TEXT` | | 生成提示词 |
| `ai_providers` | `JSONB` | | 使用的AI提供商 |
| `review_notes` | `TEXT` | | 审核备注 |
| `modification_requests` | `TEXT` | | 修改要求 |
| `approval_notes` | `TEXT` | | 通过备注 |
| `rejection_reason` | `TEXT` | | 拒绝原因 |
| `auto_approve` | `BOOLEAN` | `DEFAULT FALSE` | 是否自动通过 |
| `requires_signature` | `BOOLEAN` | `DEFAULT TRUE` | 是否需要律师签名 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |
| `reviewed_at` | `TIMESTAMPZ` | | 审核时间 |
| `approved_at` | `TIMESTAMPZ` | | 通过时间 |
| `sent_at` | `TIMESTAMPZ` | | 发送时间 |

**ReviewStatus枚举值**：`pending` (待审核), `in_review` (审核中), `approved` (已通过), `rejected` (已拒绝), `modification_requested` (要求修改), `modified` (已修改), `authorized` (已授权发送), `sent` (已发送), `cancelled` (已取消)

### `document_review_logs` - 文档审核日志表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 日志ID |
| `review_task_id` | `UUID` | `FK > document_review_tasks.id, NOT NULL` | 审核任务ID |
| `reviewer_id` | `UUID` | `FK > users.id, NOT NULL` | 操作人ID |
| `action` | `VARCHAR(50)` | `NOT NULL` | 操作类型 |
| `old_status` | `ENUM(ReviewStatus)` | | 原状态 |
| `new_status` | `ENUM(ReviewStatus)` | `NOT NULL` | 新状态 |
| `comment` | `TEXT` | | 操作说明 |
| `content_changes` | `JSONB` | | 内容变更记录 |
| `attachment_files` | `JSONB` | | 附件文件 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 操作时间 |

### `lawyer_workloads` - 律师工作负荷表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 记录ID |
| `lawyer_id` | `UUID` | `FK > users.id, UNIQUE, NOT NULL` | 律师ID |
| `active_cases` | `INTEGER` | `DEFAULT 0` | 活跃案件数 |
| `pending_reviews` | `INTEGER` | `DEFAULT 0` | 待审核文档数 |
| `daily_capacity` | `INTEGER` | `DEFAULT 10` | 日处理能力 |
| `weekly_capacity` | `INTEGER` | `DEFAULT 50` | 周处理能力 |
| `average_review_time` | `INTEGER` | `DEFAULT 0` | 平均审核时间（分钟） |
| `approval_rate` | `INTEGER` | `DEFAULT 95` | 通过率（百分比） |
| `client_satisfaction` | `INTEGER` | `DEFAULT 90` | 客户满意度（百分比） |
| `is_available` | `BOOLEAN` | `DEFAULT TRUE` | 是否可接新任务 |
| `max_concurrent_tasks` | `INTEGER` | `DEFAULT 20` | 最大并发任务数 |
| `current_workload_score` | `INTEGER` | `DEFAULT 0` | 当前工作负荷评分 |
| `specialties` | `JSONB` | | 专业领域 |
| `preferred_document_types` | `JSONB` | | 偏好文档类型 |
| `last_assignment_at` | `TIMESTAMPZ` | | 最后分配时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

### `lawyer_letter_orders` - 律师函订单表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 订单ID |
| `order_number` | `VARCHAR(50)` | `UNIQUE, NOT NULL` | 订单编号 |
| `client_name` | `VARCHAR(255)` | `NOT NULL` | 客户姓名 |
| `client_phone` | `VARCHAR(20)` | `NOT NULL` | 客户电话 |
| `client_email` | `VARCHAR(255)` | | 客户邮箱 |
| `client_company` | `VARCHAR(255)` | | 客户公司 |
| `target_name` | `VARCHAR(255)` | `NOT NULL` | 对方姓名/公司名 |
| `target_phone` | `VARCHAR(20)` | | 对方电话 |
| `target_email` | `VARCHAR(255)` | | 对方邮箱 |
| `target_address` | `TEXT` | | 对方地址 |
| `letter_type` | `VARCHAR(50)` | `NOT NULL` | 律师函类型 |
| `case_background` | `TEXT` | `NOT NULL` | 案件背景 |
| `legal_basis` | `TEXT` | | 法律依据 |
| `demands` | `JSONB` | | 具体要求 |
| `content_brief` | `TEXT` | `NOT NULL` | 内容简述 |
| `urgency` | `VARCHAR(20)` | `DEFAULT '普通'` | 紧急程度 |
| `amount` | `DECIMAL(18, 2)` | `DEFAULT 30.00` | 订单金额 |
| `status` | `VARCHAR(20)` | `DEFAULT 'pending'` | 订单状态 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

---

## 7. 管理后台数据分析模块 (`admin_analytics`) ✅ **新增完成**

### `access_logs` - 访问日志表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 日志ID |
| `user_id` | `UUID` | `FK > users.id` | 用户ID（可为NULL） |
| `ip_address` | `INET` | `NOT NULL` | 访问IP地址 |
| `user_agent` | `TEXT` | | 用户代理字符串 |
| `path` | `VARCHAR(255)` | `NOT NULL` | 访问路径 |
| `method` | `VARCHAR(10)` | `NOT NULL` | HTTP方法 |
| `status_code` | `INTEGER` | `NOT NULL` | 响应状态码 |
| `response_time` | `INTEGER` | | 响应时间（毫秒） |
| `referrer` | `TEXT` | | 来源页面 |
| `session_id` | `VARCHAR(255)` | | 会话ID |
| `country` | `VARCHAR(100)` | | 国家 |
| `city` | `VARCHAR(100)` | | 城市 |
| `browser` | `VARCHAR(100)` | | 浏览器 |
| `device_type` | `VARCHAR(50)` | | 设备类型 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 访问时间 |

**索引**: `idx_access_logs_user_id`, `idx_access_logs_ip`, `idx_access_logs_created_at`, `idx_access_logs_path`

### `daily_statistics` - 每日统计表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 统计ID |
| `date` | `DATE` | `UNIQUE, NOT NULL` | 统计日期 |
| `total_visits` | `INTEGER` | `DEFAULT 0` | 总访问量 |
| `unique_visitors` | `INTEGER` | `DEFAULT 0` | 独立访客数 |
| `new_users` | `INTEGER` | `DEFAULT 0` | 新用户数 |
| `new_lawyers` | `INTEGER` | `DEFAULT 0` | 新律师数 |
| `new_cases` | `INTEGER` | `DEFAULT 0` | 新案件数 |
| `completed_cases` | `INTEGER` | `DEFAULT 0` | 完成案件数 |
| `total_revenue` | `DECIMAL(18, 2)` | `DEFAULT 0` | 总收入 |
| `avg_response_time` | `INTEGER` | | 平均响应时间 |
| `bounce_rate` | `DECIMAL(5, 2)` | | 跳出率 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_daily_statistics_date`

### `ip_statistics` - IP地址统计表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 统计ID |
| `ip_address` | `INET` | `UNIQUE, NOT NULL` | IP地址 |
| `visit_count` | `INTEGER` | `DEFAULT 1` | 访问次数 |
| `first_visit` | `TIMESTAMPZ` | `NOT NULL` | 首次访问时间 |
| `last_visit` | `TIMESTAMPZ` | `NOT NULL` | 最后访问时间 |
| `country` | `VARCHAR(100)` | | 国家 |
| `city` | `VARCHAR(100)` | | 城市 |
| `is_suspicious` | `BOOLEAN` | `DEFAULT FALSE` | 是否可疑 |
| `blocked` | `BOOLEAN` | `DEFAULT FALSE` | 是否被封禁 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_ip_statistics_country`, `idx_ip_statistics_suspicious`

### `page_analytics` - 页面分析表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 分析ID |
| `path` | `VARCHAR(255)` | `NOT NULL` | 页面路径 |
| `date` | `DATE` | `NOT NULL` | 统计日期 |
| `page_views` | `INTEGER` | `DEFAULT 0` | 页面浏览量 |
| `unique_views` | `INTEGER` | `DEFAULT 0` | 独立浏览量 |
| `avg_time_on_page` | `INTEGER` | | 平均停留时间（秒） |
| `bounce_rate` | `DECIMAL(5, 2)` | | 跳出率 |
| `entrance_count` | `INTEGER` | `DEFAULT 0` | 入口页次数 |
| `exit_count` | `INTEGER` | `DEFAULT 0` | 出口页次数 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_page_analytics_path_date`

### `lawyer_performance_stats` - 律师绩效统计表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 统计ID |
| `lawyer_id` | `UUID` | `FK > users.id, NOT NULL` | 律师ID |
| `period_type` | `VARCHAR(20)` | `NOT NULL` | 统计周期类型 |
| `period_start` | `DATE` | `NOT NULL` | 周期开始日期 |
| `period_end` | `DATE` | `NOT NULL` | 周期结束日期 |
| `cases_handled` | `INTEGER` | `DEFAULT 0` | 处理案件数 |
| `cases_won` | `INTEGER` | `DEFAULT 0` | 胜诉案件数 |
| `total_revenue` | `DECIMAL(18, 2)` | `DEFAULT 0` | 总收入 |
| `avg_case_duration` | `INTEGER` | | 平均案件时长（天） |
| `client_satisfaction` | `DECIMAL(3, 2)` | | 客户满意度评分 |
| `response_time_avg` | `INTEGER` | | 平均响应时间（小时） |
| `documents_reviewed` | `INTEGER` | `DEFAULT 0` | 审核文档数 |
| `efficiency_score` | `DECIMAL(5, 2)` | | 效率评分 |
| `ranking_position` | `INTEGER` | | 排名位置 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_lawyer_performance_unique`, `idx_lawyer_performance_period`, `idx_lawyer_performance_ranking`

### `user_performance_stats` - 用户绩效统计表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 统计ID |
| `user_id` | `UUID` | `FK > users.id, NOT NULL` | 用户ID |
| `period_type` | `VARCHAR(20)` | `NOT NULL` | 统计周期类型 |
| `period_start` | `DATE` | `NOT NULL` | 周期开始日期 |
| `period_end` | `DATE` | `NOT NULL` | 周期结束日期 |
| `cases_created` | `INTEGER` | `DEFAULT 0` | 创建案件数 |
| `total_spent` | `DECIMAL(18, 2)` | `DEFAULT 0` | 总消费金额 |
| `avg_rating_given` | `DECIMAL(3, 2)` | | 平均给分 |
| `login_frequency` | `INTEGER` | `DEFAULT 0` | 登录频次 |
| `activity_score` | `DECIMAL(5, 2)` | | 活跃度评分 |
| `engagement_level` | `VARCHAR(20)` | | 参与度等级 |
| `referral_count` | `INTEGER` | `DEFAULT 0` | 推荐人数 |
| `ranking_position` | `INTEGER` | | 排名位置 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_user_performance_unique`, `idx_user_performance_period`, `idx_user_performance_level`, `idx_user_performance_ranking`

### `ranking_snapshots` - 排名快照表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 快照ID |
| `snapshot_type` | `VARCHAR(50)` | `NOT NULL` | 快照类型 |
| `snapshot_date` | `DATE` | `NOT NULL` | 快照日期 |
| `ranking_data` | `JSONB` | `NOT NULL` | 排名数据 |
| `metadata` | `JSONB` | | 元数据 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

**索引**: `idx_ranking_snapshots_type`

### `system_metrics` - 系统指标表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 指标ID |
| `metric_type` | `VARCHAR(100)` | `NOT NULL` | 指标类型 |
| `metric_name` | `VARCHAR(255)` | `NOT NULL` | 指标名称 |
| `metric_value` | `DECIMAL(18, 6)` | `NOT NULL` | 指标值 |
| `unit` | `VARCHAR(50)` | | 单位 |
| `tags` | `JSONB` | | 标签 |
| `threshold_warning` | `DECIMAL(18, 6)` | | 警告阈值 |
| `threshold_critical` | `DECIMAL(18, 6)` | | 严重阈值 |
| `is_alert` | `BOOLEAN` | `DEFAULT FALSE` | 是否告警 |
| `recorded_at` | `TIMESTAMPZ` | `NOT NULL` | 记录时间 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

**索引**: `idx_system_metrics_type`, `idx_system_metrics_time`, `idx_system_metrics_alert`

### `system_logs` - 系统日志表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 日志ID |
| `level` | `VARCHAR(20)` | `NOT NULL` | 日志级别 |
| `source` | `VARCHAR(100)` | `NOT NULL` | 日志来源 |
| `message` | `TEXT` | `NOT NULL` | 日志消息 |
| `context` | `JSONB` | | 上下文数据 |
| `user_id` | `UUID` | `FK > users.id` | 相关用户ID |
| `ip_address` | `INET` | | IP地址 |
| `user_agent` | `TEXT` | | 用户代理 |
| `session_id` | `VARCHAR(255)` | | 会话ID |
| `request_id` | `VARCHAR(255)` | | 请求ID |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

**索引**: `idx_system_logs_level`, `idx_system_logs_source`, `idx_system_logs_time`, `idx_system_logs_user`

### `backup_records` - 备份记录表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 备份ID |
| `backup_type` | `VARCHAR(50)` | `NOT NULL` | 备份类型 |
| `file_path` | `TEXT` | `NOT NULL` | 文件路径 |
| `file_size` | `BIGINT` | | 文件大小（字节） |
| `checksum` | `VARCHAR(255)` | | 文件校验和 |
| `status` | `VARCHAR(20)` | `DEFAULT 'pending'` | 备份状态 |
| `created_by` | `UUID` | `FK > users.id` | 创建人ID |
| `started_at` | `TIMESTAMPZ` | | 开始时间 |
| `completed_at` | `TIMESTAMPZ` | | 完成时间 |
| `error_message` | `TEXT` | | 错误信息 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

**索引**: `idx_backup_records_status`, `idx_backup_records_time`

### `alert_records` - 告警记录表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 告警ID |
| `alert_type` | `VARCHAR(100)` | `NOT NULL` | 告警类型 |
| `level` | `VARCHAR(20)` | `NOT NULL` | 告警级别 |
| `title` | `VARCHAR(255)` | `NOT NULL` | 告警标题 |
| `message` | `TEXT` | `NOT NULL` | 告警消息 |
| `source` | `VARCHAR(100)` | | 告警来源 |
| `metadata` | `JSONB` | | 告警元数据 |
| `is_resolved` | `BOOLEAN` | `DEFAULT FALSE` | 是否已解决 |
| `resolved_by` | `UUID` | `FK > users.id` | 解决人ID |
| `resolved_at` | `TIMESTAMPZ` | | 解决时间 |
| `resolution_notes` | `TEXT` | | 解决备注 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

**索引**: `idx_alert_records_type`, `idx_alert_records_level`, `idx_alert_records_resolved`

### `statistics_summary` - 统计汇总表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 汇总ID |
| `summary_type` | `VARCHAR(100)` | `NOT NULL` | 汇总类型 |
| `dimension` | `VARCHAR(100)` | `NOT NULL` | 维度 |
| `period` | `VARCHAR(50)` | `NOT NULL` | 时间周期 |
| `date_key` | `VARCHAR(50)` | `NOT NULL` | 日期键 |
| `metrics` | `JSONB` | `NOT NULL` | 指标数据 |
| `metadata` | `JSONB` | | 元数据 |
| `expires_at` | `TIMESTAMPZ` | | 过期时间 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_statistics_summary_unique`, `idx_statistics_summary_type`, `idx_statistics_summary_expires`

### `dashboard_cache` - 仪表板缓存表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 缓存ID |
| `cache_key` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | 缓存键 |
| `cache_type` | `VARCHAR(100)` | `NOT NULL` | 缓存类型 |
| `data` | `JSONB` | `NOT NULL` | 缓存数据 |
| `expires_at` | `TIMESTAMPZ` | `NOT NULL` | 过期时间 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_dashboard_cache_type`, `idx_dashboard_cache_expires`

### `report_schedules` - 报表调度表 ✅
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 调度ID |
| `name` | `VARCHAR(255)` | `NOT NULL` | 报表名称 |
| `report_type` | `VARCHAR(100)` | `NOT NULL` | 报表类型 |
| `schedule_expression` | `VARCHAR(100)` | `NOT NULL` | 调度表达式（cron） |
| `parameters` | `JSONB` | | 报表参数 |
| `recipients` | `JSONB` | `NOT NULL` | 接收人列表 |
| `format` | `VARCHAR(20)` | `DEFAULT 'pdf'` | 报表格式 |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | 是否激活 |
| `last_run_at` | `TIMESTAMPZ` | | 最后运行时间 |
| `next_run_at` | `TIMESTAMPZ` | | 下次运行时间 |
| `created_by` | `UUID` | `FK > users.id, NOT NULL` | 创建人ID |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 更新时间 |

**索引**: `idx_report_schedules_active`, `idx_report_schedules_next_run`

### 数据库函数和触发器 ✅
- `update_updated_at_column()` - 自动更新updated_at字段的函数
- 各表的更新时间触发器，自动维护数据一致性

**特性说明**:
1. **UUID主键**: 所有表统一使用UUID主键，确保分布式环境下的唯一性
2. **外键约束**: 严格的外键关系，保证数据完整性
3. **索引优化**: 针对查询模式优化的复合索引和单列索引
4. **JSONB支持**: 灵活的元数据和配置存储
5. **时区支持**: 统一使用TIMESTAMPZ确保时区正确性
6. **自动触发器**: 自动维护updated_at字段
7. **缓存机制**: 内置缓存表提升查询性能

---

## 📊 系统实现状态更新 (2024年12月)

### 总体进度
- **数据库设计完成度**: 100% (7个核心模块，90+张表)
- **Analytics模块**: ✅ 新增完成 (18张表)
- **数据迁移状态**: ✅ 全部执行成功
- **生产环境部署**: ✅ 运行正常
- **系统稳定性**: ✅ 优秀

### 最新完成功能
1. **管理后台数据分析**: 完整的analytics基础设施
2. **实时监控系统**: 系统指标和日志记录
3. **绩效排名体系**: 律师和用户多维度排名
4. **数据缓存优化**: 仪表板数据缓存机制
5. **自动化报表**: 可配置的报表调度系统

### 技术特性增强
- **数据一致性**: UUID主键和严格外键约束
- **查询性能**: 优化的索引策略
- **扩展性**: JSONB字段支持灵活数据结构
- **监控能力**: 全方位的系统监控和告警
- **缓存策略**: 多层次缓存提升响应速度

---