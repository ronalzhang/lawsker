# Lawsker业务优化系统设计文档

## 系统架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                 Lawsker (律客) 业务优化架构                    │
├─────────────────────────────────────────────────────────────┤
│  前端层 (Frontend Layer) - 现代化UI设计                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   统一认证界面    │  │   律师工作台     │  │   用户工作台      ││
│  │  邮箱验证 +     │  │  积分等级系统 +  │  │  Credits支付 +  ││
│  │  律师证认证 +   │  │  会员订阅 +     │  │  批量上传 +     ││
│  │  演示账户       │  │  专业图标       │  │  现代化UI       ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  业务服务层 (Business Service Layer)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │  统一认证服务    │  │  律师积分服务   │  │  Credits支付服务 ││
│  │  邮箱验证 +     │  │  等级计算 +     │  │  余额管理 +     ││
│  │  律师证审核 +   │  │  会员倍数 +     │  │  支付处理 +     ││
│  │  工作台路由     │  │  惩罚机制       │  │  使用控制       ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  核心API层 (Core API Layer) - 基于现有FastAPI扩展             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   认证API       │  │   会员API       │  │   支付API       ││
│  │  /auth/unified  │  │  /membership    │  │  /credits       ││
│  │  /auth/lawyer   │  │  /points        │  │  /payments      ││
│  │  /demo          │  │  /levels        │  │  /billing       ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  数据层 (Data Layer) - 基于现有42张表扩展                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   认证相关表     │  │   积分会员表     │  │   Credits表     ││
│  │  认证申请表 +   │  │  律师等级表 +   │  │  用户Credits +  ││
│  │  工作台映射 +   │  │  积分记录表 +   │  │  购买记录表 +   ││
│  │  演示账户表     │  │  会员订阅表     │  │  使用记录表     ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 核心组件设计

### 1. 统一认证系统设计

#### 1.1 认证流程架构

**统一认证流程**:
```
用户访问 → 选择登录/注册/演示 → 邮箱验证注册 → 身份选择 → 工作台重定向
    ↓
律师身份 → 律师证上传 → 管理员审核 → 认证通过 → 自动分配免费会员
    ↓
普通用户 → 直接激活 → 分配1个Credit → 用户工作台
    ↓
演示账户 → 演示数据加载 → 功能体验 → 注册转化
```

**技术实现架构**:
```python
# 统一认证服务设计
class UnifiedAuthService:
    """基于现有auth_service扩展的统一认证"""
    
    async def register_with_email_verification(self, email: str, password: str, full_name: str):
        """邮箱验证注册 - 扩展现有注册功能"""
        # 1. 复用现有用户创建逻辑
        user = await self.create_user_extended({
            'email': email,
            'password': self.hash_password(password),
            'full_name': full_name,
            'email_verified': False,
            'account_type': 'pending',
            'workspace_id': await self.generate_secure_workspace_id()
        })
        
        # 2. 发送验证邮件（复用现有邮件服务）
        await self.email_service.send_verification_email(email, user.id)
        
        return {'user_id': user.id, 'verification_required': True}
    
    async def set_user_identity_and_redirect(self, user_id: str, identity_type: str):
        """身份设置和工作台重定向"""
        if identity_type == 'lawyer':
            # 律师身份：需要认证
            await self.update_user_account_type(user_id, 'lawyer_pending')
            return {'redirect_url': f'/legal/{user.workspace_id}', 'requires_certification': True}
        else:
            # 普通用户：直接激活
            await self.update_user_account_type(user_id, 'user')
            await self.credits_service.initialize_user_credits(user_id)
            return {'redirect_url': f'/user/{user.workspace_id}'}
```

#### 1.2 律师证认证系统

**认证流程设计**:
```python
class LawyerCertificationService:
    """律师证认证服务 - 基于现有文件上传扩展"""
    
    async def submit_certification_request(self, user_id: str, cert_data: dict):
        """提交律师证认证申请"""
        # 1. 保存律师证文件（复用现有文件上传）
        cert_file = await self.file_service.save_certificate_file(
            user_id, cert_data['certificate_file']
        )
        
        # 2. 创建认证申请记录
        certification = await self.create_certification_record({
            'user_id': user_id,
            'certificate_file_path': cert_file['path'],
            'lawyer_name': cert_data['lawyer_name'],
            'license_number': cert_data['license_number'],
            'law_firm': cert_data.get('law_firm'),
            'practice_areas': cert_data.get('practice_areas', []),
            'status': 'pending'
        })
        
        # 3. 通知管理员审核（复用现有通知系统）
        await self.notification_service.notify_admin_for_review(certification.id)
        
        return certification
    
    async def approve_certification(self, cert_id: str, admin_id: str):
        """管理员审核通过"""
        # 1. 更新认证状态
        await self.update_certification_status(cert_id, 'approved', admin_id)
        
        # 2. 激活律师账户
        certification = await self.get_certification_by_id(cert_id)
        await self.update_user_account_type(certification.user_id, 'lawyer')
        
        # 3. 自动分配免费会员（新功能）
        await self.membership_service.assign_free_membership(certification.user_id)
        
        return {'approved': True, 'lawyer_id': certification.user_id}
```

