import { useEffect, useRef, useState } from 'react';

/**
 * Hero3DAircraft — real GLTF aircraft (frontend/public/models/G4_LARC_AIR_0824.glb,
 * the team's G4/LaRC model) with auto-rotation (~20 s/turn), drag-to-orbit,
 * vertical float, pitch rock, and a soft contact-shadow disc.
 *
 * three.js r147 + its non-module GLTFLoader come from jsDelivr (same CDN
 * pattern as before — no bundler dependency). The GLB is a glTF 2.0 binary
 * with embedded textures, so one file is all we need. The model is normalized
 * (centered + fitted) after load, so lighting and camera framing stay stable
 * regardless of the authoring scale. If the GLB or CDN fails, the previous
 * procedural Stitch plane is built instead — the hero is never empty.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
declare global {
  interface Window {
    THREE?: any;
  }
}

const MODEL_URL = '/models/G4_LARC_AIR_0824.glb';
const THREE_BASE = 'https://cdn.jsdelivr.net/npm/three@0.147.0';

/** Injects three.js r147 + examples GLTFLoader once, resolves when both exist. */
function loadThreeWithGLTF(): Promise<void> {
  if (window.THREE?.GLTFLoader) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const three = document.createElement('script');
    three.src = `${THREE_BASE}/build/three.min.js`;
    three.async = true;
    three.dataset.threeHero = 'three';
    three.onload = () => {
      const loader = document.createElement('script');
      loader.src = `${THREE_BASE}/examples/js/loaders/GLTFLoader.js`;
      loader.async = true;
      loader.dataset.threeHero = 'gltf';
      loader.onload = () => resolve();
      loader.onerror = () => reject(new Error('GLTFLoader failed to load'));
      document.head.appendChild(loader);
    };
    three.onerror = () => reject(new Error('three.js failed to load'));
    document.head.appendChild(three);
  });
}

/** The procedural Stitch plane — kept as the automatic fallback. */
function buildProceduralPlane(THREE: any, scene: any): any {
  const airplane = new THREE.Group();

  const bodyMat = new THREE.MeshPhongMaterial({ color: 0xffffff, specular: 0x90caf9, shininess: 40 });
  const wingMat = new THREE.MeshPhongMaterial({ color: 0xf0f4f9, specular: 0x64b5f6, shininess: 50 });
  const accentBlueMat = new THREE.MeshPhongMaterial({ color: 0x1b78b4, specular: 0xffffff, shininess: 70 });
  const glassMat = new THREE.MeshPhongMaterial({
    color: 0x1a365d, specular: 0xffffff, shininess: 90, transparent: true, opacity: 0.85,
  });
  const engineMat = new THREE.MeshPhongMaterial({ color: 0xcfd8dc, specular: 0xffffff, shininess: 60 });

  const fuselageGeo = new THREE.CylinderGeometry(1.2, 0.9, 13, 32);
  fuselageGeo.rotateZ(Math.PI / 2);
  airplane.add(new THREE.Mesh(fuselageGeo, bodyMat));

  const noseGeo = new THREE.ConeGeometry(1.2, 3.2, 32);
  noseGeo.rotateZ(-Math.PI / 2);
  const nose = new THREE.Mesh(noseGeo, bodyMat);
  nose.position.x = 8.1;
  airplane.add(nose);

  const cockpitGeo = new THREE.SphereGeometry(1.1, 16, 16, 0, Math.PI, 0, Math.PI / 2.5);
  const cockpit = new THREE.Mesh(cockpitGeo, glassMat);
  cockpit.rotation.z = -Math.PI / 3;
  cockpit.rotation.y = Math.PI / 2;
  cockpit.position.set(7.2, 0.45, 0);
  cockpit.scale.set(0.9, 0.75, 1.1);
  airplane.add(cockpit);

  const tailConeGeo = new THREE.ConeGeometry(0.9, 4.2, 32);
  tailConeGeo.rotateZ(Math.PI / 2);
  const tailCone = new THREE.Mesh(tailConeGeo, bodyMat);
  tailCone.position.x = -8.6;
  airplane.add(tailCone);

  const wingShape = new THREE.Shape();
  wingShape.moveTo(0, 0);
  wingShape.lineTo(-2.2, 11);
  wingShape.lineTo(-3.6, 10.8);
  wingShape.lineTo(-1.8, 0);
  wingShape.closePath();
  const wingGeo = new THREE.ExtrudeGeometry(wingShape, {
    depth: 0.18, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.08, bevelThickness: 0.08,
  });

  const rightWing = new THREE.Mesh(wingGeo, wingMat);
  rightWing.rotation.set(Math.PI / 2, 0.05, -Math.PI / 2);
  rightWing.position.set(2.5, -0.15, 0);
  airplane.add(rightWing);

  const leftWing = new THREE.Mesh(wingGeo, wingMat);
  leftWing.rotation.set(-Math.PI / 2, -0.05, -Math.PI / 2);
  leftWing.position.set(2.5, -0.15, 0);
  airplane.add(leftWing);

  const wingletGeo = new THREE.BoxGeometry(0.8, 0.9, 0.1);
  const wingletR = new THREE.Mesh(wingletGeo, accentBlueMat);
  wingletR.position.set(-8.4, 0.4, 11);
  airplane.add(wingletR);
  const wingletL = new THREE.Mesh(wingletGeo, accentBlueMat);
  wingletL.position.set(-8.4, 0.4, -11);
  airplane.add(wingletL);

  const finShape = new THREE.Shape();
  finShape.moveTo(0, 0);
  finShape.lineTo(-2.8, 4.5);
  finShape.lineTo(-4.2, 4.3);
  finShape.lineTo(-3.2, 0);
  finShape.closePath();
  const finGeo = new THREE.ExtrudeGeometry(finShape, {
    depth: 0.2, bevelEnabled: true, bevelSegments: 2, bevelSize: 0.05, bevelThickness: 0.05,
  });
  const verticalFin = new THREE.Mesh(finGeo, accentBlueMat);
  verticalFin.position.set(-7.5, 0.7, -0.1);
  airplane.add(verticalFin);

  const hStab = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.14, 7.2), wingMat);
  hStab.position.set(-9.8, 0.7, 0);
  airplane.add(hStab);

  function createEngine(sideZ: number) {
    const g = new THREE.Group();
    const nacelleGeo = new THREE.CylinderGeometry(0.65, 0.6, 3.2, 24);
    nacelleGeo.rotateZ(Math.PI / 2);
    g.add(new THREE.Mesh(nacelleGeo, engineMat));
    const intakeGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 24);
    intakeGeo.rotateZ(Math.PI / 2);
    const intake = new THREE.Mesh(intakeGeo, glassMat);
    intake.position.x = 1.5;
    g.add(intake);
    const pylon = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.8, 0.15), bodyMat);
    pylon.position.set(0, 0.6, 0);
    g.add(pylon);
    g.position.set(1.2, -1.1, sideZ);
    return g;
  }
  airplane.add(createEngine(4.6));
  airplane.add(createEngine(-4.6));

  const nodeGeo = new THREE.SphereGeometry(0.22, 16, 16);
  const inspectNode1 = new THREE.Mesh(nodeGeo, new THREE.MeshBasicMaterial({ color: 0x5cc4df }));
  inspectNode1.position.set(0.5, 0.1, 4.2);
  airplane.add(inspectNode1);
  const inspectNode2 = new THREE.Mesh(nodeGeo, new THREE.MeshBasicMaterial({ color: 0xf5c443 }));
  inspectNode2.position.set(4.0, 0.8, 0.6);
  airplane.add(inspectNode2);

  return airplane;
}

