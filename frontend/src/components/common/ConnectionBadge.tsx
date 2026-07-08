import type { ConnectionStatus } from '../../types/telemetry'

interface ConnectionBadgeProps {
  status: ConnectionStatus
}

export function ConnectionBadge({ status }: ConnectionBadgeProps) {
  const isLive = status === 'live'
  return (
    <div className="flex items-center gap-2 border border-[var(--color-border)] bg-[var(--color-panel)] px-2.5 py-1">
      <span
        className="h-2 w-2 rounded-full"
        style={{
          backgroundColor: isLive ? 'var(--color-safe)' : 'var(--color-slate-dim)',
          animation: isLive ? 'pulse-dot 2s ease-in-out infinite' : undefined,
        }}
      />
      <span className="font-mono text-[11px] font-semibold tracking-[0.14em] text-[var(--color-slate)]">
        {isLive ? 'LIVE' : 'MOCK'}
      </span>
    </div>
  )
}
