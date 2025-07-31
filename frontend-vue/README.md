# Lawsker Frontend Vue.js 3 项目

基于 Vue.js 3 + TypeScript + Vite + Element Plus 的现代化前端应用。

## 技术栈

- **框架**: Vue.js 3 (Composition API)
- **语言**: TypeScript
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **样式**: SCSS
- **代码规范**: ESLint + Prettier

## 项目结构

```
frontend-vue/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口
│   ├── assets/            # 资源文件
│   ├── components/        # 通用组件
│   │   ├── common/        # 基础组件
│   │   ├── business/      # 业务组件
│   │   └── layout/        # 布局组件
│   ├── composables/       # 组合式API
│   ├── router/            # 路由配置
│   ├── stores/            # 状态管理
│   ├── styles/            # 样式文件
│   ├── types/             # TypeScript类型
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── auto-imports.d.ts      # 自动导入类型声明
├── components.d.ts        # 组件类型声明
├── env.d.ts               # 环境变量类型
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript配置
└── vite.config.ts         # Vite配置
```

## 开发规范

### 1. 命名规范

- **文件命名**: 使用 PascalCase，如 `UserProfile.vue`
- **组件命名**: 使用 PascalCase，如 `<UserCard />`
- **变量命名**: 使用 camelCase，如 `userName`
- **常量命名**: 使用 UPPER_SNAKE_CASE，如 `API_BASE_URL`
- **CSS类名**: 使用 kebab-case，如 `.user-card`

### 2. 组件规范

- 使用 Composition API + `<script setup>`
- 组件文件使用 `.vue` 扩展名
- 组件名必须是多个单词，避免与HTML元素冲突
- 使用 TypeScript 进行类型检查

```vue
<template>
  <div class="user-card">
    <h3>{{ user.name }}</h3>
    <p>{{ user.email }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  user: {
    name: string
    email: string
  }
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.user-card {
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>
```

### 3. 状态管理规范

- 使用 Pinia 进行状态管理
- Store 文件使用 camelCase 命名
- 使用 Composition API 风格

```typescript
export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  
  const isLoggedIn = computed(() => !!user.value)
  
  const login = async (credentials: LoginForm) => {
    // 登录逻辑
  }
  
  return {
    user: readonly(user),
    isLoggedIn,
    login
  }
})
```

### 4. API 调用规范

- 统一使用 `src/api/` 目录管理API
- 使用 TypeScript 定义请求和响应类型
- 统一错误处理

```typescript
export const userApi = {
  login(data: LoginForm): Promise<ApiResponse<LoginResult>> {
    return request({
      url: '/auth/login',
      method: 'post',
      data
    })
  }
}
```

### 5. 样式规范

- 使用 SCSS 预处理器
- 组件样式使用 `scoped`
- 全局样式放在 `src/styles/` 目录
- 使用 CSS 变量和 SCSS 变量

```scss
// 使用 SCSS 变量
.user-card {
  padding: $spacing-md;
  background: var(--el-bg-color);
  border-radius: $border-radius-base;
}
```

## 开发指南

### 1. 环境要求

- Node.js >= 18.0.0
- npm >= 8.0.0

### 2. 安装依赖

```bash
npm install
```

### 3. 开发服务器

```bash
npm run dev
```

### 4. 构建生产版本

```bash
npm run build
```

### 5. 类型检查

```bash
npm run type-check
```

### 6. 代码格式化

```bash
npm run format
```

## 功能特性

### 1. 自动导入

- Vue 相关函数自动导入
- Element Plus 组件自动导入
- 自定义组件自动导入

### 2. 路由守卫

- 登录状态检查
- 权限验证
- 页面标题设置

### 3. 请求拦截

- 自动添加认证头
- 统一错误处理
- 请求/响应拦截

### 4. 主题切换

- 支持明暗主题切换
- 响应系统主题偏好

### 5. 响应式设计

- 移动端适配
- 设备类型检测
- 响应式布局

## 部署说明

### 1. 环境变量

创建 `.env.production` 文件：

```bash
VITE_API_BASE_URL=https://api.lawsker.com
VITE_APP_TITLE=Lawsker
VITE_WS_URL=wss://api.lawsker.com
```

### 2. 构建配置

```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

### 3. 服务器配置

推荐使用 Nginx 作为静态文件服务器：

```nginx
server {
    listen 80;
    server_name lawsker.com;
    root /var/www/lawsker/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 性能优化

### 1. 代码分割

- 路由级别的懒加载
- 组件按需导入
- 第三方库分包

### 2. 资源优化

- 图片压缩和格式优化
- CSS 和 JS 压缩
- Gzip 压缩

### 3. 缓存策略

- 浏览器缓存
- CDN 缓存
- Service Worker 缓存

## 常见问题

### 1. 开发环境代理配置

如果后端API地址变更，修改 `vite.config.ts` 中的代理配置：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### 2. 类型错误

如果遇到类型错误，确保：
- 安装了所有类型依赖
- TypeScript 配置正确
- 重启 TypeScript 服务

### 3. 样式问题

如果样式不生效：
- 检查 SCSS 语法
- 确认样式作用域
- 检查 CSS 变量定义

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License