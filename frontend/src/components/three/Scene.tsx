import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { TableSurface } from './TableSurface'
import { DangerZone } from './DangerZone'
import { ObjectMesh } from './ObjectMesh'
import { Trajectories } from './Trajectories'
import { VERDICT_COLOR } from '../../lib/colors'
import type { TelemetryFrame } from '../../types/telemetry'

interface SceneProps {
  frame: TelemetryFrame | null
}

function SceneContents({ frame }: SceneProps) {
  const objects = frame?.objects ?? []
  const mode = frame?.mode ?? 'live'
  const prediction = mode === 'live' ? frame?.prediction : null
  const verdict = prediction?.verdict
  const verdictColor = verdict ? VERDICT_COLOR[verdict] : '#4a5568'
  const dangerIntensity = verdict === 'BLOCK' ? 1 : verdict === 'CAUTION' ? 0.5 : 0.06

  const revealKey = prediction ? `${prediction.verdict}|${prediction.risk}|${prediction.outcome}` : 'none'

  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[0.6, 1.4, 0.4]} intensity={1.15} castShadow />
      <pointLight position={[-0.6, 0.5, -0.5]} intensity={0.3} color={verdictColor} />
      <hemisphereLight args={['#26313d', '#050708', 0.35]} />

      <TableSurface />
      <DangerZone intensity={dangerIntensity} />

      {objects.map((o) => (
        <ObjectMesh key={o.id} object={o} />
      ))}

      {prediction && (
        <Trajectories trajectories={prediction.trajectories} color={verdictColor} revealKey={revealKey} />
      )}

      <OrbitControls
        target={[0, 0.03, 0]}
        enablePan={false}
        minDistance={0.85}
        maxDistance={2.1}
        minPolarAngle={Math.PI * 0.16}
        maxPolarAngle={Math.PI * 0.47}
        autoRotate
        autoRotateSpeed={0.45}
        enableDamping
        dampingFactor={0.08}
      />
    </>
  )
}

export function Scene({ frame }: SceneProps) {
  return (
    <Canvas shadows camera={{ position: [0.95, 0.8, 0.95], fov: 30 }} dpr={[1, 2]}>
      <color attach="background" args={['#0a0e14']} />
      <fog attach="fog" args={['#0a0e14', 1.8, 3.6]} />
      <SceneContents frame={frame} />
    </Canvas>
  )
}
