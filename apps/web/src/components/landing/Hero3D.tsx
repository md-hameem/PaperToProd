'use client';

import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Mesh, MathUtils } from 'three';

function MorphingShape() {
  const meshRef = useRef<Mesh>(null);

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.2;
      meshRef.current.rotation.y += delta * 0.3;

      // Parallax effect based on mouse
      const targetX = (state.pointer.x * Math.PI) / 10;
      const targetY = (state.pointer.y * Math.PI) / 10;

      meshRef.current.rotation.x = MathUtils.damp(meshRef.current.rotation.x, targetY, 2, delta);
      meshRef.current.rotation.y = MathUtils.damp(meshRef.current.rotation.y, targetX, 2, delta);
    }
  });

  return (
    <mesh ref={meshRef}>
      <octahedronGeometry args={[2, 0]} />
      <meshStandardMaterial
        color="#a855f7"
        wireframe={true}
        emissive="#6366f1"
        emissiveIntensity={0.5}
      />
    </mesh>
  );
}

export function Hero3D() {
  return (
    <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, pointerEvents: 'none' }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <MorphingShape />
      </Canvas>
    </div>
  );
}
