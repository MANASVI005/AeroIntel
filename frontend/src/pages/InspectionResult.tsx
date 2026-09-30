import React, { useMemo, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeader, MetaChip, Card, Button, StatusPill,
  LoadingState, ErrorState,
} from '../components/common';
import { classMeta, aeromemoryStateMeta } from '../types/classes';
import { api, imageBaseUrl, ApiServiceError } from '../services/api';
import type { UploadResult, Detection, DecisionSupport } from '../services/types';
import { useApi } from '../hooks/useApi';

/**
 * Inspection Result — hero page (stitch/aerointel_inspection_result.html).
 * Data sources, in order:
 *   1. Router state from New Inspection (UploadResult — instant)
 *   2. GET /api/inspections/{id}/latest-result (direct URL / refresh / polling)
 * Golden rules: boxes come from the backend, frontend only draws them;
 * mm values only if backend calibration exists (v1: pixel deltas).
 *
 * Decision Support is REAL: POST /api/decisions/{detection_id} runs the backend
 * rule engine once per detection and stores the record. The backend has no GET
 * endpoint for decisions, so rows start collapsed and the engineer explicitly
 * generates the assessment (409 = already on file from an earlier visit).
 */

interface RouterState {
  result?: UploadResult;
}

/** Bbox overlay box — scales stored original-pixel coords to displayed size. */
const BboxBox: React.FC<{
  det: Detection;
  scale: { x: number; y: number };
  dimmed: boolean;
}> = ({ det, scale, dimmed }) => {
  const meta = classMeta(det.class_id);
  const color =
    det.class_id === 0 ? '#ba1a1a' : det.class_id === 1 ? '#8a4b12' : det.class_id === 2 ? '#7a5900' : '#6750a4';
  return (
    <div
      className="absolute border-2 rounded-md transition-opacity"
      style={{
        left: det.bbox.x * scale.x,
        top: det.bbox.y * scale.y,
        width: det.bbox.width * scale.x,
        height: det.bbox.height * scale.y,
        borderColor: color,
        opacity: dimmed ? 0.3 : 1,
      }}
    >
      <span
        className="absolute -top-5 left-0 px-1.5 py-0.5 rounded text-[10px] font-bold text-white whitespace-nowrap"
        style={{ backgroundColor: color }}
      >
        {meta.name} · {Math.round(det.confidence * 100)}%
      </span>
    </div>
  );
};

const SEVERITY_TONE: Record<string, 'primary' | 'attention' | 'positive' | 'error'> = {
  Low: 'positive',
  Medium: 'primary',
  High: 'attention',
  Critical: 'error',
};