### 2. 律师积分和会员系统设计

#### 2.1 传奇游戏式积分系统

**积分计算引擎**:
```python
class LawyerPointsEngine:
    """律师积分计算引擎 - 传奇游戏式指数级积分"""
    
    # 基础积分规则
    BASE_POINTS = {
        'case_complete_success': 100,
        'case_complete_excellent': 200,
        'review_5star': 200,
        'review_4star': 100,
        'review_1star': -300,
        'review_2star': -150,
        'online_hour': 5,
        'ai_credit_used': 3,
        'payment_100yuan': 100,
        'case_declined': -30,
        'late_response': -20
    }
    
    async def calculate_points_with_multiplier(self, lawyer_id: str, action: str, context: dict):
        """计算积分 - 考虑会员倍数"""
        # 1. 获取基础积分
        base_points = self.BASE_POINTS.get(action, 0)
        
        # 2. 根据上下文调整积分
        adjusted_points = await self.adjust_points_by_context(base_points, context)
        
        # 3. 获取律师会员倍数
        membership = await self.membership_service.get_lawyer_membership(lawyer_id)
        multiplier = membership.get('point_multiplier', 1.0)
        
        # 4. 应用倍数
        final_points = int(adjusted_points * multiplier)
        
        # 5. 记录积分变动
        await self.record_point_transaction(lawyer_id, action, final_points, multiplier)
        
        # 6. 检查等级升级
        await self.check_level_upgrade(lawyer_id)
        
        return {
            'points_earned': final_points,
            'multiplier_applied': multiplier,
            'membership_type': membership.get('type', 'free')
        }
    
    async def check_level_upgrade(self, lawyer_id: str):
        """检查律师等级升级"""
        lawyer_details = await self.get_lawyer_level_details(lawyer_id)
        current_points = lawyer_details.level_points
        current_level = lawyer_details.current_level
        
        # 获取下一等级要求
        next_level_requirements = await self.get_level_requirements(current_level + 1)
        
        if current_points >= next_level_requirements['level_points']:
            # 满足升级条件
            await self.upgrade_lawyer_level(lawyer_id, current_level + 1)
            
            # 发送升级通知
            await self.notification_service.send_level_upgrade_notification(
                lawyer_id, current_level + 1
            )
```

#### 2.2 会员订阅系统

**免费引流模式设计**:
```python
class LawyerMembershipService:
    """律师会员服务 - 免费引流 + 付费升级"""
    
    MEMBERSHIP_TIERS = {
        'free': {
            'name': '基础律师版（免费）',
            'monthly_fee': 0,
            'ai_credits_monthly': 20,
            'daily_case_limit': 2,
            'point_multiplier': 1.0,
            'features': ['基础案件', '基础AI工具', '邮件支持']
        },
        'professional': {
            'name': '专业律师版',
            'monthly_fee': 899,
            'ai_credits_monthly': 500,
            'daily_case_limit': 15,
            'point_multiplier': 2.0,
            'features': ['所有案件类型', '高级AI工具', '优先支持', '数据分析']
        },
        'enterprise': {
            'name': '企业律师版',
            'monthly_fee': 2999,
            'ai_credits_monthly': 2000,
            'daily_case_limit': -1,  # 无限制
            'point_multiplier': 3.0,
            'features': ['企业客户案件', '全部AI工具', '专属支持', 'API接入']
        }
    }
    
    async def assign_free_membership(self, lawyer_id: str):
        """律师认证通过后自动分配免费会员"""
        membership = await self.create_lawyer_membership({
            'lawyer_id': lawyer_id,
            'membership_type': 'free',
            'start_date': datetime.now().date(),
            'end_date': datetime.now().date() + timedelta(days=365*10),  # 10年有效期
            'benefits': self.MEMBERSHIP_TIERS['free'],
            'auto_renewal': True,
            'payment_amount': 0
        })
        
        # 初始化律师等级数据
        await self.initialize_lawyer_level_details(lawyer_id)
        
        return membership
    
    async def upgrade_membership(self, lawyer_id: str, target_tier: str):
        """会员升级"""
        tier_config = self.MEMBERSHIP_TIERS[target_tier]
        
        # 创建支付订单
        payment_order = await self.payment_service.create_membership_order(
            lawyer_id, tier_config['monthly_fee'], target_tier
        )
        
        # 支付成功后升级会员
        if payment_order['status'] == 'paid':
            await self.update_lawyer_membership(lawyer_id, target_tier)
            
            # 重新计算积分倍数
            await self.points_engine.recalculate_points_with_new_multiplier(
                lawyer_id, tier_config['point_multiplier']
            )
        
        return payment_order
```

