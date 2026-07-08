export type Verdict = 'SAFE' | 'CAUTION' | 'BLOCK'

export type SystemMode = 'live' | 'scanning' | 'predicting'

export type Vec3 = [number, number, number]

/** Normalized [x, y, w, h], each in 0-1 relative to the camera frame. */
export type PixelBBox = [number, number, number, number]

export interface DetectedObject {
  id: string
  label: string
  confidence: number
  pos: Vec3
  size: Vec3
  movable: boolean
  near_edge: boolean
  bbox: PixelBBox
}

export interface SensorInfo {
  pos_noise_mm: number
  rot_noise_deg: number
  tracking: 'ok' | 'degraded' | 'lost'
}

export interface ActionInfo {
  text: string
  object_id: string | null
  dir: Vec3
  force_n: number
}

export interface Prediction {
  risk: number
  verdict: Verdict
  outcome: string
  reason: string
  n_sims: number
  trajectories: Vec3[][]
  safety_rule: string
}

export interface TelemetryFrame {
  timestamp: number
  mode: SystemMode
  camera_frame: string | null
  objects: DetectedObject[]
  sensor: SensorInfo
  action: ActionInfo | null
  prediction: Prediction | null
}

export type ConnectionStatus = 'live' | 'mock' | 'connecting'