/** One detection's decision-support row — explicit generate, honest 409. */
const DecisionRow: React.FC<{ detection: Detection; onDecision?: (d: DecisionSupport) => void }> = ({
  detection,
  onDecision,
}) => {
  const [decision, setDecision] = useState<DecisionSupport | null>(null);
  const [loading, setLoading] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const meta = classMeta(detection.class_id);
  const firstTime = detection.id == null;

  const generate = async () => {
    if (detection.id == null || loading) return;
    setLoading(true);
    setError(null);
    setConflict(false);
    try {
      const d = await api.createDecisionSupport(detection.id);
      setDecision(d);
      onDecision?.(d);
    } catch (err) {
      if (err instanceof ApiServiceError && err.status === 409) {
        setConflict(true); // rule-engine record already stored for this detection
      } else {
        setError(err instanceof Error ? err.message : 'Decision engine unreachable.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-3.5 rounded-xl bg-surface-container-low/60 flex flex-col gap-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-2 min-w-0">
          <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${meta.dot}`} />
          <span className="font-body-md text-body-md font-semibold text-on-surface truncate">{meta.name}</span>
        </span>
        <span className="font-caption-data text-caption-data font-bold text-on-surface whitespace-nowrap">
          {Math.round(detection.confidence * 100)}% confidence
        </span>
      </div>

      {decision ? (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill tone={SEVERITY_TONE[decision.severity] ?? 'neutral'}>Severity: {decision.severity}</StatusPill>
            <MetaChip icon="trending_up" label="Progression" value={decision.progression_status} />
          </div>
          <div className="border-l-2 border-primary/60 pl-3 py-1">
            <p className="font-caption-data text-caption-data font-bold uppercase tracking-wider text-secondary mb-0.5">
              Recommended action
            </p>
            <p className="font-body-md text-body-md text-on-surface">{decision.recommended_action}</p>
          </div>
          <p className="font-caption-data text-caption-data text-secondary leading-snug">{decision.reasoning}</p>
        </>
      ) : conflict ? (
        <p className="font-caption-data text-caption-data text-secondary leading-snug">
          Assessment already on file for this detection (generated during an earlier review).
          Re-running inference on the same panel image creates a new detection, which can then be assessed.
        </p>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="font-caption-data text-caption-data text-secondary leading-snug flex-1 min-w-[220px]">
            {firstTime
              ? 'This detection has no database ID yet — re-open this inspection to generate its assessment.'
              : loading
                ? 'Consulting the rule engine…'
                : 'Rule-based assessment is generated once per detection and stored for audit.'}
          </p>
          {!firstTime && !loading && (
            <Button variant="secondary" icon="psychology" onClick={generate}>
              Generate
            </Button>
          )}
        </div>
      )}

      {error && <p className="font-caption-data text-caption-data text-error">{error}</p>}
    </div>
  );
};

export const InspectionResult: React.FC<{ onDecisionsChange?: (d: Record<number, DecisionSupport>) => void }> = ({
  onDecisionsChange,
}) => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const routerState = (location.state as RouterState | null)?.result ?? null;

  const [showBoxes, setShowBoxes] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [confThreshold, setConfThreshold] = useState(0.4);

  // Fetch latest result (no-op fallback if router state exists — still polls
  // lightly so direct URL opens work; 5 s is fine here, dashboard uses 2 s).
  const { data, loading, error } = useApi<UploadResult>(routerState);
  React.useEffect(() => {
    if (!routerState) {
      // direct URL entry — fetch once (and let AeroMemory badges refresh)
      const t = setInterval(() => {
        if (id) api.getLatestResult(parseInt(id, 10)).catch(() => undefined);
      }, 5000);
      return () => clearInterval(t);
    }
  }, [routerState, id]);

  const result: UploadResult | null = data ?? routerState;

  const visible = useMemo(
    () => (result?.detections ?? []).filter((d) => d.confidence >= confThreshold),
    [result, confThreshold]
  );
  const hiddenCount = (result?.detections?.length ?? 0) - visible.length;

  // Decision-support rows report their fetched records upward (used by Reports later).
  const [decisions, setDecisions] = useState<Record<number, DecisionSupport>>({});
  const upsertDecision = (d: DecisionSupport) =>
    setDecisions((prev) => (prev[d.detection_id]?.id === d.id ? prev : { ...prev, [d.detection_id]: d }));
  const decisionsKey = JSON.stringify(decisions);
  React.useEffect(() => {
    onDecisionsChange?.(decisions);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [decisionsKey]);

  /* image scale: displayed px / natural px — recomputed via onLoad */
  const [scale, setScale] = useState({ x: 1, y: 1 });
  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    if (result && result.image_width && result.image_height) {
      setScale({ x: img.clientWidth / result.image_width, y: img.clientHeight / result.image_height });
    }
  };

  return (
    <AppShell>
      {/* Breadcrumb + header */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 font-caption-data text-caption-data text-secondary">
          <Link to="/dashboard" className="hover:text-primary transition-colors cursor-pointer">Inspections</Link>
          <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          <span className="text-on-surface-variant font-medium">{result?.inspection_code ?? `INS-${id}`}</span>
          <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          <span className="text-primary font-semibold">Results &amp; Triage</span>
        </div>
        <PageHeader
          title="Inspection Result"
          subtitle="AI-detected defects, historical findings and decision support."
          chips={
            <>
              <MetaChip icon="tag" label="Inspection" value={result?.inspection_code ?? `#${id}`} />
              <MetaChip icon="image" label="Image" value={result ? `${result.image_width}×${result.image_height}px` : '—'} />
              <MetaChip icon="center_focus_strong" label="Detections" value={String(result?.count ?? 0)} tone="primary" />
            </>
          }
        />
      </div>

      {loading && !result && <Card><LoadingState message="Loading inspection result…" /></Card>}
      {error && !result && (
        <Card>
          <ErrorState
            message="Unable to load inspection. Please check the local AeroIntel server."
            action={<Link to="/dashboard" className="px-4 py-2 rounded-full bg-primary text-on-primary font-caption-data text-caption-data font-bold">Back to Dashboard</Link>}
          />
        </Card>
      )}

      {result && (
        <>
          {/* Main grid: viewer + defects panel */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* LEFT: image viewer */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              <div className="relative rounded-3xl bg-surface-container-lowest/90 backdrop-blur-xl p-4 card-shadow overflow-hidden">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-3 px-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowBoxes((v) => !v)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full font-caption-data text-caption-data font-semibold shadow-sm transition-all ${showBoxes ? 'bg-primary text-on-primary hover:bg-primary-container' : 'bg-surface-container text-secondary'}`}
                    >
                      <span className="material-symbols-outlined text-[16px]">{showBoxes ? 'check_circle' : 'radio_button_unchecked'}</span>
                      <span>Boxes</span>
                    </button>
                    <button
                      onClick={() => setShowLabels((v) => !v)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full font-caption-data text-caption-data font-semibold shadow-sm transition-all ${showLabels ? 'bg-primary text-on-primary hover:bg-primary-container' : 'bg-surface-container text-secondary'}`}
                    >
                      <span className="material-symbols-outlined text-[16px]">{showLabels ? 'label' : 'hide_source'}</span>
                      <span>Labels</span>
                    </button>
                  </div>
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-surface-container text-secondary font-caption-data text-caption-data">
                    <span className="material-symbols-outlined text-[14px]">photo_size_select_large</span>
                    {visible.length} boxes drawn from backend coords
                  </span>
                </div>

                <div className="relative w-full rounded-2xl overflow-hidden bg-surface-container-low">
                  <img
                    src={routerState ? undefined : `${imageBaseUrl}/${result.stored_path?.replace(/\\/g, '/')}`}
                    alt="Inspection frame"
                    className="w-full h-auto max-h-[560px] object-contain"
                    onLoad={onImageLoad}
                    ref={(el) => {
                      if (el?.complete) onImageLoad({ currentTarget: el } as React.SyntheticEvent<HTMLImageElement>);
                    }}
                  />
                  {showBoxes &&
                    visible.map((d, i) => (
                      <BboxBox key={d.id ?? i} det={d} scale={scale} dimmed={false} />
                    ))}
                </div>
              </div>

              {/* Findings table */}
              <Card title="Inspection Findings">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="text-secondary font-label-table-head text-label-table-head uppercase tracking-wider text-[11px] border-b border-surface-container-high/60">
                        <th className="py-3 px-4 rounded-l-xl font-bold">Defect</th>
                        <th className="py-3 px-4 font-bold">Confidence</th>
                        <th className="py-3 px-4 font-bold">Location</th>
                        <th className="py-3 px-4 font-bold">Size (px)</th>
                        <th className="py-3 px-4 rounded-r-xl font-bold">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-container-low font-body-md text-body-md text-on-surface">
                      {visible.length === 0 && (
                        <tr>
                          <td colSpan={5} className="py-6 px-4 text-center text-secondary">
                            No active defects detected.
                          </td>
                        </tr>
                      )}
                      {visible.map((d, i) => {
                        const meta = classMeta(d.class_id);
                        return (
                          <tr key={d.id ?? i} className="hover:bg-surface-container-lowest/60 transition-all">
                            <td className="py-3.5 px-4">
                              <span className="inline-flex items-center gap-2">
                                <span className={`w-2.5 h-2.5 rounded-full ${meta.dot}`} />
                                <span className="font-semibold text-on-surface">{meta.name}</span>
                              </span>
                            </td>
                            <td className="py-3.5 px-4 font-caption-data font-bold">{Math.round(d.confidence * 100)}%</td>
                            <td className="py-3.5 px-4 font-caption-data text-secondary">
                              x:{Math.round(d.bbox.x)} · y:{Math.round(d.bbox.y)}
                            </td>
                            <td className="py-3.5 px-4 font-mono text-secondary text-caption-data">
                              {Math.round(d.bbox.width)}×{Math.round(d.bbox.height)}
                            </td>
                            <td className="py-3.5 px-4">
                              <StatusPill tone="neutral">Open</StatusPill>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>

            {/* RIGHT: detected defects panel */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              <Card title="Detected Defects">
                <div className="flex flex-col gap-3">
                  {visible.length === 0 && (
                    <p className="font-body-md text-body-md text-secondary text-center py-6">
                      No active defects detected.
                    </p>
                  )}
                  {visible
                    .slice()
                    .sort((a, b) => b.confidence - a.confidence)
                    .map((d, i) => {
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
                              <div
                                className={`h-full rounded-full ${meta.dot}`}
                                style={{ width: `${d.confidence * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
                <div className="mt-5 pt-4 border-t border-surface-container-high/40">
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="font-caption-data text-caption-data font-bold uppercase tracking-wider text-secondary">
                      Confidence threshold
                    </label>
                    <span className="px-2 py-0.5 rounded-md bg-primary-container text-on-primary font-caption-data text-[11px] font-bold">
                      {confThreshold.toFixed(2)}
                    </span>
                  </div>
                  <input
                    type="range" min="0.10" max="0.95" step="0.05"
                    value={confThreshold}
                    onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                    className="w-full accent-primary cursor-pointer"
                  />
                  <p className="font-caption-data text-caption-data text-secondary mt-1">
                    Showing {visible.length} of {result.detections.length} detections (client-side filter — does not re-run the model).
                  </p>
                  {hiddenCount > 0 && (
                    <p className="font-caption-data text-caption-data text-tertiary mt-0.5">
                      {hiddenCount} below threshold.
                    </p>
                  )}
                </div>
              </Card>

              {/* AeroMemory Analysis strip */}
              <Card>
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-10 h-10 rounded-2xl bg-secondary-fixed flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined text-[24px]">history</span>
                  </span>
                  <div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface">AeroMemory Analysis</h3>
                    <p className="font-caption-data text-caption-data text-secondary">Longitudinal comparison with aircraft history</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {result.aeromemory.comparisons.length === 0 && (
                    <p className="font-body-md text-body-md text-secondary col-span-full text-center py-4">
                      No AeroMemory history for this airframe yet — all detections recorded as first-seen.
                    </p>
                  )}
                  {result.aeromemory.comparisons.map((c) => {
                    const m = aeromemoryStateMeta(c.state);
                    return (
                      <div key={c.defect_id} className="p-3.5 rounded-xl bg-surface-container-low/60 flex flex-col gap-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-caption-data text-caption-data font-bold text-on-surface truncate">
                            {c.defect_type} · {c.defect_id}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full font-caption-data text-[10px] font-bold whitespace-nowrap ${m.pill}`}>
                            {m.label}
                          </span>
                        </div>
                        <div className="flex items-center justify-between font-caption-data text-caption-data text-secondary">
                          <span>Severity</span>
                          <span className="font-mono font-bold text-on-surface">{c.severity}</span>
                        </div>
                        <div className="flex items-center justify-between font-caption-data text-caption-data text-secondary">
                          <span>Match confidence</span>
                          <span className="font-mono text-tertiary font-bold">
                            {c.match_confidence > 0 ? `${Math.round(c.match_confidence * 100)}%` : '— first seen'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Decision Support — REAL: POST /api/decisions/{detection_id} per detection */}
              <Card title="Decision Support" actions={
                <span className="font-caption-data text-caption-data text-secondary">per-detection · from backend rule engine</span>
              }>
                {visible.length === 0 ? (
                  <p className="font-body-md text-body-md text-secondary text-center py-4">
                    No detections — no decision support required for this image.
                  </p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {visible.map((d, i) => (
                      <DecisionRow
                        key={d.id ?? i}
                        detection={d}
                        onDecision={upsertDecision}
                      />
                    ))}
                  </div>
                )}
                <p className="font-caption-data text-caption-data text-secondary leading-snug mt-4 pt-3 border-t border-surface-container-high/40">
                  Assessments come from the rule engine (v1.0.0) and are stored per detection. Decision support only — a qualified maintenance engineer makes the final call.
                </p>
              </Card>
            </div>
          </div>

          {/* Footer actions */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 pb-4">
            <div className="flex flex-wrap items-center gap-3">
              <Link
                to="/aeromemory"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-on-primary font-body-md text-body-md font-bold shadow-sm hover:bg-primary-container transition-all"
              >
                <span className="material-symbols-outlined text-[18px]">history</span>
                Compare with History
              </Link>
              <Link
                to={`/reports/${result.inspection_id}`}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-secondary-container text-on-secondary-container font-body-md text-body-md font-bold hover:bg-surface-container-high transition-all"
              >
                <span className="material-symbols-outlined text-[18px]">summarize</span>
                Generate Report
              </Link>
              <Link
                to="/inspections/new"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-outline-variant text-on-surface-variant font-body-md text-body-md font-semibold hover:bg-surface-container-low transition-all"
              >
                <span className="material-symbols-outlined text-[18px]">add_circle</span>
                New Inspection
              </Link>
            </div>
            <span className="font-caption-data text-caption-data text-secondary">
              Inspection {result.inspection_code} · {result.count} detections · image {result.image_width}×{result.image_height}
            </span>
          </div>
        </>
      )}
    </AppShell>
  );
};

export default InspectionResult;
