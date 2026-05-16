import { useEffect, useRef } from 'react';
import * as THREE from 'three';

type FaceViewerProps = {
  isActive: boolean;
};

export function FaceViewer({ isActive }: FaceViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020617);

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0.2, 5);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch {
      container.dataset.fallback = 'webgl-unavailable';
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const keyLight = new THREE.DirectionalLight(0x7dd3fc, 2.2);
    keyLight.position.set(2, 3, 4);
    scene.add(keyLight);
    scene.add(new THREE.AmbientLight(0x94a3b8, 1.4));

    const group = new THREE.Group();
    const skin = new THREE.MeshStandardMaterial({ color: 0xf0c6a8, roughness: 0.55, metalness: 0.02 });
    const accent = new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.28, metalness: 0.2 });
    const dark = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.5 });

    const head = new THREE.Mesh(new THREE.SphereGeometry(1.25, 48, 48), skin);
    head.scale.set(0.82, 1.08, 0.72);
    group.add(head);

    const leftEye = new THREE.Mesh(new THREE.SphereGeometry(0.08, 24, 24), dark);
    leftEye.position.set(-0.32, 0.26, 0.82);
    const rightEye = leftEye.clone();
    rightEye.position.x = 0.32;
    group.add(leftEye, rightEye);

    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.018, 12, 48, Math.PI), accent);
    mouth.position.set(0, -0.35, 0.82);
    mouth.rotation.z = Math.PI;
    group.add(mouth);

    const jaw = new THREE.Mesh(new THREE.SphereGeometry(0.52, 32, 32), skin);
    jaw.scale.set(0.9, 0.38, 0.5);
    jaw.position.set(0, -0.86, 0.04);
    group.add(jaw);

    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.42, 0.9, 32), skin);
    neck.position.set(0, -1.5, -0.04);
    group.add(neck);

    const shoulders = new THREE.Mesh(new THREE.CapsuleGeometry(0.72, 1.7, 12, 32), accent);
    shoulders.position.set(0, -2.15, -0.05);
    shoulders.rotation.z = Math.PI / 2;
    group.add(shoulders);

    scene.add(group);

    let frameId = 0;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      group.rotation.y += 0.006;
      mouth.scale.y = isActive ? 0.75 + Math.sin(Date.now() * 0.012) * 0.25 : 1;
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      container.removeChild(renderer.domElement);
    };
  }, [isActive]);

  return (
    <div className="faceViewerCard">
      <div className="faceViewerHeader">
        <div>
          <p className="eyebrow">3D Face</p>
          <h2>Live face preview</h2>
        </div>
        <span className={isActive ? 'badge badgeOk' : 'badge badgeWarn'}>{isActive ? 'pipeline ready' : 'waiting'}</span>
      </div>
      <div className="faceCanvas" ref={containerRef} role="img" aria-label="3D face model preview">
        <div className="faceFallback">WebGL preview will appear here when supported.</div>
      </div>
      <p className="muted">Placeholder 3D face viewer is active now; real A2F exported model or stream can replace this source when available.</p>
    </div>
  );
}
