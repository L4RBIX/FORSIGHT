import { AnimatePresence, motion } from 'framer-motion'
import type { DetectedObject, SystemMode } from '../../types/telemetry'

interface CameraViewProps {
  objects: DetectedObject[]
  mode: SystemMode
  cameraFrame: string | null
}

export function CameraView({ objects, mode, cameraFrame }: CameraViewProps) {
  return (
    <div className="relative aspect-[4/3] w-full shrink-0 overflow-hidden border-b border-[var(--color-hairline)] bg-black">
      {cameraFrame ? (
        <img src={cameraFrame} alt="Live camera feed" className="h-full w-full object-cover" />
      ) : (
        <div
          className="absolute inset-0"
          style={{ background: 'radial-gradient(ellipse at 50% 40%, #141b26 0%, #0a0e14 75%)' }}
        >
          <div
            className="absolute inset-0 opacity-60"
            style={{
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px)',
              backgroundSize: '22px 22px',
            }}
          />
        </div>
      )}

      <div className="pointer-events-none absolute inset-3 border border-white/10" />

      <div className="pointer-events-none absolute left-2 top-2 font-mono text-[9.5px] uppercase tracking-[0.1em] text-white/45">
        RGB · 1280×720 · LIMELIGHT 3A
      </div>
      <div className="pointer-events-none absolute right-2 top-2 flex items-center gap-1.5">
        <span
          className="h-1.5 w-1.5 rounded-full"
          style={{
            background: mode === 'scanning' ? 'var(--color-caution)' : 'var(--color-safe)',
            animation: 'pulse-dot 1.6s ease-in-out infinite',
          }}
        />
        <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-white/45">
          {mode === 'scanning' ? 'scanning' : 'tracking'}
        </span>
      </div>

      {mode === 'scanning' && (
        <div
          className="pointer-events-none absolute left-0 right-0"
          style={{
            height: '2px',
            background: 'linear-gradient(90deg, transparent, var(--color-safe), transparent)',
            boxShadow: '0 0 14px 3px rgba(0,224,138,0.6)',
            animation: 'scan-sweep-y 1.9s linear infinite',
          }}
        />
      )}

      <AnimatePresence>
        {objects.map((o) => (
          <motion.div
            key={o.id}
            className="absolute border"
            style={{
              left: `${o.bbox[0] * 100}%`,
              top: `${o.bbox[1] * 100}%`,
              width: `${o.bbox[2] * 100}%`,
              height: `${o.bbox[3] * 100}%`,
              borderColor: o.near_edge ? 'var(--color-caution)' : 'var(--color-safe)',
            }}
            initial={{ opacity: 0, scale: 0.88 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          >
            <span
              className="absolute -top-[18px] left-0 whitespace-nowrap px-1 font-mono text-[10px] leading-[16px]"
              style={{
                background: 'rgba(0,0,0,0.75)',
                color: o.near_edge ? 'var(--color-caution)' : 'var(--color-safe)',
              }}
            >
              {o.label} {Math.round(o.confidence * 100)}%
            </span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
