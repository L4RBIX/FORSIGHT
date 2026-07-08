import type { ReactNode } from 'react'

export function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <span className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-[var(--color-slate-dim)]">
      {children}
    </span>
  )
}