/** Soft radial contact-shadow texture (same as the original Stitch scene). */
function makeShadowDisc(THREE: any): any {
  const shadowCanvas = document.createElement('canvas');
  shadowCanvas.width = 128;
  shadowCanvas.height = 128;
  const ctx = shadowCanvas.getContext('2d')!;
  const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gradient.addColorStop(0, 'rgba(44, 110, 203, 0.35)');
  gradient.addColorStop(0.4, 'rgba(44, 110, 203, 0.15)');
  gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 128, 128);
  return new THREE.Mesh(
    new THREE.PlaneGeometry(22, 14),
    new THREE.MeshBasicMaterial({
      map: new THREE.CanvasTexture(shadowCanvas),
      transparent: true,
      opacity: 0.65,
      depthWrite: false,
    })
  );
}

interface Hero3DAircraftProps {
  /** Accessible label for the canvas region */
  label?: string;
}

export const Hero3DAircraft: React.FC<Hero3DAircraftProps> = ({ label = '3D rotating aircraft' }) => {
  const hostRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    let disposed = false;
    let cleanup: (() => void) | undefined;

    loadThreeWithGLTF()
      .then(() => {
        if (disposed || !host) return;
        const THREE = window.THREE;
        if (!THREE) return;

        const width = host.clientWidth || 600;
        const height = host.clientHeight || 520;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        // Real framing happens in frameCamera() once the model's size is known,
        // so the plane always fits the frustum — no invisible-box clipping.
        camera.position.set(0, 4.5, 26);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(width, height);
        if (THREE.sRGBEncoding) renderer.outputEncoding = THREE.sRGBEncoding;
        host.appendChild(renderer.domElement);

        // Lighting: neutral key + cool fill for the PBR materials in the GLB
        scene.add(new THREE.AmbientLight(0xffffff, 0.9));
        const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
        dirLight.position.set(15, 25, 20);
        scene.add(dirLight);
        const blueRim = new THREE.DirectionalLight(0x2c6ecb, 0.8);
        blueRim.position.set(-15, -10, -10);
        scene.add(blueRim);

        // Soft contact-shadow disc (float animation scales it)
        const shadowPlane = makeShadowDisc(THREE);
        shadowPlane.rotation.x = -Math.PI / 2;
        shadowPlane.position.y = -6.2;
        scene.add(shadowPlane);

        // Pivot: rotation animates this; the model inside is normalized.
        const pivot = new THREE.Group();
        pivot.rotation.set(0.1, -Math.PI / 4, 0.05);
        scene.add(pivot);

        let source = 'gltf';
        let halfLength = 11.25; // updated by mountModel — drives camera framing

        // Place the camera so the model's long axis fits the visible frustum at
        // ANY rotation angle, filling as much of the canvas as possible.
        const frameCamera = () => {
          const vHalfTan = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
          const hHalfTan = vHalfTan * camera.aspect;
          // 1.0 margin = maximum zoom: broadside wingspan exactly touches the
          // frame edge without crossing it. Raise this if anything ever clips.
          const dist = Math.max(halfLength / hHalfTan, (halfLength * 0.6) / vHalfTan) * 1.0;
          camera.position.set(0, dist * 0.16, dist);
          camera.lookAt(0, 0, 0);
        };

        const mountModel = (object: any) => {
          // Center + fit the authored model; its length drives camera framing.
          const box = new THREE.Box3().setFromObject(object);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          const maxDim = Math.max(size.x, size.y, size.z) || 1;
          const fit = 22.5 / maxDim;
          object.scale.setScalar(fit);
          object.position.set(-center.x * fit, -center.y * fit, -center.z * fit);
          pivot.add(object);
          halfLength = (maxDim * fit) / 2;
          frameCamera();
        };

        const startLoop = () => {
          let isDragging = false;
          let previousMousePosition = { x: 0, y: 0 };
          let userRotationY = 0;
          let userRotationX = 0;
          const autoRotateSpeed = (2 * Math.PI) / 45; // radians/sec — one slow turn every ~45 s

          const onPointerDown = (e: PointerEvent) => {
            isDragging = true;
            previousMousePosition = { x: e.clientX, y: e.clientY };
          };
          const onPointerMove = (e: PointerEvent) => {
            if (!isDragging) return;
            userRotationY += (e.clientX - previousMousePosition.x) * 0.008;
            userRotationX = Math.max(-0.5, Math.min(0.5, userRotationX + (e.clientY - previousMousePosition.y) * 0.005));
            previousMousePosition = { x: e.clientX, y: e.clientY };
          };
          const onPointerUp = () => {
            isDragging = false;
          };
          const onWindowResize = () => {
            const w = host.clientWidth || 600;
            const h = host.clientHeight || 520;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
            frameCamera(); // re-frame when the container aspect changes
          };

          host.addEventListener('pointerdown', onPointerDown);
          window.addEventListener('pointermove', onPointerMove);
          window.addEventListener('pointerup', onPointerUp);
          window.addEventListener('resize', onWindowResize);

          const clock = new THREE.Clock();
          let lastT = 0;
          let raf = 0;
          const animate = () => {
            raf = requestAnimationFrame(animate);
            const t = clock.getElapsedTime();
            // delta-time based so the spin is identical on 60 Hz and 120 Hz screens
            const dt = Math.min(0.05, t - lastT);
            lastT = t;

            if (!isDragging) userRotationY += autoRotateSpeed * dt;

            pivot.rotation.y = -Math.PI / 4 + userRotationY;
            pivot.rotation.x = 0.1 + userRotationX;

            renderer.render(scene, camera);
          };
          animate();

          cleanup = () => {
            cancelAnimationFrame(raf);
            host.removeEventListener('pointerdown', onPointerDown);
            window.removeEventListener('pointermove', onPointerMove);
            window.removeEventListener('pointerup', onPointerUp);
            window.removeEventListener('resize', onWindowResize);
            renderer.dispose();
            if (renderer.domElement.parentElement === host) {
              host.removeChild(renderer.domElement);
            }
          };
        };

        const onGltf = (gltf: any) => {
          if (disposed) return;
          mountModel(gltf.scene);
          setLoading(false);
          startLoop();
        };

        const onGltfError = () => {
          if (disposed) return;
          // GLB unavailable → fall back to the procedural Stitch plane.
          source = 'procedural';
          mountModel(buildProceduralPlane(THREE, scene));
          setLoading(false);
          startLoop();
        };

        try {
          new THREE.GLTFLoader().load(MODEL_URL, onGltf, undefined, onGltfError);
        } catch {
          onGltfError();
        }
        void source;
      })
      .catch(() => {
        // CDN unavailable — leave the container empty; layout still holds.
        if (!disposed) setLoading(false);
      });

    return () => {
      disposed = true;
      cleanup?.();
    };
  }, []);

  return (
    <div className="relative w-full h-full">
      <div
        ref={hostRef}
        role="img"
        aria-label={label}
        className="w-full h-full cursor-grab active:cursor-grabbing select-none touch-none"
      />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <span className="material-symbols-outlined text-[36px] text-aero-ocean animate-spin">
            progress_activity
          </span>
        </div>
      )}
    </div>
  );
};

export default Hero3DAircraft;
