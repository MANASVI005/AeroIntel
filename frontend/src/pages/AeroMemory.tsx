import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeader, MetaChip, Card, Button, StatusPill,
  LoadingState, EmptyState, ErrorState, ClassChip,
} from '../components/common';
import { usePolling, useApi } from '../hooks/useApi';
import { classMeta, aeromemoryStateMeta } from '../types/classes';
import { CLASS_META } from '../types/classes';
import { api } from '../services/api';
import type { Inspection, LatestResult, Detection, AeroMemoryComparison } from '../services/types';

/**
 * AeroMemory (stitch/aerointel_aeromemory_historical_comparison.html).
 * NO-HOLLOW-UI RULE: the Stitch mockup shows a side-by-side "baseline vs
 * target" viewer with registration accuracy, FOV/gain telemetry, pixel-delta
 * callouts and a defect timeline chart — none of that has a backend behind it
 * (no stored baseline pairing endpoint, no ghost-overlay endpoint, no metrics
 * API). What the backend DOES give us:
 *   - GET /api/inspections                    → inspection selector
 *   - GET /api/inspections/{id}/latest-result → detections + aeromemory block
 *     (tracked defects with state new|stable|increased|decreased|resolved,
 *      severity, match confidence — computed by the AeroMemory engine on every
 *      upload by matching detections against previous inspections of the same
 *      aircraft + component with image registration).
 * So this screen is a per-inspection longitudinal review: pick an inspection,
 * see its tracked defects and how each one evolved. Ghost overlay / baseline
 * pairing is deferred until a compare endpoint exists (Stage 2.3).
 */

const fmtDateTime = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
};

/** defect_type arrives as a class name string; map back to the class palette. */
const typeMeta = (defectType: string) => {
  const entry = Object.values(CLASS_META).find(
    (m) => m.name.toLowerCase() === defectType.toLowerCase()
  );
  return entry ?? { name: defectType, dot: 'bg-outline', chip: 'bg-outline' };
};

/** Bar width proxy: bbox area % of frame (backend sends px, v1 has no mm). */
const areaPct = (d: Detection) =>
  d.bbox.width * d.bbox.height <= 0 ? 0 : Math.min(100, (d.bbox.width * d.bbox.height) / 100);