### 3. 用户Credits支付系统设计

#### 3.1 Credits管理服务

**Credits控制机制**:
```python
class UserCreditsService:
    """用户Credits支付控制服务"""
    
    async def initialize_user_credits(self, user_id: str):
        """初始化用户Credits - 每周1个免费"""
        await self.create_user_credits_record({
            'user_id': user_id,
            'credits_weekly': 1,
            'credits_remaining': 1,
            'credits_purchased': 0,
            'last_reset_date': datetime.now().date()
        })
    
    async def weekly_credits_reset(self):
        """每周重置Credits - 定时任务"""
        users = await self.get_all_active_users()
        
        for user in users:
            await self.reset_user_credits(user.id, credits=1)
            
        logger.info(f"Weekly credits reset completed for {len(users)} users")
    
    async def purchase_credits(self, user_id: str, credits_count: int):
        """购买Credits - 50元/个"""
        price_per_credit = 50.00
        total_amount = credits_count * price_per_credit
        
        # 创建支付订单（复用现有支付服务）
        payment_order = await self.payment_service.create_credits_order(
            user_id, total_amount, credits_count
        )
        
        # 支付成功后增加Credits
        if payment_order['status'] == 'paid':
            await self.add_user_credits(user_id, credits_count)
            
            # 记录购买记录
            await self.record_credits_purchase(user_id, credits_count, total_amount)
        
        return payment_order
    
    async def consume_credits_for_batch_upload(self, user_id: str):
        """批量上传消耗Credits"""
        user_credits = await self.get_user_credits(user_id)
        
        if user_credits['credits_remaining'] < 1:
            raise InsufficientCreditsError(
                "Credits不足，请购买或等待每周重置",
                current_credits=user_credits['credits_remaining'],
                required_credits=1
            )
        
        # 扣除1个credit
        await self.deduct_user_credits(user_id, 1)
        
        # 记录使用记录
        await self.record_credits_usage(user_id, 1, 'batch_upload')
        
        return {
            'credits_consumed': 1,
            'credits_remaining': user_credits['credits_remaining'] - 1
        }
```

### 4. 前端UI现代化设计

#### 4.1 设计系统规范

**现代化UI设计原则**:
```scss
// 设计系统变量
:root {
  // 专业色彩系统
  --primary-color: #2563eb;      // 专业蓝
  --secondary-color: #7c3aed;    // 紫色
  --success-color: #059669;      // 成功绿
  --warning-color: #d97706;      // 警告橙
  --error-color: #dc2626;        // 错误红
  
  // 中性色系
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-300: #d1d5db;
  --gray-400: #9ca3af;
  --gray-500: #6b7280;
  --gray-600: #4b5563;
  --gray-700: #374151;
  --gray-800: #1f2937;
  --gray-900: #111827;
  
  // 专业字体系统
  --font-family-sans: 'Inter', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
  --font-family-mono: 'JetBrains Mono', 'SF Mono', monospace;
  
  // 阴影系统
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
  
  // 圆角系统
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
}
```

**专业图标系统**:
```typescript
// 图标组件库配置
import { 
  UserIcon, 
  ScaleIcon, 
  DocumentTextIcon,
  CreditCardIcon,
  TrophyIcon,
  StarIcon,
  BellIcon,
  CogIcon,
  ChartBarIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'

// 图标映射系统
export const IconMap = {
  // 用户相关
  'user': UserIcon,
  'lawyer': ScaleIcon,
  'profile': UserIcon,
  
  // 业务相关
  'case': DocumentTextIcon,
  'payment': CreditCardIcon,
  'credits': CreditCardIcon,
  'level': TrophyIcon,
  'rating': StarIcon,
  
  // 系统相关
  'notification': BellIcon,
  'settings': CogIcon,
  'analytics': ChartBarIcon,
  'security': ShieldCheckIcon
}

// 图标组件
export const Icon: React.FC<{name: string, className?: string}> = ({ name, className }) => {
  const IconComponent = IconMap[name] || UserIcon
  return <IconComponent className={className} />
}
```

