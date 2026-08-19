import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';

export default function Agent3D({ id, position }) {
  const meshRef = useRef();
  
  // Offset by half grid size since the grid is centered
  const [r, c] = position || [0, 0];
  const gridOffset = 32 / 2; // Assuming 32x32 for now
  
  const x = r - gridOffset;
  const z = c - gridOffset;
  
  // UAVs fly higher, UGVs drive on ground
  const isUAV = id.includes('3') || id.includes('4'); // quick hack based on IDs
  const y = isUAV ? 3 : 0.5;

  // Add subtle hover animation
  useFrame(({ clock }) => {
    if (meshRef.current && isUAV) {
      meshRef.current.position.y = y + Math.sin(clock.elapsedTime * 2) * 0.2;
    }
  });

  return (
    <group position={[x, y, z]}>
      <mesh ref={meshRef} castShadow>
        {isUAV ? (
          <octahedronGeometry args={[0.5]} />
        ) : (
          <boxGeometry args={[0.8, 0.5, 0.8]} />
        )}
        <meshStandardMaterial color={isUAV ? "#3b82f6" : "#eab308"} metalness={0.8} />
      </mesh>
      
      {/* Label above agent */}
      <Html position={[0, 1, 0]} center>
        <div style={{
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '2px 6px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 'bold',
          pointerEvents: 'none'
        }}>
          {id}
        </div>
      </Html>
    </group>
  );
}
