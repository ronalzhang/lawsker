# Lawsker Vue 组件库

这是 Lawsker 系统的 Vue.js 组件库，包含通用组件、业务组件和布局组件。

## 目录结构

```
components/
├── common/          # 通用组件
│   ├── Button/      # 按钮组件
│   ├── Form/        # 表单组件
│   ├── Modal/       # 弹窗组件
│   └── Table/       # 表格组件
├── business/        # 业务组件
│   ├── UserCard/    # 用户卡片组件
│   └── CaseList/    # 案件列表组件
├── layout/          # 布局组件
│   ├── Header/      # 头部组件
│   ├── Sidebar/     # 侧边栏组件
│   └── Footer/      # 底部组件
└── index.ts         # 组件导出文件
```

## 通用组件

### LkButton 按钮组件

基于 Element Plus 的按钮组件，提供了更多的自定义样式和功能。

#### 基本用法

```vue
<template>
  <lk-button>默认按钮</lk-button>
  <lk-button type="primary">主要按钮</lk-button>
  <lk-button type="success">成功按钮</lk-button>
  <lk-button type="warning">警告按钮</lk-button>
  <lk-button type="danger">危险按钮</lk-button>
</template>
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string | 'default' | 按钮类型 |
| size | string | 'default' | 按钮尺寸 |
| disabled | boolean | false | 是否禁用 |
| loading | boolean | false | 是否加载中 |
| icon | Component | - | 图标组件 |
| round | boolean | false | 是否圆角 |
| circle | boolean | false | 是否圆形 |
| plain | boolean | false | 是否朴素按钮 |

#### 事件

| 事件名 | 说明 | 参数 |
|--------|------|------|
| click | 点击事件 | event: MouseEvent |

### LkForm 表单组件

基于 Element Plus 的表单组件，提供了更好的封装和验证功能。

#### 基本用法

```vue
<template>
  <lk-form :model="form" :rules="rules" ref="formRef">
    <el-form-item label="用户名" prop="username">
      <el-input v-model="form.username" />
    </el-form-item>
    <el-form-item label="密码" prop="password">
      <el-input v-model="form.password" type="password" />
    </el-form-item>
  </lk-form>
</template>
```

#### 方法

| 方法名 | 说明 | 参数 |
|--------|------|------|
| validate | 验证表单 | callback?: FormValidateCallback |
| validateField | 验证指定字段 | props: string \| string[], callback?: FormValidateCallback |
| resetFields | 重置表单 | - |
| clearValidate | 清除验证 | props?: string \| string[] |

### LkModal 弹窗组件

基于 Element Plus 的对话框组件，提供了更好的用户体验。

#### 基本用法

```vue
<template>
  <lk-modal
    v-model="visible"
    title="标题"
    show-default-footer
    @confirm="handleConfirm"
    @cancel="handleCancel"
  >
    <p>弹窗内容</p>
  </lk-modal>
</template>
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | boolean | false | 是否显示弹窗 |
| title | string | '' | 弹窗标题 |
| width | string \| number | '50%' | 弹窗宽度 |
| showDefaultFooter | boolean | false | 是否显示默认底部 |
| confirmText | string | '确定' | 确认按钮文本 |
| cancelText | string | '取消' | 取消按钮文本 |
| confirmLoading | boolean | false | 确认按钮加载状态 |

### LkTable 表格组件

基于 Element Plus 的表格组件，支持分页和更多功能。

#### 基本用法

```vue
<template>
  <lk-table
    :data="tableData"
    show-pagination
    :total="total"
    @page-change="handlePageChange"
  >
    <el-table-column prop="name" label="姓名" />
    <el-table-column prop="email" label="邮箱" />
  </lk-table>
</template>
```

## 业务组件

### UserCard 用户卡片组件

用于显示用户信息的卡片组件。

#### 基本用法

