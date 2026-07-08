import { useState, type FormEvent } from 'react'
import { PRESET_SCENARIOS } from '../../mock/scenarios'

interface BottomBarProps {
  onTriggerPreset: (id: string) => void
  onTriggerScan: () => void
  onTriggerCustomAction: (text: string) => void
}

function ScanIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <circle cx="12" cy="12" r="7" />
      <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </svg>
  )
}

export function BottomBar({ onTriggerPreset, onTriggerScan, onTriggerCustomAction }: BottomBarProps) {
  const [text, setText] = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    onTriggerCustomAction(trimmed)
    setText('')
  }

  return (
    <footer className="flex h-16 shrink-0 items-center gap-3 border-t border-[var(--color-hairline)] px-6">
      <form onSubmit={handleSubmit} className="flex min-w-0 flex-1 items-center gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Propose an action… e.g. “nudge the cup toward the edge”"
          className="min-w-0 flex-1 border border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-2 font-mono text-[13px] text-[var(--color-ink)] placeholder:text-[var(--color-slate-dim)] focus:border-[var(--color-slate)] focus:outline-none"
          style={{ boxShadow: 'none' }}
          onFocus={(e) => (e.currentTarget.style.boxShadow = 'inset 0 -2px 0 0 var(--color-safe)')}
          onBlur={(e) => (e.currentTarget.style.boxShadow = 'none')}
        />
        <button
          type="submit"
          className="shrink-0 border border-[var(--color-border)] px-4 py-2 font-sans text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--color-slate)] transition-colors hover:border-[var(--color-slate)] hover:text-[var(--color-ink)]"
        >
          Propose
        </button>
      </form>

      <div className="hidden h-8 w-px shrink-0 bg-[var(--color-hairline)] md:block" />

      <div className="hidden shrink-0 items-center gap-2 md:flex">
        {PRESET_SCENARIOS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onTriggerPreset(s.id)}
            className="shrink-0 whitespace-nowrap border border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-2 font-sans text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-slate)] transition-colors hover:border-[var(--color-slate)] hover:text-[var(--color-ink)]"
          >
            {s.presetLabel}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={onTriggerScan}
        className="flex shrink-0 items-center gap-2 bg-[var(--color-safe)] px-5 py-2.5 font-sans text-[12px] font-bold uppercase tracking-[0.1em] text-[var(--color-void)] transition-transform hover:scale-[1.03] active:scale-[0.98]"
      >
        <ScanIcon />
        Scan Scene
      </button>
    </footer>
  )
}
