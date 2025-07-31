import request from '@/utils/request'
import type { 
  Task, 
  TaskFilter, 
  TaskStats, 
  CreateTaskForm, 
  UpdateTaskForm,
  TaskApplication 
} from '@/types/task'
import type { ApiResponse, PaginatedResponse } from '@/types/api'

export const taskApi = {
  // 获取任务列表
  getTasks(params?: {
    page?: number
    size?: number
    filter?: TaskFilter
  }): Promise<ApiResponse<PaginatedResponse<Task>>> {
    return request({
      url: '/tasks',
      method: 'get',
      params
    })
  },

  // 获取任务详情
  getTask(id: string): Promise<ApiResponse<Task>> {
    return request({
      url: `/tasks/${id}`,
      method: 'get'
    })
  },

  // 创建任务
  createTask(data: CreateTaskForm): Promise<ApiResponse<Task>> {
    return request({
      url: '/tasks',
      method: 'post',
      data
    })
  },

  // 更新任务
  updateTask(id: string, data: UpdateTaskForm): Promise<ApiResponse<Task>> {
    return request({
      url: `/tasks/${id}`,
      method: 'put',
      data
    })
  },

  // 删除任务
  deleteTask(id: string): Promise<ApiResponse> {
    return request({
      url: `/tasks/${id}`,
      method: 'delete'
    })
  },

  // 获取我的任务
  getMyTasks(params?: {
    page?: number
    size?: number
    status?: string
    role?: 'client' | 'lawyer'
  }): Promise<ApiResponse<PaginatedResponse<Task>>> {
    return request({
      url: '/tasks/my',
      method: 'get',
      params
    })
  },

  // 获取任务统计
  getTaskStats(): Promise<ApiResponse<TaskStats>> {
    return request({
      url: '/tasks/stats',
      method: 'get'
    })
  },

  // 申请任务（律师）
  applyTask(taskId: string, data: {
    proposal: string
    quoted_amount: number
    estimated_duration: number
  }): Promise<ApiResponse<TaskApplication>> {
    return request({
      url: `/tasks/${taskId}/apply`,
      method: 'post',
      data
    })
  },

  // 获取任务申请列表
  getTaskApplications(taskId: string): Promise<ApiResponse<TaskApplication[]>> {
    return request({
      url: `/tasks/${taskId}/applications`,
      method: 'get'
    })
  },

  // 接受申请
  acceptApplication(taskId: string, applicationId: string): Promise<ApiResponse> {
    return request({
      url: `/tasks/${taskId}/applications/${applicationId}/accept`,
      method: 'post'
    })
  },

  // 拒绝申请
  rejectApplication(taskId: string, applicationId: string, reason?: string): Promise<ApiResponse> {
    return request({
      url: `/tasks/${taskId}/applications/${applicationId}/reject`,
      method: 'post',
      data: { reason }
    })
  },

  // 完成任务
  completeTask(id: string): Promise<ApiResponse<Task>> {
    return request({
      url: `/tasks/${id}/complete`,
      method: 'post'
    })
  },

  // 取消任务
  cancelTask(id: string, reason?: string): Promise<ApiResponse<Task>> {
    return request({
      url: `/tasks/${id}/cancel`,
      method: 'post',
      data: { reason }
    })
  },

  // 评价任务
  rateTask(id: string, data: {
    rating: number
    review: string
  }): Promise<ApiResponse> {
    return request({
      url: `/tasks/${id}/rate`,
      method: 'post',
      data
    })
  },

  // 上传附件
  uploadAttachment(taskId: string, file: File): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData()
    formData.append('file', file)
    
    return request({
      url: `/tasks/${taskId}/attachments`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除附件
  deleteAttachment(taskId: string, attachmentId: string): Promise<ApiResponse> {
    return request({
      url: `/tasks/${taskId}/attachments/${attachmentId}`,
      method: 'delete'
    })
  },

  // 获取推荐任务
  getRecommendedTasks(params?: {
    page?: number
    size?: number
  }): Promise<ApiResponse<PaginatedResponse<Task>>> {
    return request({
      url: '/tasks/recommended',
      method: 'get',
      params
    })
  },

  // 搜索任务
  searchTasks(params: {
    keyword: string
    page?: number
    size?: number
    filter?: TaskFilter
  }): Promise<ApiResponse<PaginatedResponse<Task>>> {
    return request({
      url: '/tasks/search',
      method: 'get',
      params
    })
  }
}