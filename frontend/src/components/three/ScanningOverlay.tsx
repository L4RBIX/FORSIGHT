import { AnimatePresence, motion } from 'framer-motion'
import type { SystemMode } from '../../types/telemetry'

interface ScanningOverlayProps {
  mode: SystemMode
}

export function ScanningOverlay({ mode }: ScanningOverlayProps) {
  if (mode === 'live') return null

  const label = mode === 'scanning' ? 'Analyzing scene…' : 'Simulating consequences…'
  const dotColor = mode === 'scanning' ? 'var(--color-safe)' : 'var(--color-caution)'

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        className="absolute inset-y-0 w-1/3"
        style={{
          background: 'linear-gradient(90deg, transparent, rgba(0,224,138,0.06), transparent)',
          animation: 'shimmer-sweep 2.4s linear infinite',
        }}
      />
      <AnimatePresence mode="wait">
        <motion.div
          key={label}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-2 border border-[var(--color-border)] bg-[var(--color-void)]/80 px-3 py-1.5"
        >
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ background: dotColor, animation: 'pulse-dot 1.1s ease-in-out infinite' }}
          />
          <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--color-slate)]">
            {label}
          </span>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
