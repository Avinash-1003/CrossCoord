import React from 'react';

export default function Grid3D({ mapData }) {
  if (!mapData || mapData.length === 0) return null;

  const h = mapData.length;
  const w = mapData[0].length;
  
  const blocks = [];
  
  for (let r = 0; r < h; r++) {
    for (let c = 0; c < w; c++) {
      const val = mapData[r][c];
      
      if (val === 1) {
        // Obstacle (tall red block)
        blocks.push(
          <mesh key={`obs-${r}-${c}`} position={[r, 0.5, c]} castShadow receiveShadow>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color="#ef4444" roughness={0.7} />
          </mesh>
        );
      } else if (val === 0) {
        // Free space (flat green floor)
        blocks.push(
          <mesh key={`free-${r}-${c}`} position={[r, 0, c]} receiveShadow>
            <boxGeometry args={[1, 0.1, 1]} />
            <meshStandardMaterial color="#22c55e" roughness={0.9} />
          </mesh>
        );
      }
      // -1 (Unknown) is not rendered (Fog of War)
    }
  }

  // Base plate to ground the scene
  return (
    <group position={[-h/2, 0, -w/2]}>
      {blocks}
    </group>
  );
}
