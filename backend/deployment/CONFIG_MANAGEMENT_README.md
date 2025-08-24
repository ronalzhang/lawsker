# 配置管理系统文档

## 概述

配置管理系统是Lawsker服务器部署完善项目的核心组件，提供了完整的配置文件模板管理、环境变量管理、密钥安全存储、配置验证和部署自动化功能。

## 系统架构

```
配置管理系统
├── ConfigurationManager      # 配置文件模板管理
├── SecureConfigManager      # 安全密钥管理
├── ConfigTemplates         # 预定义配置模板
├── ConfigValidator         # 配置验证器
└── ConfigManagementCLI     # 命令行工具
```

## 核心组件

### 1. ConfigurationManager (configuration_manager.py)

负责配置文件模板的创建、渲染和部署管理。

**主要功能：**
- 配置模板创建和管理
- Jinja2模板渲染
- 环境变量验证
- 配置文件生成和部署
- 配置变更检测和同步

**使用示例：**
```python
from configuration_manager import ConfigurationManager

# 初始化配置管理器
config_manager = ConfigurationManager()

# 创建配置模板
config_manager.create_template(
    name="nginx_site",
    template_content=nginx_template,
    variables={"domain": "example.com"},
    target_path="/etc/nginx/sites-available/example.com"
)

# 生成配置文件
config_manager.generate_config_file(
    template_name="nginx_site",
    output_path="/etc/nginx/sites-available/example.com",
    variables={"domain": "example.com", "ssl_enabled": True}
)
```

### 2. SecureConfigManager (secure_config_manager.py)

提供安全的密钥和证书存储管理功能。

**主要功能：**
- 密钥安全存储和加密
- 访问权限控制和审计
- 密钥自动轮换
- SSL证书管理
- 安全合规检查

**使用示例：**
```python
from secure_config_manager import SecureConfigManager

# 初始化安全配置管理器
secure_manager = SecureConfigManager()

# 存储密钥
secure_manager.store_secret(
    name="database_password",
    value="MySecurePassword123!",
    secret_type="password",
    access_level="confidential",
    expires_days=90
)

# 检索密钥
password = secure_manager.retrieve_secret("database_password")

# 轮换密钥
secure_manager.rotate_secret("database_password")
```

### 3. ConfigTemplates (config_templates.py)

预定义的配置文件模板集合。

**包含的模板：**
- Nginx站点配置
- Nginx SSL配置
- 数据库配置
- 应用程序配置
- Systemd服务配置
- Prometheus监控配置
- Grafana配置
- Redis配置
- 环境变量文件

### 4. ConfigValidator (config_validator.py)

配置文件验证和语法检查工具。

**验证功能：**
- JSON/YAML语法验证
- Nginx配置语法验证
- 环境变量验证
- SSL证书验证
- 自定义验证规则

**使用示例：**
```python
from config_validator import ConfigValidator

validator = ConfigValidator()

# 验证JSON配置
result = validator.validate_json_syntax("config.json")
if result.is_valid:
    print("配置文件语法正确")
else:
    print(f"错误: {result.errors}")

# 验证环境变量
env_result = validator.validate_environment_variables(env_vars)
```

### 5. ConfigManagementCLI (config_management_cli.py)

命令行工具，提供便捷的配置管理操作接口。

## 安装和配置

### 依赖要求

```bash
pip install cryptography jinja2 pyyaml python-dateutil
```

### 系统要求

- Python 3.8+
- OpenSSL (用于证书验证)
- Nginx (用于配置验证，可选)

### 初始化

```python
# 创建配置管理器实例
from configuration_manager import ConfigurationManager
from secure_config_manager import SecureConfigManager
from config_templates import ConfigTemplates

config_manager = ConfigurationManager()
secure_manager = SecureConfigManager()
templates = ConfigTemplates(config_manager)

# 创建所有预定义模板
templates.create_all_templates()
```

## 使用指南

### 1. 设置配置模板

```bash
# 使用CLI工具设置模板
python config_management_cli.py setup-templates
```

### 2. 创建环境配置

创建环境配置文件 `production.json`：

