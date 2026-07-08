import { useEffect, useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Line } from '@react-three/drei'
import { toSceneVec } from '../../lib/geometry'
import type { Vec3 } from '../../types/telemetry'

interface TrajectoriesProps {
  trajectories: Vec3[][]
  color: string
  revealKey: string
}

const REVEAL_MS = 950
const VOID_RGB: [number, number, number] = [10 / 255, 14 / 255, 20 / 255]

function hexToRgb01(hex: string): [number, number, number] {
  const v = hex.replace('#', '')
  return [parseInt(v.slice(0, 2), 16) / 255, parseInt(v.slice(2, 4), 16) / 255, parseInt(v.slice(4, 6), 16) / 255]
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

export function Trajectories({ trajectories, color, revealKey }: TrajectoriesProps) {
  const [progress, setProgress] = useState(0)
  const startRef = useRef(performance.now())

  useEffect(() => {
    startRef.current = performance.now()
    setProgress(0)
  }, [revealKey])

  useFrame(() => {
    if (progress >= 1) return
    const t = Math.min(1, (performance.now() - startRef.current) / REVEAL_MS)
    setProgress(1 - Math.pow(1 - t, 3))
  })

  const [r, g, b] = hexToRgb01(color)

  return (
    <group>
      {trajectories.map((traj, ti) => {
        if (traj.length < 2) return null
        const scenePts = traj.map((p) => toSceneVec(p))
        const revealCount = Math.max(2, Math.ceil(scenePts.length * progress))
        const visible = scenePts.slice(0, revealCount)
        const vertexColors: Array<[number, number, number, number]> = visible.map((_, i) => {
          const tailT = i / Math.max(1, visible.length - 1)
          const fade = Math.pow(tailT, 1.4)
          return [
            lerp(r, VOID_RGB[0], fade * 0.82),
            lerp(g, VOID_RGB[1], fade * 0.82),
            lerp(b, VOID_RGB[2], fade * 0.82),
            lerp(0.92, 0.05, fade),
          ]
        })
        return (
          <Line
            key={ti}
            points={visible}
            vertexColors={vertexColors}
            lineWidth={2}
            transparent
            depthWrite={false}
            toneMapped={false}
          />
        )
      })}
    </group>
  )
}
