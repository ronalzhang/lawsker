export interface Task {
  id: string
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  type: 'consultation' | 'contract_review' | 'litigation' | 'document_draft' | 'other'
  amount: number
  currency: string
  deadline?: string
  created_at: string
  updated_at: string
  
  // 关联用户
  client: {
    id: string
    name: string
    avatar?: string
    phone?: string
    email?: string
  }
  
  lawyer?: {
    id: string
    name: string
    avatar?: string
    rating?: number
    specialties?: string[]
  }
  
  // 任务详情
  requirements?: string
  attachments?: TaskAttachment[]
  tags?: string[]
  location?: string
  
  // 进度信息
  progress?: number
  milestones?: TaskMilestone[]
  
  // 统计信息
  view_count?: number
  application_count?: number
  
  // 评价信息
  rating?: number
  review?: string
  review_date?: string
}

export interface TaskAttachment {
  id: string
  name: string
  url: string
  size: number
  type: string
  uploaded_at: string
}

export interface TaskMilestone {
  id: string
  title: string
  description?: string
  status: 'pending' | 'completed'
  due_date?: string
  completed_at?: string
}

export interface TaskApplication {
  id: string
  task_id: string
  lawyer_id: string
  lawyer: {
    id: string
    name: string
    avatar?: string
    rating?: number
    experience_years?: number
    specialties?: string[]
  }
  proposal: string
  quoted_amount: number
  estimated_duration: number
  status: 'pending' | 'accepted' | 'rejected'
  applied_at: string
  responded_at?: string
}

export interface TaskFilter {
  status?: string[]
  type?: string[]
  priority?: string[]
  amount_min?: number
  amount_max?: number
  location?: string
  keyword?: string
  date_range?: [string, string]
}

export interface TaskStats {
  total: number
  pending: number
  in_progress: number
  completed: number
  cancelled: number
  total_amount: number
  avg_amount: number
}

export interface CreateTaskForm {
  title: string
  description: string
  type: string
  amount: number
  currency: string
  deadline?: string
  requirements?: string
  location?: string
  tags?: string[]
  attachments?: File[]
}

export interface UpdateTaskForm {
  title?: string
  description?: string
  status?: string
  priority?: string
  amount?: number
  deadline?: string
  requirements?: string
  location?: string
  tags?: string[]
  progress?: number
}