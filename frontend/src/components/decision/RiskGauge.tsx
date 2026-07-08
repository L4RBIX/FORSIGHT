import { motion } from 'framer-motion'
import { AnimatedNumber } from '../common/AnimatedNumber'
import { VERDICT_COLOR } from '../../lib/colors'
import type { SystemMode, Verdict } from '../../types/telemetry'

interface RiskGaugeProps {
  risk: number | null
  verdict: Verdict | undefined
  mode: SystemMode
}

const R = 80
const CX = 100
const CY = 100
const CIRCUMFERENCE = 2 * Math.PI * R
const SWEEP = 270
const START_ANGLE = 135
const ARC_LEN = (SWEEP / 360) * CIRCUMFERENCE
const THRESHOLD = 0.3

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

export function RiskGauge({ risk, verdict, mode }: RiskGaugeProps) {
  const indeterminate = mode !== 'live' || risk === null
  const value = risk ?? 0
  const color = verdict && !indeterminate ? VERDICT_COLOR[verdict] : 'var(--color-slate-dim)'
  const progressLen = ARC_LEN * value
  const thresholdAngle = START_ANGLE + SWEEP * THRESHOLD
  const t1 = polarToCartesian(CX, CY, R - 10, thresholdAngle)
  const t2 = polarToCartesian(CX, CY, R + 10, thresholdAngle)

  return (
    <div className="relative flex aspect-square w-full max-w-[240px] items-center justify-center">
      <svg viewBox="0 0 200 200" className="h-full w-full">
        <circle
          cx={CX}
          cy={CY}
          r={R}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={11}
          strokeLinecap="round"
          strokeDasharray={`${ARC_LEN} ${CIRCUMFERENCE}`}
          transform={`rotate(${START_ANGLE} ${CX} ${CY})`}
        />

        <line x1={t1.x} y1={t1.y} x2={t2.x} y2={t2.y} stroke="var(--color-slate-dim)" strokeWidth={2} />

        {!indeterminate && (
          <motion.circle
            cx={CX}
            cy={CY}
            r={R}
            fill="none"
            stroke={color}
            strokeWidth={11}
            strokeLinecap="round"
            strokeDasharray={`${ARC_LEN} ${CIRCUMFERENCE}`}
            initial={false}
            animate={{ strokeDashoffset: ARC_LEN - progressLen }}
            transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }}
            transform={`rotate(${START_ANGLE} ${CX} ${CY})`}
            style={{ filter: `drop-shadow(0 0 6px ${color})` }}
          />
        )}

        {indeterminate && (
          <g style={{ transformOrigin: '100px 100px', animation: 'spin 1.15s linear infinite' }}>
            <circle
              cx={CX}
              cy={CY}
              r={R}
              fill="none"
              stroke={mode === 'scanning' ? 'var(--color-safe)' : 'var(--color-caution)'}
              strokeWidth={11}
              strokeLinecap="round"
              strokeDasharray={`${ARC_LEN * 0.2} ${CIRCUMFERENCE}`}
            />
          </g>
        )}
      </svg>

      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-1">
        {indeterminate ? (
          <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--color-slate-dim)]">
            {mode === 'scanning' ? 'scanning' : mode === 'predicting' ? 'simulating' : 'standby'}
          </span>
        ) : (
          <>
            <AnimatedNumber
              value={value * 100}
              decimals={0}
              suffix="%"
              className="font-mono font-bold tabular-nums text-[clamp(1.9rem,3vw,2.6rem)]"
              style={{ color }}
            />
            <span className="font-sans text-[11px] font-bold uppercase tracking-[0.16em]" style={{ color }}>
              {verdict}
            </span>
          </>
        )}
      </div>
    </div>
  )
}
