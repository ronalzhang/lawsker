<template>
  <div class="reset-password-container">
    <div class="reset-password-card">
      <div class="reset-password-header">
        <h1>重置密码</h1>
        <p>请输入您的新密码</p>
      </div>
      
      <el-form
        ref="resetFormRef"
        :model="resetForm"
        :rules="resetRules"
        class="reset-password-form"
        @submit.prevent="handleResetPassword"
      >
        <el-form-item prop="password">
          <el-input
            v-model="resetForm.password"
            type="password"
            placeholder="请输入新密码"
            size="large"
            prefix-icon="Lock"
            show-password
            :disabled="loading"
          />
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="resetForm.confirmPassword"
            type="password"
            placeholder="请确认新密码"
            size="large"
            prefix-icon="Lock"
            show-password
            :disabled="loading"
            @keyup.enter="handleResetPassword"
          />
        </el-form-item>
        
        <el-form-item>
          <lk-button
            type="primary"
            size="large"
            class="reset-button"
            :loading="loading"
            @click="handleResetPassword"
          >
            重置密码
          </lk-button>
        </el-form-item>
      </el-form>
      
      <div class="reset-password-footer">
        <el-link type="primary" @click="$router.push('/login')">
          返回登录
        </el-link>
      </div>
      
      <!-- 成功提示 -->
      <div v-if="resetSuccess" class="success-message">
        <el-icon class="success-icon"><CircleCheck /></el-icon>
        <h3>密码重置成功</h3>
        <p>您的密码已成功重置，请使用新密码登录</p>
        
        <lk-button
          type="primary"
          @click="$router.push('/login')"
        >
          立即登录
        </lk-button>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="tokenInvalid" class="error-message">
        <el-icon class="error-icon"><CircleClose /></el-icon>
        <h3>链接已失效</h3>
        <p>密码重置链接已过期或无效，请重新申请</p>
        
        <lk-button
          type="primary"
          @click="$router.push('/forgot-password')"
        >
          重新申请
        </lk-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElForm, ElFormItem, ElInput, ElIcon, ElLink } from 'element-plus'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { LkButton } from '@/components'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()

const resetFormRef = ref<FormInstance>()
const loading = ref(false)
const resetSuccess = ref(false)
const tokenInvalid = ref(false)
const resetToken = ref('')

const resetForm = reactive({
  password: '',
  confirmPassword: ''
})

const resetRules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleResetPassword = async () => {
  if (!resetFormRef.value) return
  
  await resetFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await authApi.resetPassword(resetToken.value, resetForm.password)
        resetSuccess.value = true
        ElMessage.success('密码重置成功')
      } catch (error: any) {
        if (error.status === 400 || error.status === 404) {
          tokenInvalid.value = true
        } else {
          ElMessage.error(error.message || '重置失败，请稍后重试')
        }
      } finally {
        loading.value = false
      }
    }
  })
}

onMounted(() => {
  // 从URL参数获取重置token
  const token = route.query.token as string
  if (!token) {
    tokenInvalid.value = true
    return
  }
  
  resetToken.value = token
})
</script>

<style lang="scss" scoped>
.reset-password-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.reset-password-card {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.reset-password-header {
  text-align: center;
  margin-bottom: 32px;
  
  h1 {
    font-size: 28px;
    font-weight: 700;
    color: #303133;
    margin: 0 0 12px 0;
  }
  
  p {
    color: #909399;
    margin: 0;
  }
}

.reset-password-form {
  .el-form-item {
    margin-bottom: 24px;
  }
}

.reset-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.reset-password-footer {
  text-align: center;
  margin-top: 24px;
}

.success-message,
.error-message {
  text-align: center;
  padding: 24px 0;
  
  .success-icon {
    font-size: 48px;
    color: #67c23a;
    margin-bottom: 16px;
  }
  
  .error-icon {
    font-size: 48px;
    color: #f56c6c;
    margin-bottom: 16px;
  }
  
  h3 {
    margin: 0 0 16px 0;
    color: #303133;
    font-size: 20px;
  }
  
  p {
    margin: 0 0 24px 0;
    color: #606266;
    line-height: 1.5;
  }
}

// 响应式设计
@media (max-width: 480px) {
  .reset-password-card {
    width: 90vw;
    padding: 24px;
  }
  
  .reset-password-header {
    h1 {
      font-size: 24px;
    }
  }
}
</style>