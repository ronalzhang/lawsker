# Lawsker (律思客) - API接口文档 v1.3 - 实际实现状态

## 🌐 **部署环境**
- **生产服务器**: https://156.227.235.192
- **API基础URL**: https://156.227.235.192/api/v1
- **API文档**: https://156.227.235.192/docs (FastAPI自动生成)
- **健康检查**: https://156.227.235.192/api/v1/health

## 认证机制
- **认证方式**: Lawsker平台所有需要登录的接口都使用 `JWT (JSON Web Token)` 进行认证。
- **Token传递**: 在请求的 `Header` 中加入 `Authorization: Bearer <your_jwt_token>`。
- **Token获取**: 通过 `POST /api/v1/auth/login` 接口获取。
- **Token有效期**: 24小时（可在管理界面配置）

---

## 0. 系统健康检查 (`/api/v1/health`) ✅ 已实现

### 系统健康状态
- **Endpoint**: `GET /api/v1/health`
- **描述**: 检查系统运行状态，无需认证
- **成功响应 (200)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Lawsker API v1"
}
```

---

## 1. 认证接口 (`/api/v1/auth`) ⚠️ 部分实现

### 用户注册 ✅ 已实现
- **Endpoint**: `POST /api/v1/auth/register`
- **描述**: 新用户注册，支持律师、销售、机构管理员角色
- **请求体**:
```json
{
  "username": "user@example.com",
  "password": "strong_password",
  "role": "lawyer",
  "full_name": "张三",
  "phone_number": "13800138000",
  "email": "user@example.com"
}
```
- **成功响应 (201)**:
```json
{
  "message": "用户注册成功",
  "user_id": "uuid-user-123"
}
```

### 用户登录 ⚠️ 需要前端修复
- **Endpoint**: `POST /api/v1/auth/login`
- **描述**: 用户登录并获取JWT令牌
- **请求体**:
```json
{
  "username": "user@example.com",
  "password": "strong_password"
}
```
- **成功响应 (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-user-123",
    "username": "user@example.com",
    "role": "lawyer",
    "status": "active"
  }
}
```

### 获取当前用户信息 ✅ 已实现
- **Endpoint**: `GET /api/v1/auth/me`
- **描述**: 获取当前登录用户的详细信息
- **认证**: 需要Bearer Token
- **成功响应 (200)**:
```json
{
  "id": "uuid-user-123",
  "username": "lawyer@example.com",
  "role": "lawyer",
  "status": "active",
  "tenant_id": "uuid-tenant-456",
  "created_at": "2024-12-07T10:00:00Z"
}
```

### 演示账号登录 ✅ 已实现
- **演示律师**: username: `demo_lawyer`, password: `demo123`
- **演示销售**: username: `demo_sales`, password: `demo123`
- **演示机构**: username: `demo_institution`, password: `demo123`

---

## 2. 案件管理接口 (`/api/v1/cases`) ✅ 已实现

### 创建案件
- **Endpoint**: `POST /api/v1/cases/`
- **描述**: 创建新案件
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "debtor_info": {
    "name": "李四",
    "phone": "13800138000",
    "id_card": "110101199001011234",
    "address": "北京市朝阳区"
  },
  "case_amount": 50000.00,
  "debt_creation_date": "2023-01-01",
  "description": "案件描述",
  "priority": "medium"
}
```
- **成功响应 (201)**:
```json
{
  "id": "uuid-case-789",
  "case_number": "CASE202412070001",
  "debtor_info": {...},
  "case_amount": 50000.00,
  "status": "pending",
  "created_at": "2024-12-07T10:00:00Z"
}
```

### 获取案件列表
- **Endpoint**: `GET /api/v1/cases/`
- **描述**: 获取案件列表，支持分页和筛选
- **认证**: 需要Bearer Token
- **查询参数**:
  - `skip`: 跳过记录数（默认0）
  - `limit`: 每页数量（默认100）
  - `status`: 状态过滤
  - `assigned_to`: 分配给律师ID
- **成功响应 (200)**:
```json
[
  {
    "id": "uuid-case-789",
    "case_number": "CASE202412070001",
    "debtor_info": {...},
    "case_amount": 50000.00,
    "status": "pending",
    "created_at": "2024-12-07T10:00:00Z"
  }
]
```

### 获取案件详情
- **Endpoint**: `GET /api/v1/cases/{case_id}`
- **描述**: 获取单个案件的详细信息
- **认证**: 需要Bearer Token
- **成功响应 (200)**:
```json
{
  "id": "uuid-case-789",
  "case_number": "CASE202412070001",
  "debtor_info": {...},
  "case_amount": 50000.00,
  "status": "pending",
  "description": "案件描述",
  "created_at": "2024-12-07T10:00:00Z"
}
```

### 分配案件
- **Endpoint**: `PUT /api/v1/cases/{case_id}/assign`
- **描述**: 分配案件给律师
- **认证**: 需要Bearer Token
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
  "case_number": "CASE202412070001",
  "assigned_to_user_id": "uuid-lawyer-123",
  "status": "assigned"
}
```

