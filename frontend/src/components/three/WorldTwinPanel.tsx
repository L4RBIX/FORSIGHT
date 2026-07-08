import { Suspense } from 'react'
import { Panel } from '../common/Panel'
import { Scene } from './Scene'
import { ScanningOverlay } from './ScanningOverlay'
import { VERDICT_COLOR } from '../../lib/colors'
import type { TelemetryFrame } from '../../types/telemetry'

interface WorldTwinPanelProps {
  frame: TelemetryFrame | null
}

export function WorldTwinPanel({ frame }: WorldTwinPanelProps) {
  const mode = frame?.mode ?? 'live'
  const prediction = mode === 'live' ? frame?.prediction : null
  const accent = prediction?.verdict ?? 'neutral'

  return (
    <Panel
      title="World Twin"
      eyebrow="PyBullet simulation"
      accent={accent}
      active={mode === 'live' && !!prediction}
      className="h-full"
      bodyClassName="relative"
      headerRight={
        prediction && (
          <span
            className="font-mono text-[10.5px] font-semibold uppercase tracking-[0.12em]"
            style={{ color: VERDICT_COLOR[prediction.verdict] }}
          >
            {prediction.n_sims} sims
          </span>
        )
      }
    >
      <div className="absolute inset-0">
        <Suspense fallback={null}>
          <Scene frame={frame} />
        </Suspense>
      </div>
      <ScanningOverlay mode={mode} />
    </Panel>
  )
}
