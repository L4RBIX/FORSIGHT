import type { Verdict } from '../types/telemetry'

export const VERDICT_COLOR: Record<Verdict, string> = {
  SAFE: '#00e08a',
  CAUTION: '#ffb020',
  BLOCK: '#ff3b47',
}

export const VERDICT_COLOR_RGB: Record<Verdict, string> = {
  SAFE: '0, 224, 138',
  CAUTION: '255, 176, 32',
  BLOCK: '255, 59, 71',
}

export const VERDICT_LABEL: Record<Verdict, string> = {
  SAFE: 'SAFE',
  CAUTION: 'CAUTION',
  BLOCK: 'BLOCK',
}

export function verdictFromRisk(risk: number): Verdict {
  if (risk >= 0.6) return 'BLOCK'
  if (risk >= 0.25) return 'CAUTION'
  return 'SAFE'
}

export function verdictGlow(verdict: Verdict, intensity = 0.28): string {
  const rgb = VERDICT_COLOR_RGB[verdict]
  const strength = verdict === 'BLOCK' ? intensity + 0.06 : intensity
  return `0 0 24px 2px rgba(${rgb}, ${strength}), 0 0 64px 8px rgba(${rgb}, ${strength * 0.35})`
}
