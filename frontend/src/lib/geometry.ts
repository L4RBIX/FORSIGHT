import type { Vec3 } from '../types/telemetry'

export const TABLE = {
  halfX: 0.42,
  halfY: 0.3,
  height: 0.72,
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

function lerpVec3(a: Vec3, b: Vec3, t: number): Vec3 {
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]
}

/** Deterministic, seedable "noise" so paths look organic without RNG flakiness. */
function wiggle(i: number, seed: number): number {
  return Math.sin(i * 12.9898 + seed * 78.233) * 0.5
}

/** A settling slide from a to b: eases in, slight overshoot wobble, settles. */
export function slidePath(a: Vec3, b: Vec3, steps = 14, seed = 1): Vec3[] {
  const pts: Vec3[] = []
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const eased = 1 - Math.pow(1 - t, 3)
    const base = lerpVec3(a, b, eased)
    const settle = t > 0.7 ? wiggle(i, seed) * 0.0015 * (1 - t) * 10 : 0
    pts.push([base[0] + settle, base[1] + settle * 0.6, base[2]])
  }
  return pts
}

/** Near-static jitter around a resting point — used for "simulated but unaffected" objects. */
export function restPath(a: Vec3, steps = 10, seed = 2, amp = 0.004): Vec3[] {
  const pts: Vec3[] = []
  for (let i = 0; i <= steps; i++) {
    pts.push([a[0] + wiggle(i, seed) * amp, a[1] + wiggle(i + 5, seed) * amp, a[2]])
  }
  return pts
}

/**
 * A trajectory that slides toward the table edge then tips and falls off,
 * height (z) dropping sharply past the boundary.
 */
export function fallOffPath(a: Vec3, edge: Vec3, steps = 20, seed = 3): Vec3[] {
  const pts: Vec3[] = []
  const tip = lerpVec3(a, edge, 0.72)
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    if (t < 0.55) {
      const tt = t / 0.55
      const p = lerpVec3(a, tip, tt)
      pts.push([p[0] + wiggle(i, seed) * 0.003, p[1] + wiggle(i + 3, seed) * 0.003, p[2]])
    } else {
      const tt = (t - 0.55) / 0.45
      const p = lerpVec3(tip, edge, Math.min(tt * 1.4, 1))
      const drop = -Math.pow(tt, 2) * 0.55
      pts.push([p[0], p[1], p[2] + drop])
    }
  }
  return pts
}

/** A partial slide that stops short of the edge — the "recovers" minority outcome. */
export function recoverPath(a: Vec3, edge: Vec3, stopFraction = 0.55, steps = 16, seed = 4): Vec3[] {
  const pts: Vec3[] = []
  const stop = lerpVec3(a, edge, stopFraction)
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const eased = 1 - Math.pow(1 - t, 2)
    const p = lerpVec3(a, stop, eased)
    pts.push([p[0] + wiggle(i, seed) * 0.003, p[1] + wiggle(i + 2, seed) * 0.003, p[2]])
  }
  return pts
}

/**
 * Contract space is [x, y, z] with z = height above the table surface.
 * Three.js scene space is Y-up, so z becomes scene-Y and contract-y becomes scene-Z.
 */
export function toSceneVec(pos: Vec3, liftHalfHeight = 0): [number, number, number] {
  return [pos[0], pos[2] + liftHalfHeight, pos[1]]
}
