export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  success: boolean
}

export interface PaginationParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ListParams extends PaginationParams {
  status?: string
  category?: string
  start_date?: string
  end_date?: string
}

export interface UploadResponse {
  url: string
  filename: string
  size: number
  mime_type: string
}

export interface ErrorResponse {
  code: number
  message: string
  details?: any
}