import { AnimatePresence, motion } from 'framer-motion'
import { VERDICT_COLOR, verdictGlow } from '../../lib/colors'
import { pct } from '../../lib/format'
import type { ActionInfo, Prediction, SystemMode } from '../../types/telemetry'

interface VerdictBannerProps {
  mode: SystemMode
  prediction: Prediction | null
  action: ActionInfo | null
}

const STANDBY_COLOR = 'var(--color-slate)'

export function VerdictBanner({ mode, prediction, action }: VerdictBannerProps) {
  const verdict = mode === 'live' ? prediction?.verdict : undefined
  const color = verdict ? VERDICT_COLOR[verdict] : STANDBY_COLOR

  const label = mode === 'scanning' ? 'SCANNING' : mode === 'predicting' ? 'ANALYZING' : (verdict ?? 'STANDBY')

  const glow = verdict ? verdictGlow(verdict) : 'none'

  return (
    <div
      className="relative flex h-[126px] shrink-0 items-center justify-between overflow-hidden border-b border-[var(--color-hairline)] px-10 transition-shadow duration-700 ease-out"
      style={{ boxShadow: glow }}
    >
      <AnimatePresence>
        {verdict && (
          <motion.div
            key={verdict}
            className="pointer-events-none absolute inset-0"
            style={{ background: color }}
            initial={{ opacity: 0.4 }}
            animate={{ opacity: 0 }}
            transition={{ duration: 0.7, ease: 'easeOut' }}
          />
        )}
      </AnimatePresence>

      <div className="z-10 flex min-w-0 flex-1 flex-col gap-1">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-[var(--color-slate-dim)]">
          Proposed action
        </span>
        <span className="truncate font-sans text-[15px] font-medium text-[var(--color-slate)]">
          {action?.text ?? '—'}
        </span>
      </div>

      <div className="z-10 flex flex-[2] items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.span
            key={label}
            initial={{ opacity: 0, scale: 0.85, filter: 'blur(6px)' }}
            animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, scale: 1.06, filter: 'blur(4px)' }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="select-none text-center font-sans font-extrabold leading-none tracking-tight"
            style={{
              color,
              fontSize: 'clamp(2.6rem, 6vw, 4.6rem)',
              textShadow: verdict ? `0 0 40px rgba(0,0,0,0.4)` : undefined,
            }}
          >
            {label}
          </motion.span>
        </AnimatePresence>
      </div>

      <div className="z-10 flex min-w-0 flex-1 flex-col items-end gap-1">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-[var(--color-slate-dim)]">
          Fall / collision risk
        </span>
        <span
          className="font-mono text-[22px] font-bold tabular-nums"
          style={{ color: prediction && mode === 'live' ? color : 'var(--color-slate-dim)' }}
        >
          {prediction && mode === 'live' ? pct(prediction.risk) : '—'}
        </span>
      </div>
    </div>
  )
}
