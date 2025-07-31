import { ElMessage } from 'element-plus'
import type { ECharts } from 'echarts'

export interface ExportOptions {
  filename?: string
  sheetName?: string
  headers?: string[]
  dateFormat?: string
  numberFormat?: string
  includeHeaders?: boolean
  encoding?: string
}

export interface ChartExportOptions {
  filename?: string
  format?: 'png' | 'jpeg' | 'svg' | 'pdf'
  width?: number
  height?: number
  backgroundColor?: string
  pixelRatio?: number
}

/**
 * 数据导出工具类
 */
export class DataExporter {
  /**
   * 导出为CSV格式
   */
  static async exportToCsv<T = any>(
    data: T[],
    options: ExportOptions = {}
  ): Promise<void> {
    try {
      const {
        filename = `export_${this.getTimestamp()}.csv`,
        headers,
        includeHeaders = true,
        encoding = 'utf-8'
      } = options

      if (!data || data.length === 0) {
        ElMessage.warning('没有数据可导出')
        return
      }

      // 获取表头
      const actualHeaders = headers || Object.keys(data[0] as object)
      
      // 构建CSV内容
      let csvContent = ''
      
      // 添加BOM以支持中文
      if (encoding === 'utf-8') {
        csvContent = '\uFEFF'
      }
      
      // 添加表头
      if (includeHeaders) {
        csvContent += actualHeaders.map(header => this.escapeCsvValue(header)).join(',') + '\n'
      }
      
      // 添加数据行
      data.forEach(row => {
        const values = actualHeaders.map(header => {
          const value = (row as any)[header]
          return this.escapeCsvValue(this.formatValue(value, options))
        })
        csvContent += values.join(',') + '\n'
      })
      
      // 下载文件
      this.downloadFile(csvContent, filename, 'text/csv')
      ElMessage.success('CSV导出成功')
    } catch (error) {
      console.error('CSV export failed:', error)
      ElMessage.error('CSV导出失败')
      throw error
    }
  }

