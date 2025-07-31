<template>
  <div class="forgot-password-container">
    <div class="forgot-password-card">
      <div class="forgot-password-header">
        <h1>找回密码</h1>
        <p>请输入您的邮箱地址，我们将发送重置密码的链接</p>
      </div>
      
      <el-form
        ref="forgotFormRef"
        :model="forgotForm"
        :rules="forgotRules"
        class="forgot-password-form"
        @submit.prevent="handleSendReset"
      >
        <el-form-item prop="email">
          <el-input
            v-model="forgotForm.email"
            placeholder="请输入邮箱地址"
            size="large"
            prefix-icon="Message"
            :disabled="loading"
          />
        </el-form-item>
        
        <el-form-item>
          <lk-button
            type="primary"
            size="large"
            class="send-button"
            :loading="loading"
            @click="handleSendReset"
          >
            发送重置链接
          </lk-button>
        </el-form-item>
      </el-form>
      
      <div class="forgot-password-footer">
        <el-link type="primary" @click="$router.push('/login')">
          返回登录
        </el-link>
        <span class="divider">|</span>
        <el-link type="primary" @click="$router.push('/register')">
          注册账号
        </el-link>
      </div>
      
      <!-- 成功提示 -->
      <div v-if="emailSent" class="success-message">
        <el-icon class="success-icon"><CircleCheck /></el-icon>
        <h3>邮件已发送</h3>
        <p>我们已向 <strong>{{ forgotForm.email }}</strong> 发送了密码重置链接</p>
        <p>请检查您的邮箱（包括垃圾邮件文件夹）并点击链接重置密码</p>
        
        <div class="resend-section">
          <p>没有收到邮件？</p>
          <lk-button
            type="text"
            :disabled="resendCountdown > 0"
            @click="handleResend"
          >
            {{ resendCountdown > 0 ? `${resendCountdown}秒后可重发` : '重新发送' }}
          </lk-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElForm, ElFormItem, ElInput, ElIcon, ElLink } from 'element-plus'
import { CircleCheck } from '@element-plus/icons-vue'
import { LkButton } from '@/components'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()

const forgotFormRef = ref<FormInstance>()
const loading = ref(false)
const emailSent = ref(false)
const resendCountdown = ref(0)
let countdownTimer: NodeJS.Timeout | null = null

const forgotForm = reactive({
  email: ''
})

const forgotRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const handleSendReset = async () => {
  if (!forgotFormRef.value) return
  
  await forgotFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await authApi.sendPasswordReset(forgotForm.email)
        emailSent.value = true
        startResendCountdown()
        ElMessage.success('密码重置邮件已发送')
      } catch (error: any) {
        ElMessage.error(error.message || '发送失败，请稍后重试')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleResend = async () => {
  if (resendCountdown.value > 0) return
  
  loading.value = true
  try {
    await authApi.sendPasswordReset(forgotForm.email)
    startResendCountdown()
    ElMessage.success('邮件已重新发送')
  } catch (error: any) {
    ElMessage.error(error.message || '发送失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const startResendCountdown = () => {
  resendCountdown.value = 60
  countdownTimer = setInterval(() => {
    resendCountdown.value--
    if (resendCountdown.value <= 0) {
      clearInterval(countdownTimer!)
      countdownTimer = null
    }
  }, 1000)
}

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style lang="scss" scoped>
.forgot-password-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.forgot-password-card {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.forgot-password-header {
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
    line-height: 1.5;
  }
}

.forgot-password-form {
  .el-form-item {
    margin-bottom: 24px;
  }
}

.send-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.forgot-password-footer {
  text-align: center;
  margin-top: 24px;
  color: #909399;
  
  .divider {
    margin: 0 12px;
    color: #e4e7ed;
  }
}

.success-message {
  text-align: center;
  padding: 24px 0;
  
  .success-icon {
    font-size: 48px;
    color: #67c23a;
    margin-bottom: 16px;
  }
  
  h3 {
    margin: 0 0 16px 0;
    color: #303133;
    font-size: 20px;
  }
  
  p {
    margin: 0 0 12px 0;
    color: #606266;
    line-height: 1.5;
    
    strong {
      color: #409eff;
    }
  }
  
  .resend-section {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #e4e7ed;
    
    p {
      margin-bottom: 8px;
      color: #909399;
    }
  }
}

// 响应式设计
@media (max-width: 480px) {
  .forgot-password-card {
    width: 90vw;
    padding: 24px;
  }
  
  .forgot-password-header {
    h1 {
      font-size: 24px;
    }
  }
}
</style>