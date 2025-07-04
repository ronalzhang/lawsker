# Lawsker (律思客) - 法律服务O2O平台需求文档 v2.0

## 🚀 **项目定位**

**Lawsker (律思客)**: 专注于国内法律服务的O2O平台，以债务催收为核心业务，通过AI技术优化传统法律服务流程。

**核心价值主张**: "法律智慧，即刻送达" - 让法律服务更高效、更便民、更专业。

---

## 💼 **核心业务模块**

### **主营业务：债务催收服务**
- **业务流程**：机构委托 → 律师接单 → AI辅助催收 → 分期回款 → 自动分账
- **核心价值**：专业律师资质 + AI效率提升 + 透明分账机制
- **目标客户**：银行、助贷机构、小额贷款公司

### **次要业务：律师函服务**
- **服务特色**：30元一键快发，AI生成 + 律师资质背书
- **技术实现**：客户下单付款 → AI生成律师函 → 短信/邮件发送 → 可定时发送
- **差异化优势**：无纸化、秒级到达、成本极低

---

## 🏗️ **系统架构设计**

### **双模式运营策略**
```
SaaS在线模式（中小企业）    +    私有化部署（大企业）
├── 零门槛快速接入                ├── 数据安全私有部署
├── 按量付费成本可控              ├── 深度定制个性化流程
├── 网络效应规模经济              ├── 高客单价高粘性
└── 收入：订阅+抽成+增值          └── 收入：授权+定制+维护
```

### **核心用户角色**
1. **平台管理员**：系统配置、用户管理、财务监控
2. **助贷机构**：委托方，上传债务数据，查看催收进度
3. **执业律师**：接单催收，使用AI工具，获得佣金
4. **业务销售**：开发客户，维护关系，获得提成
5. **债务人**：接收催收通知，进行还款

---

## 💰 **商业模式与分成机制**

### **资金流设计**
```
债务人还款 → 平台托管账户 → 智能分账系统 → 各方收益账户
├── 机构返还：50%（返还委托方）
├── 平台分成：32.5%（技术服务+运营成本）
├── 律师佣金：10%（资质授权+执行服务）
└── 销售佣金：7.5%（业务开发）
```

### **律师函服务定价**
- **标准律师函**：30元/份，AI生成+律师签名
- **加急服务**：50元/份，1小时内发送
- **定制服务**：100-300元/份，个性化内容

---

## 🤖 **AI技术应用**

### **AI催收文书生成**
- **催收函模板**：友好提醒、正式通知、法律威慑三种风格
- **个性化定制**：根据债务类型、金额、逾期时长自动调整
- **法条智能引用**：自动匹配相关法律条文
- **多轮催收策略**：15天、30天、60天递进式模板

### **AI律师函生成**
- **智能模板选择**：根据案件类型自动选择合适模板
- **动态内容填充**：自动填入当事人信息、法律依据
- **格式规范化**：确保符合法律文书标准格式
- **质量检查**：AI自动检查逻辑错误和格式问题

---

## 📱 **产品功能清单**

### **机构管理端**
- [ ] 债务数据批量导入
- [ ] 案件进度实时跟踪
- [ ] 分账明细透明查询
- [ ] 律师绩效评估
- [ ] 月度对账报告

### **律师工作台**
- [ ] 案件智能推荐分配
- [ ] AI催收文书生成
- [ ] 进度跟踪管理
- [ ] 收入统计分析
- [ ] 执业资质管理

### **销售管理台**
- [ ] 客户开发管理
- [ ] 业务数据上传
- [ ] 佣金收入跟踪
- [ ] 客户关系维护
- [ ] CRM集成工具

### **律师函服务**
- [ ] 在线下单支付
- [ ] AI文书生成
- [ ] 一键发送服务
- [ ] 定时发送功能
- [ ] 发送状态跟踪

---

## 🎯 **技术实现路径**

### **后端技术栈**
- **API框架**：FastAPI（Python，高性能）
- **数据库**：PostgreSQL（多租户支持）
- **缓存**：Redis（会话+配置缓存）
- **认证**：JWT（无状态认证）
- **AI服务**：OpenAI GPT-4（文书生成）
- **支付**：微信支付+支付宝（聚合支付）

### **前端技术栈**
- **框架**：Vue.js 3 + TypeScript
- **UI组件**：Element Plus
- **状态管理**：Pinia
- **构建工具**：Vite
- **图表**：ECharts

---

## 📊 **收入预测**

### **第一年收入目标**
- **催收业务**：处理5亿催收金额，平台分成1.625亿
- **律师函服务**：10万份×30元 = 300万
- **SaaS订阅**：200家机构×3999元/月×12月 = 960万
- **总营收目标**：1.655亿元

### **运营成本控制**
- **技术团队**：800万（10人核心团队）
- **运营支持**：300万（客服、法务、财务）
- **市场推广**：500万
- **办公租赁**：100万
- **总成本**：1700万
- **净利润**：1.485亿（净利率89.7%）

---

## 🚀 **发展规划**

### **Phase 1: 催收业务MVP（2个月）**
- 完善催收业务核心功能
- 接入首批10家试点机构
- 月处理案件1000件

### **Phase 2: 律师函服务上线（1个月）**
- 开发律师函生成系统
- 集成支付和发送功能
- 月处理律师函5000份

### **Phase 3: 规模化扩展（3个月）**
- 拓展至100家合作机构
- 优化AI算法和用户体验
- 月处理金额1亿元

### **Phase 4: 生态完善（6个月）**
- 开发更多法律服务产品
- 建设开放API生态
- 实现全国化布局

---

## 📋 **数据库设计**

### **核心数据表**

#### **用户管理**
```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE,
    real_name VARCHAR(50),
    user_role VARCHAR(50),
    department VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 律师资质表
CREATE TABLE lawyer_qualifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    license_number VARCHAR(50) UNIQUE,
    license_authority VARCHAR(100),
    practice_areas TEXT[],
    verification_status VARCHAR(20) DEFAULT 'pending',
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### **案件管理**
```sql
-- 案件表
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    case_number VARCHAR(50) UNIQUE,
    debtor_name VARCHAR(100),
    debtor_phone VARCHAR(20),
    debt_amount DECIMAL(12,2),
    overdue_days INTEGER,
    assigned_lawyer_id UUID REFERENCES users(id),
    assigned_sales_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 催收记录表
CREATE TABLE collection_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    action_type VARCHAR(50),
    content TEXT,
    response TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### **律师函服务**
```sql
-- 律师函订单表
CREATE TABLE lawyer_letter_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name VARCHAR(100),
    client_phone VARCHAR(20),
    target_name VARCHAR(100),
    letter_type VARCHAR(50),
    content_brief TEXT,
    ai_generated_content TEXT,
    lawyer_id UUID REFERENCES users(id),
    amount DECIMAL(8,2),
    status VARCHAR(20) DEFAULT 'pending',
    send_method VARCHAR(20),
    scheduled_send_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

**专注核心，稳步发展！** 🎯 