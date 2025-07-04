# Lawsker AI文书生成与律师审核工作流 API文档

## 🎯 系统概述

Lawsker AI文书生成系统是平台的核心差异化功能，实现了"AI生成 + 律师审核"的完整工作流，支持两大业务场景：

1. **主业务**：催收案件律师函生成（与案件系统集成）
2. **次要业务**：独立律师函服务（30元快发服务）

## 🏗️ 技术架构

### AI双引擎架构
- **ChatGPT**：负责初稿生成，专业法律语言处理
- **Deepseek**：负责内容优化润色，提升专业性
- **智能重试**：API调用失败时的错误恢复机制

### 完整业务流程
```
用户发起需求 → AI智能生成 → 律师分配 → 审核修改 → 签名授权 → 发送执行
```

## 📊 数据模型

### 核心表结构

#### DocumentReviewTask (文档审核任务表)
```sql
- id: UUID (主键)
- task_number: String (任务编号，唯一)
- case_id: UUID (关联案件ID，可选)
- order_id: UUID (关联订单ID，可选)
- lawyer_id: UUID (分配律师ID)
- creator_id: UUID (创建者ID)
- document_type: String (文档类型)
- original_content: Text (AI生成的原始内容)
- current_content: Text (当前内容)
- final_content: Text (最终确认内容)
- status: Enum (审核状态)
- priority: Integer (优先级1-5)
- deadline: DateTime (截止时间)
- ai_metadata: JSON (AI生成元数据)
- generation_prompt: Text (生成提示词)
- ai_providers: JSON (使用的AI提供商)
```

#### DocumentReviewLog (文档审核日志表)
```sql
- id: UUID (主键)
- review_task_id: UUID (审核任务ID)
- reviewer_id: UUID (操作人ID)
- action: String (操作类型)
- old_status: Enum (原状态)
- new_status: Enum (新状态)
- comment: Text (操作说明)
- content_changes: JSON (内容变更记录)
```

#### LawyerWorkload (律师工作负荷表)
```sql
- id: UUID (主键)
- lawyer_id: UUID (律师ID，唯一)
- active_cases: Integer (活跃案件数)
- pending_reviews: Integer (待审核文档数)
- daily_capacity: Integer (日处理能力)
- max_concurrent_tasks: Integer (最大并发任务数)
- approval_rate: Integer (通过率百分比)
- client_satisfaction: Integer (客户满意度百分比)
- is_available: Boolean (是否可接新任务)
- current_workload_score: Integer (当前工作负荷评分)
```

### 状态流转
```
ReviewStatus枚举：
- pending (待审核)
- in_review (审核中)
- approved (已通过)
- rejected (已拒绝)
- modification_requested (要求修改)
- modified (已修改)
- authorized (已授权发送)
- sent (已发送)
- cancelled (已取消)
```

## 🚀 API接口详情

### 基础路由
所有AI相关接口的基础路径：`/api/v1/ai`

### 1. 文档生成接口

#### 1.1 催收律师函生成
```http
POST /api/v1/ai/documents/collection-letter
```

**请求体**：
```json
{
  "case_id": "uuid",
  "tone_style": "正式通知",  // 可选：友好提醒/正式通知/严厉警告
  "grace_period": 15,       // 宽限期天数
  "priority": 2             // 优先级1-5
}
```

**响应**：返回创建的`DocumentReviewTask`对象

#### 1.2 独立律师函生成
```http
POST /api/v1/ai/documents/independent-letter
```

**请求体**：
```json
{
  // 客户信息
  "client_name": "客户姓名",
  "client_phone": "客户电话",
  "client_email": "客户邮箱",
  "client_company": "客户公司",
  
  // 目标方信息
  "target_name": "对方姓名/公司名",
  "target_phone": "对方电话",
  "target_email": "对方邮箱",
  "target_address": "对方地址",
  
  // 律师函信息
  "letter_type": "律师函类型",
  "case_background": "案件背景",
  "legal_basis": "法律依据",
  "demands": ["具体要求1", "具体要求2"],
  "content_brief": "内容简述",
  "urgency": "普通",          // 普通/加急/紧急
  "priority": 2
}
```

#### 1.3 文档重新生成
```http
POST /api/v1/ai/documents/regenerate
```

**请求体**：
```json
{
  "original_content": "原始内容",
  "modification_requests": "修改要求",
  "document_type": "collection_letter"
}
```

### 2. 律师审核工作流接口

#### 2.1 律师接受任务
```http
POST /api/v1/ai/tasks/{task_id}/accept
```

**请求体**：
```json
{
  "notes": "接受任务的备注"
}
```

#### 2.2 审核通过
```http
POST /api/v1/ai/tasks/{task_id}/approve
```

**请求体**：
```json
{
  "approval_notes": "通过备注",
  "final_content": "最终确认内容（可选）"
}
```

#### 2.3 要求修改
```http
POST /api/v1/ai/tasks/{task_id}/modify
```

**请求体**：
```json
{
  "modification_requests": "修改要求",
  "current_content": "当前内容（可选）"
}
```

#### 2.4 授权发送
```http
POST /api/v1/ai/tasks/{task_id}/authorize
```

**请求体**：
```json
{
  "authorization_notes": "授权备注"
}
```

