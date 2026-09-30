import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { ProcessingChecklist, type StepStatus } from '../components/common';
import { api } from '../services/api';
import type { UploadResult, Inspection } from '../services/types';

/**
 * New Inspection — the core capture + detection launch page
 * (stitch/aerointel_new_inspection_capture.html).
 *
 * REAL FLOW (spec §4-§7):
 *   1. Fill inspection info → Continue
 *   2. POST /api/inspections          (creates the inspection record)
 *   3. Capture/Upload image → preview → Use Photo
 *   4. POST /api/inspections/{id}/images (save → YOLO → AeroMemory, atomic)
 *      while showing the processing checklist
 *   5. Navigate to the Inspection Result page
 */

type Flow = 'form' | 'capture' | 'processing';

const STEPS: { icon: string; title: string; sub: string }[] = [
  { icon: 'photo_camera', title: '1. Capture', sub: 'Step 01' },
  { icon: 'save', title: '2. Save', sub: 'Step 02' },
  { icon: 'document_scanner', title: '3. Detect', sub: 'Step 03' },
  { icon: 'troubleshoot', title: '4. Compare History', sub: 'Step 04' },
];

const COMPONENTS = [
  'Wing (Main Spar)',
  'Fuselage Barrel Section 43',
  'Vertical Stabilizer Root',
  'Engine Cowling & Nacelle',
  'Landing Gear Trunnion',
];

const PROCESS_STEPS: { label: string; status: StepStatus }[] = [
  { label: 'Image uploaded', status: 'done' },
  { label: 'Image stored', status: 'done' },
  { label: 'Running AI detection', status: 'active' },
  { label: 'Comparing with AeroMemory', status: 'pending' },
  { label: 'Preparing result', status: 'pending' },
];

