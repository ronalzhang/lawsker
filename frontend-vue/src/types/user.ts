export interface User {
  id: string
  username: string
  email: string
  phone?: string
  role: 'user' | 'lawyer' | 'institution' | 'admin'
  status: 'active' | 'inactive' | 'pending'
  avatar?: string
  real_name?: string
  created_at: string
  updated_at: string
  
  // 律师特有字段
  lawyer_license?: string
  law_firm?: string
  practice_areas?: string[]
  experience_years?: number
  certification_status?: 'pending' | 'approved' | 'rejected'
  
  // 机构特有字段
  institution_name?: string
  institution_type?: string
  business_license?: string
  contact_person?: string
}

export interface LoginForm {
  username: string
  password: string
  remember?: boolean
}

export interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  phone?: string
  role: 'user' | 'lawyer' | 'institution'
  real_name?: string
  
  // 律师注册字段
  licenseNumber?: string
  experience?: string
  specialties?: string[]
  
  // 机构注册字段
  institutionName?: string
  creditCode?: string
  address?: string
}

export interface ChangePasswordForm {
  old_password: string
  new_password: string
  confirm_password: string
}

export interface UserProfile {
  real_name?: string
  phone?: string
  avatar?: string
  bio?: string
  
  // 律师资料
  law_firm?: string
  practice_areas?: string[]
  experience_years?: number
  
  // 机构资料
  institution_name?: string
  institution_type?: string
  contact_person?: string
}