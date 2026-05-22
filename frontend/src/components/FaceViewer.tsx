import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { AnimationFrame, AnimationTimeline, fetchAnimationTimeline } from '../services/api';

type FaceViewerProps = {
  isReady: boolean;
  audioUrl?: string | null;
  animationUrl?: string | null;
};

type FaceModel = Awaited<ReturnType<GLTFLoader['loadAsync']>>;

const primaryFaceModelUrl = import.meta.env.VITE_FACE_MODEL_URL ?? '/models/readyplayer-talk-arkit.glb';
const nvidiaFaceModelUrl = '/models/a2f-james-v3.glb';

const faceModelPromises = new Map<string, Promise<FaceModel>>();
let fallbackModelPromise: Promise<THREE.Group> | null = null;

function preloadFaceModel(url: string): Promise<FaceModel> {
  if (!faceModelPromises.has(url)) {
    faceModelPromises.set(url, new GLTFLoader().loadAsync(url));
  }
  return faceModelPromises.get(url)!;
}

function preloadFallbackModel(): Promise<THREE.Group> {
  fallbackModelPromise ??= new FBXLoader().loadAsync('/models/head.fbx');
  return fallbackModelPromise;
}

export function FaceViewer({ isReady, audioUrl, animationUrl }: FaceViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timelineRef = useRef<AnimationTimeline | null>(null);
  const isReadyRef = useRef(isReady);
  const [timelineStatus, setTimelineStatus] = useState('Idle');
  const [modelStatus, setModelStatus] = useState('Loading avatar');

  useEffect(() => {
    isReadyRef.current = isReady;
  }, [isReady]);

  useEffect(() => {
    const audio = audioRef.current;
    if (audio && audioUrl) {
      audio.preload = 'auto';
      audio.load();
    }
  }, [audioUrl]);

  useEffect(() => {
    timelineRef.current = null;
    if (!animationUrl) {
      setTimelineStatus('Idle');
      return;
    }

    let isCancelled = false;
    setTimelineStatus('Loading timeline');
    fetchAnimationTimeline(animationUrl)
      .then((timeline) => {
        if (isCancelled) {
          return;
        }
        timelineRef.current = timeline;
        setTimelineStatus(timeline.engine);
      })
      .catch(() => {
        if (!isCancelled) {
          setTimelineStatus('Timeline unavailable');
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [animationUrl]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020617);

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0.05, 4.2);
    camera.lookAt(0, 0, 0);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch {
      container.dataset.fallback = 'webgl-unavailable';
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    container.appendChild(renderer.domElement);

    const keyLight = new THREE.DirectionalLight(0xffd2b8, 2.45);
    keyLight.position.set(1.8, 3.2, 4.2);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0x7dd3fc, 1.35);
    rimLight.position.set(-2.8, 2.3, 2.6);
    scene.add(rimLight);
    scene.add(new THREE.AmbientLight(0xb9c7d6, 1.15));

    const group = new THREE.Group();
    group.name = 'speaking-face-rig';
    const skin = new THREE.MeshStandardMaterial({
      color: 0xd8ad96,
      roughness: 0.64,
      metalness: 0,
      emissive: 0x24140f,
      emissiveIntensity: 0.035,
    });
    const accent = new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.28, metalness: 0.2 });
    const dark = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.5 });
    const lipMaterial = new THREE.MeshStandardMaterial({ color: 0xaa3f47, roughness: 0.42 });
    const mouthInterior = new THREE.MeshStandardMaterial({ color: 0x25070b, roughness: 0.72 });
    const teethMaterial = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.32 });
    const eyeWhiteMaterial = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.22, metalness: 0 });
    const irisMaterial = new THREE.MeshBasicMaterial({ color: 0x38bdf8, depthTest: false, side: THREE.DoubleSide });
    const pupilMaterial = new THREE.MeshBasicMaterial({ color: 0x020617, depthTest: false, side: THREE.DoubleSide });

    const head = new THREE.Group();
    const fallbackHead = new THREE.Mesh(new THREE.SphereGeometry(1.25, 48, 48), skin);
    fallbackHead.scale.set(0.82, 1.08, 0.72);
    head.add(fallbackHead);
    group.add(head);

    const fallbackOnly = new THREE.Group();
    const leftEye = new THREE.Mesh(new THREE.SphereGeometry(0.08, 24, 24), dark);
    leftEye.position.set(-0.32, 0.26, 0.82);
    const rightEye = leftEye.clone();
    rightEye.position.x = 0.32;
    fallbackOnly.add(leftEye, rightEye);
    group.add(fallbackOnly);

    const modelEyeOverlay = new THREE.Group();
    modelEyeOverlay.name = 'model-eye-overlay';
    modelEyeOverlay.visible = false;
    for (const side of [-1, 1]) {
      const eyeball = new THREE.Mesh(new THREE.SphereGeometry(0.096, 32, 20), eyeWhiteMaterial);
      eyeball.scale.set(1.08, 0.72, 0.52);
      eyeball.position.set(side * 0.255, 0.19, 0.785);
      const iris = new THREE.Mesh(new THREE.CircleGeometry(0.052, 32), irisMaterial);
      iris.position.set(side * 0.18, 0.17, 1.18);
      iris.renderOrder = 5;
      const pupil = new THREE.Mesh(new THREE.CircleGeometry(0.024, 24), pupilMaterial);
      pupil.position.set(side * 0.18, 0.17, 1.185);
      pupil.renderOrder = 6;
      modelEyeOverlay.add(eyeball, iris, pupil);
    }

    const morphTargets: Array<{ mesh: THREE.Mesh; index: number; name: string }> = [];
    let loadedModel: THREE.Group | null = null;
    const loadedModelBaseScale = new THREE.Vector3(1, 1, 1);
    let loadedModelHasMouthMorphs = false;
    let smoothedJawOpen = 0.06;
    let smoothedMouthWide = 0.22;
    let smoothedMouthSmile = 0.06;
    let smoothedBlendShapes: Record<string, number> = {};
    let previousFrameTime = performance.now();

    const registerModel = (model: THREE.Group, label: string) => {
      model.traverse((object) => {
        if (object instanceof THREE.Mesh && /wolf3d_(body|outfit|footwear)/i.test(object.name)) {
          object.visible = false;
        }
      });
      const box = visibleBoxFromObject(model);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const maxAxis = Math.max(size.x, size.y, size.z) || 1;
      model.scale.setScalar(2.35 / maxAxis);
      model.position.sub(center.multiplyScalar(2.35 / maxAxis));
      model.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.castShadow = true;
          object.receiveShadow = true;
          object.frustumCulled = false;
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          for (const material of materials) {
            material.side = THREE.DoubleSide;
            material.needsUpdate = true;
            if ('roughness' in material && typeof material.roughness === 'number') {
              material.roughness = Math.max(0.42, Math.min(0.78, material.roughness));
            }
          }
          const dictionary = object.morphTargetDictionary;
          if (dictionary && object.morphTargetInfluences) {
            for (const [name, index] of Object.entries(dictionary)) {
              morphTargets.push({ mesh: object, index, name });
            }
          }
        }
      });
      loadedModelHasMouthMorphs = morphTargets.some((target) => /jaw|mouth|viseme|open|smile|aa|oh|ou/i.test(target.name));
      fallbackOnly.visible = false;
      neck.visible = false;
      shoulders.visible = false;
      head.clear();
      head.add(model);
      modelEyeOverlay.visible = loadedModelHasMouthMorphs && /nvidia/i.test(label);
      head.add(modelEyeOverlay);
      loadedModel = model;
      loadedModelBaseScale.copy(model.scale);
      frameCamera(camera, model, container);
      const framedBox = visibleBoxFromObject(model);
      const framedSize = framedBox.getSize(new THREE.Vector3());
      const framedCenter = framedBox.getCenter(new THREE.Vector3());
      container.dataset.modelLoaded = 'true';
      container.dataset.modelHasMorphs = String(loadedModelHasMouthMorphs);
      container.dataset.modelMeshCount = String(morphTargets.length > 0 ? new Set(morphTargets.map((target) => target.mesh.uuid)).size : 0);
      container.dataset.modelBox = `${framedSize.x.toFixed(2)},${framedSize.y.toFixed(2)},${framedSize.z.toFixed(2)}`;
      container.dataset.modelCenter = `${framedCenter.x.toFixed(2)},${framedCenter.y.toFixed(2)},${framedCenter.z.toFixed(2)}`;
      container.dataset.camera = `${camera.position.x.toFixed(2)},${camera.position.y.toFixed(2)},${camera.position.z.toFixed(2)}`;
      renderer.compile(scene, camera);
      renderer.render(scene, camera);
      setModelStatus(loadedModelHasMouthMorphs ? `${label} - ${morphTargets.length} morph targets` : `${label} - fallback mouth rig`);
    };

    const mouthRig = new THREE.Group();
    mouthRig.name = 'timeline-driven-mouth-rig';

    const mouthCavity = new THREE.Mesh(new THREE.SphereGeometry(0.28, 32, 16), mouthInterior);
    mouthCavity.name = 'mouth-cavity';
    mouthCavity.scale.set(1.25, 0.18, 0.22);
    mouthCavity.position.set(0, -0.32, 0.82);
    mouthRig.add(mouthCavity);

    const upperLip = new THREE.Mesh(new THREE.CapsuleGeometry(0.045, 0.46, 8, 24), lipMaterial);
    upperLip.name = 'upper-lip';
    upperLip.rotation.z = Math.PI / 2;
    upperLip.position.set(0, -0.285, 0.9);
    mouthRig.add(upperLip);

    const lowerLip = upperLip.clone();
    lowerLip.name = 'lower-lip';
    lowerLip.position.set(0, -0.385, 0.9);
    mouthRig.add(lowerLip);

    const upperTeeth = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.045, 0.035), teethMaterial);
    upperTeeth.name = 'upper-teeth';
    upperTeeth.position.set(0, -0.33, 0.94);
    mouthRig.add(upperTeeth);

    const lowerTeeth = upperTeeth.clone();
    lowerTeeth.name = 'lower-teeth';
    lowerTeeth.position.set(0, -0.39, 0.94);
    mouthRig.add(lowerTeeth);

    const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.18, 24, 12), new THREE.MeshStandardMaterial({ color: 0xdc626f, roughness: 0.55 }));
    tongue.name = 'tongue';
    tongue.scale.set(1.2, 0.28, 0.45);
    tongue.position.set(0, -0.43, 0.88);
    mouthRig.add(tongue);

    const jaw = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 24), skin);
    jaw.name = 'lower-jaw';
    jaw.scale.set(0.9, 0.32, 0.48);
    jaw.position.set(0, -0.82, 0.02);
    mouthRig.add(jaw);
    group.add(mouthRig);

    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.42, 0.9, 32), skin);
    neck.position.set(0, -1.5, -0.04);
    group.add(neck);

    const shoulders = new THREE.Mesh(new THREE.CapsuleGeometry(0.72, 1.7, 12, 32), accent);
    shoulders.position.set(0, -2.15, -0.05);
    shoulders.rotation.z = Math.PI / 2;
    group.add(shoulders);

    scene.add(group);

    preloadFaceModel(primaryFaceModelUrl)
      .then((gltf) => {
        if (container.isConnected) {
          registerModel(gltf.scene, 'ReadyPlayer ARKit GLB');
        }
      })
      .catch(() => preloadFaceModel(nvidiaFaceModelUrl)
        .then((gltf) => {
          if (container.isConnected) {
            registerModel(gltf.scene, 'NVIDIA James A2F-3D v3 GLB');
          }
        })
        .catch(() => preloadFallbackModel()
          .then((model) => {
            if (container.isConnected) {
              registerModel(model, 'FBX model');
            }
          })
          .catch(() => {
          container.dataset.modelLoaded = 'fallback-rig';
          container.dataset.modelHasMorphs = 'true';
          setModelStatus('Fallback face rig');
          })));

    let frameId = 0;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const now = performance.now();
      const deltaSeconds = Math.min(0.04, Math.max(0.001, (now - previousFrameTime) / 1000));
      previousFrameTime = now;
      const audio = audioRef.current;
      const isSpeaking = Boolean(audio && !audio.paused && !audio.ended);
      const frame = sampleFrameAtTime(timelineRef.current?.frames ?? [], audio?.currentTime ?? 0);
      const fallbackOpen = isReadyRef.current && isSpeaking ? 0.22 + Math.sin(Date.now() * 0.012) * 0.12 : 0.06;
      const targetJawOpen = frame?.jawOpen ?? fallbackOpen;
      const targetMouthWide = frame?.mouthWide ?? 0.24;
      const targetMouthSmile = frame?.mouthSmile ?? 0.06;
      const damping = 1 - Math.exp(-deltaSeconds * (isSpeaking ? 22 : 9));
      smoothedJawOpen += (targetJawOpen - smoothedJawOpen) * damping;
      smoothedMouthWide += (targetMouthWide - smoothedMouthWide) * damping;
      smoothedMouthSmile += (targetMouthSmile - smoothedMouthSmile) * damping;
      smoothedJawOpen = Math.max(0, Math.min(0.78, smoothedJawOpen));
      smoothedMouthWide = Math.max(0, Math.min(0.58, smoothedMouthWide));
      smoothedMouthSmile = Math.max(0, Math.min(0.22, smoothedMouthSmile));
      smoothedBlendShapes = smoothBlendShapes(smoothedBlendShapes, frame?.blendShapes, Math.min(0.56, damping * 1.28));
      const displayFrame: AnimationFrame = {
        t: frame?.t ?? 0,
        jawOpen: smoothedJawOpen,
        mouthWide: smoothedMouthWide,
        mouthSmile: smoothedMouthSmile,
        blendShapes: Object.keys(smoothedBlendShapes).length > 0 ? smoothedBlendShapes : frame?.blendShapes,
      };
      const jawOpen = displayFrame.jawOpen;
      const mouthWide = displayFrame.mouthWide;
      const mouthSmile = displayFrame.mouthSmile;

      group.position.y = 0;
      if (loadedModel) {
        loadedModel.scale.y = loadedModelHasMouthMorphs ? loadedModelBaseScale.y : loadedModelBaseScale.y * (1 + jawOpen * 0.035);
      }
      mouthRig.visible = !loadedModelHasMouthMorphs;
      mouthRig.position.y = loadedModel ? 0.08 : 0;
      mouthRig.position.z = loadedModel ? 0.35 : 0;
      mouthCavity.scale.set(1.05 + mouthWide * 0.8, 0.16 + jawOpen * 1.25, 0.24 + jawOpen * 0.24);
      upperLip.position.y = -0.285 + mouthSmile * 0.025;
      lowerLip.position.y = -0.385 - jawOpen * 0.22 + mouthSmile * 0.018;
      upperLip.scale.set(1 + mouthWide * 0.45, 1, 1);
      lowerLip.scale.set(1 + mouthWide * 0.55, 1, 1);
      upperTeeth.position.y = -0.335 - jawOpen * 0.015;
      lowerTeeth.position.y = -0.39 - jawOpen * 0.2;
      lowerTeeth.visible = jawOpen > 0.12;
      tongue.position.y = -0.43 - jawOpen * 0.1;
      tongue.visible = jawOpen > 0.18;
      jaw.position.y = -0.86 - jawOpen * 0.18;
      jaw.scale.y = 0.34 + jawOpen * 0.28;
      for (const target of morphTargets) {
        if (target.mesh.morphTargetInfluences) {
          target.mesh.morphTargetInfluences[target.index] = getBlendShapeValue(displayFrame, target.name, jawOpen);
        }
      }
      container.dataset.mouthDrive = 'timeline';
      container.dataset.jawOpen = jawOpen.toFixed(3);
      container.dataset.mouthWide = mouthWide.toFixed(3);
      container.dataset.mouthSmile = mouthSmile.toFixed(3);
      container.dataset.smoothing = damping.toFixed(3);
      container.dataset.mouthRig = loadedModelHasMouthMorphs ? 'nvidia-a2f-v3-morphs' : 'morphable';
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
  }, []);

  return (
    <div className="faceViewerCard">
      <div className="faceViewerHeader">
        <div>
          <p className="eyebrow">Live Preview</p>
          <h2>Avatar render</h2>
        </div>
        <span className={isReady ? 'badge badgeOk' : 'badge badgeWarn'}>{isReady ? 'ready' : 'idle'}</span>
      </div>
      <div className="faceCanvas" ref={containerRef} role="img" aria-label="3D speaking face model preview">
        <div className="faceFallback">Loading avatar</div>
      </div>
      {audioUrl ? <audio className="faceAudio" controls preload="auto" ref={audioRef} src={audioUrl} /> : <p className="muted">No speech rendered yet.</p>}
      <div className="previewMeta">
        <span>{modelStatus}</span>
        <span>{timelineStatus}</span>
      </div>
    </div>
  );
}

