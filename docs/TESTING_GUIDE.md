# Lawsker测试指南

## 📋 目录

- [测试概述](#测试概述)
- [测试环境搭建](#测试环境搭建)
- [单元测试](#单元测试)
- [集成测试](#集成测试)
- [端到端测试](#端到端测试)
- [性能测试](#性能测试)
- [安全测试](#安全测试)
- [测试覆盖率](#测试覆盖率)
- [测试最佳实践](#测试最佳实践)

## 🎯 测试概述

### 测试金字塔
```
    /\
   /  \     E2E Tests (少量)
  /____\    
 /      \   Integration Tests (适量)
/__________\ Unit Tests (大量)
```

### 测试类型
- **单元测试**: 测试单个函数或类
- **集成测试**: 测试模块间的交互
- **端到端测试**: 测试完整的用户流程
- **性能测试**: 测试系统性能和负载
- **安全测试**: 测试安全漏洞和威胁

### 测试原则
- **快速**: 测试应该快速执行
- **独立**: 测试之间不应相互依赖
- **可重复**: 测试结果应该一致
- **自验证**: 测试应该自动判断成功或失败
- **及时**: 测试应该及时编写

## 🛠️ 测试环境搭建

### 后端测试环境
```bash
# 安装测试依赖
cd backend
pip install -r requirements-test.txt

# 配置测试数据库
export DATABASE_URL="postgresql://test_user:test_pass@localhost/lawsker_test"

# 运行数据库迁移
python -m alembic upgrade head

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_user_service.py

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 前端测试环境
```bash
# 安装测试依赖
cd frontend
npm install

# 运行单元测试
npm run test:unit

# 运行E2E测试
npm run test:e2e

# 运行测试并监听文件变化
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

### Docker测试环境
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-db:
    image: postgres:14
    environment:
      POSTGRES_DB: lawsker_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"
  
  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
```

## 🧪 单元测试

### 后端单元测试 (pytest)

#### 测试结构
```python
# tests/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate

class TestUserService:
    """用户服务测试类"""
    
    @pytest.fixture
    def user_service(self):
        """用户服务实例"""
        return UserService()
    
    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
    
    def test_create_user_success(self, user_service, sample_user_data):
        """测试成功创建用户"""
        # Arrange
        user_create = UserCreate(**sample_user_data)
        
        # Act
        with patch.object(user_service, 'db') as mock_db:
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            result = user_service.create_user(user_create)
        
        # Assert
        assert result.email == sample_user_data["email"]
        assert result.full_name == sample_user_data["full_name"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """测试创建重复邮箱用户"""
        # Arrange
        user_create = UserCreate(**sample_user_data)
        
        # Act & Assert
        with patch.object(user_service, 'get_user_by_email') as mock_get:
            mock_get.return_value = User(email=sample_user_data["email"])
            
            with pytest.raises(ValueError, match="邮箱已存在"):
                user_service.create_user(user_create)
    
    @pytest.mark.parametrize("email,expected", [
        ("valid@example.com", True),
        ("invalid-email", False),
        ("", False),
        (None, False)
    ])
    def test_validate_email(self, user_service, email, expected):
        """测试邮箱验证"""
        result = user_service.validate_email(email)
        assert result == expected
```

#### 测试配置
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "postgresql://test_user:test_pass@localhost/lawsker_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db():
    """数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    """测试客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
```

### 前端单元测试 (Jest + Vue Test Utils)

#### 组件测试
```typescript
// tests/unit/UserCard.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import UserCard from '@/components/UserCard.vue'

describe('UserCard.vue', () => {
  const mockUser = {
    id: 1,
    name: 'Test User',
    email: 'test@example.com',
    avatar: 'https://example.com/avatar.jpg'
  }

  it('renders user information correctly', () => {
    const wrapper = mount(UserCard, {
      props: { user: mockUser }
    })

    expect(wrapper.find('.user-name').text()).toBe(mockUser.name)
    expect(wrapper.find('.user-email').text()).toBe(mockUser.email)
    expect(wrapper.find('img').attributes('src')).toBe(mockUser.avatar)
  })

  it('emits edit event when edit button is clicked', async () => {
    const wrapper = mount(UserCard, {
      props: { user: mockUser }
    })

    await wrapper.find('.edit-button').trigger('click')
    
    expect(wrapper.emitted('edit')).toBeTruthy()
    expect(wrapper.emitted('edit')[0]).toEqual([mockUser.id])
  })

  it('shows placeholder when no avatar provided', () => {
    const userWithoutAvatar = { ...mockUser, avatar: null }
    const wrapper = mount(UserCard, {
      props: { user: userWithoutAvatar }
    })

    expect(wrapper.find('.avatar-placeholder').exists()).toBe(true)
  })
})
```

#### 服务测试
```typescript
// tests/unit/userService.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { userService } from '@/services/userService'
import { http } from '@/utils/http'

vi.mock('@/utils/http')

describe('userService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch user list successfully', async () => {
    const mockUsers = [
      { id: 1, name: 'User 1', email: 'user1@example.com' },
      { id: 2, name: 'User 2', email: 'user2@example.com' }
    ]

    vi.mocked(http.get).mockResolvedValue({
      data: { data: mockUsers }
    })

    const result = await userService.getUserList()

    expect(http.get).toHaveBeenCalledWith('/api/v1/users')
    expect(result).toEqual(mockUsers)
  })

  it('should handle API error gracefully', async () => {
    vi.mocked(http.get).mockRejectedValue(new Error('Network error'))

    await expect(userService.getUserList()).rejects.toThrow('Network error')
  })
})
```

## 🔗 集成测试

### API集成测试
```python
# tests/integration/test_user_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestUserAPI:
    """用户API集成测试"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_create_user_integration(self, client):
        """测试用户创建API"""
        user_data = {
            "email": "integration@example.com",
            "password": "password123",
            "full_name": "Integration Test User"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "password" not in data  # 密码不应返回
    
    def test_user_login_flow(self, client):
        """测试用户登录流程"""
        # 1. 创建用户
        user_data = {
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login Test User"
        }
        client.post("/api/v1/users", json=user_data)
        
        # 2. 登录
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        
        # 3. 使用token访问受保护的端点
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["email"] == user_data["email"]
```

### 数据库集成测试
```python
# tests/integration/test_database.py
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.case import Case
from app.services.case_service import CaseService

class TestDatabaseIntegration:
    """数据库集成测试"""
    
    def test_user_case_relationship(self, db: Session):
        """测试用户和案件的关系"""
        # 创建用户
        user = User(
            email="db_test@example.com",
            hashed_password="hashed_password",
            full_name="DB Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建案件
        case = Case(
            title="测试案件",
            description="这是一个测试案件",
            user_id=user.id,
            status="pending"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        
        # 验证关系
        assert case.user_id == user.id
        assert len(user.cases) == 1
        assert user.cases[0].title == "测试案件"
    
    def test_case_service_with_database(self, db: Session):
        """测试案件服务与数据库的集成"""
        case_service = CaseService(db)
        
        # 创建用户
        user = User(
            email="service_test@example.com",
            hashed_password="hashed_password",
            full_name="Service Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 使用服务创建案件
        case_data = {
            "title": "服务测试案件",
            "description": "通过服务创建的案件",
            "category": "民事纠纷"
        }
        
        case = case_service.create_case(user.id, case_data)
        
        # 验证案件创建
        assert case.title == case_data["title"]
        assert case.user_id == user.id
        assert case.status == "pending"
        
        # 验证数据库中的数据
        db_case = db.query(Case).filter(Case.id == case.id).first()
        assert db_case is not None
        assert db_case.title == case_data["title"]
```

## 🌐 端到端测试

### Playwright E2E测试
```typescript
// tests/e2e/user-registration.spec.ts
import { test, expect } from '@playwright/test'

test.describe('用户注册流程', () => {
  test('完整的用户注册流程', async ({ page }) => {
    // 访问注册页面
    await page.goto('/register')
    
    // 填写注册表单
    await page.fill('[data-testid="email-input"]', 'e2e@example.com')
    await page.fill('[data-testid="password-input"]', 'password123')
    await page.fill('[data-testid="confirm-password-input"]', 'password123')
    await page.fill('[data-testid="full-name-input"]', 'E2E Test User')
    
    // 提交表单
    await page.click('[data-testid="register-button"]')
    
    // 验证注册成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="success-message"]')).toContainText('注册成功')
    
    // 验证跳转到登录页面
    await expect(page).toHaveURL('/login')
  })
  
  test('注册表单验证', async ({ page }) => {
    await page.goto('/register')
    
    // 提交空表单
    await page.click('[data-testid="register-button"]')
    
    // 验证错误消息
    await expect(page.locator('[data-testid="email-error"]')).toContainText('邮箱不能为空')
    await expect(page.locator('[data-testid="password-error"]')).toContainText('密码不能为空')
    
    // 填写无效邮箱
    await page.fill('[data-testid="email-input"]', 'invalid-email')
    await page.click('[data-testid="register-button"]')
    
    await expect(page.locator('[data-testid="email-error"]')).toContainText('邮箱格式不正确')
  })
})
```

### 用户流程测试
```typescript
// tests/e2e/case-management.spec.ts
import { test, expect } from '@playwright/test'

test.describe('案件管理流程', () => {
  test.beforeEach(async ({ page }) => {
    // 登录用户
    await page.goto('/login')
    await page.fill('[data-testid="email-input"]', 'test@example.com')
    await page.fill('[data-testid="password-input"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/dashboard')
  })
  
  test('创建和管理案件', async ({ page }) => {
    // 进入案件创建页面
    await page.click('[data-testid="create-case-button"]')
    await expect(page).toHaveURL('/cases/create')
    
    // 填写案件信息
    await page.fill('[data-testid="case-title"]', '测试案件标题')
    await page.fill('[data-testid="case-description"]', '这是一个测试案件的详细描述')
    await page.selectOption('[data-testid="case-category"]', '民事纠纷')
    
    // 上传文件
    await page.setInputFiles('[data-testid="file-upload"]', 'tests/fixtures/test-document.pdf')
    
    // 提交案件
    await page.click('[data-testid="submit-case-button"]')
    
    // 验证案件创建成功
    await expect(page.locator('[data-testid="success-notification"]')).toBeVisible()
    await expect(page).toHaveURL('/cases')
    
    // 验证案件出现在列表中
    await expect(page.locator('[data-testid="case-list"]')).toContainText('测试案件标题')
    
    // 查看案件详情
    await page.click('[data-testid="case-item"]:first-child')
    await expect(page.locator('[data-testid="case-title"]')).toContainText('测试案件标题')
    await expect(page.locator('[data-testid="case-status"]')).toContainText('待处理')
  })
})
```

## ⚡ 性能测试

### 负载测试 (Locust)
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """用户开始时的操作"""
        # 登录
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test@example.com",
            "password": "password123"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(3)
    def view_dashboard(self):
        """查看仪表盘"""
        self.client.get("/api/v1/dashboard")
    
    @task(2)
    def list_cases(self):
        """查看案件列表"""
        self.client.get("/api/v1/cases")
    
    @task(1)
    def create_case(self):
        """创建案件"""
        self.client.post("/api/v1/cases", json={
            "title": "性能测试案件",
            "description": "这是一个性能测试案件",
            "category": "民事纠纷"
        })
    
    @task(1)
    def view_profile(self):
        """查看个人资料"""
        self.client.get("/api/v1/users/me")
```

### 数据库性能测试
```python
# tests/performance/test_database_performance.py
import pytest
import time
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.case import Case

class TestDatabasePerformance:
    """数据库性能测试"""
    
    def test_bulk_user_creation(self, db: Session):
        """测试批量用户创建性能"""
        start_time = time.time()
        
        users = []
        for i in range(1000):
            user = User(
                email=f"perf_test_{i}@example.com",
                hashed_password="hashed_password",
                full_name=f"Performance Test User {i}"
            )
            users.append(user)
        
        db.bulk_save_objects(users)
        db.commit()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 断言执行时间小于5秒
        assert execution_time < 5.0, f"批量创建1000个用户耗时 {execution_time:.2f} 秒，超过预期"
    
    def test_complex_query_performance(self, db: Session):
        """测试复杂查询性能"""
        # 准备测试数据
        self.setup_performance_data(db)
        
        start_time = time.time()
        
        # 执行复杂查询
        result = db.query(Case).join(User).filter(
            User.email.like('%test%'),
            Case.status == 'pending'
        ).limit(100).all()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 断言查询时间小于1秒
        assert execution_time < 1.0, f"复杂查询耗时 {execution_time:.2f} 秒，超过预期"
        assert len(result) > 0, "查询结果不能为空"
```

## 🔒 安全测试

### API安全测试
```python
# tests/security/test_api_security.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestAPISecurity:
    """API安全测试"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_sql_injection_protection(self, client):
        """测试SQL注入防护"""
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.get(f"/api/v1/users?search={malicious_input}")
        
        # 应该返回正常响应，而不是服务器错误
        assert response.status_code in [200, 400]
        
        # 验证数据库表仍然存在
        response = client.get("/api/v1/users")
        assert response.status_code == 200
    
    def test_xss_protection(self, client):
        """测试XSS防护"""
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post("/api/v1/cases", json={
            "title": xss_payload,
            "description": "正常描述"
        })
        
        if response.status_code == 201:
            case_id = response.json()["id"]
            response = client.get(f"/api/v1/cases/{case_id}")
            
            # 验证脚本被转义或过滤
            assert "<script>" not in response.text
    
    def test_authentication_required(self, client):
        """测试认证要求"""
        protected_endpoints = [
            "/api/v1/users/me",
            "/api/v1/cases",
            "/api/v1/dashboard"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"端点 {endpoint} 应该要求认证"
    
    def test_rate_limiting(self, client):
        """测试限流保护"""
        # 快速发送多个请求
        responses = []
        for _ in range(100):
            response = client.post("/api/v1/auth/login", json={
                "username": "test@example.com",
                "password": "wrong_password"
            })
            responses.append(response.status_code)
        
        # 应该有一些请求被限流
        assert 429 in responses, "应该触发限流保护"
```

### 前端安全测试
```typescript
// tests/security/xss.spec.ts
import { test, expect } from '@playwright/test'

test.describe('XSS防护测试', () => {
  test('输入框XSS防护', async ({ page }) => {
    await page.goto('/cases/create')
    
    const xssPayload = '<img src=x onerror=alert("XSS")>'
    
    // 在标题输入框中输入XSS载荷
    await page.fill('[data-testid="case-title"]', xssPayload)
    await page.fill('[data-testid="case-description"]', '正常描述')
    await page.click('[data-testid="submit-case-button"]')
    
    // 验证没有执行恶意脚本
    const alerts = []
    page.on('dialog', dialog => {
      alerts.push(dialog.message())
      dialog.dismiss()
    })
    
    await page.waitForTimeout(1000)
    expect(alerts).toHaveLength(0)
    
    // 验证内容被正确转义
    await page.goto('/cases')
    const caseTitle = await page.locator('[data-testid="case-title"]').first().textContent()
    expect(caseTitle).not.toContain('<img')
  })
})
```

## 📊 测试覆盖率

### 覆盖率配置
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    security: marks tests as security tests
```

### 覆盖率报告
```bash
# 生成覆盖率报告
pytest --cov=app --cov-report=html --cov-report=term

# 查看详细报告
open htmlcov/index.html

# 检查覆盖率是否达标
pytest --cov=app --cov-fail-under=85
```

### 覆盖率分析脚本
```python
# scripts/analyze_coverage.py
import json
import sys
from pathlib import Path

def analyze_coverage():
    """分析测试覆盖率"""
    coverage_file = Path("coverage.json")
    
    if not coverage_file.exists():
        print("覆盖率文件不存在，请先运行测试")
        return False
    
    with open(coverage_file) as f:
        data = json.load(f)
    
    total_coverage = data["totals"]["percent_covered"]
    
    print(f"总体覆盖率: {total_coverage:.2f}%")
    
    # 分析各模块覆盖率
    low_coverage_files = []
    for filename, file_data in data["files"].items():
        coverage = file_data["summary"]["percent_covered"]
        if coverage < 80:
            low_coverage_files.append((filename, coverage))
    
    if low_coverage_files:
        print("\n覆盖率较低的文件:")
        for filename, coverage in sorted(low_coverage_files, key=lambda x: x[1]):
            print(f"  {filename}: {coverage:.2f}%")
    
    return total_coverage >= 85

if __name__ == "__main__":
    success = analyze_coverage()
    sys.exit(0 if success else 1)
```

## 🏆 测试最佳实践

### 测试命名规范
```python
# 好的测试命名
def test_create_user_with_valid_data_should_return_user():
    pass

def test_create_user_with_duplicate_email_should_raise_error():
    pass

def test_login_with_invalid_credentials_should_return_401():
    pass

# 避免的命名
def test_user():  # 太模糊
    pass

def test_1():  # 没有意义
    pass
```

### 测试数据管理
```python
# tests/factories.py
import factory
from app.models.user import User
from app.models.case import Case

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    hashed_password = "hashed_password"

class CaseFactory(factory.Factory):
    class Meta:
        model = Case
    
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text")
    status = "pending"
    user = factory.SubFactory(UserFactory)
```

### 测试隔离
```python
# 使用事务回滚确保测试隔离
@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

### 异步测试
```python
# 异步测试示例
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_user_creation():
    """测试异步用户创建"""
    user_service = AsyncUserService()
    
    user_data = {
        "email": "async@example.com",
        "password": "password123"
    }
    
    user = await user_service.create_user(user_data)
    
    assert user.email == user_data["email"]
```

### 测试文档化
```python
def test_user_registration_flow():
    """
    测试用户注册流程
    
    场景:
    1. 用户提交有效的注册信息
    2. 系统验证信息并创建用户
    3. 发送确认邮件
    4. 用户激活账户
    
    预期结果:
    - 用户成功创建
    - 确认邮件发送
    - 用户状态为已激活
    """
    # 测试实现...
```

## 🚀 持续集成测试

### GitHub Actions配置
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: lawsker_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

**文档版本**: v1.0
**最后更新**: 2024-01-30
**维护团队**: QA团队