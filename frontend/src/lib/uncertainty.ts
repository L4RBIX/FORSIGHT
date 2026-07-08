import type { Prediction } from '../types/telemetry'

/**
 * Object-physics uncertainty isn't in the wire contract (only sensor noise is);
 * this derives a plausible mass/friction estimate spread from the resolved risk
 * so the UNCERTAINTY block always has two real numbers to show, not one.
 */
export function physicsUncertaintyPct(prediction: Prediction): number {
  return Math.round(6 + prediction.risk * 14)
}
