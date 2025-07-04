# Lawsker (律思客) - O2O专业服务平台

> **法律智慧，即刻送达** - AI驱动的灵活用工SaaS平台

## 🚀 项目概述

Lawsker (律思客) 是一个基于WorkBridge技术架构的O2O专业服务平台，以法律催收为首发场景，通过AI优化传统业务流程，实现高效的专业服务匹配和智能化资金分账。

### 核心特性

- 🤖 **AI驱动**: 智能文档生成、风险评估、任务分配
- 💰 **智能分账**: 30秒实时分账，多方收益透明化
- 🏢 **多租户架构**: SaaS在线 + 独立部署双模式
- 📱 **微信生态**: 深度集成企业微信和微信支付
- 🔒 **合规安全**: 严格的法律合规和数据安全保护
- 🌐 **Web3就绪**: 支持DID身份、加密货币支付、DAO治理

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI (Python 3.9+)
- **数据库**: PostgreSQL 14+
- **缓存**: Redis 6+
- **认证**: JWT Token
- **异步任务**: Celery + Redis
- **文件存储**: MinIO

### 前端
- **框架**: Vue.js 3 + TypeScript
- **构建工具**: Vite
- **UI框架**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts
- **样式**: SCSS + CSS Modules

### 开发工具
- **API文档**: FastAPI Swagger
- **代码规范**: ESLint + Prettier + Black
- **版本控制**: Git
- **容器化**: Docker + Docker Compose

## 📁 项目结构

```
lawsker/
├── backend/                 # 后端API服务
│   ├── app/                # 应用核心代码
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 后端测试
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端应用
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   └── package.json       # Node.js依赖
├── docs/                  # 项目文档
├── scripts/               # 部署脚本
├── docker-compose.yml     # 开发环境配置
└── README.md             # 项目说明
```

## 🚦 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 14+
- Redis 6+

### 开发环境搭建

1. **克隆项目**
```bash
git clone https://github.com/your-org/lawsker.git
cd lawsker
```

2. **后端环境**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **前端环境**
```bash
cd frontend
npm install
```

4. **数据库初始化**
```bash
# 启动PostgreSQL和Redis
docker-compose up -d postgres redis

# 运行数据库迁移
cd backend
alembic upgrade head
```

5. **启动服务**
```bash
# 后端API (终端1)
cd backend
uvicorn app.main:app --reload --port 8000

# 前端开发服务器 (终端2)
cd frontend
npm run dev
```

访问 http://localhost:3000 查看前端界面
访问 http://localhost:8000/docs 查看API文档

## 📖 文档

- [需求文档](./lawsker_Requirements.md)
- [数据库设计](./lawsker_数据库设计.md)
- [API文档](./lawsker_API文档.md)
- [项目计划](./lawsker完整项目计划.md)
- [业务流程图](./lawsker_flowchart.html)

## 🤝 开发规范

### 代码提交规范
```bash
git commit -m "feat: 添加案件管理功能"
git commit -m "fix: 修复分账计算逻辑"
git commit -m "docs: 更新API文档"
```

### 分支命名规范
- `feature/案件管理系统`
- `bugfix/修复支付分账`
- `hotfix/紧急修复登录问题`

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 团队

- **产品负责人**: [姓名]
- **技术负责人**: [姓名]
- **前端开发**: [姓名]
- **后端开发**: [姓名]

---

**Lawsker (律思客)** - Powered by WorkBridge Technology 