import { useEffect, useRef } from 'react';

/**
 * Hero3DAircraft — React port of the Stitch three.js hero scene
 * (stitch/three.js.html). Procedural aircraft with auto-rotation (~20 s/turn),
 * drag-to-orbit, vertical float, pitch rock, and a soft contact-shadow disc.
 *
 * three.js r125 is loaded from the same CDN the Stitch file used; the scene
 * code below is a faithful port with a React-safe mount/unmount lifecycle.
 */

declare global {
  interface Window {
    THREE?: unknown;
  }
}

/** Injects the three.js r125 script once and resolves when loaded. */
function loadThree(): Promise<void> {
  if (window.THREE) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-three-r125]');
    if (existing) {
      existing.addEventListener('load', () => resolve());
      existing.addEventListener('error', () => reject(new Error('three.js failed to load')));
      return;
    }
    const s = document.createElement('script');
    s.src = 'https://ajax.googleapis.com/ajax/libs/threejs/r125/three.min.js';
    s.async = true;
    s.dataset.threeR125 = 'true';
    s.onload = () => resolve();
    s.onerror = () => reject(new Error('three.js failed to load'));
    document.head.appendChild(s);
  });
}

interface Hero3DAircraftProps {
  /** Accessible label for the canvas region */
  label?: string;
}