```vue
<template>
  <user-card
    :user="user"
    show-stats
    clickable
    @click="handleUserClick"
  />
</template>
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| user | User | - | 用户信息对象 |
| avatarSize | number | 60 | 头像尺寸 |
| showStatus | boolean | false | 是否显示在线状态 |
| showStats | boolean | false | 是否显示统计信息 |
| clickable | boolean | false | 是否可点击 |

### CaseList 案件列表组件

用于显示案件列表的组件。

#### 基本用法

```vue
<template>
  <case-list
    :cases="cases"
    :loading="loading"
    show-filters
    show-pagination
    :total="total"
    @case-click="handleCaseClick"
    @filter-change="handleFilterChange"
  />
</template>
```

## 布局组件

### LkHeader 头部组件

应用的头部导航组件。

#### 基本用法

```vue
<template>
  <lk-header
    :menu-items="menuItems"
    :notification-count="5"
    :message-count="2"
    @menu-select="handleMenuSelect"
    @search="handleSearch"
  />
</template>
```

### LkSidebar 侧边栏组件

应用的侧边栏导航组件。

#### 基本用法

```vue
<template>
  <lk-sidebar
    v-model:collapsed="collapsed"
    :menu-items="menuItems"
    @menu-select="handleMenuSelect"
  />
</template>
```

### LkFooter 底部组件

应用的底部信息组件。

#### 基本用法

```vue
<template>
  <lk-footer
    :contact-phone="'400-123-4567'"
    :contact-email="'contact@lawsker.com'"
    @link-click="handleLinkClick"
  />
</template>
```

## 工具函数

### 格式化函数

在 `utils/format.ts` 中提供了多种格式化函数：

- `formatDate(date, format)` - 格式化日期
- `formatAmount(amount, currency)` - 格式化金额
- `formatPhone(phone)` - 格式化手机号
- `formatFileSize(size)` - 格式化文件大小
- `formatPercentage(value, decimals)` - 格式化百分比
- `truncateText(text, length, suffix)` - 截断文本

#### 使用示例

```typescript
import { formatDate, formatAmount, formatPhone } from '@/utils/format'

// 格式化日期
formatDate('2024-01-01 12:00:00') // '2024-01-01 12:00:00'
formatDate('2024-01-01', 'YYYY年MM月DD日') // '2024年01月01日'

// 格式化金额
formatAmount(1234.56) // '¥1,234.56'
formatAmount(1234.56, '$') // '$1,234.56'

// 格式化手机号
formatPhone('13812345678') // '138 1234 5678'
```

## 样式规范

### CSS 变量

组件使用 Element Plus 的 CSS 变量系统，支持主题定制：

```scss
:root {
  --el-color-primary: #409eff;
  --el-color-success: #67c23a;
  --el-color-warning: #e6a23c;
  --el-color-danger: #f56c6c;
  --el-color-info: #909399;
}
```

### 响应式设计

所有组件都支持响应式设计，在移动端会自动适配：

- 桌面端：>= 1024px
- 平板端：768px - 1023px
- 移动端：< 768px

### 命名规范

- 组件类名使用 `lk-` 前缀
- 使用 BEM 命名规范
- 状态类使用 `is-` 前缀

```scss
.lk-button {
  &__icon {
    // 元素样式
  }
  
  &--primary {
    // 修饰符样式
  }
  
  &.is-loading {
    // 状态样式
  }
}
```

## 开发指南

### 添加新组件

1. 在对应目录下创建组件文件夹
2. 创建 `index.vue` 文件
3. 在 `components/index.ts` 中导出组件
4. 添加组件文档和使用示例

### 组件开发规范

1. 使用 TypeScript 进行类型定义
2. 提供完整的 Props 接口
3. 使用 `defineEmits` 定义事件
4. 提供 `defineExpose` 暴露方法
5. 添加完整的样式和响应式支持

### 测试

建议为每个组件编写单元测试：

```typescript
import { mount } from '@vue/test-utils'
import LkButton from '@/components/common/Button/index.vue'

describe('LkButton', () => {
  it('renders correctly', () => {
    const wrapper = mount(LkButton, {
      slots: {
        default: 'Test Button'
      }
    })
    
    expect(wrapper.text()).toBe('Test Button')
  })
})
```

## 更新日志

### v1.0.0 (2024-01-30)

- 初始版本发布
- 包含基础通用组件
- 包含核心业务组件
- 包含完整布局组件
- 支持响应式设计
- 提供完整的 TypeScript 支持