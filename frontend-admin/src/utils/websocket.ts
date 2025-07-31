import { io, Socket } from 'socket.io-client'
import type { WebSocketMessage } from '@/types'

class WebSocketManager {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 5000
  private listeners: Map<string, Function[]> = new Map()

  connect(token: string) {
    if (this.socket?.connected) {
      return
    }

    this.socket = io(import.meta.env.VITE_WS_URL || 'ws://localhost:8000', {
      auth: {
        token
      },
      transports: ['websocket'],
      timeout: 20000
    })

    this.setupEventListeners()
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.listeners.clear()
    this.reconnectAttempts = 0
  }

  private setupEventListeners() {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      this.emit('connected')
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      this.emit('disconnected', reason)
      
      if (reason === 'io server disconnect') {
        // 服务器主动断开，不重连
        return
      }
      
      this.handleReconnect()
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.emit('error', error)
      this.handleReconnect()
    })

    // 监听业务消息
    this.socket.on('stats_update', (data) => {
      this.emit('stats_update', data)
    })

    this.socket.on('alert', (data) => {
      this.emit('alert', data)
    })

    this.socket.on('notification', (data) => {
      this.emit('notification', data)
    })

    this.socket.on('user_activity', (data) => {
      this.emit('user_activity', data)
    })
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      this.emit('max_reconnect_attempts')
      return
    }

    this.reconnectAttempts++
    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      if (this.socket && !this.socket.connected) {
        this.socket.connect()
      }
    }, this.reconnectInterval)
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(callback)
  }

  off(event: string, callback?: Function) {
    if (!this.listeners.has(event)) return

    if (callback) {
      const callbacks = this.listeners.get(event)!
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    } else {
      this.listeners.delete(event)
    }
  }

  private emit(event: string, data?: any) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.forEach(callback => callback(data))
    }
  }

  send(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }

  get connected() {
    return this.socket?.connected || false
  }
}

export const wsManager = new WebSocketManager()
export default wsManager