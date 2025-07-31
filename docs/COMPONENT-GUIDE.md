# Lawsker组件使用指南

## 📋 目录

- [组件概述](#组件概述)
- [通用组件](#通用组件)
- [业务组件](#业务组件)
- [图表组件](#图表组件)
- [表单组件](#表单组件)
- [布局组件](#布局组件)
- [开发规范](#开发规范)

## 🎯 组件概述

### 设计原则
- 可复用性
- 一致性
- 可维护性
- 性能优化
- 类型安全

### 技术栈
- Vue.js 3 + Composition API
- TypeScript
- Element Plus
- Vite

## 🧩 通用组件

### Button 按钮组件
```vue
<template>
  <Button 
    type="primary" 
    size="medium" 
    :loading="loading"
    @click="handleClick"
  >
    确认
  </Button>
</template>

<script setup lang="ts">
import { Button } from '@/components/common'

const loading = ref(false)

const handleClick = () => {
  loading.value = true
  // 处理点击事件
}
</script>
```

**Props:**
- `type`: 按钮类型 (primary | success | warning | danger | info)
- `size`: 按钮大小 (large | medium | small)
- `loading`: 加载状态
- `disabled`: 禁用状态

### Modal 弹窗组件
```vue
<template>
  <Modal 
    v-model:visible="visible"
    title="确认操作"
    width="500px"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  >
    <p>确定要执行此操作吗？</p>
  </Modal>
</template>

<script setup lang="ts">
import { Modal } from '@/components/common'

const visible = ref(false)

const handleConfirm = () => {
  // 确认操作
  visible.value = false
}

const handleCancel = () => {
  visible.value = false
}
</script>
```

### Table 表格组件
```vue
<template>
  <Table 
    :data="tableData"
    :columns="columns"
    :loading="loading"
    :pagination="pagination"
    @page-change="handlePageChange"
  />
</template>

<script setup lang="ts">
import { Table } from '@/components/common'

const tableData = ref([])
const loading = ref(false)

const columns = [
  { prop: 'name', label: '姓名', width: 120 },
  { prop: 'email', label: '邮箱', width: 200 },
  { prop: 'status', label: '状态', width: 100 }
]

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})
</script>
```

## 💼 业务组件

### UserCard 用户卡片
```vue
<template>
  <UserCard 
    :user="userInfo"
    :show-actions="true"
    @edit="handleEdit"
    @delete="handleDelete"
  />
</template>

<script setup lang="ts">
import { UserCard } from '@/components/business'

interface User {
  id: string
  name: string
  avatar: string
  email: string
  role: string
}

const userInfo = ref<User>({
  id: '1',
  name: '张三',
  avatar: '/avatars/user1.jpg',
  email: 'zhangsan@example.com',
  role: 'user'
})
</script>
```

### CaseList 案件列表
```vue
<template>
  <CaseList 
    :cases="caseList"
    :loading="loading"
    @select="handleSelect"
    @status-change="handleStatusChange"
  />
</template>

<script setup lang="ts">
import { CaseList } from '@/components/business'

const caseList = ref([])
const loading = ref(false)

const handleSelect = (caseId: string) => {
  // 处理案件选择
}

const handleStatusChange = (caseId: string, status: string) => {
  // 处理状态变更
}
</script>
```