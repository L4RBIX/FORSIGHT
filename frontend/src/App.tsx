import { useForesightData } from './hooks/useForesightData'
import { TopBar } from './components/layout/TopBar'
import { VerdictBanner } from './components/layout/VerdictBanner'
import { BottomBar } from './components/layout/BottomBar'
import { PerceptionPanel } from './components/perception/PerceptionPanel'
import { WorldTwinPanel } from './components/three/WorldTwinPanel'
import { DecisionPanel } from './components/decision/DecisionPanel'

export default function App() {
  const { frame, connection, preference, setPreference, triggerPreset, triggerScan, triggerCustomAction } =
    useForesightData()

  const mode = frame?.mode ?? 'live'
  const prediction = mode === 'live' ? (frame?.prediction ?? null) : null

  return (
    <div className="relative flex h-dvh w-dvw flex-col overflow-hidden">
      <div className="hud-backdrop" />
      <div className="hud-vignette" />

      <div className="relative z-10 flex h-full min-h-0 flex-col">
        <TopBar connection={connection} preference={preference} onSetPreference={setPreference} />
        <VerdictBanner mode={mode} prediction={prediction} action={frame?.action ?? null} />

        <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-[28%_44%_28%]">
          <PerceptionPanel frame={frame} />
          <WorldTwinPanel frame={frame} />
          <DecisionPanel frame={frame} />
        </main>

        <BottomBar
          onTriggerPreset={triggerPreset}
          onTriggerScan={triggerScan}
          onTriggerCustomAction={triggerCustomAction}
        />
      </div>
    </div>
  )
}
