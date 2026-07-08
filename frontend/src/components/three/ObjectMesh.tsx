import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { toSceneVec } from '../../lib/geometry'
import type { DetectedObject } from '../../types/telemetry'

interface ObjectMeshProps {
  object: DetectedObject
}

interface MaterialSpec {
  color: string
  roughness: number
  metalness?: number
  transparent?: boolean
  opacity?: number
}

const MATERIALS: Record<string, MaterialSpec> = {
  box: { color: '#c9a876', roughness: 0.9 },
  cup: { color: '#e8e2d8', roughness: 0.35 },
  bottle: { color: '#4a8a7a', roughness: 0.15, transparent: true, opacity: 0.62 },
  ball: { color: '#e0742f', roughness: 0.6 },
  glasses: { color: '#9aa5b5', roughness: 0.28, metalness: 0.55 },
}

function Geometry({ label, size }: { label: string; size: DetectedObject['size'] }) {
  const [sx, sy, sz] = size
  switch (label) {
    case 'cup':
      return <cylinderGeometry args={[(sx / 2) * 0.92, (sx / 2) * 0.78, sz, 28]} />
    case 'bottle':
      return <cylinderGeometry args={[sx / 2, (sx / 2) * 1.05, sz, 22]} />
    case 'ball':
      return <sphereGeometry args={[sx / 2, 24, 24]} />
    case 'glasses':
      return <boxGeometry args={[sx, sy, sz]} />
    case 'box':
    default:
      return <boxGeometry args={[sx, sy, sz]} />
  }
}

export function ObjectMesh({ object }: ObjectMeshProps) {
  const groupRef = useRef<THREE.Group>(null)
  const mat = MATERIALS[object.label] ?? MATERIALS.box
  const [, , sz] = object.size
  const targetPos = toSceneVec(object.pos, sz / 2)

  useFrame((_, delta) => {
    const g = groupRef.current
    if (!g) return
    const targetScale = 0.3 + 0.7 * Math.max(0.02, object.confidence)
    g.scale.x = THREE.MathUtils.damp(g.scale.x, targetScale, 7, delta)
    g.scale.y = g.scale.x
    g.scale.z = g.scale.x
    g.position.x = THREE.MathUtils.damp(g.position.x, targetPos[0], 9, delta)
    g.position.y = THREE.MathUtils.damp(g.position.y, targetPos[1], 9, delta)
    g.position.z = THREE.MathUtils.damp(g.position.z, targetPos[2], 9, delta)
  })

  return (
    <group ref={groupRef} position={targetPos} scale={0.3}>
      <mesh castShadow receiveShadow>
        <Geometry label={object.label} size={object.size} />
        <meshStandardMaterial
          color={mat.color}
          roughness={mat.roughness}
          metalness={mat.metalness ?? 0.05}
          transparent={mat.transparent}
          opacity={mat.opacity ?? 1}
        />
      </mesh>
      {object.near_edge && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -sz / 2 + 0.003, 0]}>
          <ringGeometry args={[object.size[0] * 0.62, object.size[0] * 0.78, 32]} />
          <meshBasicMaterial color="#ffb020" transparent opacity={0.75} />
        </mesh>
      )}
    </group>
  )
}