const ComparisonCard: React.FC<{ c: AeroMemoryComparison }> = ({ c }) => {
  const m = aeromemoryStateMeta(c.state);
  const tm = typeMeta(c.defect_type);
  const isNew = c.state === 'new';
  const progress = isNew ? 0 : Math.min(0.95, Math.max(0.05, c.match_confidence));
  return (
    <div className="p-4 rounded-xl bg-surface-container-low/60 flex flex-col gap-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-2 min-w-0">
          <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${tm.dot}`} />
          <span className="font-body-md text-body-md font-semibold text-on-surface truncate">
            {tm.name}
          </span>
          <span className="font-mono text-[11px] text-secondary">{c.defect_id}</span>
        </span>
        <span className={`px-2 py-0.5 rounded-full font-caption-data text-[10px] font-bold whitespace-nowrap ${m.pill}`}>
          {m.label}
        </span>
      </div>
      <div className="flex items-center justify-between font-caption-data text-caption-data text-secondary">
        <span>Severity</span>
        <StatusPill tone={c.severity === 'Critical' || c.severity === 'High' ? 'error' : c.severity === 'Medium' ? 'attention' : 'positive'}>
          {c.severity}
        </StatusPill>
      </div>
      {!isNew && (
        <>
          <div className="flex items-center justify-between font-caption-data text-caption-data text-secondary">
            <span>Match confidence</span>
            <span className="font-mono font-bold text-on-surface">{Math.round(c.match_confidence * 100)}%</span>
          </div>
          <div>
            <div className="flex items-center justify-between font-caption-data text-[10px] text-secondary mb-1">
              <span>Relative growth (0.95 max)</span>
              <span className="font-mono">{Math.round(progress * 100)}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-surface-container overflow-hidden">
              <div className={`h-full rounded-full ${tm.dot}`} style={{ width: `${progress * 100}%` }} />
            </div>
          </div>
        </>
      )}
      {isNew && (
        <p className="font-caption-data text-caption-data text-secondary leading-snug">
          First time this defect was seen on this airframe/component — it now has a tracked record for future comparisons.
        </p>
      )}
    </div>
  );
};

export const AeroMemory: React.FC = () => {
  // Live inspection list (selector) — 10 s refresh, same endpoint as History.
  const { data: inspections, error: listError } = usePolling<Inspection[]>(() => api.listInspections(), 10000);
  const list = inspections ?? [];

  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Default to the newest inspection once the list arrives.
  useEffect(() => {
    if (selectedId === null && list.length > 0) setSelectedId(list[0].id);
  }, [list, selectedId]);

  // Result fetch for the selected inspection.
  const { data: result, loading, error, run } = useApi<LatestResult | null>(null);
  useEffect(() => {
    if (selectedId !== null) run(() => api.getLatestResult(selectedId));
  }, [selectedId, run]);

  const hasResult = result?.has_result === true;
  const comparisons = result?.aeromemory?.comparisons ?? [];
  const detections = result?.detections ?? [];

  const classCounts = useMemo(() => {
    const counts = new Map<number, number>();
    detections.forEach((d) => counts.set(d.class_id, (counts.get(d.class_id) ?? 0) + 1));
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  }, [detections]);

  const selected = list.find((i) => i.id === selectedId) ?? null;
  const matchedCount = comparisons.filter((c) => c.state !== 'new').length;
  const newCount = comparisons.filter((c) => c.state === 'new').length;

  return (
    <AppShell>
      {/* Header */}
      <PageHeader
        title="AeroMemory"
        subtitle="Longitudinal defect tracking — what the engine matched against earlier inspections of the same airframe & component."
        chips={
          <>
            <MetaChip icon="neurology" label="Tracked defects" value={String(comparisons.length)} tone="primary" />
            <MetaChip icon="sync" label="Matched" value={String(matchedCount)} />
            <MetaChip icon="fiber_new" label="First-seen" value={String(newCount)} />
          </>
        }
      />

      {/* Inspection selector */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-end gap-4">
          <div className="flex-1">
            <label className="font-caption-data text-caption-data font-bold uppercase tracking-wider text-secondary block mb-1.5">
              Inspection
            </label>
            {list.length === 0 ? (
              <div className="h-11 px-4 rounded-xl bg-surface-container-low flex items-center text-secondary font-body-md text-body-md">
                {listError ? 'Backend offline — start the server on port 8000.' : 'No inspections recorded yet.'}
              </div>
            ) : (
              <select
                className="w-full h-11 px-4 rounded-xl bg-surface-container-low text-on-surface font-body-md text-body-md focus:outline-none focus:bg-surface-container cursor-pointer appearance-none"
                value={selectedId ?? ''}
                onChange={(e) => setSelectedId(parseInt(e.target.value, 10))}
              >
                {list.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.inspection_code} · {i.aircraft_code ?? 'unknown airframe'} · {i.panel_code ?? `panel #${i.panel_id}`} · {fmtDateTime(i.inspection_date)}
                  </option>
                ))}
              </select>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" icon="refresh" onClick={() => selectedId !== null && run(() => api.getLatestResult(selectedId))}>
              Refresh
            </Button>
            {selectedId !== null && (
              <Link to={`/inspections/${selectedId}`}>
                <Button icon="visibility">Open result</Button>
              </Link>
            )}
          </div>
        </div>
      </Card>

      {/* Body */}
      {!selectedId && list.length === 0 && !listError && (
        <Card>
          <EmptyState
            icon="neurology"
            message="Nothing to compare yet — run your first inspection."
            action={
              <Link to="/inspections/new">
                <Button icon="add_circle">New Inspection</Button>
              </Link>
            }
          />
        </Card>
      )}

      {selectedId !== null && loading && !result && (
        <Card>
          <LoadingState message="Loading tracked defects for this inspection…" />
        </Card>
      )}

      {selectedId !== null && error && !result && (
        <Card>
          <ErrorState
            message="Unable to load the latest result. Check that the AeroIntel server is running."
            action={
              <Button variant="secondary" icon="refresh" onClick={() => run(() => api.getLatestResult(selectedId))}>
                Retry
              </Button>
            }
          />
        </Card>
      )}

      {selectedId !== null && result && !hasResult && (
        <Card>
          <EmptyState
            icon="add_photo_alternate"
            message={`No captures yet for ${result.inspection_code ?? 'this inspection'} — the AeroMemory comparison runs when an image is uploaded.`}
            action={
              <Link to="/inspections/new">
                <Button icon="add_circle">New Inspection</Button>
              </Link>
            }
          />
        </Card>
      )}

      {selectedId !== null && result && hasResult && (
        <>
          {/* Context strip — real fields only */}
          <div className="flex flex-wrap items-center gap-3 px-5 py-3.5 rounded-2xl bg-surface-container-lowest/90 backdrop-blur-xl card-shadow">
            <span className="font-mono font-bold text-primary">{result.inspection_code}</span>
            <span className="w-1 h-1 rounded-full bg-outline-variant" />
            <span className="font-caption-data text-caption-data text-secondary">
              {selected?.aircraft_code ?? '—'} · {selected?.panel_code ?? `panel #${result.inspection_id}`}
            </span>
            <span className="w-1 h-1 rounded-full bg-outline-variant" />
            <span className="font-caption-data text-caption-data text-secondary">
              {result.image_width}×{result.image_height}px · {result.count} detection{result.count === 1 ? '' : 's'}
            </span>
            <span className="w-1 h-1 rounded-full bg-outline-variant" />
            <span className="font-caption-data text-caption-data text-secondary">
              engine matched {matchedCount} · first-seen {newCount}
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Tracked defects */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              <Card title="Tracked Defects">
                {comparisons.length === 0 ? (
                  <p className="font-body-md text-body-md text-secondary py-6 text-center">
                    No tracked defects for this inspection — the image produced no detections.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {comparisons.map((c) => (
                      <ComparisonCard key={c.defect_id} c={c} />
                    ))}
                  </div>
                )}
                <p className="font-caption-data text-caption-data text-secondary leading-snug mt-4 pt-3 border-t border-surface-container-high/40">
                  States: <span className="font-bold text-on-surface">NEW</span> first sighting ·{' '}
                  <span className="font-bold text-on-surface">STABLE</span> size unchanged ·{' '}
                  <span className="font-bold text-on-surface">PROGRESSING</span> grew vs last inspection ·{' '}
                  <span className="font-bold text-on-surface">IMPROVING</span> shrank ·{' '}
                  <span className="font-bold text-on-surface">REPAIRED</span> closed out.
                </p>
              </Card>
            </div>

            {/* Detections of this scan */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              <Card title="This Scan's Detections">
                {classCounts.length === 0 ? (
                  <p className="font-body-md text-body-md text-secondary py-6 text-center">
                    No detections in the latest image.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {classCounts.map(([classId, n]) => (
                      <ClassChip key={classId} classId={classId} count={n} />
                    ))}
                  </div>
                )}
                <div className="flex flex-col gap-3">
                  {detections.map((d, i) => {
                    const meta = classMeta(d.class_id);
                    return (
                      <div key={d.id ?? i} className="flex items-center gap-3">
                        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${meta.dot}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-body-md text-body-md font-semibold text-on-surface">{meta.name}</span>
                            <span className="font-caption-data text-caption-data font-bold text-on-surface">
                              {Math.round(d.confidence * 100)}%
                            </span>
                          </div>
                          <div className="h-1.5 rounded-full bg-surface-container overflow-hidden">
                            <div className={`h-full rounded-full ${meta.dot}`} style={{ width: `${d.confidence * 100}%` }} />
                          </div>
                          <div className="font-caption-data text-caption-data text-secondary mt-1">
                            bbox {Math.round(d.bbox.width)}×{Math.round(d.bbox.height)}px @ ({Math.round(d.bbox.x)}, {Math.round(d.bbox.y)})
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <p className="font-caption-data text-caption-data text-secondary leading-snug mt-4 pt-3 border-t border-surface-container-high/40">
                  Sizes are pixel measurements (bbox {`{x, y, width, height}`} in original image px). Physical units arrive with calibration (Stage 2+).
                </p>
              </Card>

              {/* How this works — REAL pipeline summary */}
              <Card title="How the comparison works">
                <ol className="flex flex-col gap-2.5 font-body-md text-body-md text-on-surface list-decimal pl-5">
                  <li>Upload runs YOLO detection on the image (atomic save in the same request).</li>
                  <li>The engine fetches the previous inspection of the same airframe + component.</li>
                  <li>Previous boxes are image-registered onto the new frame, then matched to current detections.</li>
                  <li>Matched defects get a progression state + re-assessed severity; unmatched ones become NEW tracked defects (DEF-#### IDs).</li>
                </ol>
                <p className="font-caption-data text-caption-data text-secondary leading-snug mt-3">
                  Per-defect history timelines and ghost-overlay views land with the AeroMemory compare endpoint (Stage 2.3).
                </p>
              </Card>
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
};

export default AeroMemory;