### 3. 任务管理接口

#### 3.1 获取待处理任务列表
```http
GET /api/v1/ai/tasks/pending?limit=20&offset=0
```

**响应**：返回`DocumentReviewTask`对象数组

#### 3.2 获取任务详情
```http
GET /api/v1/ai/tasks/{task_id}
```

**响应**：返回完整的`DocumentReviewTask`对象

#### 3.3 获取任务统计
```http
GET /api/v1/ai/statistics
```

**响应**：
```json
{
  "status_counts": {
    "pending": 5,
    "in_review": 3,
    "approved": 12,
    "authorized": 8,
    "sent": 25
  },
  "today_created": 8,
  "overdue": 2,
  "total": 53
}
```

#### 3.4 获取全部任务统计（管理员）
```http
GET /api/v1/ai/statistics/all
```

### 4. 工具接口

#### 4.1 获取文档类型列表
```http
GET /api/v1/ai/document-types
```

**响应**：
```json
{
  "document_types": [
    {
      "value": "collection_letter",
      "name": "催收律师函"
    },
    {
      "value": "demand_letter", 
      "name": "催告函"
    }
    // ...更多类型
  ]
}
```

#### 4.2 获取审核状态列表
```http
GET /api/v1/ai/review-statuses
```

## 🔧 智能律师分配算法

### 工作负荷评分算法
```python
def calculate_workload_score(lawyer, workload):
    # 基础评分：当前任务占比
    base_score = (workload.pending_reviews / workload.max_concurrent_tasks) * 100
    
    # 质量调整：通过率和满意度影响
    quality_bonus = (workload.approval_rate + workload.client_satisfaction) / 20
    
    # 最终评分（越低越适合分配）
    final_score = base_score - quality_bonus
    
    return max(0, int(final_score))
```

### 分配策略
1. **可用性检查**：只有`is_available=True`的律师参与分配
2. **容量检查**：`pending_reviews < max_concurrent_tasks`
3. **评分排序**：选择工作负荷评分最低的律师
4. **实时更新**：分配后立即更新工作负荷统计

## ⚡ 性能优化

### AI服务优化
- **连接池管理**：复用HTTP连接，减少建连开销
- **异步处理**：所有AI API调用均为异步
- **错误重试**：智能重试机制，Deepseek失败时使用原内容
- **超时控制**：60秒超时，避免长时间等待

### 数据库优化
- **索引覆盖**：关键查询字段均有索引支持
- **分页查询**：避免大数据量查询影响性能
- **异步事务**：使用SQLAlchemy异步模式
- **连接池**：数据库连接池管理

## 🔒 安全与权限

### 认证方式
- **JWT Token**：Bearer token认证
- **用户权限**：基于角色的访问控制

### 权限检查
- **任务访问**：只有分配的律师或创建者可以查看任务
- **操作权限**：只有指定律师可以执行审核操作
- **数据隔离**：多租户数据隔离

## 📝 使用示例

### 完整业务流程示例

#### 1. 创建催收律师函任务
```bash
curl -X POST "http://localhost:8000/api/v1/ai/documents/collection-letter" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "123e4567-e89b-12d3-a456-426614174000",
    "tone_style": "正式通知",
    "grace_period": 15,
    "priority": 3
  }'
```

#### 2. 律师接受任务
```bash
curl -X POST "http://localhost:8000/api/v1/ai/tasks/456e7890-e89b-12d3-a456-426614174001/accept" \
  -H "Authorization: Bearer LAWYER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "接受任务，开始审核"
  }'
```

#### 3. 要求修改
```bash
curl -X POST "http://localhost:8000/api/v1/ai/tasks/456e7890-e89b-12d3-a456-426614174001/modify" \
  -H "Authorization: Bearer LAWYER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "modification_requests": "请在第二段中增加相关法律条文引用，语气可以更严厉一些"
  }'
```

#### 4. 审核通过并授权
```bash
curl -X POST "http://localhost:8000/api/v1/ai/tasks/456e7890-e89b-12d3-a456-426614174001/approve" \
  -H "Authorization: Bearer LAWYER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_notes": "内容规范，法律条文引用准确，可以发送"
  }'

curl -X POST "http://localhost:8000/api/v1/ai/tasks/456e7890-e89b-12d3-a456-426614174001/authorize" \
  -H "Authorization: Bearer LAWYER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "authorization_notes": "授权发送"
  }'
```

## 🎯 30元律师函快发服务实现

基于此AI文书生成系统，我们已经具备了实现"30元一键快发律师函"的完整技术能力：

### 成本结构
- **AI生成成本**：< ¥1元（ChatGPT + Deepseek API调用）
- **律师审核成本**：¥8-12元（按15分钟计算）
- **发送成本**：¥2-5元（邮件/短信/快递）
- **平台运营成本**：¥3-5元
- **净利润**：¥10-15元

### 效率优势
- **生成时间**：15秒（相比人工2小时，提升480倍）
- **审核时间**：5-15分钟（相比传统30-60分钟）
- **总处理时间**：20分钟内完成（相比传统2-3天）

这个AI文书生成系统真正实现了Lawsker"法律智慧，即刻送达"的品牌承诺！ 