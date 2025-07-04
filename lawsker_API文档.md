# Lawsker (律思客) - API接口文档 v1.2 (Powered by WorkBridge)

## 认证机制
- **认证方式**: Lawsker平台所有需要登录的接口都使用 `JWT (JSON Web Token)` 进行认证。
- **Token传递**: 在请求的 `Header` 中加入 `Authorization: Bearer <your_jwt_token>`。
- **Token获取**: 通过 `POST /api/v1/auth/login` 接口获取。

---

## 1. 认证接口 (`/api/v1/auth`)

### 用户注册
- **Endpoint**: `POST /api/v1/auth/register`
- **描述**: 新用户注册，支持律师、销售、机构管理员角色
- **请求体**:
```json
{
  "email": "user@example.com",
  "password": "strong_password",
  "role": "lawyer",
  "full_name": "张三"
}
```
- **成功响应 (201)**:
```json
{
  "message": "注册成功",
  "user_id": "uuid-user-123",
  "status": "success"
}
```

### 用户登录
- **Endpoint**: `POST /api/v1/auth/login`
- **描述**: 用户登录并获取JWT令牌
- **请求体**:
```json
{
  "email": "user@example.com",
  "password": "strong_password"
}
```
- **成功响应 (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 用户登出
- **Endpoint**: `POST /api/v1/auth/logout`
- **描述**: 用户登出
- **成功响应 (200)**:
```json
{
  "message": "登出成功",
  "status": "success"
}
```

### 获取当前用户信息
- **Endpoint**: `GET /api/v1/auth/me`
- **描述**: 获取当前登录用户的详细信息
- **成功响应 (200)**:
```json
{
  "id": "uuid-user-123",
  "email": "lawyer@example.com",
  "role": "lawyer",
  "status": "active"
}
```

### 刷新令牌
- **Endpoint**: `POST /api/v1/auth/refresh`
- **描述**: 刷新JWT令牌
- **成功响应 (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 2. 案件管理接口 (`/api/v1/cases`)

### 创建案件
- **Endpoint**: `POST /api/v1/cases/`
- **描述**: 创建新案件
- **请求体**:
```json
{
  "client_id": "uuid-client-123",
  "debtor_info": {
    "name": "李四",
    "phone": "13800138000",
    "id_card": "110101199001011234",
    "address": "北京市朝阳区"
  },
  "case_amount": 50000.00,
  "sales_user_id": "uuid-sales-456",
  "debt_creation_date": "2023-01-01",
  "description": "案件描述",
  "notes": "备注",
  "tags": ["紧急", "高优先级"]
}
```
- **成功响应 (200)**:
```json
{
  "id": "uuid-case-789",
  "case_number": "CASE202312070001",
  "debtor_info": {...},
  "case_amount": 50000.00,
  "status": "pending",
  "created_at": "2023-12-07T10:00:00Z"
}
```

### 获取案件列表
- **Endpoint**: `GET /api/v1/cases/`
- **描述**: 获取案件列表，支持分页和筛选
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认20）
  - `status_filter`: 状态过滤
  - `assigned_to`: 分配给律师ID
  - `keyword`: 关键词搜索
- **成功响应 (200)**:
```json
{
  "items": [
    {
      "id": "uuid-case-789",
      "case_number": "CASE202312070001",
      "debtor_info": {...},
      "case_amount": 50000.00,
      "status": "pending",
      "created_at": "2023-12-07T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 获取案件详情
- **Endpoint**: `GET /api/v1/cases/{case_id}`
- **描述**: 获取单个案件的详细信息
- **成功响应 (200)**:
```json
{
  "id": "uuid-case-789",
  "case_number": "CASE202312070001",
  "debtor_info": {...},
  "case_amount": 50000.00,
  "status": "pending",
  "description": "案件描述",
  "notes": "备注",
  "created_at": "2023-12-07T10:00:00Z"
}
```

### 分配案件
- **Endpoint**: `POST /api/v1/cases/{case_id}/assign`
- **描述**: 分配案件给律师
- **请求体**:
```json
{
  "lawyer_id": "uuid-lawyer-123"
}
```
- **成功响应 (200)**:
```json
{
  "id": "uuid-case-789",
  "case_number": "CASE202312070001",
  "assigned_to_user_id": "uuid-lawyer-123",
  "status": "assigned"
}
```

### 智能分配案件
- **Endpoint**: `POST /api/v1/cases/{case_id}/smart-assign`
- **描述**: 基于AI算法智能分配案件
- **成功响应 (200)**:
```json
{
  "id": "uuid-case-789",
  "case_number": "CASE202312070001",
  "assigned_to_user_id": "uuid-lawyer-123",
  "status": "assigned"
}
```

### 更新案件状态
- **Endpoint**: `PATCH /api/v1/cases/{case_id}/status`
- **描述**: 更新案件状态
- **请求体**:
```json
{
  "status": "in_progress",
  "notes": "开始处理案件"
}
```
- **成功响应 (200)**:
```json
{
  "id": "uuid-case-789",
  "status": "in_progress",
  "updated_at": "2023-12-07T11:00:00Z"
}
```

### 获取案件统计
- **Endpoint**: `GET /api/v1/cases/statistics/overview`
- **描述**: 获取案件统计信息
- **成功响应 (200)**:
```json
{
  "total_cases": 1000,
  "pending_cases": 150,
  "in_progress_cases": 300,
  "completed_cases": 550,
  "success_rate": 0.85,
  "average_completion_time": 15.5
}
```

## 3. AI文书审核系统 (`/api/v1/ai`)

### 创建催收律师函
- **Endpoint**: `POST /api/v1/ai/documents/collection-letter`
- **描述**: 为催收案件创建律师函审核任务
- **请求体**:
```json
{
  "case_id": "uuid-case-456",
  "tone_style": "正式通知",
  "grace_period": 15,
  "priority": 2
}
```
- **成功响应 (200)**:
```json
{
  "id": "uuid-task-123",
  "task_number": "REV202312070001",
  "case_id": "uuid-case-456",
  "document_type": "collection_letter",
  "status": "pending",
  "priority": 2,
  "created_at": "2023-12-07T10:00:00Z"
}
```

### 创建独立律师函
- **Endpoint**: `POST /api/v1/ai/documents/independent-letter`
- **描述**: 为独立律师函服务创建审核任务
- **请求体**:
```json
{
  "client_name": "张三",
  "client_phone": "13800138000",
  "target_name": "李四公司",
  "letter_type": "debt_collection",
  "case_background": "合同纠纷案件",
  "demands": ["立即停止违约行为", "支付违约金"],
  "content_brief": "要求履行合同义务",
  "urgency": "普通",
  "priority": 2
}
```

### 律师接受任务
- **Endpoint**: `POST /api/v1/ai/tasks/{task_id}/accept`
- **描述**: 律师接受审核任务
- **请求体**:
```json
{
  "notes": "已接受任务，开始审核"
}
```
- **成功响应 (200)**:
```json
{
  "id": "uuid-task-123",
  "status": "in_review",
  "reviewed_at": "2023-12-07T11:00:00Z"
}
```

### 律师通过审核
- **Endpoint**: `POST /api/v1/ai/tasks/{task_id}/approve`
- **描述**: 律师通过文档审核
- **请求体**:
```json
{
  "approval_notes": "文档内容符合要求",
  "final_content": "经律师审核确认的最终内容"
}
```
- **成功响应 (200)**:
```json
{
  "id": "uuid-task-123",
  "status": "approved",
  "approved_at": "2023-12-07T12:00:00Z"
}
```

### 律师要求修改
- **Endpoint**: `POST /api/v1/ai/tasks/{task_id}/modify`
- **描述**: 律师要求修改文档
- **请求体**:
```json
{
  "modification_requests": "需要修改第三段的法律条款引用",
  "current_content": "当前文档内容"
}
```

### 律师授权发送
- **Endpoint**: `POST /api/v1/ai/tasks/{task_id}/authorize`
- **描述**: 律师授权发送文档
- **请求体**:
```json
{
  "authorization_notes": "授权发送，已确认所有信息准确"
}
```

### 获取待处理任务
- **Endpoint**: `GET /api/v1/ai/tasks/pending`
- **描述**: 获取律师待处理任务列表
- **查询参数**:
  - `limit`: 限制数量（默认20）
  - `offset`: 偏移量（默认0）
- **成功响应 (200)**:
```json
[
  {
    "id": "uuid-task-123",
    "task_number": "REV202312070001",
    "document_type": "collection_letter",
    "status": "pending",
    "priority": 2,
    "created_at": "2023-12-07T10:00:00Z"
  }
]
```

### 获取任务详情
- **Endpoint**: `GET /api/v1/ai/tasks/{task_id}`
- **描述**: 获取任务详情
- **成功响应 (200)**:
```json
{
  "id": "uuid-task-123",
  "task_number": "REV202312070001",
  "case_id": "uuid-case-456",
  "document_type": "collection_letter",
  "original_content": "AI生成的原始内容",
  "current_content": "当前内容",
  "status": "pending",
  "priority": 2,
  "created_at": "2023-12-07T10:00:00Z"
}
```

### 获取任务统计
- **Endpoint**: `GET /api/v1/ai/statistics`
- **描述**: 获取任务统计信息
- **成功响应 (200)**:
```json
{
  "status_counts": {
    "pending": 10,
    "in_review": 5,
    "approved": 20
  },
  "today_created": 8,
  "overdue": 2,
  "total": 35
}
```

### 重新生成文档
- **Endpoint**: `POST /api/v1/ai/documents/regenerate`
- **描述**: 重新生成文档
- **请求体**:
```json
{
  "original_content": "原始文档内容",
  "modification_requests": "修改要求",
  "document_type": "collection_letter"
}
```
- **成功响应 (200)**:
```json
{
  "content": "重新生成的文档内容",
  "regenerated_at": "2023-12-07T13:00:00Z",
  "modification_requests": "修改要求"
}
```

## 4. 财务管理接口 (`/api/v1/finance`)

### 创建支付订单
- **Endpoint**: `POST /api/v1/finance/payment/create`
- **描述**: 创建微信支付订单
- **请求体**:
```json
{
  "case_id": "uuid-case-456",
  "amount": 50000.00,
  "description": "案件支付"
}
```
- **成功响应 (200)**:
```json
{
  "success": true,
  "out_trade_no": "ORDER202312070001",
  "qr_code": "weixin://wxpay/s/A123456",
  "message": "支付订单创建成功"
}
```

### 处理支付回调
- **Endpoint**: `POST /api/v1/finance/payment/callback`
- **描述**: 处理微信支付回调（系统内部使用）
- **请求体**:
```json
{
  "out_trade_no": "ORDER202312070001",
  "transaction_id": "WX123456789",
  "total_fee": "5000000",
  "time_end": "20231207120000"
}
```
- **成功响应 (200)**:
```json
{
  "return_code": "SUCCESS",
  "return_msg": "OK"
}
```

### 获取用户钱包
- **Endpoint**: `GET /api/v1/finance/wallet`
- **描述**: 获取用户钱包信息
- **成功响应 (200)**:
```json
{
  "user_id": "uuid-user-123",
  "balance": 15000.00,
  "withdrawable_balance": 12000.00,
  "frozen_balance": 3000.00,
  "total_earned": 50000.00,
  "total_withdrawn": 35000.00,
  "commission_count": 25,
  "last_commission_at": "2023-12-06T15:30:00Z"
}
```

### 获取分账汇总
- **Endpoint**: `GET /api/v1/finance/commission/summary`
- **描述**: 获取用户分账汇总统计
- **查询参数**:
  - `days`: 统计天数（默认30天）
- **成功响应 (200)**:
```json
{
  "total_count": 25,
  "total_amount": 15000.00,
  "average_amount": 600.00,
  "monthly_trend": [
    {
      "month": "2023-12",
      "amount": 8000.00,
      "count": 15
    }
  ]
}
```

### 获取分账明细
- **Endpoint**: `GET /api/v1/finance/commission/details`
- **描述**: 获取用户分账明细记录
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认20）
- **成功响应 (200)**:
```json
{
  "items": [
    {
      "id": "uuid-split-123",
      "transaction_id": "uuid-txn-456",
      "case_number": "CASE202312070001",
      "role_at_split": "lawyer",
      "amount": 1500.00,
      "percentage": 0.30,
      "status": "paid",
      "created_at": "2023-12-07T12:00:00Z",
      "paid_at": "2023-12-07T12:30:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20,
  "total_pages": 2
}
```

### 获取交易记录
- **Endpoint**: `GET /api/v1/finance/transactions`
- **描述**: 获取交易记录列表
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认20）
  - `transaction_type`: 交易类型过滤
  - `status_filter`: 状态过滤
- **成功响应 (200)**:
```json
{
  "items": [
    {
      "id": "uuid-txn-456",
      "case_id": "uuid-case-789",
      "case_number": "CASE202312070001",
      "amount": 50000.00,
      "transaction_type": "payment",
      "status": "completed",
      "payment_gateway": "wechat_pay",
      "gateway_txn_id": "WX123456789",
      "description": "案件支付",
      "created_at": "2023-12-07T12:00:00Z",
      "completed_at": "2023-12-07T12:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### 申请提现
- **Endpoint**: `POST /api/v1/finance/wallet/withdraw`
- **描述**: 用户申请提现
- **请求体**:
```json
{
  "amount": 5000.00
}
```
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "提现申请已提交，请等待处理",
  "amount": 5000.00,
  "estimated_arrival": "1-3个工作日"
}
```

## 5. 机构管理员接口 (`/api/institution`)

### 获取业务总览
- **Endpoint**: `GET /api/institution/dashboard`
- **描述**: 获取机构在Lawsker平台的业务数据总览
- **成功响应 (200)**:
```json
{
  "active_cases": 150,
  "total_recovery_amount": 1200000.00,
  "success_rate": 0.75,
  "current_roi": 2.5
}
```

### 为案件购买保险
- **Endpoint**: `POST /api/institution/cases/{caseId}/insurances`
- **描述**: 为超过特定金额（如10万）的案件上传保险信息
- **请求体**:
```json
{
  "policy_number": "POLICY123456789",
  "insurance_company": "平安保险",
  "premium_amount": 500.00
}
```
- **成功响应 (201)**:
```json
{
  "message": "Insurance information uploaded successfully."
}
```

### 查看分账明细
- **Endpoint**: `GET /api/institution/settlements`
- **描述**: 查看机构在Lawsker平台的资金分账明细
- **成功响应 (200)**:
```json
[
  {
    "case_id": "uuid-case-456",
    "total_payment": 100000.00,
    "settlement_amount": 50000.00, // 50%返还
    "status": "PAID",
    "paid_at": "2023-10-28T10:00:00Z"
  }
]
```

## 6. Web3 接口 (`/api/web3`)

### 提交DAO治理提案
- **Endpoint**: `POST /api/web3/dao/proposals`
- **描述**: 社区成员提交一个新的DAO治理提案
- **请求体**:
```json
{
  "title": "关于调整律师分成比例的提案",
  "description": "建议将律师的基础分成比例从10%提升至12%..."
}
```
- **成功响应 (201)**:
```json
{
  "message": "Proposal submitted successfully.",
  "proposal_id": "uuid-proposal-abc"
}
```

### 对提案进行投票
- **Endpoint**: `POST /api/web3/dao/proposals/{proposalId}/vote`
- **描述**: 对一个激活的提案进行投票
- **请求体**:
```json
{
  "decision": true // true for 'approve', false for 'reject'
}
```
- **成功响应 (200)**:
```json
{
  "message": "Your vote has been recorded."
}
```

## 5. 系统配置管理接口 (`/api/v1/admin`)

### 获取配置类别
- **Endpoint**: `GET /api/v1/admin/configs/categories`
- **描述**: 获取所有配置类别列表
- **查询参数**:
  - `tenant_id`: 租户ID（可选，空表示全局配置）
- **成功响应 (200)**:
```json
[
  "ai_api_keys",
  "payment_keys", 
  "business",
  "third_party_apis",
  "security_keys"
]
```

### 获取类别配置
- **Endpoint**: `GET /api/v1/admin/configs/{category}`
- **描述**: 获取指定类别的所有配置项
- **查询参数**:
  - `tenant_id`: 租户ID（可选）
  - `decrypt_sensitive`: 是否解密敏感配置（默认true）
- **成功响应 (200)**:
```json
{
  "success": true,
  "data": [
    {
      "category": "ai_api_keys",
      "key": "openai",
      "value": {
        "api_key": "sk-proj-...",
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1"
      },
      "description": "OpenAI配置",
      "is_editable": true
    }
  ],
  "total": 1
}
```

### 获取单个配置项
- **Endpoint**: `GET /api/v1/admin/configs/{category}/{key}`
- **描述**: 获取单个配置项详情
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "获取配置成功",
  "data": {
    "category": "ai_api_keys",
    "key": "openai",
    "value": {
      "api_key": "sk-proj-...",
      "model": "gpt-4"
    },
    "description": "OpenAI配置"
  }
}
```

### 创建配置项
- **Endpoint**: `POST /api/v1/admin/configs`
- **描述**: 创建新的配置项
- **请求体**:
```json
{
  "category": "ai_api_keys",
  "key": "deepseek",
  "value": {
    "api_key": "sk-deepseek-...",
    "model": "deepseek-chat"
  },
  "description": "Deepseek配置",
  "is_editable": true
}
```
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "配置创建成功",
  "data": {
    "id": "uuid-config-123",
    "category": "ai_api_keys",
    "key": "deepseek"
  }
}
```

### 更新配置项
- **Endpoint**: `PUT /api/v1/admin/configs/{category}/{key}`
- **描述**: 更新指定配置项
- **请求体**:
```json
{
  "value": {
    "api_key": "sk-new-key-...",
    "model": "gpt-4-turbo"
  },
  "description": "更新后的OpenAI配置"
}
```
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "配置更新成功"
}
```

### 删除配置项
- **Endpoint**: `DELETE /api/v1/admin/configs/{category}/{key}`
- **描述**: 删除指定配置项
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "配置删除成功"
}
```

### 更新AI配置
- **Endpoint**: `POST /api/v1/admin/configs/ai`
- **描述**: 专用接口更新AI服务配置
- **请求体**:
```json
{
  "provider": "openai",
  "api_key": "sk-proj-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4"
}
```
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "OPENAI 配置更新成功"
}
```

### 更新业务配置
- **Endpoint**: `POST /api/v1/admin/configs/business`
- **描述**: 更新业务规则配置
- **请求体**:
```json
{
  "commission_rates": {
    "platform": 0.50,
    "lawyer": 0.30,
    "sales": 0.20
  },
  "risk_thresholds": {
    "insurance_threshold": 100000.0,
    "high_risk_threshold": 500000.0
  },
  "business_rules": {
    "max_cases_per_lawyer": 50,
    "auto_assignment_enabled": true
  }
}
```
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "业务配置更新成功"
}
```

### 更新支付配置
- **Endpoint**: `POST /api/v1/admin/configs/payment`
- **描述**: 更新支付服务配置
- **请求体**:
```json
{
  "wechat_pay": {
    "app_id": "wx1234567890",
    "mch_id": "1234567890",
    "api_key": "payment_api_key_here"
  },
  "alipay": {
    "app_id": "2021001234567890",
    "private_key": "alipay_private_key_here"
  }
}
```
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "支付配置更新成功"
}
```

### 初始化默认配置
- **Endpoint**: `POST /api/v1/admin/configs/initialize`
- **描述**: 初始化系统默认配置
- **成功响应 (200)**:
```json
{
  "success": true,
  "message": "默认配置初始化成功"
}
```

## **业务API (Business APIs)**

### **1. 案件管理 (Cases Management)**

- **Endpoint**: `GET /api/cases`
- **Description**: 查询案件列表（供律师、销售、机构、管理员使用，根据角色返回不同范围数据）。
- **Auth**: `JWT Token`
- **Query Parameters**:
  - `page` (int): 页码
  - `limit` (int): 每页数量
  - `sort_by` (string): 排序字段，例如 `created_at`, `-data_freshness_score` (负号表示降序)
  - `status` (string): 按生命周期状态筛选, e.g., `active`, `processing`, `expired`
  - `legal_status` (string): 按法律状态筛选, e.g., `valid`, `expiring_soon`
- **Success Response (200 OK)**:
  ```json
  {
    "total": 120,
    "items": [
      {
        "id": 1,
        "debtor_name": "李四",
        "total_debt_amount": "5500.00",
        "status": "active",
        "legal_status": "valid",
        "data_freshness_score": 95,
        "created_at": "2023-10-01T10:00:00Z"
      }
    ]
  }
  ```

--- 

--- 