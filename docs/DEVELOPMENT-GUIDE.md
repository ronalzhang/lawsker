# Lawsker开发指南

## 📋 目录

- [开发环境搭建](#开发环境搭建)
- [项目结构](#项目结构)
- [开发规范](#开发规范)
- [Git工作流](#git工作流)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)

## 🛠️ 开发环境搭建

### 1. 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Git

### 2. 克隆项目
```bash
git clone https://github.com/your-org/lawsker.git
cd lawsker
```

### 3. 后端环境搭建
```bash
# 创建虚拟环境
python3.11 -m venv backend_env
source backend_env/bin/activate  # Linux/Mac
# backend_env\Scripts\activate  # Windows

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local 文件

# 运行数据库迁移
python -m alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 前端环境搭建

#### 用户端
```bash
cd frontend-vue
npm install
npm run dev
```

#### 管理后台
```bash
cd frontend-admin
npm install
npm run dev
```

## 📁 项目结构

```
lawsker/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心模块
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── migrations/         # 数据库迁移
│   ├── tests/             # 测试文件
│   └── requirements.txt   # Python依赖
├── frontend-vue/          # 用户端前端
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面
│   │   ├── stores/        # 状态管理
│   │   ├── api/           # API接口
│   │   └── utils/         # 工具函数
│   └── package.json
├── frontend-admin/        # 管理后台
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面
│   │   ├── stores/        # 状态管理
│   │   └── utils/         # 工具函数
│   └── package.json
├── docs/                  # 文档
├── scripts/               # 脚本文件
└── docker-compose.yml     # Docker配置
```

## 📝 开发规范

### 1. 代码风格

#### Python (后端)
- 使用 Black 格式化代码
- 使用 isort 排序导入
- 使用 flake8 检查代码质量
- 遵循 PEP 8 规范

```bash
# 格式化代码
black backend/
isort backend/
flake8 backend/
```

#### TypeScript (前端)
- 使用 ESLint + Prettier
- 遵循 Vue.js 官方风格指南
- 使用 TypeScript 严格模式

```bash
# 检查代码
npm run lint
npm run type-check

# 格式化代码
npm run format
```

### 2. 命名规范

#### 文件命名
- 组件文件: PascalCase (UserCard.vue)
- 页面文件: PascalCase (UserListView.vue)
- 工具文件: camelCase (formatUtils.ts)
- 常量文件: UPPER_CASE (API_CONSTANTS.ts)

#### 变量命名
- 变量和函数: camelCase
- 常量: UPPER_CASE
- 类名: PascalCase
- 接口: PascalCase (以I开头)

### 3. 注释规范
```python
# Python
def calculate_fee(amount: float, rate: float) -> float:
    """
    计算服务费用
    
    Args:
        amount: 基础金额
        rate: 费率
        
    Returns:
        计算后的费用
        
    Raises:
        ValueError: 当金额或费率为负数时
    """
    if amount < 0 or rate < 0:
        raise ValueError("金额和费率不能为负数")
    return amount * rate
```

```typescript
// TypeScript
/**
 * 格式化金额显示
 * @param amount 金额
 * @param currency 货币符号
 * @returns 格式化后的金额字符串
 */
function formatAmount(amount: number, currency = '¥'): string {
  return `${currency}${amount.toFixed(2)}`
}
```