import { useEffect, useRef, useState } from 'react';
import { RotateCcw, SlidersHorizontal } from 'lucide-react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { AnimationFrame, AnimationTimeline, fetchAnimationTimeline } from '../services/api';

type FaceViewerProps = {
  isReady: boolean;
  audioUrl?: string | null;
  animationUrl?: string | null;
  modelUrl?: string;
  modelLabel?: string;
  faceScale?: number;
  expressionIntensity?: number;
  onOpenSettings?: () => void;
};

type FaceModel = Awaited<ReturnType<GLTFLoader['loadAsync']>>;

const primaryFaceModelUrl = import.meta.env.VITE_FACE_MODEL_URL ?? '/models/readyplayer-talk-arkit.glb';

const faceModelPromises = new Map<string, Promise<FaceModel>>();

function preloadFaceModel(url: string): Promise<FaceModel> {
  if (!faceModelPromises.has(url)) {
    faceModelPromises.set(url, new GLTFLoader().loadAsync(url));
  }
  return faceModelPromises.get(url)!;
}

type ViewerTuning = {
  faceScale: number;
  expressionIntensity: number;
};

type NaturalExpression = {
  blink: number;
  brow: number;
  squint: number;
  smile: number;
  cheek: number;
};

export function FaceViewer({
  isReady,
  audioUrl,
  animationUrl,
  modelUrl = primaryFaceModelUrl,
  modelLabel = 'ReadyPlayer ARKit',
  faceScale = 1,
  expressionIntensity = 0.68,
  onOpenSettings,
}: FaceViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const previousAudioUrlRef = useRef<string | null>(null);
  const timelineRef = useRef<AnimationTimeline | null>(null);
  const isReadyRef = useRef(isReady);
  const tuningRef = useRef<ViewerTuning>({ faceScale, expressionIntensity });
  const [timelineStatus, setTimelineStatus] = useState('Idle');
  const [modelStatus, setModelStatus] = useState('');
  const [isPlaybackBlocked, setIsPlaybackBlocked] = useState(false);

  useEffect(() => {
    isReadyRef.current = isReady;
  }, [isReady]);

  useEffect(() => {
    tuningRef.current = { faceScale, expressionIntensity };
  }, [faceScale, expressionIntensity]);

  useEffect(() => {
    const audio = audioRef.current;
    const previousAudioUrl = previousAudioUrlRef.current;
    if (previousAudioUrl && previousAudioUrl !== audioUrl && previousAudioUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previousAudioUrl);
    }
    previousAudioUrlRef.current = audioUrl ?? null;

    if (!audio) {
      return;
    }
    audio.pause();
    audio.currentTime = 0;

    if (!audioUrl) {
      audio.removeAttribute('src');
      audio.load();
      setIsPlaybackBlocked(false);
      return;
    }

    audio.preload = 'auto';
    audio.load();
    const playPromise = audio.play();
    if (playPromise) {
      playPromise.then(() => setIsPlaybackBlocked(false)).catch(() => setIsPlaybackBlocked(true));
    }
  }, [audioUrl]);

  useEffect(() => {
    return () => {
      const audio = audioRef.current;
      if (audio) {
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
      }
      const previousAudioUrl = previousAudioUrlRef.current;
      if (previousAudioUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(previousAudioUrl);
      }
      previousAudioUrlRef.current = null;
    };
  }, []);

  function handleReplayLatest() {
    const audio = audioRef.current;
    if (!audio || !audioUrl) {
      return;
    }
    audio.pause();
    audio.currentTime = 0;
    const playPromise = audio.play();
    if (playPromise) {
      playPromise.then(() => setIsPlaybackBlocked(false)).catch(() => setIsPlaybackBlocked(true));
    }
  }

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
    container.dataset.modelLoaded = 'loading';
    container.dataset.mouthRig = 'none';
    setModelStatus('');

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020617);

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0.05, 4.2);
    camera.lookAt(0, 0, 0);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch {
      container.dataset.renderError = 'webgl-unavailable';
      setModelStatus('WebGL unavailable');
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
    group.visible = false;

    const head = new THREE.Group();
    group.add(head);

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
      morphTargets.length = 0;
      model.traverse((object) => {
        if (object instanceof THREE.Mesh && /wolf3d_(body|outfit|footwear)/i.test(object.name)) {
          object.visible = false;
        }
      });
      const box = visibleBoxFromObject(model);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const maxAxis = Math.max(size.x, size.y, size.z) || 1;
      const baseScalar = 2.35 / maxAxis;
      model.scale.setScalar(baseScalar);
      model.position.sub(center.multiplyScalar(baseScalar));
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
      head.clear();
      head.add(model);
      loadedModel = model;
      loadedModelBaseScale.copy(model.scale);
      group.visible = true;
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
      setModelStatus(loadedModelHasMouthMorphs ? `${label} - ${morphTargets.length} morph targets` : `${label} - no mouth morphs`);
    };

    scene.add(group);

    preloadFaceModel(modelUrl)
      .then((gltf) => {
        if (container.isConnected) {
          registerModel(gltf.scene, modelLabel);
        }
      })
      .catch(() => {
        container.dataset.modelLoaded = 'false';
        setModelStatus('Avatar model unavailable');
      });

    let frameId = 0;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const now = performance.now();
      const deltaSeconds = Math.min(0.04, Math.max(0.001, (now - previousFrameTime) / 1000));
      previousFrameTime = now;
      const audio = audioRef.current;
      const isSpeaking = Boolean(audio && !audio.paused && !audio.ended);
      const frame = sampleFrameAtTime(timelineRef.current?.frames ?? [], audio?.currentTime ?? 0);
      const tuning = tuningRef.current;
      const naturalExpression = buildNaturalExpression(now, isSpeaking, tuning.expressionIntensity);
      const restOpen = isReadyRef.current && isSpeaking ? 0.22 + Math.sin(Date.now() * 0.012) * 0.12 : 0.06;
      const targetJawOpen = frame?.jawOpen ?? restOpen;
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
        const breathing = 1 + Math.sin(now * 0.0018) * 0.006 * tuning.expressionIntensity;
        loadedModel.scale.set(
          loadedModelBaseScale.x * tuning.faceScale,
          loadedModelBaseScale.y * tuning.faceScale * breathing,
          loadedModelBaseScale.z * tuning.faceScale,
        );
        loadedModel.rotation.x = Math.sin(now * 0.0013) * 0.014 * tuning.expressionIntensity + (isSpeaking ? -jawOpen * 0.018 : 0);
        loadedModel.rotation.y = Math.sin(now * 0.001) * 0.025 * tuning.expressionIntensity;
        loadedModel.rotation.z = Math.sin(now * 0.0008) * 0.01 * tuning.expressionIntensity;
      }
      for (const target of morphTargets) {
        if (target.mesh.morphTargetInfluences) {
          target.mesh.morphTargetInfluences[target.index] = getBlendShapeValue(displayFrame, target.name, jawOpen, naturalExpression);
        }
      }
      container.dataset.mouthDrive = 'timeline';
      container.dataset.jawOpen = jawOpen.toFixed(3);
      container.dataset.mouthWide = mouthWide.toFixed(3);
      container.dataset.mouthSmile = mouthSmile.toFixed(3);
      container.dataset.blink = naturalExpression.blink.toFixed(3);
      container.dataset.expression = tuning.expressionIntensity.toFixed(2);
      container.dataset.smoothing = damping.toFixed(3);
      container.dataset.mouthRig = loadedModelHasMouthMorphs ? 'model-morphs' : 'none';
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
  }, [modelLabel, modelUrl]);

  return (
    <div className="faceViewerCard">
      <div className="faceViewerHeader">
        <div>
          <p className="eyebrow">Live</p>
          <h2>{modelLabel}</h2>
        </div>
        <div className="faceViewerActions">
          {onOpenSettings && (
            <button className="iconButton secondary" type="button" aria-label="Avatar" title="Avatar" onClick={onOpenSettings}>
              <SlidersHorizontal size={17} />
            </button>
          )}
          {audioUrl && (
            <button
              className={isPlaybackBlocked ? 'iconButton secondary playbackBlocked' : 'iconButton secondary'}
              type="button"
              aria-label="Replay latest answer"
              title="Replay latest answer"
              onClick={handleReplayLatest}
            >
              <RotateCcw size={17} />
            </button>
          )}
          <span className={isReady ? 'badge badgeOk' : 'badge badgeWarn'}>{isReady ? 'ready' : 'idle'}</span>
        </div>
      </div>
      <div className="faceCanvas" ref={containerRef} role="img" aria-label="3D speaking face model preview">
        <div className="facePlaceholder" aria-hidden="true">
          <span className="faceLoadingTrack">
            <span />
          </span>
        </div>
      </div>
      <audio className="faceAudioHidden" preload="auto" ref={audioRef} src={audioUrl ?? undefined} />
      {!audioUrl && <p className="muted">No speech rendered yet.</p>}
      <div className="previewMeta">
        {modelStatus && <span>{modelStatus}</span>}
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

function buildNaturalExpression(now: number, isSpeaking: boolean, intensity: number): NaturalExpression {
  const normalizedIntensity = Math.max(0, Math.min(1, intensity));
  const blinkWave = Math.sin(now * 0.0034);
  const blink = Math.max(0, Math.pow(blinkWave, 28)) * 0.9 * normalizedIntensity;
  const talkEnergy = isSpeaking ? 1 : 0.32;
  return {
    blink,
    brow: (0.08 + Math.sin(now * 0.0011) * 0.045 + (isSpeaking ? 0.035 : 0)) * normalizedIntensity,
    squint: (0.045 + Math.sin(now * 0.0017 + 1.8) * 0.025) * normalizedIntensity,
    smile: (0.05 + Math.sin(now * 0.0012 + 0.6) * 0.025 + talkEnergy * 0.035) * normalizedIntensity,
    cheek: (0.04 + Math.sin(now * 0.0016 + 2.2) * 0.025 + talkEnergy * 0.025) * normalizedIntensity,
  };
}

function getBlendShapeValue(frame: AnimationFrame | null, targetName: string, restJawOpen: number, expression: NaturalExpression): number {
  const blendShapes = frame?.blendShapes;
  const expressionValue = expressionBlendShapeValue(targetName, expression);
  if (blendShapes) {
    const directValue = blendShapes[targetName] ?? blendShapes[lowerFirst(targetName)] ?? blendShapes[upperFirst(targetName)];
    if (typeof directValue === 'number') {
      return Math.max(scaleBlendShape(targetName, directValue), expressionValue);
    }
    return expressionValue;
  }
  const restValue = /jaw|mouth|viseme|open|aa|oh|ou/i.test(targetName) ? scaleBlendShape(targetName, restJawOpen) : 0;
  return Math.max(restValue, expressionValue);
}

function expressionBlendShapeValue(targetName: string, expression: NaturalExpression): number {
  const normalized = targetName.toLowerCase();
  if (normalized.includes('eyeblink')) {
    return expression.blink;
  }
  if (normalized.includes('eyesquint')) {
    return expression.squint;
  }
  if (normalized.includes('browinnerup') || normalized.includes('browouterup')) {
    return expression.brow;
  }
  if (normalized.includes('mouthsmile')) {
    return expression.smile;
  }
  if (normalized.includes('cheeksquint')) {
    return expression.cheek;
  }
  return 0;
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
