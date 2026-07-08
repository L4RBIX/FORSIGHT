import { motion } from 'framer-motion'
import type { DetectedObject } from '../../types/telemetry'

interface ConfidenceRowProps {
  object: DetectedObject
}

export function ConfidenceRow({ object }: ConfidenceRowProps) {
  const color = object.near_edge ? 'var(--color-caution)' : 'var(--color-safe)'
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-center gap-3 border-b border-[var(--color-hairline)] px-4 py-2.5 last:border-b-0"
    >
      <div className="flex w-[92px] shrink-0 items-center gap-1.5">
        <span className="truncate font-sans text-[12.5px] font-semibold capitalize text-[var(--color-ink)]">
          {object.label}
        </span>
        {object.near_edge && (
          <span
            title="Near table edge"
            className="h-1.5 w-1.5 shrink-0 rounded-full"
            style={{ background: 'var(--color-caution)' }}
          />
        )}
      </div>
      <div className="relative h-1.5 flex-1 overflow-hidden bg-[var(--color-border)]">
        <motion.div
          className="absolute inset-y-0 left-0"
          style={{ background: color }}
          initial={false}
          animate={{ width: `${object.confidence * 100}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-[11.5px] tabular-nums text-[var(--color-slate)]">
        {Math.round(object.confidence * 100)}%
      </span>
    </motion.div>
  )
}
