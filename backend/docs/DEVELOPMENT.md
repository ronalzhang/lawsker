# Lawsker Backend 开发文档

## 技术栈

### 核心框架
- **FastAPI 0.104.1**: 现代异步Web框架
- **Uvicorn**: ASGI服务器
- **Python 3.11+**: 编程语言

### 数据库
- **PostgreSQL**: 主数据库
- **SQLAlchemy 2.0**: ORM框架
- **Asyncpg**: 异步PostgreSQL驱动
- **Alembic**: 数据库迁移工具

### 认证和安全
- **Python-JOSE**: JWT处理
- **Passlib**: 密码哈希
- **Cryptography**: 加密算法

### 配置管理
- **Pydantic Settings**: 配置验证
- **Python-dotenv**: 环境变量管理

### 日志系统
- **Structlog 25.4.0**: 结构化日志

### 缓存
- **Redis**: 缓存和会话存储

### 文件存储
- **MinIO**: 对象存储
- **AIOFiles**: 异步文件处理

### AI集成
- **OpenAI**: AI服务集成
- **DeepSeek**: 国产AI模型

### 数据处理
- **Pandas**: 数据分析
- **OpenPyXL**: Excel文件处理

## 开发环境设置

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 数据库配置
```bash
# 创建PostgreSQL数据库
createdb lawsker

# 运行数据库迁移
alembic upgrade head

# 初始化测试数据
python scripts/init_test_data.py
```

### 3. 环境变量配置
创建 `.env` 文件：
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/lawsker
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
```

### 4. 启动开发服务器
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 项目结构

```
backend/
├── app/
│   ├── api/v1/           # API路由
│   ├── core/             # 核心配置
│   ├── models/           # 数据模型
│   ├── services/         # 业务逻辑
│   ├── utils/            # 工具函数
│   └── main.py           # 应用入口
├── alembic/              # 数据库迁移
├── scripts/              # 脚本工具
├── tests/                # 测试代码
├── docs/                 # 文档
└── requirements.txt      # 依赖列表
```

## 开发规范

### 代码风格
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查
- 使用 mypy 进行类型检查

### 数据库操作
- 使用 SQLAlchemy 2.0 异步语法
- 所有数据库操作必须包含异常处理
- 使用 Alembic 进行数据库迁移

### API开发
- 遵循 RESTful 设计原则
- 使用 Pydantic 进行数据验证
- 统一错误处理和响应格式

### 测试
- 使用 pytest 进行单元测试
- 使用 pytest-asyncio 进行异步测试
- 测试覆盖率目标：80%以上

## 最新更新记录

### 2024-01-XX - 统计功能开发
- 添加统计服务模块 (`app/services/statistics_service.py`)
- 新增统计数据模型 (`app/models/statistics.py`)
- 实现基于角色的仪表盘数据API
- 添加用户活动日志记录功能
- 创建测试数据初始化脚本

### 依赖更新
- 新增 `structlog==25.4.0` 用于结构化日志
- 新增 `asyncpg==0.30.0` 用于PostgreSQL异步连接
- 更新 `requirements.txt` 完整依赖列表

### 数据库变更
- 新增 `case_logs` 表用于案件操作日志
- 新增 `system_statistics` 表用于系统统计数据
- 新增 `user_activity_logs` 表用于用户活动记录
- 新增 `data_upload_records` 表用于数据上传记录
- 新增 `task_publish_records` 表用于任务发布记录

## 部署说明

### 生产环境部署
1. 使用 PM2 进行进程管理
2. 使用 Nginx 作为反向代理
3. PostgreSQL 作为生产数据库
4. Redis 用于缓存和会话

### 服务器配置
- 服务器IP: 156.227.235.192
- 应用目录: `/root/lawsker`
- 使用 PM2 管理应用进程

### 部署流程
1. 本地开发和测试
2. 提交代码到 GitHub
3. 服务器拉取最新代码
4. 重启 PM2 服务

```bash
# 服务器部署命令
cd /root/lawsker
git pull origin main
pm2 restart all
``` 