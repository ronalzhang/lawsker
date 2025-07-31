# 依赖管理系统

这个依赖管理系统提供了完整的Python依赖包管理、验证和诊断功能。

## 功能特性

### DependencyManager类
- ✅ Python虚拟环境创建和管理
- ✅ requirements.txt解析和依赖安装
- ✅ 关键依赖包验证
- ✅ 依赖更新和回滚机制
- ✅ 依赖冲突检测和解决

### DependencyValidator类
- ✅ 关键依赖包检查
- ✅ 依赖版本兼容性验证
- ✅ 依赖安装状态报告
- ✅ 依赖问题诊断工具
- ✅ 安全漏洞检查
- ✅ 包导入测试

## 使用方法

### 1. 编程接口使用

```python
from deployment.dependency_manager import DependencyManager
from deployment.dependency_validator import DependencyValidator

# 创建依赖管理器
manager = DependencyManager(
    requirements_file="requirements-prod.txt",
    venv_path="venv",
    project_root="."
)

# 创建虚拟环境
success = manager.create_virtual_environment()

# 安装依赖
if success:
    success = manager.install_dependencies()

# 验证依赖
verification_results = manager.verify_dependencies()

# 创建验证器进行详细检查
validator = DependencyValidator(manager)
report = validator.validate_all_dependencies()

# 诊断问题
diagnosis = validator.diagnose_dependency_issues()
```

### 2. 命令行工具使用

```bash
# 验证依赖（基本）
python scripts/validate_dependencies.py validate

# 验证依赖（详细）
python scripts/validate_dependencies.py validate --detailed

# 诊断问题
python scripts/validate_dependencies.py diagnose

# 检查单个包
python scripts/validate_dependencies.py check fastapi

# 生成安装报告
python scripts/validate_dependencies.py report

# 保存结果到文件
python scripts/validate_dependencies.py validate --output validation_report.json
```

### 3. 高级功能

```python
# 获取依赖详细信息
dep_info = manager.get_dependency_info()
for name, info in dep_info.items():
    print(f"{name}: {info.version} (critical: {info.is_critical})")

# 获取虚拟环境信息
venv_info = manager.get_virtual_environment_info()
print(f"Python: {venv_info.python_version}")
print(f"Pip: {venv_info.pip_version}")

# 检查单个包兼容性
check_result = validator.check_package_compatibility('fastapi')
print(f"兼容性: {check_result.compatibility_level}")

# 生成完整报告
report = validator.validate_all_dependencies()
validator.save_report_to_file(report, 'dependency_report.json')
```

## 关键依赖包

系统会特别关注以下关键依赖包：

- `fastapi`: Web框架
- `uvicorn`: ASGI服务器
- `sqlalchemy`: 数据库ORM
- `redis`: 缓存客户端
- `celery`: 任务队列
- `cryptography`: 加密库
- `prometheus-client`: 监控客户端
- `psycopg2-binary`: PostgreSQL客户端
- `pydantic`: 数据验证

## 错误处理

系统提供了完善的错误处理和恢复机制：

1. **自动备份**: 在安装/更新前自动创建备份
2. **回滚机制**: 安装失败时自动回滚到上一个版本
3. **冲突检测**: 检测已知的包冲突并提供解决建议
4. **安全检查**: 检测已知的安全漏洞
5. **导入测试**: 验证包是否可以正常导入

## 输出示例

### 验证报告示例
```
============================================================
依赖验证报告摘要
============================================================
时间: 2024-01-20T10:30:00
Python版本: 3.11.7
虚拟环境: /path/to/venv
总包数: 36
关键包数: 9
整体状态: healthy

验证结果统计:
  ✓ 成功: 34
  ⚠ 警告: 2
  ✗ 错误: 0

兼容性检查:
  ✓ 兼容: 35
  ✗ 不兼容: 1

建议:
  1. 依赖状态良好，建议定期检查更新
```

### 诊断结果示例
```
============================================================
依赖问题诊断结果
============================================================

Missing Packages:
  - some-package: 1.0.0 (critical: False)
    修复: pip install some-package==1.0.0

Version Conflicts:
  - fastapi: 0.103.0 != 0.104.1
    修复: pip install fastapi==0.104.1

修复建议:
  1. 安装缺失的包：pip install -r requirements.txt
  2. 解决版本冲突：更新到兼容版本
```

## 配置选项

### 环境变量
- `DEPENDENCY_BACKUP_ENABLED`: 启用/禁用自动备份（默认: true）
- `DEPENDENCY_STRICT_MODE`: 严格模式，警告也视为错误（默认: false）
- `DEPENDENCY_TIMEOUT`: 安装超时时间（默认: 600秒）

### 配置文件
可以通过配置文件自定义关键依赖包列表和冲突检测规则。

## 故障排除

### 常见问题

1. **虚拟环境创建失败**
   - 检查Python版本（需要3.8+）
   - 检查磁盘空间
   - 检查权限

2. **依赖安装失败**
   - 检查网络连接
   - 检查pip版本
   - 查看详细错误信息

3. **导入测试失败**
   - 检查包是否正确安装
   - 检查依赖关系
   - 查看Python路径

### 日志文件
系统会生成详细的日志文件：
- `dependency_validation.log`: 验证日志
- `deployment/backups/`: 备份文件

## 集成示例

在部署脚本中集成依赖管理：

```python
def deploy_with_dependency_management():
    manager = DependencyManager("requirements-prod.txt", "venv")
    validator = DependencyValidator(manager)
    
    # 1. 创建虚拟环境
    if not manager.create_virtual_environment():
        raise Exception("虚拟环境创建失败")
    
    # 2. 安装依赖
    if not manager.install_dependencies():
        raise Exception("依赖安装失败")
    
    # 3. 验证依赖
    report = validator.validate_all_dependencies()
    if report.overall_status == 'critical':
        raise Exception("依赖验证失败")
    
    # 4. 继续部署其他组件...
    print("依赖管理完成，继续部署...")
```

这个依赖管理系统为Lawsker系统的部署提供了可靠的依赖管理基础。