#### 4.2 游戏化UI组件

**律师等级展示组件**:
```vue
<template>
  <div class="lawyer-level-card">
    <!-- 等级徽章 -->
    <div class="level-badge" :class="`level-${currentLevel}`">
      <Icon name="trophy" class="level-icon" />
      <span class="level-text">{{ levelName }}</span>
    </div>
    
    <!-- 积分进度条 -->
    <div class="points-progress">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: `${progressPercentage}%` }"
        ></div>
      </div>
      <div class="progress-text">
        {{ currentPoints.toLocaleString() }} / {{ nextLevelPoints.toLocaleString() }}
      </div>
    </div>
    
    <!-- 会员倍数显示 -->
    <div class="membership-multiplier" v-if="membershipMultiplier > 1">
      <Icon name="star" class="multiplier-icon" />
      <span>{{ membershipMultiplier }}x 积分倍数</span>
    </div>
    
    <!-- 升级动画 -->
    <div class="level-up-animation" v-if="showLevelUpAnimation">
      <div class="celebration-effect">
        <Icon name="trophy" class="celebration-icon" />
        <span class="celebration-text">恭喜升级！</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lawyer-level-card {
  @apply bg-white rounded-xl shadow-lg p-6 border border-gray-200;
}

.level-badge {
  @apply flex items-center gap-2 mb-4;
}

.level-1, .level-2 { @apply text-gray-600; }
.level-3, .level-4 { @apply text-blue-600; }
.level-5, .level-6 { @apply text-purple-600; }
.level-7, .level-8 { @apply text-orange-600; }
.level-9, .level-10 { @apply text-red-600; }

.progress-bar {
  @apply w-full bg-gray-200 rounded-full h-3 mb-2;
}

.progress-fill {
  @apply bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500;
}

.level-up-animation {
  @apply fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50;
  animation: fadeIn 0.5s ease-in-out;
}

.celebration-effect {
  @apply bg-white rounded-xl p-8 text-center shadow-2xl;
  animation: bounceIn 0.8s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes bounceIn {
  0% { transform: scale(0.3); opacity: 0; }
  50% { transform: scale(1.05); }
  70% { transform: scale(0.9); }
  100% { transform: scale(1); opacity: 1; }
}
</style>
```

**Credits余额组件**:
```vue
<template>
  <div class="credits-balance-card">
    <div class="credits-header">
      <Icon name="credits" class="credits-icon" />
      <h3>Credits余额</h3>
    </div>
    
    <div class="credits-amount">
      <span class="amount-number">{{ creditsRemaining }}</span>
      <span class="amount-unit">Credits</span>
    </div>
    
    <div class="credits-info">
      <div class="info-item">
        <span class="info-label">下次重置</span>
        <span class="info-value">{{ nextResetDate }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">已购买</span>
        <span class="info-value">{{ creditsPurchased }}</span>
      </div>
    </div>
    
    <button 
      class="purchase-button"
      @click="showPurchaseModal = true"
    >
      <Icon name="payment" class="button-icon" />
      购买Credits (¥50/个)
    </button>
    
    <!-- 购买模态框 -->
    <CreditsurchaseModal 
      v-if="showPurchaseModal"
      @close="showPurchaseModal = false"
      @purchase="handlePurchase"
    />
  </div>
</template>

<style scoped>
.credits-balance-card {
  @apply bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl p-6 border border-blue-200;
}

.credits-amount {
  @apply text-3xl font-bold text-blue-600 mb-4;
}

.purchase-button {
  @apply w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2;
}
</style>
```

#### 1.2 管理后台架构

**特殊需求考虑**:
- 大数据量表格展示
- 实时数据更新
- 复杂图表可视化
- 多维度数据分析

**技术栈增强**:
```typescript
// 管理后台专用依赖
{
  "dependencies": {
    "vue": "^3.3.0",
    "typescript": "^5.0.0",
    "element-plus": "^2.4.0",
    "echarts": "^5.4.0",
    "socket.io-client": "^4.7.0",
    "@tanstack/vue-table": "^8.10.0",
    "vue-leaflet": "^0.10.0",
    "dayjs": "^1.11.0",
    "lodash-es": "^4.17.0",
    "xlsx": "^0.18.0"
  }
}
```