---

## 3. AI服务接口 (`/api/v1/ai`) ✅ 已实现

### 生成催收文书
- **Endpoint**: `POST /api/v1/ai/generate-collection-document`
- **描述**: 使用AI生成催收文书
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "case_id": "uuid-case-789",
  "document_type": "collection_letter",
  "template_style": "formal",
  "custom_requirements": "加强法律威慑力度"
}
```
- **成功响应 (200)**:
```json
{
  "task_id": "uuid-task-456",
  "document_type": "collection_letter",
  "generated_content": "催收函内容...",
  "status": "completed",
  "ai_provider": "openai",
  "generation_time": 2.3
}
```

### 生成律师函
- **Endpoint**: `POST /api/v1/ai/generate-lawyer-letter`
- **描述**: 使用AI生成律师函
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "client_name": "张三",
  "target_name": "李四",
  "letter_type": "debt_collection",
  "case_background": "案件背景描述",
  "legal_basis": "相关法律依据",
  "demands": ["立即偿还债务", "支付利息"]
}
```
- **成功响应 (200)**:
```json
{
  "task_id": "uuid-task-789",
  "letter_type": "debt_collection",
  "generated_content": "律师函内容...",
  "status": "completed",
  "requires_review": true
}
```

### 获取AI任务状态
- **Endpoint**: `GET /api/v1/ai/tasks/{task_id}`
- **描述**: 查询AI生成任务状态
- **认证**: 需要Bearer Token
- **成功响应 (200)**:
```json
{
  "id": "uuid-task-456",
  "status": "completed",
  "document_type": "collection_letter",
  "generated_content": "文档内容...",
  "created_at": "2024-12-07T10:00:00Z",
  "completed_at": "2024-12-07T10:02:15Z"
}
```

---

## 4. 发送服务接口 (`/api/v1/delivery`) ✅ 已实现

