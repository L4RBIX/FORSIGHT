import type { ActionInfo, DetectedObject, Prediction, SensorInfo } from '../types/telemetry'
import { fallOffPath, recoverPath, restPath, slidePath } from '../lib/geometry'

export interface Scenario {
  id: string
  presetLabel: string | null
  objects: DetectedObject[]
  action: ActionInfo
  prediction: Prediction
  sensor: SensorInfo
}

const SAFETY_RULE = 'Block if fall probability > 30%'

// ---------------------------------------------------------------------------
// Scenario 1 — SAFE: push a box in open space
// ---------------------------------------------------------------------------
const safeBox: DetectedObject = {
  id: 'box_1',
  label: 'box',
  confidence: 0.96,
  pos: [-0.16, 0.04, 0.0],
  size: [0.1, 0.08, 0.08],
  movable: true,
  near_edge: false,
  bbox: [0.12, 0.32, 0.19, 0.24],
}
const safeCup: DetectedObject = {
  id: 'cup_1',
  label: 'cup',
  confidence: 0.91,
  pos: [0.17, -0.1, 0.0],
  size: [0.07, 0.07, 0.11],
  movable: true,
  near_edge: false,
  bbox: [0.58, 0.42, 0.13, 0.22],
}

export const SAFE_SCENARIO: Scenario = {
  id: 'safe-push-box',
  presetLabel: 'Push blue box right',
  objects: [safeBox, safeCup],
  action: { text: 'push blue box right', object_id: 'box_1', dir: [1, 0, 0], force_n: 3.5 },
  prediction: {
    risk: 0.06,
    verdict: 'SAFE',
    outcome: 'box slides 12cm right and settles mid-table',
    reason: '0 of 30 simulations end with any object leaving the table',
    n_sims: 30,
    safety_rule: SAFETY_RULE,
    trajectories: [
      slidePath(safeBox.pos, [-0.03, 0.05, 0.0], 14, 1),
      restPath(safeCup.pos, 10, 2),
    ],
  },
  sensor: { pos_noise_mm: 3.2, rot_noise_deg: 1.4, tracking: 'ok' },
}

// ---------------------------------------------------------------------------
// Scenario 2 — BLOCK: sliding the cup toward the edge tips it off
// ---------------------------------------------------------------------------
const blockBox: DetectedObject = {
  id: 'box_2',
  label: 'box',
  confidence: 0.94,
  pos: [-0.08, 0.08, 0.0],
  size: [0.1, 0.08, 0.08],
  movable: true,
  near_edge: false,
  bbox: [0.2, 0.3, 0.18, 0.22],
}
const blockCup: DetectedObject = {
  id: 'cup_2',
  label: 'cup',
  confidence: 0.89,
  pos: [0.14, 0.2, 0.0],
  size: [0.07, 0.07, 0.11],
  movable: true,
  near_edge: true,
  bbox: [0.52, 0.16, 0.13, 0.22],
}
const blockBottle: DetectedObject = {
  id: 'bottle_2',
  label: 'bottle',
  confidence: 0.87,
  pos: [-0.28, -0.18, 0.0],
  size: [0.06, 0.06, 0.19],
  movable: true,
  near_edge: false,
  bbox: [0.08, 0.6, 0.1, 0.3],
}

const cupEdgeTarget: [number, number, number] = [0.16, 0.34, 0.0]

export const BLOCK_SCENARIO: Scenario = {
  id: 'block-cup-off-edge',
  presetLabel: 'Slide cup toward edge',
  objects: [blockBox, blockCup, blockBottle],
  action: { text: 'slide cup toward edge', object_id: 'cup_2', dir: [0.15, 1, 0], force_n: 4.0 },
  prediction: {
    risk: 0.87,
    verdict: 'BLOCK',
    outcome: 'cup falls off table',
    reason: '26 of 30 simulations end with the cup leaving the table',
    n_sims: 30,
    safety_rule: SAFETY_RULE,
    trajectories: [
      fallOffPath(blockCup.pos, cupEdgeTarget, 20, 3),
      fallOffPath(blockCup.pos, [cupEdgeTarget[0] - 0.02, cupEdgeTarget[1] + 0.01, 0], 20, 8),
      fallOffPath(blockCup.pos, [cupEdgeTarget[0] + 0.03, cupEdgeTarget[1] - 0.01, 0], 20, 15),
      recoverPath(blockCup.pos, cupEdgeTarget, 0.5, 16, 21),
      restPath(blockBox.pos, 10, 5),
      restPath(blockBottle.pos, 10, 6),
    ],
  },
  sensor: { pos_noise_mm: 4.6, rot_noise_deg: 2.1, tracking: 'ok' },
}

