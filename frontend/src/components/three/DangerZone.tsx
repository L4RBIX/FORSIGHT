import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { TABLE } from '../../lib/geometry'

interface DangerZoneProps {
  /** 0 = idle hazard marking, 1 = full alert (BLOCK). */
  intensity: number
}

const STRIP_WIDTH = 0.05
const BASE_OPACITY = 0.1
const ALERT_OPACITY = 0.42

export function DangerZone({ intensity }: DangerZoneProps) {
  const { halfX, halfY } = TABLE
  const materials = useRef<(THREE.MeshBasicMaterial | null)[]>([])

  useFrame(({ clock }) => {
    const pulse = intensity > 0.3 ? Math.sin(clock.getElapsedTime() * (2 + intensity * 2)) * 0.12 * intensity : 0
    const target = BASE_OPACITY + (ALERT_OPACITY - BASE_OPACITY) * intensity + pulse
    materials.current.forEach((mat) => {
      if (mat) mat.opacity = THREE.MathUtils.damp(mat.opacity, target, 6, 0.016)
    })
  })

  const strips: Array<{ pos: [number, number, number]; size: [number, number] }> = [
    { pos: [0, 0.0015, halfY - STRIP_WIDTH / 2], size: [halfX * 2, STRIP_WIDTH] },
    { pos: [0, 0.0015, -(halfY - STRIP_WIDTH / 2)], size: [halfX * 2, STRIP_WIDTH] },
    { pos: [halfX - STRIP_WIDTH / 2, 0.0015, 0], size: [STRIP_WIDTH, halfY * 2] },
    { pos: [-(halfX - STRIP_WIDTH / 2), 0.0015, 0], size: [STRIP_WIDTH, halfY * 2] },
  ]

  return (
    <group>
      {strips.map((s, i) => (
        <mesh key={i} position={s.pos}>
          <boxGeometry args={[s.size[0], 0.002, s.size[1]]} />
          <meshBasicMaterial
            ref={(el) => {
              materials.current[i] = el
            }}
            color="#ff3b47"
            transparent
            opacity={BASE_OPACITY}
          />
        </mesh>
      ))}
    </group>
  )
}
