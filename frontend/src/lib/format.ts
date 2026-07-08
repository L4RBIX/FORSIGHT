export function pct(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`
}

export function clockTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function missionClock(startedAt: number, now: number): string {
  const elapsed = Math.max(0, now - startedAt)
  const totalSeconds = Math.floor(elapsed / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `T+${pad(h)}:${pad(m)}:${pad(s)}`
}