function frameCamera(camera: THREE.PerspectiveCamera, object: THREE.Object3D, container: HTMLElement): void {
  const box = visibleBoxFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxAxis = Math.max(size.x, size.y, size.z) || 1;
  const distance = maxAxis / (2 * Math.tan((camera.fov * Math.PI) / 360));
  camera.position.set(center.x, center.y + size.y * 0.03, center.z + distance * 1.18);
  camera.near = Math.max(0.01, distance / 80);
  camera.far = Math.max(100, distance * 80);
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.lookAt(center);
  camera.updateProjectionMatrix();
}

function visibleBoxFromObject(object: THREE.Object3D): THREE.Box3 {
  const box = new THREE.Box3();
  const meshBox = new THREE.Box3();
  object.updateWorldMatrix(true, true);
  object.traverse((child) => {
    if (!(child instanceof THREE.Mesh) || !child.visible) {
      return;
    }
    const geometry = child.geometry;
    geometry.computeBoundingBox();
    if (geometry.boundingBox) {
      meshBox.copy(geometry.boundingBox).applyMatrix4(child.matrixWorld);
      box.union(meshBox);
    }
  });
  return box.isEmpty() ? new THREE.Box3().setFromObject(object) : box;
}

function getBlendShapeValue(frame: AnimationFrame | null, targetName: string, fallbackJawOpen: number): number {
  const blendShapes = frame?.blendShapes;
  if (blendShapes) {
    const directValue = blendShapes[targetName] ?? blendShapes[lowerFirst(targetName)] ?? blendShapes[upperFirst(targetName)];
    if (typeof directValue === 'number') {
      return scaleBlendShape(targetName, directValue);
    }
    return 0;
  }
  return /jaw|mouth|viseme|open|aa|oh|ou/i.test(targetName) ? scaleBlendShape(targetName, fallbackJawOpen) : 0;
}