  /**
   * 导出为Excel格式
   */
  static async exportToExcel<T = any>(
    data: T[],
    options: ExportOptions = {}
  ): Promise<void> {
    try {
      const XLSX = await import('xlsx')
      
      const {
        filename = `export_${this.getTimestamp()}.xlsx`,
        sheetName = 'Sheet1',
        headers,
        includeHeaders = true
      } = options

      if (!data || data.length === 0) {
        ElMessage.warning('没有数据可导出')
        return
      }

      // 处理数据
      let exportData = data.map(row => {
        const processedRow: any = {}
        Object.keys(row as object).forEach(key => {
          processedRow[key] = this.formatValue((row as any)[key], options)
        })
        return processedRow
      })

      // 如果指定了表头，只导出指定列
      if (headers) {
        exportData = exportData.map(row => {
          const filteredRow: any = {}
          headers.forEach(header => {
            filteredRow[header] = row[header]
          })
          return filteredRow
        })
      }

      // 创建工作表
      const ws = XLSX.utils.json_to_sheet(exportData, {
        header: headers,
        skipHeader: !includeHeaders
      })

      // 设置列宽
      const colWidths = this.calculateColumnWidths(exportData, headers)
      ws['!cols'] = colWidths

      // 创建工作簿
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, sheetName)

      // 导出文件
      XLSX.writeFile(wb, filename)
      ElMessage.success('Excel导出成功')
    } catch (error) {
      console.error('Excel export failed:', error)
      ElMessage.error('Excel导出失败，请确保已安装xlsx库')
      throw error
    }
  }

  /**
   * 导出为JSON格式
   */
  static async exportToJson<T = any>(
    data: T[],
    options: ExportOptions = {}
  ): Promise<void> {
    try {
      const {
        filename = `export_${this.getTimestamp()}.json`
      } = options

      if (!data || data.length === 0) {
        ElMessage.warning('没有数据可导出')
        return
      }

      const jsonContent = JSON.stringify(data, null, 2)
      this.downloadFile(jsonContent, filename, 'application/json')
      ElMessage.success('JSON导出成功')
    } catch (error) {
      console.error('JSON export failed:', error)
      ElMessage.error('JSON导出失败')
      throw error
    }
  }

  /**
   * 导出图表为图片
   */
  static async exportChartAsImage(
    chart: ECharts,
    options: ChartExportOptions = {}
  ): Promise<void> {
    try {
      const {
        filename = `chart_${this.getTimestamp()}.png`,
        format = 'png',
        width,
        height,
        backgroundColor = '#ffffff',
        pixelRatio = 2
      } = options

      // 获取图表的DataURL
      const dataURL = chart.getDataURL({
        type: format,
        width,
        height,
        backgroundColor,
        pixelRatio
      })

      // 下载图片
      this.downloadDataURL(dataURL, filename)
      ElMessage.success('图表导出成功')
    } catch (error) {
      console.error('Chart export failed:', error)
      ElMessage.error('图表导出失败')
      throw error
    }
  }

  /**
   * 导出图表为SVG
   */
  static async exportChartAsSvg(
    chart: ECharts,
    options: ChartExportOptions = {}
  ): Promise<void> {
    try {
      const {
        filename = `chart_${this.getTimestamp()}.svg`
      } = options

      // 获取SVG字符串
      const svgStr = chart.renderToSVGString()
      
      // 下载SVG文件
      this.downloadFile(svgStr, filename, 'image/svg+xml')
      ElMessage.success('SVG导出成功')
    } catch (error) {
      console.error('SVG export failed:', error)
      ElMessage.error('SVG导出失败')
      throw error
    }
  }

  /**
   * 批量导出多个图表
   */
  static async exportMultipleCharts(
    charts: { chart: ECharts; name: string }[],
    options: ChartExportOptions = {}
  ): Promise<void> {
    try {
      const {
        format = 'png',
        backgroundColor = '#ffffff',
        pixelRatio = 2
      } = options

      const zip = await import('jszip')
      const JSZip = zip.default

      const zipFile = new JSZip()
      const timestamp = this.getTimestamp()

      // 添加每个图表到ZIP
      for (let i = 0; i < charts.length; i++) {
        const { chart, name } = charts[i]
        const dataURL = chart.getDataURL({
          type: format,
          backgroundColor,
          pixelRatio
        })
        
        // 将DataURL转换为Blob
        const response = await fetch(dataURL)
        const blob = await response.blob()
        
        zipFile.file(`${name}.${format}`, blob)
      }

      // 生成ZIP文件
      const zipBlob = await zipFile.generateAsync({ type: 'blob' })
      this.downloadBlob(zipBlob, `charts_${timestamp}.zip`)
      
      ElMessage.success('批量导出成功')
    } catch (error) {
      console.error('Multiple charts export failed:', error)
      ElMessage.error('批量导出失败，请确保已安装jszip库')
      throw error
    }
  }

  /**
   * 导出报表（包含数据和图表）
   */
  static async exportReport<T = any>(
    data: {
      title: string
      description?: string
      tables: Array<{
        name: string
        data: T[]
        headers?: string[]
      }>
      charts?: Array<{
        name: string
        chart: ECharts
      }>
    },
    options: ExportOptions = {}
  ): Promise<void> {
    try {
      const XLSX = await import('xlsx')
      
      const {
        filename = `report_${this.getTimestamp()}.xlsx`
      } = options

      const wb = XLSX.utils.book_new()

      // 创建概览页
      const overviewData = [
        ['报表标题', data.title],
        ['生成时间', new Date().toLocaleString()],
        ['描述', data.description || ''],
        [''],
        ['数据表数量', data.tables.length],
        ['图表数量', data.charts?.length || 0]
      ]
      
      const overviewWs = XLSX.utils.aoa_to_sheet(overviewData)
      XLSX.utils.book_append_sheet(wb, overviewWs, '概览')

      // 添加数据表
      data.tables.forEach((table, index) => {
        if (table.data && table.data.length > 0) {
          const ws = XLSX.utils.json_to_sheet(table.data, {
            header: table.headers
          })
          
          // 设置列宽
          const colWidths = this.calculateColumnWidths(table.data, table.headers)
          ws['!cols'] = colWidths
          
          XLSX.utils.book_append_sheet(wb, ws, table.name || `数据表${index + 1}`)
        }
      })

      // 导出Excel文件
      XLSX.writeFile(wb, filename)
      
      // 如果有图表，单独导出
      if (data.charts && data.charts.length > 0) {
        await this.exportMultipleCharts(data.charts, {
          format: 'png',
          backgroundColor: '#ffffff'
        })
      }

      ElMessage.success('报表导出成功')
    } catch (error) {
      console.error('Report export failed:', error)
      ElMessage.error('报表导出失败')
      throw error
    }
  }

  /**
   * 格式化值
   */
  private static formatValue(value: any, options: ExportOptions): string {
    if (value === null || value === undefined) {
      return ''
    }

    // 日期格式化
    if (value instanceof Date) {
      return options.dateFormat 
        ? this.formatDate(value, options.dateFormat)
        : value.toLocaleString()
    }

    // 数字格式化
    if (typeof value === 'number') {
      return options.numberFormat
        ? this.formatNumber(value, options.numberFormat)
        : value.toString()
    }

    return String(value)
  }

  /**
   * 转义CSV值
   */
  private static escapeCsvValue(value: string): string {
    if (typeof value !== 'string') {
      value = String(value)
    }

    // 如果包含逗号、引号或换行符，需要用引号包围
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      // 转义引号
      value = value.replace(/"/g, '""')
      return `"${value}"`
    }

    return value
  }

  /**
   * 计算列宽
   */
  private static calculateColumnWidths<T>(data: T[], headers?: string[]): any[] {
    if (!data || data.length === 0) return []

    const keys = headers || Object.keys(data[0] as object)
    return keys.map(key => {
      const maxLength = Math.max(
        key.length,
        ...data.map(row => String((row as any)[key] || '').length)
      )
      return { wch: Math.min(maxLength + 2, 50) }
    })
  }

  /**
   * 格式化日期
   */
  private static formatDate(date: Date, format: string): string {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return format
      .replace('YYYY', year.toString())
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds)
  }

  /**
   * 格式化数字
   */
  private static formatNumber(num: number, format: string): string {
    // 简单的数字格式化，可以根据需要扩展
    if (format === 'currency') {
      return num.toLocaleString('zh-CN', {
        style: 'currency',
        currency: 'CNY'
      })
    }
    
    if (format === 'percent') {
      return (num * 100).toFixed(2) + '%'
    }

    return num.toLocaleString()
  }

  /**
   * 获取时间戳
   */
  private static getTimestamp(): string {
    const now = new Date()
    return now.getFullYear() +
      String(now.getMonth() + 1).padStart(2, '0') +
      String(now.getDate()).padStart(2, '0') +
      '_' +
      String(now.getHours()).padStart(2, '0') +
      String(now.getMinutes()).padStart(2, '0') +
      String(now.getSeconds()).padStart(2, '0')
  }

  /**
   * 下载文件
   */
  private static downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType })
    this.downloadBlob(blob, filename)
  }

  /**
   * 下载DataURL
   */
  private static downloadDataURL(dataURL: string, filename: string): void {
    const link = document.createElement('a')
    link.href = dataURL
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  /**
   * 下载Blob
   */
  private static downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
}

/**
 * 导出工具函数
 */
export const exportUtils = {
  /**
   * 快速导出CSV
   */
  csv: <T>(data: T[], filename?: string, options?: ExportOptions) => 
    DataExporter.exportToCsv(data, { ...options, filename }),

  /**
   * 快速导出Excel
   */
  excel: <T>(data: T[], filename?: string, options?: ExportOptions) => 
    DataExporter.exportToExcel(data, { ...options, filename }),

  /**
   * 快速导出JSON
   */
  json: <T>(data: T[], filename?: string, options?: ExportOptions) => 
    DataExporter.exportToJson(data, { ...options, filename }),

  /**
   * 快速导出图表
   */
  chart: (chart: ECharts, filename?: string, options?: ChartExportOptions) => 
    DataExporter.exportChartAsImage(chart, { ...options, filename }),

  /**
   * 快速导出SVG
   */
  svg: (chart: ECharts, filename?: string, options?: ChartExportOptions) => 
    DataExporter.exportChartAsSvg(chart, { ...options, filename })
}

export default DataExporter