### 2. 后端架构优化

#### 2.1 安全性增强设计

**认证机制升级**:
```python
# 新的认证架构
class SecurityConfig:
    # HttpOnly Cookie配置
    COOKIE_SETTINGS = {
        "httponly": True,
        "secure": True,
        "samesite": "strict",
        "max_age": 86400  # 24小时
    }
    
    # CSRF保护
    CSRF_SECRET_KEY = "your-csrf-secret"
    CSRF_TOKEN_LOCATION = ["cookies", "headers"]
    
    # 限流配置
    RATE_LIMIT_STORAGE_URL = "redis://localhost:6379"
    DEFAULT_RATE_LIMIT = "100/hour"
    
    # JWT配置
    JWT_ALGORITHM = "RS256"  # 使用RSA算法
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
```

**API安全中间件**:
```python
class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # 1. IP白名单检查
        if not self.check_ip_whitelist(request.client.host):
            raise HTTPException(403, "IP not allowed")
        
        # 2. 请求限流
        if not await self.check_rate_limit(request):
            raise HTTPException(429, "Rate limit exceeded")
        
        # 3. CSRF检查
        if request.method in ["POST", "PUT", "DELETE"]:
            if not self.verify_csrf_token(request):
                raise HTTPException(403, "CSRF token invalid")
        
        # 4. 请求日志
        await self.log_request(request)
        
        response = await call_next(request)
        
        # 5. 响应头安全设置
        self.set_security_headers(response)
        
        return response
```

#### 2.2 数据采集系统设计

**访问日志采集器**:
```python
class AccessLogCollector:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.batch_size = 100
        self.batch_timeout = 5  # 秒
        
    async def collect_access_log(self, log_data: dict):
        """收集访问日志"""
        # 1. 数据预处理
        processed_data = await self.preprocess_log(log_data)
        
        # 2. 批量写入Redis队列
        await self.redis_client.lpush("access_logs", json.dumps(processed_data))
        
        # 3. 触发批量处理
        if await self.redis_client.llen("access_logs") >= self.batch_size:
            await self.process_batch()
    
    async def process_batch(self):
        """批量处理日志"""
        logs = []
        for _ in range(self.batch_size):
            log_data = await self.redis_client.rpop("access_logs")
            if log_data:
                logs.append(json.loads(log_data))
        
        if logs:
            await self.batch_insert_to_db(logs)
            await self.update_realtime_stats(logs)
```

**实时数据推送系统**:
```python
class RealtimeDataPusher:
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.redis_pubsub = redis.Redis().pubsub()
        
    async def start_listening(self):
        """开始监听数据变化"""
        await self.redis_pubsub.subscribe("stats_update", "alert")
        
        async for message in self.redis_pubsub.listen():
            if message["type"] == "message":
                await self.handle_message(message)
    
    async def handle_message(self, message):
        """处理消息并推送"""
        channel = message["channel"].decode()
        data = json.loads(message["data"])
        
        if channel == "stats_update":
            await self.websocket_manager.broadcast_stats(data)
        elif channel == "alert":
            await self.websocket_manager.send_alert(data)
```

### 3. 数据库优化设计

#### 3.1 查询优化策略

**索引优化**:
```sql
-- 访问日志表索引优化
CREATE INDEX CONCURRENTLY idx_access_logs_user_time 
ON access_logs(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_access_logs_ip_time 
ON access_logs(ip_address, created_at DESC);

CREATE INDEX CONCURRENTLY idx_access_logs_path_time 
ON access_logs(path, created_at DESC);

-- 用户表复合索引
CREATE INDEX CONCURRENTLY idx_users_role_status 
ON users(role, status) WHERE status = 'active';

-- 案件表索引优化
CREATE INDEX CONCURRENTLY idx_cases_status_created 
ON cases(status, created_at DESC) WHERE status IN ('pending', 'assigned');
```

