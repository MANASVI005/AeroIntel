import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Card, Button, LoadingState, ErrorState } from '../components/common';
import { aeromemoryStateMeta, classMeta } from '../types/classes';
import { api, imageBaseUrl } from '../services/api';
import type { Inspection, LatestResult } from '../services/types';

/**
 * Formal Inspection Report (stitch/aerointel_inspection_report.html).
 * Rendered LIVE from stored backend data — no report entity exists server-side:
 *   - Inspection record fields ← GET /api/inspections
 *   - Latest scan: image, detections, AeroMemory tracking ← GET /api/inspections/{id}/latest-result
 * Everything on the page is real; Export JSON downloads the fetched payload.
 * NO-HOLLOW-UI drops vs Stitch: FAA/EASA alignment badge, "RESTRICTED" seal +
 * security numbers, doc refs, authorization line, invented mm measurements /
 * growth percentages, "AI Neural Core" branding, hangar/facility fields we
 * don't track, and per-detection decision states (no decisions GET endpoint —
 * decisions are generated per-detection on the Result screen).
 */

const fmtDateTime = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString(undefined, { dateStyle: 'full', timeStyle: 'short' });
};

const CLASS_ACCENT: Record<number, string> = {
  0: '#ba1a1a',
  1: '#8a4b12',
  2: '#7a5900',
  3: '#6750a4',
};

