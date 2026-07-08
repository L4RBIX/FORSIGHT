import type { TelemetryFrame } from '../types/telemetry'
import type { ForesightCommand } from '../types/commands'

export interface ForesightSocketHandlers {
  onFrame: (frame: TelemetryFrame) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: () => void
}

export class ForesightSocket {
  private socket: WebSocket | null = null
  private closedByUser = false

  constructor(
    private url: string,
    private handlers: ForesightSocketHandlers,
  ) {}

  connect(): void {
    this.closedByUser = false
    try {
      this.socket = new WebSocket(this.url)
    } catch {
      this.handlers.onError?.()
      return
    }
    this.socket.onopen = () => this.handlers.onOpen?.()
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TelemetryFrame
        this.handlers.onFrame(data)
      } catch {
        // malformed frame — ignore, keep waiting for a good one
      }
    }
    this.socket.onerror = () => this.handlers.onError?.()
    this.socket.onclose = () => {
      if (!this.closedByUser) this.handlers.onClose?.()
    }
  }

  send(command: ForesightCommand): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(command))
    }
  }

  close(): void {
    this.closedByUser = true
    this.socket?.close()
    this.socket = null
  }
}
