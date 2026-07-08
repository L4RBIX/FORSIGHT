import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Panel } from '../common/Panel'
import { FieldLabel } from '../common/FieldLabel'
import { AnimatedNumber } from '../common/AnimatedNumber'
import { RiskGauge } from './RiskGauge'
import { VERDICT_COLOR } from '../../lib/colors'
import { physicsUncertaintyPct } from '../../lib/uncertainty'
import type { Prediction, TelemetryFrame } from '../../types/telemetry'

interface DecisionPanelProps {
  frame: TelemetryFrame | null
}

const DEFAULT_SAFETY_RULE = 'Block if fall probability > 30%'

export function DecisionPanel({ frame }: DecisionPanelProps) {
  const mode = frame?.mode ?? 'live'
  const prediction = mode === 'live' ? (frame?.prediction ?? null) : null
  const [lastPrediction, setLastPrediction] = useState<Prediction | null>(null)

  useEffect(() => {
    if (frame?.prediction) setLastPrediction(frame.prediction)
  }, [frame?.prediction])

  const safetyRule = prediction?.safety_rule ?? lastPrediction?.safety_rule ?? DEFAULT_SAFETY_RULE
  const accentColor = prediction ? VERDICT_COLOR[prediction.verdict] : 'var(--color-slate)'

  return (
    <Panel
      title="Decision"
      eyebrow="Predictive gate"
      accent={prediction?.verdict ?? 'neutral'}
      active={!!prediction}
      className="h-full"
      bodyClassName="flex flex-col gap-4 overflow-y-auto p-4"
    >
      <div className="min-w-0">
        <FieldLabel>Proposed action</FieldLabel>
        <p className="mt-0.5 truncate font-sans text-[13.5px] text-[var(--color-ink)]">
          {frame?.action?.text ?? 'Awaiting proposal…'}
        </p>
      </div>

      <div className="flex items-center justify-center">
        <RiskGauge risk={prediction?.risk ?? null} verdict={prediction?.verdict} mode={mode} />
      </div>

      <div className="min-h-[3.2rem]">
        <FieldLabel>Reason</FieldLabel>
        <AnimatePresence mode="wait">
          <motion.p
            key={prediction?.reason ?? mode}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="mt-0.5 text-[13px] leading-snug text-[var(--color-ink)]/90"
          >
            {prediction?.reason ??
              (mode === 'scanning' ? 'Awaiting scene scan…' : 'Running Monte-Carlo rollouts…')}
          </motion.p>
        </AnimatePresence>
      </div>

      <div className="flex items-center justify-between border-y border-[var(--color-hairline)] py-2">
        <FieldLabel>Monte-Carlo simulations</FieldLabel>
        {prediction ? (
          <AnimatedNumber
            value={prediction.n_sims}
            className="font-mono text-[17px] font-bold tabular-nums text-[var(--color-ink)]"
          />
        ) : (
          <span className="font-mono text-[17px] font-bold tabular-nums text-[var(--color-slate-dim)]">—</span>
        )}
      </div>

      <div>
        <FieldLabel>Uncertainty</FieldLabel>
        <div className="mt-1.5 grid grid-cols-2 gap-2">
          <UncertaintyStat label="Sensor position" value={`± ${frame?.sensor.pos_noise_mm.toFixed(1) ?? '—'} mm`} />
          <UncertaintyStat label="Sensor rotation" value={`± ${frame?.sensor.rot_noise_deg.toFixed(1) ?? '—'}°`} />
          <UncertaintyStat
            label="Mass / friction est."
            value={prediction ? `± ${physicsUncertaintyPct(prediction)}%` : '—'}
            span
          />
        </div>
      </div>

      <div className="mt-auto border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-3 py-2.5">
        <FieldLabel>Active safety rule</FieldLabel>
        <p className="mt-0.5 font-mono text-[12px]" style={{ color: accentColor }}>
          “{safetyRule}”
        </p>
      </div>
    </Panel>
  )
}

function UncertaintyStat({ label, value, span }: { label: string; value: string; span?: boolean }) {
  return (
    <div className={`border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2.5 py-1.5 ${span ? 'col-span-2' : ''}`}>
      <div className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-[var(--color-slate-dim)]">{label}</div>
      <div className="mt-0.5 font-mono text-[13px] font-semibold tabular-nums text-[var(--color-ink)]">{value}</div>
    </div>
  )
}
