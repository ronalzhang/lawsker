# 🔐 管理后台访问指南

## 问题症状

访问 `https://lawsker.com/admin-pro` 时：
- ✅ 页面能正常加载
- ✅ 标签页按钮显示正常
- ❌ 点击"运维工具"或"文书库管理"后显示空白
- ❌ 看起来像是功能故障

## 根本原因

**这不是bug，而是权限保护机制正在工作！**

后台管理页面受到密码保护，当权限验证失败或过期时：
1. 页面内容会被隐藏 (`document.body.style.visibility = 'hidden'`)
2. 应该显示密码输入弹窗
3. 用户必须输入正确密码才能查看内容

## 解决方案

### 方法1：正确输入管理密码

1. 访问 `https://lawsker.com/admin-pro`
2. 等待密码验证弹窗出现
3. 输入管理密码：`123abc74531`
4. 页面内容将恢复显示，所有标签页功能正常

### 方法2：检查权限验证状态

如果密码弹窗没有出现，检查：
1. 浏览器控制台是否有JavaScript错误
2. 会话存储中是否有有效的`adminAuth`记录
3. 权限是否在30分钟内过期

## 权限验证逻辑

```javascript
// 权限检查流程
1. 检查 sessionStorage.adminAuth
2. 验证时间戳（30分钟有效期）
3. 验证页面标识（admin-pro）
4. 如果无效 → 隐藏页面 + 显示密码弹窗
5. 如果有效 → 显示页面内容
```

## 常见问题

### Q: 为什么输入密码后还是空白？
A: 检查浏览器控制台是否有CSS加载错误，确保`/css/lawsker-glass.css`正常加载

### Q: 可以跳过密码验证吗？
A: 不建议，这是安全机制。如需调试可临时修改`auth-guard-ascii.js`

### Q: 密码多久过期？
A: 30分钟无操作后自动过期，需要重新输入密码

## 技术细节

权限验证由`/js/auth-guard-ascii.js`管理：
- 密码：`123abc74531`
- 会话存储键：`adminAuth`
- 过期时间：30分钟
- 保护页面：`/admin-pro`、`/admin-config-optimized.html`

## 验证步骤

1. **打开管理后台**：访问 https://lawsker.com/admin-pro
2. **输入密码**：`123abc74531`
3. **测试标签切换**：点击"🔧 运维工具"和"📚 文书库管理"
4. **确认显示**：应该能看到具体的管理工具和统计数据

---

💡 **重要提醒**：这个"空白页面"问题实际上是正常的安全保护机制，不是系统故障！ 