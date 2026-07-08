import { Panel } from '../common/Panel'
import { CameraView } from './CameraView'
import { ConfidenceRow } from './ConfidenceRow'
import type { TelemetryFrame } from '../../types/telemetry'

interface PerceptionPanelProps {
  frame: TelemetryFrame | null
}

export function PerceptionPanel({ frame }: PerceptionPanelProps) {
  const objects = frame?.objects ?? []
  const mode = frame?.mode ?? 'live'

  return (
    <Panel
      title="Perception"
      eyebrow={`${objects.length} object${objects.length === 1 ? '' : 's'}`}
      className="h-full"
      bodyClassName="flex flex-col overflow-hidden"
    >
      <CameraView objects={objects} mode={mode} cameraFrame={frame?.camera_frame ?? null} />
      <div className="flex-1 overflow-y-auto">
        {objects.length === 0 ? (
          <div className="flex h-full min-h-[80px] items-center justify-center px-4 text-center font-mono text-[11.5px] uppercase tracking-[0.08em] text-[var(--color-slate-dim)]">
            No objects detected
          </div>
        ) : (
          objects.map((o) => <ConfidenceRow key={o.id} object={o} />)
        )}
      </div>
    </Panel>
  )
}