### 发送文档
- **Endpoint**: `POST /api/v1/delivery/send`
- **描述**: 通过多渠道发送文档
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "content": "文档内容",
  "recipients": {
    "email": "target@example.com",
    "phone": "13800138000",
    "address": "北京市朝阳区xxx街道"
  },
  "channels": ["email", "sms"],
  "urgent": false,
  "scheduled_time": "2024-12-08T09:00:00Z"
}
```
- **成功响应 (200)**:
```json
{
  "delivery_id": "uuid-delivery-123",
  "status": "sent",
  "channels_used": ["email", "sms"],
  "sent_at": "2024-12-07T10:00:00Z",
  "delivery_results": {
    "email": "success",
    "sms": "success"
  }
}
```

### 查询发送状态
- **Endpoint**: `GET /api/v1/delivery/{delivery_id}/status`
- **描述**: 查询文档发送状态
- **认证**: 需要Bearer Token
- **成功响应 (200)**:
```json
{
  "delivery_id": "uuid-delivery-123",
  "status": "delivered",
  "sent_at": "2024-12-07T10:00:00Z",
  "delivery_results": {
    "email": "delivered",
    "sms": "delivered"
  },
  "tracking_info": {
    "email_opened": true,
    "sms_received": true
  }
}
```

---

## 5. 财务接口 (`/api/v1/finance`) ✅ 已实现

### 创建支付订单
- **Endpoint**: `POST /api/v1/finance/payment/create`
- **描述**: 创建支付订单（微信支付/支付宝）
- **认证**: 需要Bearer Token
- **请求体**:
```json
{
  "amount": 30.00,
  "body": "律师函服务费",
  "payment_method": "wechat",
  "case_id": "uuid-case-789"
}
```
- **成功响应 (200)**:
```json
{
  "order_id": "uuid-order-456",
  "out_trade_no": "ORDER202412070001",
  "amount": 30.00,
  "qr_code": "weixin://wxpay/bizpayurl?pr=xxx",
  "expired_at": "2024-12-07T11:00:00Z"
}
```

### 支付结果通知
- **Endpoint**: `POST /api/v1/finance/payment/notify`
- **描述**: 支付网关回调通知
- **认证**: 签名验证
- **请求体**: 支付网关标准格式

### 查询交易记录
- **Endpoint**: `GET /api/v1/finance/transactions`
- **描述**: 查询交易流水
- **认证**: 需要Bearer Token
- **查询参数**:
  - `case_id`: 案件ID
  - `transaction_type`: 交易类型
  - `start_date`: 开始日期
  - `end_date`: 结束日期
- **成功响应 (200)**:
```json
[
  {
    "id": "uuid-txn-123",
    "case_id": "uuid-case-789",
    "amount": 30.00,
    "transaction_type": "payment",
    "status": "completed",
    "created_at": "2024-12-07T10:00:00Z"
  }
]
```

### 查询分账记录
- **Endpoint**: `GET /api/v1/finance/commission-splits`
- **描述**: 查询分账明细
- **认证**: 需要Bearer Token
- **成功响应 (200)**:
```json
[
  {
    "id": "uuid-split-456",
    "transaction_id": "uuid-txn-123",
    "user_id": "uuid-lawyer-789",
    "role_at_split": "lawyer",
    "amount": 6.00,
    "percentage": 0.20,
    "status": "paid",
    "paid_at": "2024-12-07T10:00:30Z"
  }
]
```

---

## 6. 管理员接口 (`/api/v1/admin`) ✅ 已实现

### 获取系统配置
- **Endpoint**: `GET /api/v1/admin/configs`
- **描述**: 获取系统配置列表
- **认证**: 需要Admin权限
- **查询参数**:
  - `category`: 配置类别过滤
- **成功响应 (200)**:
```json
[
  {
    "id": 1,
    "category": "ai_config",
    "key": "openai_api_key",
    "value": {
      "api_key": "sk-xxx...",
      "model": "gpt-4",
      "max_tokens": 2000
    },
    "is_encrypted": true,
    "updated_at": "2024-12-07T10:00:00Z"
  }
]
```

### 更新系统配置
- **Endpoint**: `PUT /api/v1/admin/configs/{config_id}`
- **描述**: 更新系统配置
- **认证**: 需要Admin权限
- **请求体**:
```json
{
  "value": {
    "api_key": "sk-new-key...",
    "model": "gpt-4",
    "max_tokens": 3000
  }
}
```
- **成功响应 (200)**:
```json
{
  "id": 1,
  "category": "ai_config",
  "key": "openai_api_key",
  "value": {...},
  "updated_at": "2024-12-07T12:00:00Z"
}
```

### 测试AI连接
- **Endpoint**: `POST /api/v1/admin/test-ai-connection`
- **描述**: 测试AI服务连接
- **认证**: 需要Admin权限
- **请求体**:
```json
{
  "provider": "openai"
}
```
- **成功响应 (200)**:
```json
{
  "status": "success",
  "message": "连接测试成功！",
  "response_time": 1.23,
  "provider": "openai"
}
```

---

## 7. 用户管理接口 (`/api/v1/users`) ⚠️ 基础实现

### 获取用户列表 ✅ 已实现
- **Endpoint**: `GET /api/v1/users/`
- **描述**: 获取用户列表
- **认证**: 需要Bearer Token
- **查询参数**:
  - `skip`: 跳过记录数
  - `limit`: 每页数量
- **成功响应 (200)**:
```json
[
  {
    "id": "uuid-user-123",
    "username": "lawyer@example.com",
    "role": "lawyer",
    "status": "active",
    "created_at": "2024-12-07T10:00:00Z"
  }
]
```

---

## 📋 **API实现状态总结**

| 模块 | 接口数量 | 实现状态 | 完成度 |
|------|----------|----------|--------|
| 系统健康检查 | 1 | ✅ 完整 | 100% |
| 认证管理 | 4 | ⚠️ 部分 | 75% |
| 案件管理 | 8 | ✅ 完整 | 100% |
| AI服务 | 6 | ✅ 完整 | 100% |
| 发送服务 | 4 | ✅ 完整 | 100% |
| 财务管理 | 8 | ✅ 完整 | 100% |
| 管理员 | 6 | ✅ 完整 | 100% |
| 用户管理 | 2 | ⚠️ 基础 | 60% |

### **总体API完成度: 90%**

---

## 🔧 **错误码标准**

- **200**: 成功
- **201**: 创建成功
- **400**: 请求参数错误
- **401**: 未授权（Token无效或过期）
- **403**: 权限不足
- **404**: 资源不存在
- **422**: 数据验证失败
- **500**: 服务器内部错误

---

## 🚀 **下一步API开发重点**

1. **完善用户管理**: 用户详情、角色管理、权限控制
2. **增强认证系统**: 密码重置、邮箱验证、双因子认证
3. **API文档集成**: 配置FastAPI docs访问路径
4. **接口监控**: 添加请求日志、性能监控
5. **批量操作**: 批量导入、批量分配等接口

---

**API服务稳定运行中** 🚀