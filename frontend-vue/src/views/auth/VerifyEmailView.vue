<template>
  <div class="verify-email-container">
    <div class="verify-email-card">
      <div class="verify-email-header">
        <el-icon class="email-icon"><Message /></el-icon>
        <h1>验证邮箱地址</h1>
        <p v-if="!isVerifying && !verificationResult">
          我们已向 <strong>{{ userStore.user?.email }}</strong> 发送了验证邮件
        </p>
      </div>
      
      <!-- 验证中状态 -->
      <div v-if="isVerifying" class="verifying-state">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>正在验证您的邮箱...</p>
      </div>
      
      <!-- 验证成功 -->
      <div v-else-if="verificationResult === 'success'" class="success-state">
        <el-icon class="success-icon"><CircleCheck /></el-icon>
        <h3>邮箱验证成功</h3>
        <p>您的邮箱地址已成功验证</p>
        
        <lk-button
          type="primary"
          @click="$router.push('/dashboard')"
        >
          继续使用
        </lk-button>
      </div>
      
      <!-- 验证失败 -->
      <div v-else-if="verificationResult === 'failed'" class="failed-state">
        <el-icon class="error-icon"><CircleClose /></el-icon>
        <h3>验证失败</h3>
        <p>验证链接已过期或无效，请重新发送验证邮件</p>
        
        <lk-button
          type="primary"
          :loading="userStore.loading"
          @click="handleResendVerification"
        >
          重新发送验证邮件
        </lk-button>
      </div>
      
      <!-- 默认状态 -->
      <div v-else class="default-state">
        <div class="verification-tips">
          <h3>请检查您的邮箱</h3>
          <ul>
            <li>点击邮件中的验证链接完成验证</li>
            <li>如果没有收到邮件，请检查垃圾邮件文件夹</li>
            <li>验证链接有效期为24小时</li>
          </ul>
        </div>
        
        <div class="verification-actions">
          <lk-button
            :loading="userStore.loading"
            :disabled="resendCountdown > 0"
            @click="handleResendVerification"
          >
            {{ resendCountdown > 0 ? `${resendCountdown}秒后可重发` : '重新发送验证邮件' }}
          </lk-button>
          
          <lk-button
            type="text"
            @click="handleSkipVerification"
          >
            暂时跳过
          </lk-button>
        </div>
        
        <div class="change-email">
          <p>邮箱地址有误？</p>
          <el-link type="primary" @click="showChangeEmailDialog = true">
            更换邮箱地址
          </el-link>
        </div>
      </div>
    </div>
    
    <!-- 更换邮箱对话框 -->
    <lk-modal
      v-model="showChangeEmailDialog"
      title="更换邮箱地址"
      show-default-footer
      :confirm-loading="changingEmail"
      @confirm="handleChangeEmail"
      @cancel="showChangeEmailDialog = false"
    >
      <lk-form
        ref="emailFormRef"
        :model="emailForm"
        :rules="emailRules"
        label-width="80px"
      >
        <el-form-item label="新邮箱" prop="email">
          <el-input
            v-model="emailForm.email"
            placeholder="请输入新的邮箱地址"
            prefix-icon="Message"
          />
        </el-form-item>
      </lk-form>
    </lk-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElIcon, ElLink } from 'element-plus'
import { Message, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { LkButton, LkModal, LkForm } from '@/components'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isVerifying = ref(false)
const verificationResult = ref<'success' | 'failed' | null>(null)
const resendCountdown = ref(0)
const showChangeEmailDialog = ref(false)
const changingEmail = ref(false)
let countdownTimer: NodeJS.Timeout | null = null

const emailFormRef = ref<FormInstance>()
const emailForm = reactive({
  email: ''
})

const emailRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const handleResendVerification = async () => {
  if (resendCountdown.value > 0) return
  
  try {
    await userStore.sendEmailVerification()
    startResendCountdown()
  } catch (error) {
    console.error('Failed to resend verification email:', error)
  }
}

const handleSkipVerification = () => {
  ElMessage.warning('建议您尽快完成邮箱验证以确保账户安全')
  router.push('/dashboard')
}

const handleChangeEmail = async () => {
  if (!emailFormRef.value) return
  
  await emailFormRef.value.validate(async (valid) => {
    if (valid) {
      changingEmail.value = true
      try {
        await userStore.updateProfile({ email: emailForm.email })
        showChangeEmailDialog.value = false
        emailForm.email = ''
        ElMessage.success('邮箱地址已更新，请查收验证邮件')
      } catch (error) {
        console.error('Failed to change email:', error)
      } finally {
        changingEmail.value = false
      }
    }
  })
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

const verifyEmailToken = async (token: string) => {
  isVerifying.value = true
  try {
    await userStore.verifyEmail(token)
    verificationResult.value = 'success'
  } catch (error) {
    verificationResult.value = 'failed'
  } finally {
    isVerifying.value = false
  }
}

onMounted(() => {
  // 检查URL中是否有验证token
  const token = route.query.token as string
  if (token) {
    verifyEmailToken(token)
  } else if (userStore.isEmailVerified) {
    // 如果已经验证过，直接跳转
    router.push('/dashboard')
  }
})

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style lang="scss" scoped>
.verify-email-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.verify-email-card {
  width: 500px;
  max-width: 90vw;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.verify-email-header {
  margin-bottom: 32px;
  
  .email-icon {
    font-size: 48px;
    color: #409eff;
    margin-bottom: 16px;
  }
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 12px 0;
  }
  
  p {
    color: #606266;
    margin: 0;
    line-height: 1.5;
    
    strong {
      color: #409eff;
    }
  }
}

.verifying-state {
  padding: 40px 0;
  
  .loading-icon {
    font-size: 48px;
    color: #409eff;
    margin-bottom: 16px;
    animation: rotating 2s linear infinite;
  }
  
  p {
    color: #606266;
    margin: 0;
  }
}

.success-state,
.failed-state {
  padding: 20px 0;
  
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
    margin: 0 0 12px 0;
    color: #303133;
    font-size: 18px;
  }
  
  p {
    margin: 0 0 24px 0;
    color: #606266;
    line-height: 1.5;
  }
}

.default-state {
  .verification-tips {
    margin-bottom: 32px;
    text-align: left;
    
    h3 {
      margin: 0 0 16px 0;
      color: #303133;
      font-size: 18px;
      text-align: center;
    }
    
    ul {
      margin: 0;
      padding-left: 20px;
      color: #606266;
      line-height: 1.6;
      
      li {
        margin-bottom: 8px;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
  
  .verification-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 24px;
  }
  
  .change-email {
    padding-top: 24px;
    border-top: 1px solid #e4e7ed;
    
    p {
      margin: 0 0 8px 0;
      color: #909399;
      font-size: 14px;
    }
  }
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .verify-email-card {
    padding: 24px;
  }
  
  .verification-actions {
    .lk-button {
      width: 100%;
    }
  }
}
</style>