function scaleBlendShape(targetName: string, value: number): number {
  const normalized = targetName.toLowerCase();
  let multiplier = 1;
  if (normalized.includes('jawopen')) {
    multiplier = 1.34;
  } else if (normalized.includes('mouthfunnel') || normalized.includes('mouthpucker')) {
    multiplier = 1.25;
  } else if (normalized.includes('mouthstretch')) {
    multiplier = 0.86;
  } else if (normalized.includes('mouthsmile')) {
    multiplier = 0.72;
  } else if (normalized.includes('mouthclose') || normalized.includes('mouthpress')) {
    multiplier = 0.9;
  } else if (normalized.includes('mouthlowerdown') || normalized.includes('mouthupperup')) {
    multiplier = 1.16;
  } else if (normalized.includes('tongue')) {
    multiplier = 0.55;
  }
  return Math.max(0, Math.min(1, value * multiplier));
}

function lowerFirst(value: string): string {
  return value.length > 0 ? value[0].toLowerCase() + value.slice(1) : value;
}

function upperFirst(value: string): string {
  return value.length > 0 ? value[0].toUpperCase() + value.slice(1) : value;
}

function sampleFrameAtTime(frames: AnimationFrame[], time: number): AnimationFrame | null {
  if (frames.length === 0) {
    return null;
  }
  if (time <= frames[0].t) {
    return frames[0];
  }
  for (let index = 1; index < frames.length; index += 1) {
    const next = frames[index];
    if (next.t >= time) {
      const previous = frames[index - 1];
      const span = Math.max(0.001, next.t - previous.t);
      const amount = Math.max(0, Math.min(1, (time - previous.t) / span));
      return interpolateFrame(previous, next, easeInOut(amount));
    }
  }
  return frames[frames.length - 1];
}