// ---------------------------------------------------------------------------
// Scenario 3 — CAUTION: reaching across the table risks clipping a bottle
// ---------------------------------------------------------------------------
const cautionBox: DetectedObject = {
  id: 'box_3',
  label: 'box',
  confidence: 0.95,
  pos: [-0.2, -0.05, 0.0],
  size: [0.1, 0.08, 0.08],
  movable: true,
  near_edge: false,
  bbox: [0.1, 0.4, 0.18, 0.22],
}
const cautionBottle: DetectedObject = {
  id: 'bottle_3',
  label: 'bottle',
  confidence: 0.88,
  pos: [0.24, 0.22, 0.0],
  size: [0.06, 0.06, 0.19],
  movable: true,
  near_edge: true,
  bbox: [0.66, 0.14, 0.11, 0.32],
}
const cautionBall: DetectedObject = {
  id: 'ball_3',
  label: 'ball',
  confidence: 0.9,
  pos: [0.02, 0.12, 0.0],
  size: [0.06, 0.06, 0.06],
  movable: true,
  near_edge: false,
  bbox: [0.42, 0.34, 0.1, 0.14],
}

const bottleEdge: [number, number, number] = [0.26, 0.34, 0.0]

export const CAUTION_SCENARIO: Scenario = {
  id: 'caution-reach-across',
  presetLabel: 'Reach across table',
  objects: [cautionBox, cautionBall, cautionBottle],
  action: { text: 'reach across table', object_id: 'bottle_3', dir: [0.1, 1, 0], force_n: 1.8 },
  prediction: {
    risk: 0.4,
    verdict: 'CAUTION',
    outcome: 'gripper sweep may clip the bottle near the edge',
    reason: '12 of 30 simulations show the bottle shifting toward the edge',
    n_sims: 30,
    safety_rule: SAFETY_RULE,
    trajectories: [
      recoverPath(cautionBottle.pos, bottleEdge, 0.42, 14, 11),
      recoverPath(cautionBottle.pos, bottleEdge, 0.58, 14, 17),
      fallOffPath(cautionBottle.pos, bottleEdge, 18, 24),
      restPath(cautionBox.pos, 10, 9),
      restPath(cautionBall.pos, 10, 13),
    ],
  },
  sensor: { pos_noise_mm: 3.8, rot_noise_deg: 1.7, tracking: 'ok' },
}

// ---------------------------------------------------------------------------
// Scenario 4 — SCAN: judge places a new object, open-vocabulary detection
// ---------------------------------------------------------------------------
const scanBox: DetectedObject = {
  id: 'box_4',
  label: 'box',
  confidence: 0.95,
  pos: [-0.22, -0.12, 0.0],
  size: [0.1, 0.08, 0.08],
  movable: true,
  near_edge: false,
  bbox: [0.1, 0.5, 0.17, 0.2],
}
const scanCup: DetectedObject = {
  id: 'cup_4',
  label: 'cup',
  confidence: 0.92,
  pos: [0.05, -0.18, 0.0],
  size: [0.07, 0.07, 0.11],
  movable: true,
  near_edge: false,
  bbox: [0.4, 0.56, 0.12, 0.2],
}
const scanGlasses: DetectedObject = {
  id: 'glasses_1',
  label: 'glasses',
  confidence: 0.78,
  pos: [0.2, 0.1, 0.0],
  size: [0.14, 0.05, 0.045],
  movable: true,
  near_edge: false,
  bbox: [0.6, 0.36, 0.16, 0.1],
}

export const SCAN_SCENARIO: Scenario = {
  id: 'scan-new-object',
  presetLabel: null,
  objects: [scanBox, scanCup, scanGlasses],
  action: { text: 'center glasses on table', object_id: 'glasses_1', dir: [-1, 0, 0], force_n: 1.5 },
  prediction: {
    risk: 0.05,
    verdict: 'SAFE',
    outcome: 'glasses settle centered, no edge risk',
    reason: '0 of 20 simulations show any object leaving the table',
    n_sims: 20,
    safety_rule: SAFETY_RULE,
    trajectories: [
      slidePath(scanGlasses.pos, [0.08, 0.1, 0.0], 12, 31),
      restPath(scanBox.pos, 8, 27),
      restPath(scanCup.pos, 8, 29),
    ],
  },
  sensor: { pos_noise_mm: 2.9, rot_noise_deg: 1.2, tracking: 'ok' },
}

export const SCENARIOS: Scenario[] = [SAFE_SCENARIO, BLOCK_SCENARIO, CAUTION_SCENARIO, SCAN_SCENARIO]

export const PRESET_SCENARIOS = SCENARIOS.filter((s) => s.presetLabel !== null)
