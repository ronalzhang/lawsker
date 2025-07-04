# WorkBridge - API接口文档 v1.0

## 认证机制
- **认证方式**: 所有需要登录的接口都使用 `JWT (JSON Web Token)` 进行认证。
- **Token传递**: 在请求的 `Header` 中加入 `Authorization: Bearer <your_jwt_token>`。
- **Token获取**: 通过 `POST /api/auth/login` 接口获取。

---

## 1. 公开接口 (`/api/public`)

### 注册
- **Endpoint**: `POST /api/public/register`
- **描述**: 新用户注册
- **请求体**:
```json
{
  "email": "user@example.com",
  "password": "strong_password",
  "role": "lawyer" // 'lawyer', 'sales', or 'institution_admin'
}
```
- **成功响应 (201)**:
```json
{
  "message": "Registration successful, please check your email for verification."
}
```

### 登录
- **Endpoint**: `POST /api/public/login`
- **描述**: 用户登录并获取JWT
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
  "token_type": "bearer"
}
```

## 2. 用户接口 (`/api/user`)

### 获取当前用户信息
- **Endpoint**: `GET /api/user/me`
- **描述**: 获取当前登录用户的详细信息
- **成功响应 (200)**:
```json
{
  "id": "uuid-user-123",
  "email": "lawyer@example.com",
  "role": "lawyer",
  "profile": {
    "full_name": "张三",
    "verification_status": "VERIFIED"
  }
}
```

### 更新用户信息
- **Endpoint**: `PUT /api/user/profile`
- **描述**: 更新用户的个人资料
- **请求体**:
```json
{
  "full_name": "张三丰",
  "qualification_details": {
    "license_id": "123456789"
  }
}
```
- **成功响应 (200)**:
```json
{
  "message": "Profile updated successfully."
}
```

## 3. 律师专用接口 (`/api/lawyer`)

### 获取案件列表
- **Endpoint**: `GET /api/lawyer/cases`
- **描述**: 获取分配给当前律师的案件列表，支持分页和筛选
- **查询参数**:
  - `status`: `pending`, `in_progress`, `completed`
  - `page`: `1`
  - `limit`: `10`
- **成功响应 (200)**:
```json
{
  "total": 25,
  "cases": [
    {
      "id": "uuid-case-456",
      "debtor_name": "李四",
      "case_amount": 100000.00,
      "status": "in_progress",
      "created_at": "2023-10-27T10:00:00Z"
    }
  ]
}
```

### 获取案件详情
- **Endpoint**: `GET /api/lawyer/cases/{caseId}`
- **描述**: 获取单个案件的详细信息
- **成功响应 (200)**:
```json
{
  "id": "uuid-case-456",
  "debtor_info": { "name": "李四", "phone": "13800138000" },
  "case_amount": 100000.00,
  "status": "in_progress",
  "logs": [
    { "action": "案件创建", "timestamp": "..." },
    { "action": "分配给律师 张三", "timestamp": "..." }
  ]
}
```

### 使用AI工具
- **Endpoint**: `POST /api/lawyer/ai/generate-document`
- **描述**: 请求AI生成法律文书
- **请求体**:
```json
{
  "case_id": "uuid-case-456",
  "template_id": "lawyer_letter_template_1",
  "custom_params": {
    "due_date": "2023-11-10"
  }
}
```
- **成功响应 (200)**:
```json
{
  "document_url": "https://storage.workbridge.com/docs/generated_doc_xyz.pdf"
}
```

### 获取AI风险评估
- **Endpoint**: `GET /api/lawyer/cases/{caseId}/risk-assessment`
- **描述**: 获取指定案件的AI风险评估结果
- **成功响应 (200)**:
```json
{
  "case_id": "uuid-case-456",
  "risk_score": 85, // 0-100分，分越高风险越高
  "assessment_details": "该案件关联的债务人历史信用良好，但涉案金额较大，建议优先采用协商方式..."
}
```

## 4. 销售专用接口 (`/api/sales`)

### 上传业务/案件
- **Endpoint**: `POST /api/sales/cases`
- **描述**: 销售人员批量或单个上传案件
- **请求体**:
```json
[
  {
    "client_id": "uuid-client-789",
    "debtor_info": { "name": "王五", "id_card": "..." },
    "case_amount": 50000.00
  }
]
```
- **成功响应 (201)**:
```json
{
  "message": "1 case(s) created successfully.",
  "created_case_ids": ["uuid-new-case-1"]
}
```

### 获取客户列表
- **Endpoint**: `GET /api/sales/clients`
- **描述**: 获取当前销售名下的客户列表
- **成功响应 (200)**:
```json
{
  "total": 10,
  "clients": [
    {
      "id": "uuid-client-789",
      "name": "某某消费金融公司",
      "total_case_volume": 500000.00
    }
  ]
}
```

## 5. 机构管理员接口 (`/api/institution`)

### 获取业务总览
- **Endpoint**: `GET /api/institution/dashboard`
- **描述**: 获取机构的业务数据总览
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
- **描述**: 查看机构的资金分账明细
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

## 7. 平台管理员接口 (`/api/admin`)

### 为租户生成API Key
- **Endpoint**: `POST /api/admin/tenants/{tenantId}/api-keys`
- **描述**: 为指定租户生成一个新的API密钥，用于开放平台调用
- **成功响应 (200)**:
```json
{
  "message": "API Key generated successfully. Please store it securely, it will not be shown again.",
  "api_key": "wbx_sk_xxxxxxxxxxxxxxxxxxxx" // "wbx_sk_" is the prefix
}
```

### 配置分成比例
- **Endpoint**: `PUT /api/admin/configs/commission`
- **描述**: 修改平台或某个租户的分成比例
- **请求体**:
```json
{
  "tenant_id": "uuid-tenant-abc", // 可选，不填则为全局配置
  "rates": {
    "platform": 0.35,
    "lawyer": 0.10, // 基于总额
    "sales": 0.05 // 基于总额
  }
}
```
- **成功响应 (200)**:
```json
{
  "message": "Commission rates updated successfully."
}
```

--- 