export const InspectionReport: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [result, setResult] = useState<LatestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const list = await api.listInspections();
        const insp = list.find((i) => i.id === parseInt(id ?? '', 10)) ?? null;
        if (cancelled) return;
        setInspection(insp);
        const res = await api.getLatestResult(parseInt(id ?? '0', 10));
        if (cancelled) return;
        setResult(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load report data.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const exportJson = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify({ inspection, result }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.inspection_code ?? `inspection-${id}`}-report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  /* bbox scale: displayed px / natural px — same proven pattern as InspectionResult */
  const [scale, setScale] = useState({ x: 1, y: 1 });
  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    if (result && result.image_width && result.image_height) {
      setScale({ x: img.clientWidth / result.image_width, y: img.clientHeight / result.image_height });
    }
  };

  if (loading && !inspection && !result) {
    return (
      <AppShell>
        <Card>
          <LoadingState message="Building report from stored inspection data…" />
        </Card>
      </AppShell>
    );
  }

  if (error && !inspection && !result) {
    return (
      <AppShell>
        <Card>
          <ErrorState message={`Unable to build the report: ${error}`} />
        </Card>
      </AppShell>
    );
  }

  const hasResult = result?.has_result === true;

  return (
    <AppShell>
      {/* Screen-only action bar (hidden when printing) */}
      <div className="no-print flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 font-caption-data text-caption-data text-secondary">
          <Link to="/reports" className="hover:text-primary transition-colors">Reports</Link>
          <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          <span className="text-on-surface-variant font-medium">{inspection?.inspection_code ?? `#${id}`}</span>
          <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          <span className="text-primary font-semibold">Formal Inspection Report</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" icon="arrow_back" onClick={() => navigate(-1)}>
            Back
          </Button>
          <Button variant="secondary" icon="data_object" onClick={exportJson} disabled={!hasResult}>
            Export JSON
          </Button>
          <Button icon="print" onClick={() => window.print()}>
            Print / Save PDF
          </Button>
        </div>
      </div>

      {/* ── The report document ── */}
      <div className="report-sheet bg-surface-container-lowest rounded-2xl card-shadow p-8 md:p-10 text-on-surface">
        {/* Document header */}
        <div className="flex items-start justify-between gap-6 pb-5 border-b-2 border-primary/70">
          <div className="flex items-center gap-3">
            <img src="/brand/aerointel-logo.png" alt="AeroIntel" className="h-10 w-auto object-contain" />
            <div className="flex flex-col">
              <span className="font-headline-md text-headline-md font-bold text-on-surface tracking-tight">
                Structural Integrity &amp; AI Damage Inspection Report
              </span>
              <span className="font-caption-data text-caption-data text-secondary">
                Generated {fmtDateTime(new Date().toISOString())} · AeroIntel v1.0.0 (aerointel_v1 · YOLO11s)
              </span>
            </div>
          </div>
          <span className="hidden md:inline-flex px-2.5 py-1 rounded-full bg-error-container text-on-error-container font-caption-data text-caption-data font-bold">
            UNVERIFIED DRAFT — REVIEW REQUIRED
          </span>
        </div>

        {/* Inspection details — real fields only */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-4 py-6 border-b border-surface-container-high/60">
          {[
            { label: 'Inspection ID', value: inspection?.inspection_code ?? `#${id}` },
            { label: 'Aircraft', value: inspection?.aircraft_code ?? '—' },
            { label: 'Panel', value: inspection?.panel_code ?? `#${inspection?.panel_id ?? id}` },
            { label: 'Inspector', value: inspection?.inspector_name ?? '—' },
            { label: 'Recorded', value: inspection ? fmtDateTime(inspection.inspection_date) : '—' },
            { label: 'Detection model', value: 'aerointel_v1 · YOLO11s · ONNX' },
            { label: 'Image', value: hasResult ? `${result.image_width}×${result.image_height}px` : '—' },
            { label: 'Detections', value: hasResult ? String(result.count) : '0' },
          ].map((f) => (
            <div key={f.label} className="flex flex-col gap-0.5">
              <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
                {f.label}
              </span>
              <span className="font-body-md text-body-md font-semibold text-on-surface break-words">{f.value}</span>
            </div>
          ))}
        </div>

        {/* Latest scan image with bbox overlay */}
        {hasResult && (
          <div className="py-6 border-b border-surface-container-high/60">
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface mb-3">
              Latest captured frame — {result.original_filename}
            </h3>
            <div className="relative w-full max-w-2xl rounded-xl overflow-hidden bg-surface-container-low">
              <img
                src={`${imageBaseUrl}/${(result.stored_path ?? '').replace(/\\/g, '/')}`}
                alt="Inspection frame"
                className="w-full h-auto"
                onLoad={onImageLoad}
                ref={(el) => {
                  if (el?.complete) onImageLoad({ currentTarget: el } as React.SyntheticEvent<HTMLImageElement>);
                }}
              />
              {result.detections.map((d, i) => (
                <div
                  key={d.id ?? i}
                  className="absolute border-2 rounded"
                  style={{
                    left: d.bbox.x * scale.x,
                    top: d.bbox.y * scale.y,
                    width: d.bbox.width * scale.x,
                    height: d.bbox.height * scale.y,
                    borderColor: CLASS_ACCENT[d.class_id] ?? '#666',
                  }}
                >
                  <span
                    className="absolute -top-5 left-0 px-1.5 py-0.5 rounded text-[10px] font-bold text-white whitespace-nowrap"
                    style={{ backgroundColor: CLASS_ACCENT[d.class_id] ?? '#666' }}
                  >
                    {classMeta(d.class_id).name} · {Math.round(d.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
            <p className="font-caption-data text-caption-data text-secondary mt-2">
              Boxes drawn from backend bbox coordinates ({'{x, y, width, height}'} in original-image pixels).
            </p>
          </div>
        )}

        {/* Findings table */}
        <div className="py-6 border-b border-surface-container-high/60">
          <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface mb-3">
            Detected Defects &amp; Classification —{' '}
            {hasResult ? `${result.count} detection${result.count === 1 ? '' : 's'}` : 'no captures yet'}
          </h3>
          {!hasResult ? (
            <p className="font-body-md text-body-md text-secondary">
              No image has been captured for this inspection, so there is no detection data to report.
            </p>
          ) : result.detections.length === 0 ? (
            <p className="font-body-md text-body-md text-secondary">
              The model found no defects in the captured frame.
            </p>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-secondary font-label-table-head text-label-table-head uppercase tracking-wider text-[11px] border-b border-surface-container-high/60">
                  <th className="py-2.5 px-3 font-bold">Defect</th>
                  <th className="py-2.5 px-3 font-bold">Confidence</th>
                  <th className="py-2.5 px-3 font-bold">Location (px)</th>
                  <th className="py-2.5 px-3 font-bold">Size (px)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-low font-body-md text-body-md">
                {result.detections.map((d, i) => (
                  <tr key={d.id ?? i}>
                    <td className="py-2.5 px-3 font-semibold">
                      <span className="inline-flex items-center gap-2">
                        <span className={`w-2.5 h-2.5 rounded-full ${classMeta(d.class_id).dot}`} />
                        {classMeta(d.class_id).name}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-caption-data font-bold">{Math.round(d.confidence * 100)}%</td>
                    <td className="py-2.5 px-3 font-caption-data text-secondary">
                      x:{Math.round(d.bbox.x)} · y:{Math.round(d.bbox.y)}
                    </td>
                    <td className="py-2.5 px-3 font-caption-data text-secondary">
                      {Math.round(d.bbox.width)}×{Math.round(d.bbox.height)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* AeroMemory tracking */}
        {hasResult && (
          <div className="py-6 border-b border-surface-container-high/60">
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface mb-3">
              AeroMemory Longitudinal Tracking — {result.aeromemory.comparisons.length} tracked defect
              {result.aeromemory.comparisons.length === 1 ? '' : 's'}
            </h3>
            {result.aeromemory.comparisons.length === 0 ? (
              <p className="font-body-md text-body-md text-secondary">
                No tracked defects on record for this airframe/component yet.
              </p>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-secondary font-label-table-head text-label-table-head uppercase tracking-wider text-[11px] border-b border-surface-container-high/60">
                    <th className="py-2.5 px-3 font-bold">Defect ID</th>
                    <th className="py-2.5 px-3 font-bold">Type</th>
                    <th className="py-2.5 px-3 font-bold">State</th>
                    <th className="py-2.5 px-3 font-bold">Severity</th>
                    <th className="py-2.5 px-3 font-bold">Match conf.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container-low font-body-md text-body-md">
                  {result.aeromemory.comparisons.map((c) => {
                    const m = aeromemoryStateMeta(c.state);
                    return (
                      <tr key={c.defect_id}>
                        <td className="py-2.5 px-3 font-mono font-bold text-primary">{c.defect_id}</td>
                        <td className="py-2.5 px-3 font-semibold">{c.defect_type}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded-full font-caption-data text-[10px] font-bold ${m.pill}`}>
                            {m.label}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-semibold">{c.severity}</td>
                        <td className="py-2.5 px-3 font-mono">
                          {c.match_confidence > 0 ? `${Math.round(c.match_confidence * 100)}%` : 'first seen'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Decision-support note + sign-off block */}
        <div className="py-6">
          <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface mb-2">Review &amp; Sign-off</h3>
          <p className="font-body-md text-body-md text-secondary leading-relaxed max-w-3xl">
            AI detections and severity assessments are decision support only — a qualified maintenance engineer must
            review every finding before maintenance action. Per-detection decision-support assessments can be
            generated on the inspection result screen.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-6">
            {['Inspected by', 'Approved by'].map((role) => (
              <div key={role} className="flex flex-col gap-1">
                <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
                  {role}
                </span>
                <span className="border-b border-outline-variant h-8" />
                <span className="font-caption-data text-caption-data text-secondary">Name / signature / date</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
};

export default InspectionReport;
