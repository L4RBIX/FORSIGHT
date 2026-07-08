import type { DetectedObject, SystemMode, TelemetryFrame, Vec3 } from '../types/telemetry'
import { SCENARIOS, SCAN_SCENARIO, type Scenario } from './scenarios'
import { buildCustomScenario } from './customAction'

const TICK_MS = 80 // ~12.5Hz, matches the 10-15Hz data contract
const SCAN_MS = 1900
const PREDICT_MS = 1500
const HOLD_MS = 7000

type Phase = 'scanning' | 'predicting' | 'settled'
type Listener = (frame: TelemetryFrame) => void

function jitter(seed: number, t: number, amp: number): number {
  return Math.sin(t * 0.0021 + seed * 13.37) * amp
}

export class MockEngine {
  private listeners = new Set<Listener>()
  private tickHandle: ReturnType<typeof setTimeout> | null = null
  private phaseTimeout: ReturnType<typeof setTimeout> | null = null

  private queue: Scenario[] = SCENARIOS
  private queueIndex = 0
  private currentScenario: Scenario = this.queue[0]
  private phase: Phase = 'scanning'
  private phaseStartedAt = Date.now()
  private revealedCount = 0
  private revealTimes: number[] = []

  constructor() {
    this.startPhase('scanning', this.currentScenario)
    this.tick()
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn)
    fn(this.buildFrame())
    return () => this.listeners.delete(fn)
  }

  triggerScenario(scenario: Scenario): void {
    const idx = this.queue.indexOf(scenario)
    if (idx >= 0) this.queueIndex = idx
    this.startPhase('scanning', scenario)
  }

  triggerPresetById(id: string): void {
    const scenario = SCENARIOS.find((s) => s.id === id)
    if (scenario) this.triggerScenario(scenario)
  }

  triggerScan(): void {
    this.startPhase('scanning', SCAN_SCENARIO)
  }

  triggerCustomAction(text: string): void {
    if (!text.trim()) return
    this.startPhase('scanning', buildCustomScenario(text))
  }

  destroy(): void {
    if (this.tickHandle) clearTimeout(this.tickHandle)
    if (this.phaseTimeout) clearTimeout(this.phaseTimeout)
    this.listeners.clear()
  }

  private startPhase(phase: Phase, scenario: Scenario): void {
    this.currentScenario = scenario
    this.phase = phase
    this.phaseStartedAt = Date.now()
    if (phase === 'scanning') {
      this.revealedCount = 0
      this.revealTimes = new Array(scenario.objects.length).fill(0)
    } else {
      this.revealedCount = scenario.objects.length
    }
    if (this.phaseTimeout) clearTimeout(this.phaseTimeout)
    const duration = phase === 'scanning' ? SCAN_MS : phase === 'predicting' ? PREDICT_MS : HOLD_MS
    this.phaseTimeout = setTimeout(() => this.advance(), duration)
  }

  private advance(): void {
    if (this.phase === 'scanning') {
      this.startPhase('predicting', this.currentScenario)
    } else if (this.phase === 'predicting') {
      this.startPhase('settled', this.currentScenario)
    } else {
      this.queueIndex = (this.queueIndex + 1) % this.queue.length
      this.startPhase('scanning', this.queue[this.queueIndex])
    }
  }

  private tick = (): void => {
    if (this.phase === 'scanning') {
      const elapsed = Date.now() - this.phaseStartedAt
      const per = SCAN_MS / (this.currentScenario.objects.length + 1)
      this.revealedCount = Math.min(this.currentScenario.objects.length, Math.floor(elapsed / per))
    }
    this.emit()
    this.tickHandle = setTimeout(this.tick, TICK_MS)
  }

  private emit(): void {
    const frame = this.buildFrame()
    this.listeners.forEach((fn) => fn(frame))
  }

  private liveObject(o: DetectedObject, index: number, now: number): DetectedObject {
    if (index >= this.revealedCount) return o
    if (!this.revealTimes[index]) this.revealTimes[index] = now
    const elapsed = now - this.revealTimes[index]
    const rampFactor = Math.min(1, elapsed / 450)
    const eased = 1 - Math.pow(1 - rampFactor, 2)
    const pos: Vec3 = [
      o.pos[0] + jitter(index, now, 0.0018),
      o.pos[1] + jitter(index + 50, now, 0.0018),
      o.pos[2],
    ]
    return { ...o, confidence: o.confidence * eased, pos }
  }

  private buildFrame(): TelemetryFrame {
    const now = Date.now()
    const scenario = this.currentScenario
    const mode: SystemMode = this.phase === 'scanning' ? 'scanning' : this.phase === 'predicting' ? 'predicting' : 'live'
    const objects = scenario.objects
      .slice(0, Math.max(this.revealedCount, mode === 'scanning' ? this.revealedCount : scenario.objects.length))
      .map((o, i) => this.liveObject(o, i, now))

    return {
      timestamp: now / 1000,
      mode,
      camera_frame: null,
      objects,
      sensor: scenario.sensor,
      action: mode === 'scanning' ? null : scenario.action,
      prediction: mode === 'live' ? scenario.prediction : null,
    }
  }
}
