# WorkBridge - 数据库表结构设计 v1.0

## 核心设计原则
- **多租户隔离**：所有核心业务表都包含 `tenant_id` 字段，用于SaaS数据隔离。
- **配置化**：关键业务规则（如分成比例）存储在配置表中，而非硬编码。
- **可扩展性**：用户和角色系统设计灵活，方便未来扩展到更多业务场景。
- **审计与日志**：关键操作（如资金变动、权限修改）都有对应的日志记录。

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
| `name` | `VARCHAR(50)` | `NOT NULL` | 角色名称（如：律师、销售、机构管理员） |
| `description` | `TEXT` | | 角色描述 |

### `user_roles` - 用户角色关联表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `user_id` | `UUID` | `FK > users.id` | 用户ID |
| `role_id` | `INTEGER` | `FK > roles.id` | 角色ID |
| **PK** | `(user_id, role_id)` | | 联合主键 |

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
| `type` | `ENUM('PAYMENT', 'REFUND', 'PAYOUT')` | `NOT NULL` | 交易类型（回款、退款、分账支出） |
| `status` | `ENUM('PENDING', 'COMPLETED', 'FAILED')` | `NOT NULL` | 交易状态 |
| `payment_gateway` | `VARCHAR(50)` | | 支付渠道（微信支付、支付宝） |
| `gateway_txn_id` | `VARCHAR(255)` | `UNIQUE` | 支付网关交易号 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

### `commission_splits` - 分账记录表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | `UUID` | **PK** | 分账记录ID |
| `transaction_id` | `UUID` | `FK > transactions.id` | 关联的原始回款交易ID |
| `user_id` | `UUID` | `FK > users.id` | 收款用户ID |
| `role_at_split` | `VARCHAR(50)` | `NOT NULL` | 分账时的角色（律师、销售、平台） |
| `amount` | `DECIMAL(18, 2)` | `NOT NULL` | 分账金额 |
| `status` | `ENUM('PENDING', 'PAID', 'FAILED')` | `NOT NULL` | 支付状态 |
| `created_at` | `TIMESTAMPZ` | `NOT NULL` | 创建时间 |

### `wallets` - 用户钱包表
| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `user_id` | `UUID` | **PK, FK > users.id** | 用户ID |
| `balance` | `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 账户余额 |
| `withdrawable_balance`| `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 可提现余额 |
| `frozen_balance` | `DECIMAL(18, 2)` | `NOT NULL, DEFAULT 0` | 冻结余额（如15%安全边际） |
| `updated_at` | `TIMESTAMPZ` | `NOT NULL` | 最后更新时间 |

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
| `key` | `VARCHAR(255)` | `NOT NULL` | 配置项键（如：`commission_rate.lawyer`） |
| `value` | `JSONB` | `NOT NULL` | 配置项值 |
| `description` | `TEXT` | | 配置描述 |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | 是否启用 |

--- 