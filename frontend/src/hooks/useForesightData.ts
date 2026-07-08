import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ConnectionStatus, TelemetryFrame } from '../types/telemetry'
import { MockEngine } from '../mock/mockEngine'
import { ForesightSocket } from '../ws/client'
import { SCENARIOS } from '../mock/scenarios'

export type ConnectionPreference = 'live' | 'mock'

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws'
const RETRY_MS = 4000

export function useForesightData() {
  const [frame, setFrame] = useState<TelemetryFrame | null>(null)
  const [connection, setConnection] = useState<ConnectionStatus>('connecting')
  const [preference, setPreferenceState] = useState<ConnectionPreference>('live')

  const engineRef = useRef<MockEngine | null>(null)
  const socketRef = useRef<ForesightSocket | null>(null)
  const liveActiveRef = useRef(false)
  const preferenceRef = useRef<ConnectionPreference>('live')
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  if (!engineRef.current) {
    engineRef.current = new MockEngine()
  }

  useEffect(() => {
    const engine = engineRef.current!
    return engine.subscribe((f) => {
      if (!liveActiveRef.current) setFrame(f)
    })
  }, [])

  const connectSocket = useCallback(() => {
    if (preferenceRef.current !== 'live' || socketRef.current) return
    const socket = new ForesightSocket(WS_URL, {
      onFrame: (f) => {
        liveActiveRef.current = true
        setConnection('live')
        setFrame(f)
      },
      onClose: () => {
        liveActiveRef.current = false
        socketRef.current = null
        setConnection('mock')
        scheduleRetry()
      },
      onError: () => {
        liveActiveRef.current = false
      },
    })
    socketRef.current = socket
    socket.connect()
    // Give the backend a moment; if no frame arrives, treat as mock rather
    // than hanging on "connecting" forever.
    window.setTimeout(() => {
      if (!liveActiveRef.current && preferenceRef.current === 'live') setConnection('mock')
    }, 1500)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const scheduleRetry = useCallback(() => {
    if (retryTimerRef.current) return
    retryTimerRef.current = setTimeout(() => {
      retryTimerRef.current = null
      if (preferenceRef.current === 'live') connectSocket()
    }, RETRY_MS)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const setPreference = useCallback(
    (pref: ConnectionPreference) => {
      preferenceRef.current = pref
      setPreferenceState(pref)
      if (pref === 'mock') {
        liveActiveRef.current = false
        socketRef.current?.close()
        socketRef.current = null
        if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
        retryTimerRef.current = null
        setConnection('mock')
      } else {
        setConnection('connecting')
        connectSocket()
      }
    },
    [connectSocket],
  )

  useEffect(() => {
    connectSocket()
    return () => {
      // Must null this out (not just close()) — StrictMode's dev-only
      // mount/cleanup/remount cycle would otherwise leave socketRef pointing
      // at a dead socket, and connectSocket()'s `|| socketRef.current` guard
      // would then skip creating the real connection on remount, permanently
      // stranding the app on "mock" even with a healthy backend running.
      socketRef.current?.close()
      socketRef.current = null
      liveActiveRef.current = false
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
      retryTimerRef.current = null
    }
  }, [connectSocket])

  const actions = useMemo(
    () => ({
      triggerPreset: (id: string) => {
        if (liveActiveRef.current) {
          const scenario = SCENARIOS.find((s) => s.id === id)
          socketRef.current?.send({ type: 'propose_action', text: scenario?.action.text ?? id })
        } else {
          engineRef.current!.triggerPresetById(id)
        }
      },
      triggerScan: () => {
        if (liveActiveRef.current) {
          socketRef.current?.send({ type: 'scan' })
        } else {
          engineRef.current!.triggerScan()
        }
      },
      triggerCustomAction: (text: string) => {
        if (liveActiveRef.current) {
          socketRef.current?.send({ type: 'propose_action', text })
        } else {
          engineRef.current!.triggerCustomAction(text)
        }
      },
    }),
    [],
  )

  return { frame, connection, preference, setPreference, ...actions }
}