function interpolateFrame(previous: AnimationFrame, next: AnimationFrame, amount: number): AnimationFrame {
  return {
    t: previous.t + (next.t - previous.t) * amount,
    jawOpen: lerp(previous.jawOpen, next.jawOpen, amount),
    mouthWide: lerp(previous.mouthWide, next.mouthWide, amount),
    mouthSmile: lerp(previous.mouthSmile, next.mouthSmile, amount),
    blendShapes: interpolateBlendShapes(previous.blendShapes, next.blendShapes, amount),
  };
}

function interpolateBlendShapes(
  previous: Record<string, number> | undefined,
  next: Record<string, number> | undefined,
  amount: number,
): Record<string, number> | undefined {
  if (!previous && !next) {
    return undefined;
  }
  const keys = new Set([...Object.keys(previous ?? {}), ...Object.keys(next ?? {})]);
  const values: Record<string, number> = {};
  for (const key of keys) {
    values[key] = lerp(previous?.[key] ?? 0, next?.[key] ?? 0, amount);
  }
  return values;
}

function smoothBlendShapes(
  current: Record<string, number>,
  target: Record<string, number> | undefined,
  amount: number,
): Record<string, number> {
  const keys = new Set([...Object.keys(current), ...Object.keys(target ?? {})]);
  const nextValues: Record<string, number> = {};
  for (const key of keys) {
    const nextValue = current[key] + ((target?.[key] ?? 0) - (current[key] ?? 0)) * amount;
    if (Math.abs(nextValue) > 0.001) {
      nextValues[key] = Math.max(0, Math.min(1, nextValue));
    }
  }
  return nextValues;
}

function easeInOut(value: number): number {
  return value * value * (3 - 2 * value);
}

function lerp(start: number, end: number, amount: number): number {
  return start + (end - start) * amount;
}
