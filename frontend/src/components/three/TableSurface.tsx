import { Grid } from '@react-three/drei'
import { TABLE } from '../../lib/geometry'

export function TableSurface() {
  const { halfX, halfY } = TABLE
  const legOffsetX = halfX - 0.035
  const legOffsetZ = halfY - 0.035

  return (
    <group>
      <mesh position={[0, -0.011, 0]} receiveShadow>
        <boxGeometry args={[halfX * 2, 0.02, halfY * 2]} />
        <meshStandardMaterial color="#141a22" roughness={0.5} metalness={0.4} />
      </mesh>

      <Grid
        position={[0, 0.0011, 0]}
        args={[halfX * 2, halfY * 2]}
        cellSize={0.05}
        cellThickness={0.5}
        cellColor="#1c2530"
        sectionSize={0.2}
        sectionThickness={1}
        sectionColor="#2a3846"
        fadeDistance={3}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid={false}
      />

      {[
        [1, 1],
        [1, -1],
        [-1, 1],
        [-1, -1],
      ].map(([sx, sz], i) => (
        <mesh key={i} position={[sx * legOffsetX, -0.22, sz * legOffsetZ]}>
          <cylinderGeometry args={[0.012, 0.012, 0.42, 10]} />
          <meshStandardMaterial color="#0d1319" roughness={0.6} metalness={0.4} />
        </mesh>
      ))}
    </group>
  )
}
