import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Task, TaskFilter, TaskStats, CreateTaskForm, UpdateTaskForm } from '@/types/task'
import { taskApi } from '@/api/task'
import { ElMessage } from 'element-plus'

export const useTaskStore = defineStore('task', () => {
  // 状态
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const stats = ref<TaskStats>({
    total: 0,
    pending: 0,
    in_progress: 0,
    completed: 0,
    cancelled: 0,
    total_amount: 0,
    avg_amount: 0
  })
  
  const loading = ref(false)
  const pagination = ref({
    current: 1,
    size: 10,
    total: 0
  })
  
  const filter = ref<TaskFilter>({})

  // 计算属性
  const pendingTasks = computed(() => 
    tasks.value.filter(task => task.status === 'pending')
  )
  
  const inProgressTasks = computed(() => 
    tasks.value.filter(task => task.status === 'in_progress')
  )
  
  const completedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'completed')
  )

  // 动作
  const fetchTasks = async (params?: {
    page?: number
    size?: number
    filter?: TaskFilter
  }) => {
    loading.value = true
    try {
      const response = await taskApi.getTasks(params)
      const { data, pagination: paginationData } = response.data
      
      tasks.value = data
      pagination.value = {
        current: paginationData.current,
        size: paginationData.size,
        total: paginationData.total
      }
      
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '获取任务列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchTask = async (id: string) => {
    loading.value = true
    try {
      const response = await taskApi.getTask(id)
      currentTask.value = response.data
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '获取任务详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createTask = async (data: CreateTaskForm) => {
    loading.value = true
    try {
      const response = await taskApi.createTask(data)
      tasks.value.unshift(response.data)
      ElMessage.success('任务创建成功')
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '创建任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateTask = async (id: string, data: UpdateTaskForm) => {
    loading.value = true
    try {
      const response = await taskApi.updateTask(id, data)
      
      // 更新列表中的任务
      const index = tasks.value.findIndex(task => task.id === id)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      
      // 更新当前任务
      if (currentTask.value?.id === id) {
        currentTask.value = response.data
      }
      
      ElMessage.success('任务更新成功')
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '更新任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteTask = async (id: string) => {
    loading.value = true
    try {
      await taskApi.deleteTask(id)
      
      // 从列表中移除
      const index = tasks.value.findIndex(task => task.id === id)
      if (index !== -1) {
        tasks.value.splice(index, 1)
      }
      
      // 清除当前任务
      if (currentTask.value?.id === id) {
        currentTask.value = null
      }
      
      ElMessage.success('任务删除成功')
    } catch (error: any) {
      ElMessage.error(error.message || '删除任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchMyTasks = async (params?: {
    page?: number
    size?: number
    status?: string
    role?: 'client' | 'lawyer'
  }) => {
    loading.value = true
    try {
      const response = await taskApi.getMyTasks(params)
      const { data, pagination: paginationData } = response.data
      
      tasks.value = data
      pagination.value = {
        current: paginationData.current,
        size: paginationData.size,
        total: paginationData.total
      }
      
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '获取我的任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchTaskStats = async () => {
    try {
      const response = await taskApi.getTaskStats()
      stats.value = response.data
      return response
    } catch (error: any) {
      console.error('获取任务统计失败:', error)
      throw error
    }
  }

  const applyTask = async (taskId: string, data: {
    proposal: string
    quoted_amount: number
    estimated_duration: number
  }) => {
    loading.value = true
    try {
      const response = await taskApi.applyTask(taskId, data)
      ElMessage.success('申请提交成功')
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '申请任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const completeTask = async (id: string) => {
    loading.value = true
    try {
      const response = await taskApi.completeTask(id)
      
      // 更新任务状态
      const index = tasks.value.findIndex(task => task.id === id)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      
      if (currentTask.value?.id === id) {
        currentTask.value = response.data
      }
      
      ElMessage.success('任务已完成')
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '完成任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const cancelTask = async (id: string, reason?: string) => {
    loading.value = true
    try {
      const response = await taskApi.cancelTask(id, reason)
      
      // 更新任务状态
      const index = tasks.value.findIndex(task => task.id === id)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      
      if (currentTask.value?.id === id) {
        currentTask.value = response.data
      }
      
      ElMessage.success('任务已取消')
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '取消任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const rateTask = async (id: string, data: {
    rating: number
    review: string
  }) => {
    loading.value = true
    try {
      await taskApi.rateTask(id, data)
      
      // 更新任务评价信息
      const task = tasks.value.find(t => t.id === id)
      if (task) {
        task.rating = data.rating
        task.review = data.review
        task.review_date = new Date().toISOString()
      }
      
      if (currentTask.value?.id === id) {
        currentTask.value.rating = data.rating
        currentTask.value.review = data.review
        currentTask.value.review_date = new Date().toISOString()
      }
      
      ElMessage.success('评价提交成功')
    } catch (error: any) {
      ElMessage.error(error.message || '提交评价失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const searchTasks = async (params: {
    keyword: string
    page?: number
    size?: number
    filter?: TaskFilter
  }) => {
    loading.value = true
    try {
      const response = await taskApi.searchTasks(params)
      const { data, pagination: paginationData } = response.data
      
      tasks.value = data
      pagination.value = {
        current: paginationData.current,
        size: paginationData.size,
        total: paginationData.total
      }
      
      return response
    } catch (error: any) {
      ElMessage.error(error.message || '搜索任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const setFilter = (newFilter: TaskFilter) => {
    filter.value = { ...newFilter }
  }

  const clearFilter = () => {
    filter.value = {}
  }

  const resetTasks = () => {
    tasks.value = []
    currentTask.value = null
    pagination.value = {
      current: 1,
      size: 10,
      total: 0
    }
  }

  return {
    // 状态
    tasks: readonly(tasks),
    currentTask: readonly(currentTask),
    stats: readonly(stats),
    loading: readonly(loading),
    pagination: readonly(pagination),
    filter: readonly(filter),
    
    // 计算属性
    pendingTasks,
    inProgressTasks,
    completedTasks,
    
    // 动作
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    deleteTask,
    fetchMyTasks,
    fetchTaskStats,
    applyTask,
    completeTask,
    cancelTask,
    rateTask,
    searchTasks,
    setFilter,
    clearFilter,
    resetTasks
  }
})