import type { ReactNode } from 'react'
import { VERDICT_COLOR } from '../../lib/colors'
import type { Verdict } from '../../types/telemetry'

export interface PanelProps {
  title?: string
  eyebrow?: string
  accent?: Verdict | 'neutral'
  active?: boolean
  className?: string
  bodyClassName?: string
  children: ReactNode
  headerRight?: ReactNode
}

export function Panel({
  title,
  eyebrow,
  accent = 'neutral',
  active = false,
  className = '',
  bodyClassName = '',
  children,
  headerRight,
}: PanelProps) {
  const bracketColor = accent === 'neutral' ? undefined : VERDICT_COLOR[accent]
  const style = bracketColor && active ? ({ '--bracket-color': bracketColor } as React.CSSProperties) : undefined

  return (
    <div
      className={`relative flex flex-col border border-[var(--color-border)] bg-[var(--color-panel)]/90 backdrop-blur-[1px] transition-[border-color] duration-500 ${className}`}
      style={style}
    >
      <span className="hud-bracket hud-bracket-tl" />
      <span className="hud-bracket hud-bracket-tr" />
      <span className="hud-bracket hud-bracket-bl" />
      <span className="hud-bracket hud-bracket-br" />

      {(title || eyebrow) && (
        <div className="flex items-center justify-between border-b border-[var(--color-hairline)] px-4 py-2.5">
          <div className="flex items-baseline gap-2">
            {title && (
              <h2 className="font-sans text-[13px] font-bold uppercase tracking-[0.1em] text-[var(--color-ink)]">
                {title}
              </h2>
            )}
            {eyebrow && (
              <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--color-slate-dim)]">
                {eyebrow}
              </span>
            )}
          </div>
          {headerRight}
        </div>
      )}

      <div className={`flex-1 min-h-0 ${bodyClassName}`}>{children}</div>
    </div>
  )
}