```json
{
  "variables": {
    "app_name": "lawsker",
    "domain": "lawsker.com",
    "ssl_enabled": true,
    "backend_url": "http://127.0.0.1:8000"
  },
  "encrypted_variables": {},
  "config_files": [
    "/etc/nginx/sites-available/lawsker.com",
    "/opt/lawsker/config/app.conf"
  ],
  "validation_rules": {
    "app_name": {"required": true, "type": "str"},
    "domain": {"required": true, "pattern": "^[a-zA-Z0-9.-]+$"}
  }
}
```

```bash
# 创建环境
python config_management_cli.py create-env production production.json

# 部署环境
python config_management_cli.py deploy production
```

### 3. 密钥管理

```bash
# 存储密钥
python config_management_cli.py store-secret database_password "MySecurePassword123!" --type password --access-level confidential

# 检索密钥
python config_management_cli.py get-secret database_password

# 轮换密钥
python config_management_cli.py rotate-secret database_password

# 检查过期密钥
python config_management_cli.py check-expiring --days 30

# 检查需要轮换的密钥
python config_management_cli.py check-rotation
```

### 4. 安全合规检查

```bash
# 运行安全合规检查
python config_management_cli.py check-compliance
```

### 5. 配置验证

```bash
# 检测配置变更
python config_management_cli.py detect-changes /etc/nginx/sites-available/* /opt/lawsker/config/*

# 生成配置文件
python config_management_cli.py generate-config nginx_site /etc/nginx/sites-available/lawsker.com variables.json
```

## 安全特性

### 1. 密钥加密存储

- 使用Fernet对称加密算法
- 主密钥安全存储，权限控制为600
- 支持密钥分层访问控制

### 2. 访问控制和审计

- 基于用户和角色的访问控制
- 完整的操作审计日志
- 失败尝试跟踪和锁定机制

### 3. 密钥轮换

- 自动密钥轮换策略
- 密钥历史版本管理
- 轮换前自动备份

### 4. 合规检查

- 文件权限检查
- 密钥强度验证
- 过期密钥检测
- 轮换策略合规性

## 配置模板

### Nginx站点配置模板

支持以下功能：
- HTTP到HTTPS重定向
- SSL/TLS配置
- 安全头设置
- 反向代理配置
- 静态文件服务
- WebSocket支持
- Gzip压缩

### 应用程序配置模板

包含：
- 服务器配置
- 数据库连接
- Redis配置
- 安全设置
- 日志配置
- 监控设置
- 功能开关

### 数据库配置模板

支持：
- 连接池配置
- SSL连接设置
- 性能优化参数
- 日志配置

## 最佳实践

### 1. 密钥管理

- 使用强密码策略
- 定期轮换密钥
- 分级访问控制
- 定期安全审计

### 2. 配置管理

- 使用版本控制跟踪配置变更
- 环境隔离配置
- 配置验证自动化
- 部署前测试

### 3. 安全配置

- 最小权限原则
- 定期合规检查
- 审计日志监控
- 备份和恢复策略

## 故障排除

### 常见问题

1. **权限错误**
   ```bash
   # 检查文件权限
   ls -la /opt/lawsker/vault/
   # 修复权限
   chmod 700 /opt/lawsker/vault/
   ```

2. **模板渲染失败**
   ```bash
   # 检查模板语法
   python -c "from jinja2 import Template; Template('{{ variable }}').render(variable='test')"
   ```

3. **密钥检索失败**
   ```bash
   # 检查密钥是否存在
   python config_management_cli.py check-expiring --days 0
   ```

### 日志分析

```bash
# 查看审计日志
tail -f /var/log/lawsker/security_audit.log

# 查看应用日志
tail -f /var/log/lawsker/config_management.log
```

## 测试

运行集成测试：

```bash
python test_config_management.py
```

测试覆盖：
- 模板创建和渲染
- 密钥存储和检索
- 配置文件生成
- 验证功能
- 安全合规检查
- 环境部署
- 变更检测

## API参考

详细的API文档请参考各个模块的docstring文档。

## 贡献指南

1. 遵循PEP 8代码规范
2. 添加适当的类型注解
3. 编写完整的docstring文档
4. 添加单元测试
5. 更新相关文档

## 许可证

本项目采用MIT许可证。

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 完整的配置管理功能
- 安全密钥管理
- 配置验证和合规检查
- CLI工具和集成测试