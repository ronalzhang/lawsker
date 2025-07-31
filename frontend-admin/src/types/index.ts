// 通用API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    current: number
    size: number
    total: number
    pages: number
  }
}

// 用户类型
export interface AdminUser {
  id: string
  username: string
  email: string
  role: 'super_admin' | 'admin' | 'operator'
  status: 'active' | 'inactive'
  avatar?: string
  last_login?: string
  created_at: string
  permissions: string[]
}

// 统计数据类型
export interface DashboardStats {
  users: {
    total: number
    active: number
    new_today: number
    growth_rate: number
  }
  lawyers: {
    total: number
    verified: number
    pending: number
    growth_rate: number
  }
  cases: {
    total: number
    pending: number
    in_progress: number
    completed: number
    growth_rate: number
  }
  revenue: {
    total: number
    today: number
    this_month: number
    growth_rate: number
  }
}

// 图表数据类型
export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
  }[]
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'stats_update' | 'alert' | 'notification'
  data: any
  timestamp: string
}

// 访问数据分析类型
export interface AccessAnalytics {
  pageViews: {
    total: number
    unique: number
    bounce_rate: number
    avg_session_duration: number
  }
  topPages: Array<{
    path: string
    views: number
    unique_views: number
    bounce_rate: number
  }>
  geoDistribution: Array<{
    country: string
    region: string
    city: string
    count: number
    percentage: number
  }>
  deviceStats: {
    desktop: number
    mobile: number
    tablet: number
  }
  browserStats: Array<{
    name: string
    version: string
    count: number
    percentage: number
  }>
  trafficSources: Array<{
    source: string
    medium: string
    count: number
    percentage: number
  }>
}

// IP分析数据类型
export interface IpAnalysis {
  topIps: Array<{
    ip: string
    country: string
    city: string
    requests: number
    last_seen: string
    is_suspicious: boolean
  }>
  geoData: Array<{
    country: string
    country_code: string
    latitude: number
    longitude: number
    count: number
  }>
}

// 用户路径分析类型
export interface UserPathAnalysis {
  commonPaths: Array<{
    path: string[]
    count: number
    conversion_rate: number
  }>
  entryPages: Array<{
    page: string
    count: number
    bounce_rate: number
  }>
  exitPages: Array<{
    page: string
    count: number
    exit_rate: number
  }>
}

// 用户管理分析类型
export interface UserManagementAnalytics {
  userRegistration: {
    total: number
    today: number
    this_week: number
    this_month: number
    growth_rate: number
  }
  userActivity: {
    active_users: number
    inactive_users: number
    new_users_retention: number
    avg_session_duration: number
  }
  lawyerCertification: {
    total_lawyers: number
    verified: number
    pending: number
    rejected: number
    verification_rate: number
  }
  userBehavior: Array<{
    action: string
    count: number
    percentage: number
    avg_duration: number
  }>
}

// 用户注册趋势数据
export interface UserRegistrationTrend {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
  }>
}

// 律师认证状态数据
export interface LawyerCertificationData {
  id: string
  name: string
  email: string
  phone: string
  license_number: string
  status: 'pending' | 'verified' | 'rejected'
  submitted_at: string
  reviewed_at?: string
  reviewer?: string
  rejection_reason?: string
  documents: Array<{
    type: string
    url: string
    status: 'pending' | 'approved' | 'rejected'
  }>
}

// 用户活跃度数据
export interface UserActivityData {
  user_id: string
  username: string
  email: string
  last_login: string
  login_count: number
  session_duration: number
  page_views: number
  actions_count: number
  activity_score: number
  status: 'active' | 'inactive' | 'dormant'
}

// 用户行为轨迹数据
export interface UserBehaviorTrace {
  user_id: string
  username: string
  actions: Array<{
    action: string
    page: string
    timestamp: string
    duration: number
    details?: any
  }>
  session_info: {
    start_time: string
    end_time: string
    duration: number
    page_count: number
    device: string
    browser: string
  }
}

// 业绩排行系统类型
export interface PerformanceRanking {
  lawyerRanking: Array<{
    lawyer_id: string
    name: string
    avatar?: string
    total_revenue: number
    cases_completed: number
    client_rating: number
    response_time: number
    rank: number
    rank_change: number
    growth_rate: number
  }>
  userConsumption: Array<{
    user_id: string
    username: string
    avatar?: string
    total_spent: number
    cases_count: number
    avg_case_value: number
    last_payment: string
    rank: number
    rank_change: number
    loyalty_score: number
  }>
  platformRevenue: {
    total_revenue: number
    lawyer_fees: number
    platform_commission: number
    growth_rate: number
    monthly_trend: Array<{
      month: string
      revenue: number
      commission: number
      cases: number
    }>
  }
}

// 业绩对比数据
export interface PerformanceComparison {
  period: string
  lawyers: Array<{
    lawyer_id: string
    name: string
    current_revenue: number
    previous_revenue: number
    growth_rate: number
    cases_current: number
    cases_previous: number
    rating_current: number
    rating_previous: number
  }>
  categories: Array<{
    category: string
    current_value: number
    previous_value: number
    growth_rate: number
  }>
}

// 趋势预测数据
export interface TrendPrediction {
  revenue_forecast: Array<{
    date: string
    actual?: number
    predicted: number
    confidence_interval: {
      lower: number
      upper: number
    }
  }>
  lawyer_performance_forecast: Array<{
    lawyer_id: string
    name: string
    predicted_revenue: number
    predicted_cases: number
    confidence_score: number
  }>
  market_trends: Array<{
    indicator: string
    current_value: number
    predicted_value: number
    trend_direction: 'up' | 'down' | 'stable'
    impact_score: number
  }>
}