export const NewInspection: React.FC = () => {
  const navigate = useNavigate();

  /* ── flow state ── */
  const [flow, setFlow] = useState<Flow>('form');
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [uploading, setUploading] = useState(false);

  /* ── form fields ── */
  const [aircraft, setAircraft] = useState('VT-ALB');
  const [aircraftModel, setAircraftModel] = useState('Boeing 737-800');
  const [component, setComponent] = useState(COMPONENTS[0]);
  const [panel, setPanel] = useState('Left Wing Panel LP-14B');
  const [engineer, setEngineer] = useState('A. Sharma (Staff Inspector #4102)');

  /* ── media ── */
  const [tab, setTab] = useState<'upload' | 'camera'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dims, setDims] = useState<{ w: number; h: number } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [conf, setConf] = useState(0.40);
  const [iou, setIou] = useState(0.50);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  /* generate a local inspection code (server dedupes by code; auto-gen per spec) */
  const inspectionCode = `INS-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${String(
    Math.floor(Math.random() * 900) + 100
  )}`;

  /* camera lifecycle */
  useEffect(() => {
    if (tab === 'camera' && flow === 'capture') {
      navigator.mediaDevices
        ?.getUserMedia({ video: { facingMode: 'environment' } })
        .then((s) => {
          streamRef.current = s;
          if (videoRef.current) videoRef.current.srcObject = s;
        })
        .catch(() => setError('Camera unavailable — use Upload instead.'));
    }
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, [tab, flow]);

  const readFile = useCallback((f: File) => {
    if (!/image\/(jpeg|jpg|png|bmp|webp)/.test(f.type)) {
      setError('Unsupported file type — JPG/PNG/BMP/WEBP only.');
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError('Image exceeds the 10 MB limit.');
      return;
    }
    setError(null);
    setFile(f);
    const url = URL.createObjectURL(f);
    setPreviewUrl(url);
    const img = new Image();
    img.onload = () => setDims({ w: img.naturalWidth, h: img.naturalHeight });
    img.src = url;
  }, []);

  /* Step 2: create inspection record */
  const handleContinue = useCallback(async () => {
    setCreating(true);
    setError(null);
    try {
      // NOTE: backend needs a panel_id; until the aircraft/panel creation
      // endpoint exists, panel_id=1 is the seeded first panel (Stage 2 fixes).
      const insp = await api.createInspection({
        panel_id: 1,
        inspection_code: inspectionCode,
        inspector_name: engineer,
        notes: `${aircraft} • ${aircraftModel} • ${component} • ${panel}`,
      });
      setInspection(insp);
      setFlow('capture');
    } catch (e) {
      setError(
        e instanceof Error && 'status' in e && (e as { status: number }).status === 409
          ? 'That inspection code already exists — retry to generate a new one.'
          : 'Could not create the inspection. Check that the local AeroIntel server is running.'
      );
    } finally {
      setCreating(false);
    }
  }, [aircraft, aircraftModel, component, panel, engineer, inspectionCode]);

  /* Step 4: upload → detect → AeroMemory (single atomic call) */
  const handleUsePhoto = useCallback(async () => {
    if (!file || !inspection) return;
    setUploading(true);
    setError(null);
    try {
      const result = await api.uploadInspectionImage(inspection.id, file);
      setUploadResult(result);
    } catch (e) {
      setError('Detection failed on the server. Check the local AeroIntel server and retry.');
    } finally {
      setUploading(false);
    }
  }, [file, inspection]);

  /* processing checklist completes → navigate to result */
  useEffect(() => {
    if (!uploadResult) return;
    const t = setTimeout(() => {
      navigate(`/inspections/${uploadResult.inspection_id}`, {
        state: { result: uploadResult },
      });
    }, 1200);
    return () => clearTimeout(t);
  }, [uploadResult, navigate]);

  const steps = PROCESS_STEPS.map((s, i) => {
    if (uploadResult) return { ...s, status: 'done' as StepStatus };
    // stage-wise animation while the single atomic call is in flight
    if (i < 2) return { ...s, status: 'done' as StepStatus };
    if (i === 2) return { ...s, status: 'active' as StepStatus };
    return { ...s, status: 'pending' as StepStatus };
  });

  const fmtSize = (b: number) => (b / (1024 * 1024)).toFixed(1) + ' MB';

  return (
    <AppShell>
      {/* Breadcrumb + header */}
      <section className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 font-caption-data text-caption-data text-secondary mb-2">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px]">flight_takeoff</span>
              <span>Inspections</span>
            </span>
            <span className="text-outline-variant">/</span>
            <span className="text-on-surface font-semibold">Create New Scan</span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">New Inspection</h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-xl">
            Capture image, run AI detection and store in AeroMemory chronological archive.
          </p>
        </div>
        <div className="flex items-center gap-3 px-4 py-2.5 rounded-2xl bg-surface-container-lowest/80 backdrop-blur-xl shadow-[0_10px_30px_rgba(160,195,225,0.18)] self-start md:self-auto">
          <div className="flex flex-col text-right">
            <span className="font-caption-data text-[11px] uppercase tracking-wider text-secondary">Inspection Record</span>
            <span className="font-label-kpi-sub text-label-kpi-sub text-primary font-bold">
              {inspection ? `Created · #${inspection.id}` : 'Not created yet'}
            </span>
          </div>
          <div className="w-9 h-9 rounded-xl bg-primary-container/10 flex items-center justify-center text-primary">
            <span className="material-symbols-outlined text-[20px]">{inspection ? 'check_circle' : 'pending'}</span>
          </div>
        </div>
      </section>

      {/* Stepper — connector segments run BETWEEN icons only, never over text */}
      <section className="w-full bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl p-4 sm:p-5 shadow-[0_10px_30px_-4px_rgba(160,195,225,0.22)]">
        <div className="flex flex-col md:flex-row items-start md:items-center">
          {STEPS.map((s, i) => {
            const done =
              (flow === 'capture' && i === 0) || flow === 'processing';
            const active =
              (flow === 'form' && i === 0) || (flow === 'capture' && i <= 1) || flow === 'processing';
            const isLast = i === STEPS.length - 1;
            return (
              <React.Fragment key={s.title}>
                <div className={`flex items-center gap-3 shrink-0 ${active ? '' : 'opacity-70'}`}>
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full font-headline-sm text-[15px] shrink-0 ${
                      done
                        ? 'bg-tertiary-container text-on-tertiary-container'
                        : active
                          ? 'bg-primary-container text-on-primary shadow-[0_8px_20px_rgba(44,110,203,0.35)] ring-4 ring-primary-container/20'
                          : 'bg-surface-container text-secondary'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[19px]">
                      {done ? 'check' : s.icon}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span
                      className={`font-caption-data text-[11px] uppercase tracking-wider font-bold ${
                        active ? 'text-primary' : 'text-secondary'
                      }`}
                    >
                      {s.sub}
                    </span>
                    <span className="text-on-surface whitespace-nowrap font-body-md text-body-md font-semibold">
                      {s.title}
                    </span>
                  </div>
                </div>
                {!isLast && (
                  <div className="hidden md:flex flex-1 h-0.5 mx-3 mb-0.5 rounded-full overflow-hidden bg-surface-container self-center">
                    <div
                      className="h-full bg-primary-container transition-all duration-500"
                      style={{
                        width:
                          flow === 'processing' ? '100%' : flow === 'capture' ? (i === 0 ? '100%' : '0%') : '0%',
                      }}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </section>

      {/* PROCESSING overlay state (spec: don't jump straight to result) */}
      {flow === 'processing' && (
        <section className="bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl p-8 shadow-[0_10px_30px_-4px_rgba(160,195,225,0.20)]">
          <h2 className="font-headline-md text-headline-md text-on-surface mb-6">Processing Inspection</h2>
          <ProcessingChecklist steps={steps} />
          {uploadResult && (
            <p className="font-caption-data text-caption-data text-tertiary mt-6">
              Detection complete — {uploadResult.count} defects · AeroMemory: {uploadResult.aeromemory.new_count} new, {uploadResult.aeromemory.matched_count} matched. Opening result…
            </p>
          )}
        </section>
      )}

      {/* FORM state */}
      {flow === 'form' && (
        <section className="bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl p-6 sm:p-8 shadow-[0_10px_30px_-4px_rgba(160,195,225,0.20)]">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-surface-container flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-[22px]">assignment</span>
              </div>
              <div>
                <h2 className="font-headline-md text-headline-md text-on-surface">Inspection Information</h2>
                <p className="font-caption-data text-caption-data text-secondary">Airframe telemetry, registration, and assigned crew</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container text-on-secondary-container font-caption-data text-caption-data font-semibold">
              <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
              {inspection ? `Record #${inspection.id} created` : 'Step 1 — create record first'}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="font-caption-data text-caption-data font-semibold text-secondary uppercase tracking-wider">Inspection ID</label>
              <div className="flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-surface-container-low font-body-md text-body-md text-primary font-bold shadow-inner">
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-primary">tag</span>
                  {inspectionCode}
                </span>
                <span className="px-2 py-0.5 rounded-md bg-primary-container text-on-primary font-caption-data text-[11px] font-semibold">Auto-Gen</span>
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-caption-data text-caption-data font-semibold text-secondary uppercase tracking-wider" htmlFor="aircraft-id">Aircraft Registration</label>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-[18px] text-secondary">flight</span>
                <input id="aircraft-id" type="text" value={aircraft} onChange={(e) => setAircraft(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-container-low font-body-md text-body-md text-on-surface font-semibold focus:outline-none focus:bg-surface-container transition-all" />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-caption-data text-caption-data font-semibold text-secondary uppercase tracking-wider" htmlFor="aircraft-model">Aircraft Model</label>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-[18px] text-secondary">airplanemode_active</span>
                <input id="aircraft-model" type="text" value={aircraftModel} onChange={(e) => setAircraftModel(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-container-low font-body-md text-body-md text-on-surface font-semibold focus:outline-none focus:bg-surface-container transition-all" />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-caption-data text-caption-data font-semibold text-secondary uppercase tracking-wider" htmlFor="component-select">Structural Component</label>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-[18px] text-secondary">view_in_ar</span>
                <select id="component-select" value={component} onChange={(e) => setComponent(e.target.value)}
                  className="w-full appearance-none pl-10 pr-10 py-2.5 rounded-xl bg-surface-container-low font-body-md text-body-md text-on-surface font-semibold focus:outline-none focus:bg-surface-container transition-all cursor-pointer">
                  {COMPONENTS.map((c) => <option key={c}>{c}</option>)}
                </select>
                <span className="material-symbols-outlined absolute right-3.5 text-[18px] text-secondary pointer-events-none">expand_more</span>
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-caption-data text-caption-data font-semibold text-secondary uppercase tracking-wider" htmlFor="panel-area">Panel / Specific Area</label>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-[18px] text-secondary">grid_view</span>
                <input id="panel-area" type="text" value={panel} onChange={(e) => setPanel(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-container-low font-body-md text-body-md text-on-surface font-semibold focus:outline-none focus:bg-surface-container transition-all" />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-caption-data text-caption-data font-semibold text-secondary uppercase tracking-wider" htmlFor="engineer-name">Lead Engineer / Sign-off</label>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-[18px] text-secondary">badge</span>
                <input id="engineer-name" type="text" value={engineer} onChange={(e) => setEngineer(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-container-low font-body-md text-body-md text-on-surface font-semibold focus:outline-none focus:bg-surface-container transition-all" />
              </div>
            </div>
          </div>

          <div className="mt-8 pt-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5 text-secondary">
              <span className="material-symbols-outlined text-[20px] text-primary shrink-0">neurology</span>
              <span className="font-caption-data text-caption-data">
                All metadata will be linked with <strong className="text-on-surface font-semibold">AeroMemory</strong> chronological index and airframe digital twin.
              </span>
            </div>
            <button
              onClick={handleContinue}
              disabled={creating}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3 rounded-full bg-primary-container text-on-primary font-body-md text-body-md font-bold shadow-[0_10px_24px_rgba(44,110,203,0.35)] hover:shadow-[0_14px_28px_rgba(44,110,203,0.45)] hover:scale-[1.02] active:scale-[0.98] transition-all group disabled:opacity-50"
            >
              <span>{creating ? 'Creating…' : 'Continue'}</span>
              <span className="material-symbols-outlined text-[18px] group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </button>
          </div>
        </section>
      )}

      {/* CAPTURE state */}
      {flow === 'capture' && (
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* LEFT: tabbed input */}
          <div className="lg:col-span-6 flex flex-col gap-4 bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl p-6 sm:p-7 shadow-[0_10px_30px_-4px_rgba(160,195,225,0.20)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">perm_media</span>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Media Acquisition</h3>
              </div>
              <span className="font-caption-data text-caption-data px-2.5 py-1 rounded-full bg-surface-container text-on-surface-variant font-medium">Source Selection</span>
            </div>

            <div className="p-1 rounded-xl bg-surface-container-low flex items-center gap-1">
              <button
                onClick={() => setTab('upload')}
                className={`flex-1 py-2 px-4 rounded-lg font-body-md text-body-md transition-all flex items-center justify-center gap-2 ${tab === 'upload' ? 'bg-surface-container-lowest text-primary font-bold shadow-sm' : 'text-secondary hover:text-on-surface font-medium'}`}
              >
                <span className="material-symbols-outlined text-[18px]">cloud_upload</span>
                <span>Upload File</span>
              </button>
              <button
                onClick={() => setTab('camera')}
                className={`flex-1 py-2 px-4 rounded-lg font-body-md text-body-md transition-all flex items-center justify-center gap-2 ${tab === 'camera' ? 'bg-surface-container-lowest text-primary font-bold shadow-sm' : 'text-secondary hover:text-on-surface font-medium'}`}
              >
                <span className="material-symbols-outlined text-[18px]">videocam</span>
                <span>Live Camera</span>
              </button>
            </div>

            {tab === 'upload' ? (
              <div className="flex flex-col gap-4">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files?.[0]; if (f) readFile(f); }}
                  className={`relative group cursor-pointer rounded-2xl p-8 text-center flex flex-col items-center justify-center min-h-[260px] transition-all ${dragOver ? 'bg-primary-container/20 ring-2 ring-primary' : 'bg-surface-container-low/50 hover:bg-surface-container-low'}`}
                >
                  <div className="w-16 h-16 mb-4 rounded-2xl bg-surface-container flex items-center justify-center text-primary group-hover:scale-110 group-hover:bg-primary group-hover:text-on-primary transition-all duration-300 shadow-sm">
                    <span className="material-symbols-outlined text-[32px]">cloud_upload</span>
                  </div>
                  <h4 className="font-headline-sm text-[16px] text-on-surface mb-1">Drop aircraft image here or browse</h4>
                  <p className="font-caption-data text-caption-data text-secondary max-w-sm mb-4">
                    Supports high-resolution drone scans, borescope captures &amp; handheld DSLR images (JPG/PNG, max 10 MB).
                  </p>
                  <span className="px-5 py-2.5 rounded-full bg-surface-container-lowest hover:bg-surface-container text-primary font-body-md text-body-md font-bold shadow-[0_4px_12px_rgba(160,195,225,0.25)] transition-all flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">folder_open</span>
                    <span>Browse Local Files</span>
                  </span>
                  <input ref={fileInputRef} accept="image/jpeg,image/png,image/bmp,image/webp" className="hidden" type="file" onChange={(e) => { const f = e.target.files?.[0]; if (f) readFile(f); }} />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { icon: 'straighten', iconCls: 'text-primary', k: 'Max size', v: '10 MB' },
                    { icon: 'image', iconCls: 'text-tertiary', k: 'Formats', v: 'JPG PNG' },
                    { icon: 'backup', iconCls: 'text-primary-container', k: 'Storage', v: 'Local server' },
                  ].map((c) => (
                    <div key={c.k} className="flex items-center gap-2 p-2.5 rounded-xl bg-surface-container-low/80">
                      <span className={`material-symbols-outlined text-[18px] ${c.iconCls}`}>{c.icon}</span>
                      <div className="flex flex-col">
                        <span className="font-caption-data text-[10px] uppercase text-secondary">{c.k}</span>
                        <span className="font-caption-data text-[12px] font-bold text-on-surface">{c.v}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="relative rounded-2xl bg-on-secondary-fixed overflow-hidden aspect-[4/3] flex items-center justify-center">
                  <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
                  {!previewUrl && (
                    <div className="text-center text-surface-container-lowest z-10 flex flex-col items-center relative">
                      <span className="material-symbols-outlined text-[44px] text-tertiary-fixed-dim animate-pulse mb-2">videocam</span>
                      <p className="font-body-md text-body-md font-semibold">Live Optical Feed</p>
                      <span className="font-caption-data text-caption-data text-secondary-fixed-dim mt-1">Rear camera active — frame the panel</span>
                    </div>
                  )}
                  <button
                    onClick={() => {
                      const v = videoRef.current;
                      if (!v) return;
                      const canvas = document.createElement('canvas');
                      canvas.width = v.videoWidth;
                      canvas.height = v.videoHeight;
                      canvas.getContext('2d')?.drawImage(v, 0, 0);
                      canvas.toBlob((blob) => {
                        if (blob) readFile(new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' }));
                      }, 'image/jpeg');
                    }}
                    className="absolute bottom-4 left-1/2 -translate-x-1/2 px-6 py-2 rounded-full bg-primary text-on-primary font-bold text-[13px] shadow-lg flex items-center gap-2 z-10"
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-error animate-ping" />
                    <span>Capture Frame</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: preview */}
          <div className="lg:col-span-6 flex flex-col gap-4 bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl p-6 sm:p-7 shadow-[0_10px_30px_-4px_rgba(160,195,225,0.20)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">visibility</span>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Source Preview</h3>
              </div>
              <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full font-caption-data text-caption-data font-bold ${previewUrl ? 'bg-surface-container text-tertiary' : 'bg-surface-container text-secondary'}`}>
                <span className={`w-2 h-2 rounded-full ${previewUrl ? 'bg-tertiary' : 'bg-secondary'}`} />
                {previewUrl ? 'Image Selected' : 'No Image Yet'}
              </div>
            </div>

            <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden shadow-inner group bg-surface-container-low">
              {previewUrl ? (
                <>
                  <img src={previewUrl} alt="Selected inspection frame" className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
                  {/* Minimal real-info overlay: actual file facts, no invented telemetry */}
                  <div className="absolute inset-x-0 bottom-0 p-3 flex items-center justify-between text-[11px] font-caption-data font-semibold text-on-primary bg-on-secondary-fixed/50 backdrop-blur-md">
                    <span>{dims ? `${dims.w} × ${dims.h} px` : 'READING…'}</span>
                    <span>{file ? fmtSize(file.size) : '—'}</span>
                  </div>
                </>
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-secondary">
                  <span className="material-symbols-outlined text-[44px]">image</span>
                  <span className="font-caption-data text-caption-data">Upload or capture an image to preview</span>
                </div>
              )}
            </div>

            {/* File details */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3.5 rounded-xl bg-surface-container-low/70">
              <div className="flex flex-col">
                <span className="font-caption-data text-[10px] uppercase text-secondary">Filename</span>
                <span className="font-caption-data text-[12px] font-bold text-on-surface truncate" title={file?.name}>{file?.name ?? '—'}</span>
              </div>
              <div className="flex flex-col">
                <span className="font-caption-data text-[10px] uppercase text-secondary">Resolution</span>
                <span className="font-caption-data text-[12px] font-bold text-on-surface">{dims ? `${dims.w} × ${dims.h} px` : '—'}</span>
              </div>
              <div className="flex flex-col">
                <span className="font-caption-data text-[10px] uppercase text-secondary">Payload Size</span>
                <span className="font-caption-data text-[12px] font-bold text-on-surface">{file ? fmtSize(file.size) : '—'}</span>
              </div>
              <div className="flex flex-col">
                <span className="font-caption-data text-[10px] uppercase text-secondary">Format</span>
                <span className="font-caption-data text-[12px] font-bold text-on-surface">{file ? file.type.replace('image/', '').toUpperCase() : '—'}</span>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 pt-2">
              <button
                onClick={() => { setFile(null); setPreviewUrl(null); setDims(null); }}
                className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-surface-container-low hover:bg-surface-container text-on-surface font-body-md text-body-md font-bold transition-all"
              >
                <span className="material-symbols-outlined text-[18px]">replay</span>
                <span>Retake Photo</span>
              </button>
              <button
                onClick={handleUsePhoto}
                disabled={!file || uploading}
                className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-primary-container hover:bg-primary text-on-primary font-body-md text-body-md font-bold shadow-[0_8px_20px_rgba(44,110,203,0.3)] transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40"
              >
                <span className="material-symbols-outlined text-[18px]">check_circle</span>
                <span>{uploading ? 'Detecting…' : 'Use Photo'}</span>
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Advanced settings (both states) */}
      {flow !== 'processing' && (
        <section className="bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl shadow-[0_10px_30px_-4px_rgba(160,195,225,0.20)] overflow-hidden">
          <div className="px-6 pb-6 pt-6 flex flex-col gap-6">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-surface-container flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-[20px]">tune</span>
              </div>
              <div className="flex flex-col">
                <span className="font-headline-sm text-headline-sm text-on-surface">Advanced Detection &amp; Model Parameters</span>
                <span className="font-caption-data text-caption-data text-secondary">Tune neural confidence gates &amp; suppression metrics (client-side filter defaults)</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col gap-3 p-4 rounded-xl bg-surface-container-low/60">
                <div className="flex items-center justify-between">
                  <label className="font-caption-data text-caption-data font-bold uppercase tracking-wider text-secondary" htmlFor="slider-conf">Confidence Threshold</label>
                  <span className="px-2 py-0.5 rounded-md bg-primary-container text-on-primary font-caption-data text-[11px] font-bold">{conf.toFixed(2)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-caption-data text-caption-data text-secondary">0.1</span>
                  <input id="slider-conf" type="range" min="0.10" max="0.95" step="0.05" value={conf} onChange={(e) => setConf(parseFloat(e.target.value))} className="w-full accent-primary cursor-pointer" />
                  <span className="font-caption-data text-caption-data text-secondary">1.0</span>
                </div>
                <p className="font-caption-data text-[12px] text-on-surface-variant leading-snug">
                  Minimum neural score to classify candidate anomalies (cracks, dents, corrosion).
                </p>
              </div>
              <div className="flex flex-col gap-3 p-4 rounded-xl bg-surface-container-low/60">
                <div className="flex items-center justify-between">
                  <label className="font-caption-data text-caption-data font-bold uppercase tracking-wider text-secondary" htmlFor="slider-iou">IoU Threshold</label>
                  <span className="px-2 py-0.5 rounded-md bg-primary-container text-on-primary font-caption-data text-[11px] font-bold">{iou.toFixed(2)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-caption-data text-caption-data text-secondary">0.1</span>
                  <input id="slider-iou" type="range" min="0.10" max="0.90" step="0.05" value={iou} onChange={(e) => setIou(parseFloat(e.target.value))} className="w-full accent-primary cursor-pointer" />
                  <span className="font-caption-data text-caption-data text-secondary">0.9</span>
                </div>
                <p className="font-caption-data text-[12px] text-on-surface-variant leading-snug">
                  Non-maximum suppression overlap limit for deduplicating bounding boxes.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-error-container text-on-error-container">
          <span className="material-symbols-outlined text-[22px]">error</span>
          <span className="font-body-md text-body-md font-semibold">{error}</span>
        </div>
      )}
    </AppShell>
  );
};

export default NewInspection;
