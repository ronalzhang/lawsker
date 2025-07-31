<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h1>注册 Lawsker</h1>
        <p>加入法律服务O2O平台</p>
      </div>
      
      <el-steps :active="currentStep" align-center class="register-steps">
        <el-step title="基本信息" />
        <el-step title="身份选择" />
        <el-step title="完成注册" />
      </el-steps>
      
      <!-- 步骤1: 基本信息 -->
      <div v-if="currentStep === 0" class="step-content">
        <lk-form
          ref="basicFormRef"
          :model="registerForm"
          :rules="basicRules"
          label-width="80px"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              size="large"
              prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱地址"
              size="large"
              prefix-icon="Message"
            />
          </el-form-item>
          
          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="registerForm.phone"
              placeholder="请输入手机号"
              size="large"
              prefix-icon="Phone"
            />
          </el-form-item>
          
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
        </lk-form>
      </div>
      
      <!-- 步骤2: 身份选择 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="role-selection">
          <h3>请选择您的身份</h3>
          <div class="role-cards">
            <div
              class="role-card"
              :class="{ active: registerForm.role === 'user' }"
              @click="selectRole('user')"
            >
              <el-icon class="role-icon"><User /></el-icon>
              <h4>普通用户</h4>
              <p>寻求法律服务和咨询</p>
            </div>
            
            <div
              class="role-card"
              :class="{ active: registerForm.role === 'lawyer' }"
              @click="selectRole('lawyer')"
            >
              <el-icon class="role-icon"><UserFilled /></el-icon>
              <h4>律师</h4>
              <p>提供专业法律服务</p>
            </div>
            
            <div
              class="role-card"
              :class="{ active: registerForm.role === 'institution' }"
              @click="selectRole('institution')"
            >
              <el-icon class="role-icon"><OfficeBuilding /></el-icon>
              <h4>法律机构</h4>
              <p>法律服务机构或律所</p>
            </div>
          </div>
        </div>
        
        <!-- 律师额外信息 -->
        <div v-if="registerForm.role === 'lawyer'" class="lawyer-info">
          <lk-form
            ref="lawyerFormRef"
            :model="registerForm"
            :rules="lawyerRules"
            label-width="100px"
          >
            <el-form-item label="执业证号" prop="licenseNumber">
              <el-input
                v-model="registerForm.licenseNumber"
                placeholder="请输入律师执业证号"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="执业年限" prop="experience">
              <el-select
                v-model="registerForm.experience"
                placeholder="请选择执业年限"
                size="large"
                style="width: 100%"
              >
                <el-option label="1年以下" value="0-1" />
                <el-option label="1-3年" value="1-3" />
                <el-option label="3-5年" value="3-5" />
                <el-option label="5-10年" value="5-10" />
                <el-option label="10年以上" value="10+" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="专业领域" prop="specialties">
              <el-select
                v-model="registerForm.specialties"
                placeholder="请选择专业领域"
                size="large"
                multiple
                style="width: 100%"
              >
                <el-option label="民事纠纷" value="civil" />
                <el-option label="刑事辩护" value="criminal" />
                <el-option label="商事纠纷" value="commercial" />
                <el-option label="行政诉讼" value="administrative" />
                <el-option label="知识产权" value="intellectual" />
                <el-option label="劳动争议" value="labor" />
                <el-option label="婚姻家庭" value="family" />
                <el-option label="房产纠纷" value="property" />
              </el-select>
            </el-form-item>
          </lk-form>
        </div>
        
        <!-- 机构额外信息 -->
        <div v-if="registerForm.role === 'institution'" class="institution-info">
          <lk-form
            ref="institutionFormRef"
            :model="registerForm"
            :rules="institutionRules"
            label-width="100px"
          >
            <el-form-item label="机构名称" prop="institutionName">
              <el-input
                v-model="registerForm.institutionName"
                placeholder="请输入机构名称"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="统一社会信用代码" prop="creditCode">
              <el-input
                v-model="registerForm.creditCode"
                placeholder="请输入统一社会信用代码"
                size="large"
              />
            </el-form-item>
            
            <el-form-item label="机构地址" prop="address">
              <el-input
                v-model="registerForm.address"
                placeholder="请输入机构地址"
                size="large"
              />
            </el-form-item>
          </lk-form>
        </div>
      </div>
      
      <!-- 步骤3: 完成注册 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="register-summary">
          <h3>注册信息确认</h3>
          <div class="summary-item">
            <label>用户名：</label>
            <span>{{ registerForm.username }}</span>
          </div>
          <div class="summary-item">
            <label>邮箱：</label>
            <span>{{ registerForm.email }}</span>
          </div>
          <div class="summary-item">
            <label>手机号：</label>
            <span>{{ registerForm.phone }}</span>
          </div>
          <div class="summary-item">
            <label>身份：</label>
            <span>{{ getRoleText(registerForm.role) }}</span>
          </div>
          
          <div class="terms-agreement">
            <el-checkbox v-model="agreeTerms">
              我已阅读并同意
              <el-link type="primary" @click="showTerms">《用户协议》</el-link>
              和
              <el-link type="primary" @click="showPrivacy">《隐私政策》</el-link>
            </el-checkbox>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="register-actions">
        <lk-button
          v-if="currentStep > 0"
          @click="prevStep"
        >
          上一步
        </lk-button>
        
        <lk-button
          v-if="currentStep < 2"
          type="primary"
          @click="nextStep"
        >
          下一步
        </lk-button>
        
        <lk-button
          v-if="currentStep === 2"
          type="primary"
          :loading="userStore.loading"
          :disabled="!agreeTerms"
          @click="handleRegister"
        >
          完成注册
        </lk-button>
      </div>
      
      <div class="register-footer">
        <span>已有账号？</span>
        <el-link type="primary" @click="$router.push('/login')">
          立即登录
        </el-link>
      </div>
    </div>
    
    <!-- 条款弹窗 -->
    <lk-modal
      v-model="termsVisible"
      title="用户协议"
      width="60%"
    >
      <div class="terms-content">
        <p>这里是用户协议的内容...</p>
      </div>
    </lk-modal>
    
    <lk-modal
      v-model="privacyVisible"
      title="隐私政策"
      width="60%"
    >
      <div class="privacy-content">
        <p>这里是隐私政策的内容...</p>
      </div>
    </lk-modal>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElSteps, ElStep, ElIcon, ElSelect, ElOption, ElCheckbox, ElLink } from 'element-plus'
