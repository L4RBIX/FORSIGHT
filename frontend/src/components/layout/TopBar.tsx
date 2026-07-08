import { useEffect, useState } from 'react'
import { ConnectionBadge } from '../common/ConnectionBadge'
import { clockTime } from '../../lib/format'
import type { ConnectionPreference } from '../../hooks/useForesightData'
import type { ConnectionStatus } from '../../types/telemetry'

interface TopBarProps {
  connection: ConnectionStatus
  preference: ConnectionPreference
  onSetPreference: (pref: ConnectionPreference) => void
}

export function TopBar({ connection, preference, onSetPreference }: TopBarProps) {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-hairline)] px-6">
      <div className="flex items-baseline gap-3">
        <span className="font-sans text-[19px] font-extrabold tracking-tight text-[var(--color-ink)]">
          FORESIGHT
        </span>
        <span className="hidden font-mono text-[10.5px] uppercase tracking-[0.16em] text-[var(--color-slate-dim)] lg:inline">
          · Predictive Safety Layer for Physical AI
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="font-mono text-[13px] tabular-nums text-[var(--color-slate)]">{clockTime(now)}</span>
        <ConnectionBadge status={connection} />
        <div className="flex border border-[var(--color-border)] text-[10.5px] font-semibold uppercase tracking-[0.1em]">
          <button
            type="button"
            onClick={() => onSetPreference('mock')}
            className="px-2.5 py-1 transition-colors"
            style={{
              color: preference === 'mock' ? 'var(--color-void)' : 'var(--color-slate-dim)',
              backgroundColor: preference === 'mock' ? 'var(--color-slate)' : 'transparent',
            }}
          >
            Mock
          </button>
          <button
            type="button"
            onClick={() => onSetPreference('live')}
            className="px-2.5 py-1 transition-colors"
            style={{
              color: preference === 'live' ? 'var(--color-void)' : 'var(--color-slate-dim)',
              backgroundColor: preference === 'live' ? 'var(--color-safe)' : 'transparent',
            }}
          >
            Live
          </button>
        </div>
      </div>
    </header>
  )
}