export const Hero3DAircraft: React.FC<Hero3DAircraftProps> = ({ label = '3D rotating aircraft' }) => {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    let disposed = false;
    let cleanup: (() => void) | undefined;

    loadThree()
      .then(() => {
        if (disposed || !host) return;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const THREE = (window as any).THREE;
        if (!THREE) return;

        const width = host.clientWidth || 600;
        const height = host.clientHeight || 520;

        const scene = new THREE.Scene();

        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.set(0, 8, 24);

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(width, height);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        host.appendChild(renderer.domElement);

        // Lighting (identical to Stitch)
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xdff0ff, 1.2);
        dirLight.position.set(15, 25, 20);
        scene.add(dirLight);

        const blueRimLight = new THREE.DirectionalLight(0x2c6ecb, 0.7);
        blueRimLight.position.set(-15, -10, -10);
        scene.add(blueRimLight);

        // Aircraft group
        const airplane = new THREE.Group();

        const bodyMat = new THREE.MeshPhongMaterial({ color: 0xffffff, specular: 0x90caf9, shininess: 40 });
        const wingMat = new THREE.MeshPhongMaterial({ color: 0xf0f4f9, specular: 0x64b5f6, shininess: 50 });
        const accentBlueMat = new THREE.MeshPhongMaterial({ color: 0x1b78b4, specular: 0xffffff, shininess: 70 });
        const glassMat = new THREE.MeshPhongMaterial({
          color: 0x1a365d, specular: 0xffffff, shininess: 90, transparent: true, opacity: 0.85,
        });
        const engineMat = new THREE.MeshPhongMaterial({ color: 0xcfd8dc, specular: 0xffffff, shininess: 60 });

        // Fuselage
        const fuselageGeo = new THREE.CylinderGeometry(1.2, 0.9, 13, 32);
        fuselageGeo.rotateZ(Math.PI / 2);
        airplane.add(new THREE.Mesh(fuselageGeo, bodyMat));

        // Nose cone
        const noseGeo = new THREE.ConeGeometry(1.2, 3.2, 32);
        noseGeo.rotateZ(-Math.PI / 2);
        const nose = new THREE.Mesh(noseGeo, bodyMat);
        nose.position.x = 8.1;
        airplane.add(nose);

        // Cockpit windshield
        const cockpitGeo = new THREE.SphereGeometry(1.1, 16, 16, 0, Math.PI, 0, Math.PI / 2.5);
        const cockpit = new THREE.Mesh(cockpitGeo, glassMat);
        cockpit.rotation.z = -Math.PI / 3;
        cockpit.rotation.y = Math.PI / 2;
        cockpit.position.set(7.2, 0.45, 0);
        cockpit.scale.set(0.9, 0.75, 1.1);
        airplane.add(cockpit);

        // Tail cone
        const tailConeGeo = new THREE.ConeGeometry(0.9, 4.2, 32);
        tailConeGeo.rotateZ(Math.PI / 2);
        const tailCone = new THREE.Mesh(tailConeGeo, bodyMat);
        tailCone.position.x = -8.6;
        airplane.add(tailCone);

        // Wings (swept-back, extruded shape)
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

        // Winglets
        const wingletGeo = new THREE.BoxGeometry(0.8, 0.9, 0.1);
        const wingletR = new THREE.Mesh(wingletGeo, accentBlueMat);
        wingletR.position.set(-8.4, 0.4, 11);
        airplane.add(wingletR);
        const wingletL = new THREE.Mesh(wingletGeo, accentBlueMat);
        wingletL.position.set(-8.4, 0.4, -11);
        airplane.add(wingletL);

        // Vertical stabilizer
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

        // Horizontal stabilizers
        const hStab = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.14, 7.2), wingMat);
        hStab.position.set(-9.8, 0.7, 0);
        airplane.add(hStab);

        // Engines
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

        // Inspection target nodes (AI damage-detection highlights)
        const nodeGeo = new THREE.SphereGeometry(0.22, 16, 16);
        const inspectNode1 = new THREE.Mesh(nodeGeo, new THREE.MeshBasicMaterial({ color: 0x5cc4df }));
        inspectNode1.position.set(0.5, 0.1, 4.2);
        airplane.add(inspectNode1);
        const inspectNode2 = new THREE.Mesh(nodeGeo, new THREE.MeshBasicMaterial({ color: 0xf5c443 }));
        inspectNode2.position.set(4.0, 0.8, 0.6);
        airplane.add(inspectNode2);

        // Soft contact-shadow disc
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
        const shadowPlane = new THREE.Mesh(
          new THREE.PlaneGeometry(22, 14),
          new THREE.MeshBasicMaterial({
            map: new THREE.CanvasTexture(shadowCanvas),
            transparent: true,
            opacity: 0.65,
            depthWrite: false,
          })
        );
        shadowPlane.rotation.x = -Math.PI / 2;
        shadowPlane.position.y = -6.2;
        scene.add(shadowPlane);

        airplane.rotation.set(0.18, -Math.PI / 3.8, 0.12);
        scene.add(airplane);

        // Interaction
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        let userRotationY = 0;
        let userRotationX = 0;
        const autoRotateSpeed = (2 * Math.PI) / (20 * 60); // ~20 s per turn

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
        };

        host.addEventListener('pointerdown', onPointerDown);
        window.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);
        window.addEventListener('resize', onWindowResize);

        // Animation loop
        const clock = new THREE.Clock();
        let raf = 0;
        const animate = () => {
          raf = requestAnimationFrame(animate);
          const t = clock.getElapsedTime();

          const floatOffset = Math.sin(t * 1.5) * 0.35;
          airplane.position.y = floatOffset;
          shadowPlane.scale.set(1 + floatOffset * 0.08, 1 + floatOffset * 0.08, 1);

          const rockRoll = Math.cos(t * 1.2) * 0.03;
          if (!isDragging) userRotationY += autoRotateSpeed;

          airplane.rotation.y = userRotationY - Math.PI / 3.8;
          airplane.rotation.x = 0.18 + userRotationX + rockRoll;

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
      })
      .catch(() => {
        // CDN unavailable — leave the container empty; layout still holds.
      });

    return () => {
      disposed = true;
      cleanup?.();
    };
  }, []);

  return (
    <div
      ref={hostRef}
      role="img"
      aria-label={label}
      className="w-full h-full cursor-grab active:cursor-grabbing select-none touch-none"
    />
  );
};

export default Hero3DAircraft;
