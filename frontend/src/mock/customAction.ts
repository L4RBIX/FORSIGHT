import type { DetectedObject, Vec3 } from '../types/telemetry'
import type { Scenario } from './scenarios'
import { verdictFromRisk } from '../lib/colors'
import { fallOffPath, recoverPath, restPath, slidePath } from '../lib/geometry'

function hashToUnit(str: string): number {
  let h = 2166136261
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return ((h >>> 0) % 10000) / 10000
}

const RISK_MODIFIERS: [RegExp, number][] = [
  [/edge|off|knock|drop|fall|tip|topple/i, 0.32],
  [/fast|hard|shove|yank|slam|throw/i, 0.18],
  [/gentle|slow|careful|center|steady|light|softly/i, -0.32],
  [/reach|across|sweep|far/i, 0.1],
]

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

interface ObjectTemplate extends DetectedObject {}

const OBJECT_POOL: Record<string, ObjectTemplate> = {
  cup: {
    id: 'cup_x',
    label: 'cup',
    confidence: 0.9,
    pos: [0.16, -0.05, 0.0],
    size: [0.07, 0.07, 0.11],
    movable: true,
    near_edge: false,
    bbox: [0.56, 0.4, 0.13, 0.22],
  },
  box: {
    id: 'box_x',
    label: 'box',
    confidence: 0.95,
    pos: [-0.18, 0.02, 0.0],
    size: [0.1, 0.08, 0.08],
    movable: true,
    near_edge: false,
    bbox: [0.12, 0.34, 0.18, 0.22],
  },
  bottle: {
    id: 'bottle_x',
    label: 'bottle',
    confidence: 0.87,
    pos: [0.22, 0.16, 0.0],
    size: [0.06, 0.06, 0.19],
    movable: true,
    near_edge: false,
    bbox: [0.64, 0.2, 0.11, 0.3],
  },
  ball: {
    id: 'ball_x',
    label: 'ball',
    confidence: 0.9,
    pos: [0.0, 0.1, 0.0],
    size: [0.06, 0.06, 0.06],
    movable: true,
    near_edge: false,
    bbox: [0.42, 0.36, 0.1, 0.14],
  },
  glasses: {
    id: 'glasses_x',
    label: 'glasses',
    confidence: 0.79,
    pos: [0.1, 0.18, 0.0],
    size: [0.14, 0.05, 0.045],
    movable: true,
    near_edge: false,
    bbox: [0.5, 0.3, 0.16, 0.1],
  },
}

const EDGE_TARGET: Vec3 = [0.2, 0.34, 0.0]

export function buildCustomScenario(rawText: string): Scenario {
  const text = rawText.trim()
  const lower = text.toLowerCase()

  let risk = hashToUnit(text) * 0.42 + 0.12
  for (const [re, delta] of RISK_MODIFIERS) {
    if (re.test(lower)) risk += delta
  }
  risk = clamp(risk, 0.02, 0.97)
  const verdict = verdictFromRisk(risk)

  const matchedLabel = Object.keys(OBJECT_POOL).find((label) => lower.includes(label)) ?? 'box'
  const target: DetectedObject = {
    ...OBJECT_POOL[matchedLabel],
    near_edge: verdict !== 'SAFE',
  }
  const bystanderLabels = Object.keys(OBJECT_POOL).filter((l) => l !== matchedLabel).slice(0, 2)
  const bystanders = bystanderLabels.map((l) => OBJECT_POOL[l])

  const nSims = 24
  const failCount = Math.round(risk * nSims)

  let outcome: string
  let reason: string
  let trajectories: Vec3[][]

  if (verdict === 'BLOCK') {
    outcome = `${target.label} falls off the table`
    reason = `${failCount} of ${nSims} simulations end with the ${target.label} leaving the table`
    trajectories = [
      fallOffPath(target.pos, EDGE_TARGET, 20, 3),
      fallOffPath(target.pos, [EDGE_TARGET[0] - 0.02, EDGE_TARGET[1] + 0.01, 0], 20, 9),
      recoverPath(target.pos, EDGE_TARGET, 0.5, 16, 14),
    ]
  } else if (verdict === 'CAUTION') {
    outcome = `${target.label} may shift toward the edge`
    reason = `${failCount} of ${nSims} simulations show the ${target.label} shifting toward the edge`
    trajectories = [
      recoverPath(target.pos, EDGE_TARGET, 0.45, 14, 11),
      recoverPath(target.pos, EDGE_TARGET, 0.6, 14, 17),
    ]
  } else {
    outcome = `${target.label} settles safely mid-table`
    reason = `0 of ${nSims} simulations end with any object leaving the table`
    trajectories = [slidePath(target.pos, [target.pos[0] * 0.4, target.pos[1] * 0.4, 0], 14, 6)]
  }
  trajectories.push(...bystanders.map((b, i) => restPath(b.pos, 10, 30 + i)))

  return {
    id: `custom-${Date.now()}`,
    presetLabel: null,
    objects: [target, ...bystanders],
    action: { text, object_id: target.id, dir: [1, 0.2, 0], force_n: 3.0 },
    prediction: {
      risk,
      verdict,
      outcome,
      reason,
      n_sims: nSims,
      trajectories,
      safety_rule: 'Block if fall probability > 30%',
    },
    sensor: { pos_noise_mm: 3.6, rot_noise_deg: 1.6, tracking: 'ok' },
  }
}
