import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.locale('zh-cn')
dayjs.extend(relativeTime)

/**
 * 格式化日期
 * @param date 日期
 * @param format 格式
 * @returns 格式化后的日期字符串
 */
export function formatDate(date: string | Date, format = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return ''
  return dayjs(date).format(format)
}

/**
 * 格式化相对时间
 * @param date 日期
 * @returns 相对时间字符串
 */
export function formatRelativeTime(date: string | Date): string {
  if (!date) return ''
  return dayjs(date).fromNow()
}

/**
 * 格式化金额
 * @param amount 金额
 * @param currency 货币符号
 * @returns 格式化后的金额字符串
 */
export function formatAmount(amount: number | string, currency = '¥'): string {
  if (amount === null || amount === undefined || amount === '') return ''
  
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) return ''
  
  return `${currency}${num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`
}

/**
 * 格式化文件大小
 * @param size 文件大小（字节）
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(size: number): string {
  if (!size || size === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const index = Math.floor(Math.log(size) / Math.log(1024))
  const value = size / Math.pow(1024, index)
  
  return `${value.toFixed(2)} ${units[index]}`
}

/**
 * 格式化手机号
 * @param phone 手机号
 * @returns 格式化后的手机号
 */
export function formatPhone(phone: string): string {
  if (!phone) return ''
  
  // 移除所有非数字字符
  const cleaned = phone.replace(/\D/g, '')
  
  // 中国手机号格式化
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return cleaned.replace(/(\d{3})(\d{4})(\d{4})/, '$1 $2 $3')
  }
  
  return phone
}

/**
 * 格式化身份证号
 * @param idCard 身份证号
 * @param mask 是否脱敏
 * @returns 格式化后的身份证号
 */
export function formatIdCard(idCard: string, mask = true): string {
  if (!idCard) return ''
  
  if (mask && idCard.length >= 8) {
    return idCard.replace(/(\d{4})\d*(\d{4})/, '$1****$2')
  }
  
  return idCard
}

/**
 * 格式化银行卡号
 * @param cardNumber 银行卡号
 * @param mask 是否脱敏
 * @returns 格式化后的银行卡号
 */
export function formatBankCard(cardNumber: string, mask = true): string {
  if (!cardNumber) return ''
  
  // 移除所有非数字字符
  const cleaned = cardNumber.replace(/\D/g, '')
  
  if (mask && cleaned.length >= 8) {
    const first = cleaned.slice(0, 4)
    const last = cleaned.slice(-4)
    const middle = '*'.repeat(cleaned.length - 8)
    return `${first}${middle}${last}`.replace(/(.{4})/g, '$1 ').trim()
  }
  
  // 每4位添加空格
  return cleaned.replace(/(.{4})/g, '$1 ').trim()
}

/**
 * 格式化百分比
 * @param value 数值
 * @param decimals 小数位数
 * @returns 格式化后的百分比字符串
 */
export function formatPercentage(value: number, decimals = 2): string {
  if (value === null || value === undefined || isNaN(value)) return ''
  
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 格式化数字
 * @param value 数值
 * @param decimals 小数位数
 * @returns 格式化后的数字字符串
 */
export function formatNumber(value: number, decimals = 0): string {
  if (value === null || value === undefined || isNaN(value)) return ''
  
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * 截断文本
 * @param text 文本
 * @param length 最大长度
 * @param suffix 后缀
 * @returns 截断后的文本
 */
export function truncateText(text: string, length = 50, suffix = '...'): string {
  if (!text) return ''
  
  if (text.length <= length) return text
  
  return text.slice(0, length) + suffix
}

/**
 * 高亮搜索关键词
 * @param text 文本
 * @param keyword 关键词
 * @param className CSS类名
 * @returns 高亮后的HTML字符串
 */
export function highlightKeyword(text: string, keyword: string, className = 'highlight'): string {
  if (!text || !keyword) return text
  
  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, `<span class="${className}">$1</span>`)
}

/**
 * 格式化地址
 * @param address 地址对象
 * @returns 格式化后的地址字符串
 */
export function formatAddress(address: {
  province?: string
  city?: string
  district?: string
  detail?: string
}): string {
  if (!address) return ''
  
  const parts = [
    address.province,
    address.city,
    address.district,
    address.detail
  ].filter(Boolean)
  
  return parts.join('')
}

/**
 * 格式化时长
 * @param seconds 秒数
 * @returns 格式化后的时长字符串
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '0秒'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60
  
  const parts = []
  if (hours > 0) parts.push(`${hours}小时`)
  if (minutes > 0) parts.push(`${minutes}分钟`)
  if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds}秒`)
  
  return parts.join('')
}