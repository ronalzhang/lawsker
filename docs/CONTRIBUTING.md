# Lawsker贡献指南

## 🎯 欢迎贡献

感谢您对Lawsker项目的关注！我们欢迎各种形式的贡献，包括但不限于：

- 🐛 Bug报告和修复
- ✨ 新功能开发
- 📚 文档改进
- 🎨 UI/UX优化
- 🔧 性能优化
- 🧪 测试用例编写

## 📋 目录

- [开始之前](#开始之前)
- [开发环境搭建](#开发环境搭建)
- [贡献流程](#贡献流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request指南](#pull-request指南)
- [Issue指南](#issue指南)
- [代码审查](#代码审查)

## 🚀 开始之前

### 行为准则
请阅读并遵守我们的[行为准则](CODE_OF_CONDUCT.md)，确保为所有参与者创造一个友好、包容的环境。

### 技能要求
- **后端开发**: Python 3.11+, FastAPI, PostgreSQL, Redis
- **前端开发**: Vue.js 3, TypeScript, HTML/CSS
- **DevOps**: Docker, NGINX, Linux系统管理
- **测试**: pytest, Jest, E2E测试

### 联系方式
- **技术讨论**: GitHub Discussions
- **即时沟通**: 微信群/钉钉群
- **邮件联系**: dev-team@lawsker.com

## 🛠️ 开发环境搭建

### 1. Fork和克隆项目
```bash
# Fork项目到你的GitHub账户
# 然后克隆你的fork
git clone https://github.com/YOUR_USERNAME/lawsker.git
cd lawsker

# 添加上游仓库
git remote add upstream https://github.com/original-org/lawsker.git
```

### 2. 环境配置
```bash
# 安装Python依赖
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑.env.local文件
```

### 3. 数据库设置
```bash
# 启动PostgreSQL和Redis
docker-compose up -d postgres redis

# 运行数据库迁移
cd backend
python -m alembic upgrade head

# 加载测试数据
python scripts/load_test_data.py
```

### 4. 启动开发服务器
```bash
# 启动后端服务
cd backend
uvicorn app.main:app --reload --port 8000

# 启动前端服务
cd frontend
npm run dev
```

## 🔄 贡献流程

### 1. 选择Issue
- 查看[Issues列表](https://github.com/org/lawsker/issues)
- 选择标有`good first issue`或`help wanted`的Issue
- 在Issue中评论表明你要处理这个问题

### 2. 创建分支
```bash
# 同步最新代码
git checkout main
git pull upstream main

# 创建功能分支
git checkout -b feature/issue-123-add-user-profile
# 或者修复分支
git checkout -b fix/issue-456-login-bug
```

### 3. 开发和测试
```bash
# 进行开发工作
# ...

# 运行测试
cd backend
pytest tests/

cd ../frontend
npm run test

# 运行代码检查
npm run lint
black backend/
flake8 backend/
```

### 4. 提交代码
```bash
# 添加文件
git add .

# 提交代码（遵循提交规范）
git commit -m "feat: add user profile management

- Add user profile API endpoints
- Implement profile update functionality
- Add profile validation tests

Closes #123"
```

### 5. 推送和创建PR
```bash
# 推送到你的fork
git push origin feature/issue-123-add-user-profile

# 在GitHub上创建Pull Request
```

## 📝 代码规范

### Python代码规范
```python
# 使用类型注解
def calculate_fee(amount: float, rate: float) -> float:
    """计算服务费用"""
    return amount * rate

# 使用docstring
class UserService:
    """用户服务类
    
    提供用户相关的业务逻辑处理
    """
    
    def create_user(self, user_data: dict) -> User:
        """创建新用户
        
        Args:
            user_data: 用户数据字典
            
        Returns:
            创建的用户对象
            
        Raises:
            ValidationError: 数据验证失败
        """
        pass
```

### TypeScript代码规范
```typescript
// 使用接口定义类型
interface User {
  id: number
  name: string
  email: string
  createdAt: Date
}

// 使用函数注释
/**
 * 格式化用户显示名称
 * @param user 用户对象
 * @returns 格式化后的显示名称
 */
function formatUserName(user: User): string {
  return `${user.name} (${user.email})`
}

// 使用枚举
enum UserRole {
  USER = 'user',
  LAWYER = 'lawyer',
  ADMIN = 'admin'
}
```

### 代码格式化
```bash
# Python格式化
black backend/
isort backend/
flake8 backend/

# TypeScript格式化
npm run lint:fix
npm run format
```

## 📋 提交规范

### 提交消息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 示例
```bash
# 新功能
git commit -m "feat(auth): add OAuth2 login support

- Implement Google OAuth2 integration
- Add OAuth2 configuration settings
- Update login UI with OAuth2 button

Closes #234"

# Bug修复
git commit -m "fix(api): resolve user registration validation error

The email validation was incorrectly rejecting valid email addresses
with plus signs. Updated regex pattern to handle all valid email formats.

Fixes #456"

# 文档更新
git commit -m "docs: update API documentation for user endpoints

- Add missing parameter descriptions
- Update response examples
- Fix typos in authentication section"
```

## 🔍 Pull Request指南

### PR标题格式
```
[类型] 简短描述 (#Issue号)
```

### PR描述模板
```markdown
## 📝 变更描述
简要描述这个PR的目的和实现的功能。

## 🔗 相关Issue
Closes #123
Related to #456

## 📋 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 重大变更
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 🧪 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成
- [ ] 添加了新的测试用例

## 📸 截图（如适用）
如果是UI相关的变更，请提供截图。

## 📋 检查清单
- [ ] 代码遵循项目规范
- [ ] 自测通过
- [ ] 文档已更新
- [ ] 变更日志已更新
- [ ] 没有引入新的警告
```

### PR审查要求
- 至少需要1个维护者的审查
- 所有CI检查必须通过
- 代码覆盖率不能降低
- 必须解决所有审查意见

## 🐛 Issue指南

### Bug报告模板
```markdown
## 🐛 Bug描述
清晰简洁地描述bug是什么。

## 🔄 复现步骤
1. 进入 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 🎯 期望行为
清晰简洁地描述你期望发生什么。

## 📸 截图
如果适用，添加截图来帮助解释你的问题。

## 🖥️ 环境信息
- OS: [e.g. Ubuntu 20.04]
- Browser: [e.g. Chrome 91]
- Version: [e.g. v1.2.3]

## 📋 附加信息
添加任何其他关于问题的信息。
```

### 功能请求模板
```markdown
## 🚀 功能描述
清晰简洁地描述你想要的功能。

## 💡 动机
解释为什么这个功能对项目有用。

## 📋 详细描述
提供功能的详细描述，包括：
- 用户界面设计
- API接口设计
- 数据库变更
- 性能考虑

## 🎯 验收标准
- [ ] 标准1
- [ ] 标准2
- [ ] 标准3

## 📋 附加信息
添加任何其他信息，如截图、原型等。
```

## 👥 代码审查

### 审查者指南
1. **功能性**: 代码是否实现了预期功能？
2. **可读性**: 代码是否清晰易懂？
3. **性能**: 是否有性能问题？
4. **安全性**: 是否存在安全漏洞？
5. **测试**: 是否有足够的测试覆盖？

### 审查清单
- [ ] 代码逻辑正确
- [ ] 错误处理完善
- [ ] 性能考虑充分
- [ ] 安全性检查通过
- [ ] 测试覆盖充分
- [ ] 文档更新完整
- [ ] 代码风格一致

### 审查反馈示例
```markdown
## 总体评价
代码实现了预期功能，逻辑清晰。有几个小问题需要修改。

## 具体意见

### 🔧 必须修改
1. **安全问题** (第45行): SQL查询存在注入风险，请使用参数化查询
2. **性能问题** (第78行): 循环中的数据库查询会影响性能，建议批量查询

### 💡 建议改进
1. **代码风格** (第23行): 变量名建议更具描述性
2. **错误处理** (第56行): 建议添加更详细的错误信息

### ✅ 做得好的地方
1. 测试覆盖率很好
2. 文档更新及时
3. 代码结构清晰
```

## 🏆 贡献者认可

### 贡献者等级
- **新手贡献者**: 首次贡献
- **活跃贡献者**: 多次贡献
- **核心贡献者**: 长期活跃贡献
- **维护者**: 项目维护权限

### 认可方式
- GitHub贡献者页面展示
- 项目README中的贡献者列表
- 年度贡献者奖励
- 技术分享机会

## 📚 学习资源

### 技术文档
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Vue.js官方文档](https://vuejs.org/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)

### 项目相关
- [系统架构文档](./SYSTEM-ARCHITECTURE.md)
- [API接口文档](./API-DOCUMENTATION.md)
- [开发指南](./DEVELOPMENT-GUIDE.md)

## ❓ 常见问题

### Q: 如何选择合适的Issue？
A: 新贡献者建议从标有`good first issue`的Issue开始，这些通常比较简单且有详细说明。

### Q: 代码审查需要多长时间？
A: 通常在1-3个工作日内会有初步反馈，复杂的PR可能需要更长时间。

### Q: 如何处理合并冲突？
A: 
```bash
git checkout main
git pull upstream main
git checkout your-branch
git rebase main
# 解决冲突后
git push --force-with-lease origin your-branch
```

### Q: 测试失败怎么办？
A: 
1. 查看CI日志了解失败原因
2. 在本地运行相同的测试
3. 修复问题后重新提交
4. 如需帮助，在PR中@维护者

## 📞 获取帮助

### 联系方式
- **GitHub Discussions**: 技术讨论和问题
- **Issue评论**: 具体问题讨论
- **邮件**: dev-team@lawsker.com
- **微信群**: 扫描二维码加入

### 响应时间
- **Issue回复**: 1-2个工作日
- **PR审查**: 1-3个工作日
- **邮件回复**: 1个工作日
- **紧急问题**: 24小时内

---

**感谢您的贡献！** 🎉

每一个贡献都让Lawsker变得更好。无论是代码、文档、测试还是反馈，我们都非常感谢您的参与。

**文档版本**: v1.0
**最后更新**: 2024-01-30
**维护团队**: Lawsker开发团队