import { User, UserFilled, OfficeBuilding } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { LkForm, LkButton, LkModal } from '@/components'
import type { FormInstance, FormRules } from 'element-plus'
import type { RegisterForm } from '@/types/user'

const router = useRouter()
const userStore = useUserStore()

const currentStep = ref(0)
const agreeTerms = ref(false)
const termsVisible = ref(false)
const privacyVisible = ref(false)

const basicFormRef = ref<FormInstance>()
const lawyerFormRef = ref<FormInstance>()
const institutionFormRef = ref<FormInstance>()

const registerForm = reactive<RegisterForm>({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
  role: 'user',
  licenseNumber: '',
  experience: '',
  specialties: [],
  institutionName: '',
  creditCode: '',
  address: ''
})

// 基本信息验证规则
const basicRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 律师信息验证规则
const lawyerRules: FormRules = {
  licenseNumber: [
    { required: true, message: '请输入律师执业证号', trigger: 'blur' }
  ],
  experience: [
    { required: true, message: '请选择执业年限', trigger: 'change' }
  ],
  specialties: [
    { required: true, message: '请选择专业领域', trigger: 'change' }
  ]
}

// 机构信息验证规则
const institutionRules: FormRules = {
  institutionName: [
    { required: true, message: '请输入机构名称', trigger: 'blur' }
  ],
  creditCode: [
    { required: true, message: '请输入统一社会信用代码', trigger: 'blur' },
    { pattern: /^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$/, message: '请输入正确的统一社会信用代码', trigger: 'blur' }
  ],
  address: [
    { required: true, message: '请输入机构地址', trigger: 'blur' }
  ]
}

const selectRole = (role: string) => {
  registerForm.role = role
}

const getRoleText = (role: string) => {
  const roleMap = {
    user: '普通用户',
    lawyer: '律师',
    institution: '法律机构'
  }
  return roleMap[role as keyof typeof roleMap] || '未知'
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    // 验证基本信息
    if (!basicFormRef.value) return
    
    const valid = await basicFormRef.value.validate().catch(() => false)
    if (!valid) return
  } else if (currentStep.value === 1) {
    // 验证角色相关信息
    if (registerForm.role === 'lawyer' && lawyerFormRef.value) {
      const valid = await lawyerFormRef.value.validate().catch(() => false)
      if (!valid) return
    } else if (registerForm.role === 'institution' && institutionFormRef.value) {
      const valid = await institutionFormRef.value.validate().catch(() => false)
      if (!valid) return
    }
  }
  
  currentStep.value++
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const handleRegister = async () => {
  try {
    await userStore.register(registerForm)
    router.push('/login')
  } catch (error) {
    console.error('Registration failed:', error)
  }
}

const showTerms = () => {
  termsVisible.value = true
}

const showPrivacy = () => {
  privacyVisible.value = true
}
</script>

<style lang="scss" scoped>
.register-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  width: 600px;
  max-width: 90vw;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
  
  h1 {
    font-size: 28px;
    font-weight: 700;
    color: #303133;
    margin: 0 0 8px 0;
  }
  
  p {
    color: #909399;
    margin: 0;
  }
}

.register-steps {
  margin-bottom: 32px;
}

.step-content {
  margin-bottom: 32px;
  min-height: 300px;
}

.role-selection {
  text-align: center;
  
  h3 {
    margin-bottom: 24px;
    color: #303133;
  }
  
  .role-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  
  .role-card {
    padding: 24px 16px;
    border: 2px solid #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      border-color: #409eff;
      box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
    }
    
    &.active {
      border-color: #409eff;
      background-color: #f0f9ff;
    }
    
    .role-icon {
      font-size: 32px;
      color: #409eff;
      margin-bottom: 12px;
    }
    
    h4 {
      margin: 0 0 8px 0;
      color: #303133;
    }
    
    p {
      margin: 0;
      color: #909399;
      font-size: 14px;
    }
  }
}

.lawyer-info,
.institution-info {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.register-summary {
  .summary-item {
    display: flex;
    margin-bottom: 16px;
    
    label {
      width: 80px;
      color: #606266;
      font-weight: 500;
    }
    
    span {
      color: #303133;
    }
  }
  
  .terms-agreement {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #e4e7ed;
    text-align: center;
  }
}

.register-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
  
  .lk-button {
    min-width: 100px;
  }
}

.register-footer {
  text-align: center;
  color: #909399;
  
  span {
    margin-right: 8px;
  }
}

.terms-content,
.privacy-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
  line-height: 1.6;
}

// 响应式设计
@media (max-width: 768px) {
  .register-card {
    padding: 24px;
  }
  
  .role-cards {
    grid-template-columns: 1fr;
  }
  
  .register-actions {
    flex-direction: column;
    gap: 12px;
    
    .lk-button {
      width: 100%;
    }
  }
}
</style>