**分区表设计**:
```sql
-- 访问日志按月分区
CREATE TABLE access_logs (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID,
    ip_address INET NOT NULL,
    path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    -- 其他字段...
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE access_logs_2024_01 PARTITION OF access_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE access_logs_2024_02 PARTITION OF access_logs
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### 3.2 缓存策略设计

**多层缓存架构**:
```python
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.local_cache = {}  # 进程内缓存
        
    async def get(self, key: str, fetch_func=None):
        """多层缓存获取"""
        # 1. 进程内缓存
        if key in self.local_cache:
            return self.local_cache[key]
        
        # 2. Redis缓存
        cached = await self.redis_client.get(key)
        if cached:
            data = json.loads(cached)
            self.local_cache[key] = data  # 回填本地缓存
            return data
        
        # 3. 数据库查询
        if fetch_func:
            data = await fetch_func()
            await self.set(key, data, expire=300)
            return data
        
        return None
    
    async def set(self, key: str, value: any, expire: int = 300):
        """设置缓存"""
        # 设置Redis缓存
        await self.redis_client.setex(key, expire, json.dumps(value))
        
        # 设置本地缓存
        self.local_cache[key] = value
        
        # 本地缓存清理策略
        if len(self.local_cache) > 1000:
            # 清理最老的50%
            keys_to_remove = list(self.local_cache.keys())[:500]
            for k in keys_to_remove:
                del self.local_cache[k]
```

### 4. 监控和运维设计

#### 4.1 监控指标体系

**系统指标监控**:
```python
from prometheus_client import Counter, Histogram, Gauge

# 定义监控指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')

class MetricsCollector:
    @staticmethod
    def record_request(method: str, endpoint: str, status: int, duration: float):
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.observe(duration)
    
    @staticmethod
    def update_active_users(count: int):
        ACTIVE_USERS.set(count)
    
    @staticmethod
    def update_db_connections(count: int):
        DATABASE_CONNECTIONS.set(count)
```

**业务指标监控**:
```python
# 业务指标定义
CASE_CREATED = Counter('cases_created_total', 'Total cases created', ['user_type'])
LAWYER_RESPONSE_TIME = Histogram('lawyer_response_time_seconds', 'Lawyer response time')
PAYMENT_SUCCESS_RATE = Gauge('payment_success_rate', 'Payment success rate')

class BusinessMetrics:
    @staticmethod
    def record_case_creation(user_type: str):
        CASE_CREATED.labels(user_type=user_type).inc()
    
    @staticmethod
    def record_lawyer_response(response_time: float):
        LAWYER_RESPONSE_TIME.observe(response_time)
    
    @staticmethod
    def update_payment_success_rate(rate: float):
        PAYMENT_SUCCESS_RATE.set(rate)
```

#### 4.2 告警系统设计

**告警规则配置**:
```yaml
# alerting_rules.yml
groups:
  - name: lawsker_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: DatabaseConnectionHigh
        expr: database_connections_active > 80
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Database connections high"
          description: "Database connections: {{ $value }}"
      
      - alert: DiskSpaceHigh
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low"
          description: "Disk space usage is above 90%"
```

## 数据流设计

### 1. 用户访问数据流

```
用户请求 → NGINX → 访问日志中间件 → 业务处理 → 响应
    ↓
访问日志收集器 → Redis队列 → 批量处理 → PostgreSQL
    ↓
实时统计计算 → Redis发布 → WebSocket推送 → 管理后台更新
```

### 2. 实时监控数据流

```
系统指标采集 → Prometheus → 告警规则检查 → 告警通知
    ↓
Grafana仪表盘 ← Prometheus查询 ← 指标存储
    ↓
管理后台 ← WebSocket推送 ← 实时数据处理
```

## 安全设计

### 1. 认证授权流程

```
用户登录 → 验证凭据 → 生成JWT + 设置HttpOnly Cookie
    ↓
请求API → 验证Cookie → 检查权限 → 执行业务逻辑
    ↓
记录审计日志 → 更新用户活动 → 返回响应
```

### 2. 数据保护策略

- **传输加密**: 全站HTTPS，TLS 1.3
- **存储加密**: 敏感字段AES-256加密
- **访问控制**: RBAC权限模型
- **审计日志**: 完整的操作记录
- **数据脱敏**: 日志中敏感信息脱敏

## 性能优化设计

### 1. 前端性能优化

- **代码分割**: 路由级别的懒加载
- **资源优化**: 图片压缩、CDN加速
- **缓存策略**: 浏览器缓存、Service Worker
- **虚拟滚动**: 大数据量表格优化

### 2. 后端性能优化

- **数据库优化**: 索引优化、查询优化、连接池
- **缓存策略**: 多层缓存、缓存预热
- **异步处理**: Celery任务队列
- **负载均衡**: NGINX负载均衡

## 部署架构设计

### 1. 容器化部署

```dockerfile
# 前端Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### 2. 服务编排

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/lawsker
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=lawsker
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

这个设计文档为系统优化提供了完整的技术架构和实现方案，确保优化过程有明确的技术指导和标准。