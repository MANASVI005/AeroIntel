import React from 'react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeader, MetaChip, Card, Button,
  LoadingState, ErrorState,
} from '../components/common';
import { useApi } from '../hooks/useApi';
import { api } from '../services/api';
import type { ModelMetrics } from '../services/types';

/**
 * Model Performance (stitch/aerointel_model_performance.html).
 * Data: GET /api/metrics (new endpoint) — serves the verified test-split
 * evaluation and measured latency verbatim from logs/*.json + models/registry.json.
 * NO-HOLLOW-UI drops vs Stitch: invented "+2.4%" trend chips, "Run Benchmark"
 * button (no such endpoint), invented per-class P/R values that contradict our
 * real eval, and the invented "Detection Distribution" donut (2,418 detections
 * with no source). Overall metrics, per-class P/R/mAP, latency p50/p95 and
 * dataset size are the REAL numbers.
 */

const fmt3 = (v: number | null | undefined) => (v == null ? '—' : v.toFixed(3));

const CLASS_KEYS: { key: string; id: number; color: string }[] = [
  { key: 'Crack', id: 0, color: '#ba1a1a' },
  { key: 'Corrosion', id: 1, color: '#8a4b12' },
  { key: 'Dent', id: 2, color: '#7a5900' },
  { key: 'Missing Fastener', id: 3, color: '#6750a4' },
];

const MetricTile: React.FC<{ label: string; value: string; sub: string }> = ({
  label,
  value,
  sub,
}) => (
  <div className="p-5 rounded-2xl bg-surface-container-lowest/90 backdrop-blur-xl card-shadow flex flex-col gap-1">
    <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
      {label}
    </span>
    <span className="font-metric-stat text-metric-stat text-primary">{value}</span>
    <span className="font-caption-data text-caption-data text-secondary">{sub}</span>
  </div>
);

const ClassBar: React.FC<{ label: string; value: number; color: string }> = ({ label, value, color }) => (
  <div>
    <div className="flex items-center justify-between mb-1.5">
      <span className="flex items-center gap-2 font-body-md text-body-md font-semibold text-on-surface">
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </span>
      <span className="font-caption-data text-caption-data font-bold text-on-surface">{fmt3(value)}</span>
    </div>
    <div className="h-2 rounded-full bg-surface-container overflow-hidden">
      <div className="h-full rounded-full" style={{ width: `${value * 100}%`, backgroundColor: color }} />
    </div>
  </div>
);

export const ModelPerformance: React.FC = () => {
  const { data, loading, error, run } = useApi<ModelMetrics | null>(null);

  React.useEffect(() => {
    run(() => api.getMetrics());
  }, [run]);

  if (loading && !data) {
    return (
      <AppShell>
        <Card>
          <LoadingState message="Loading model metrics…" />
        </Card>
      </AppShell>
    );
  }

  if (error && !data) {
    return (
      <AppShell>
        <Card>
          <ErrorState
            message="Unable to load model metrics. Check that the AeroIntel server is running."
            action={
              <Button variant="secondary" icon="refresh" onClick={() => run(() => api.getMetrics())}>
                Retry
              </Button>
            }
          />
        </Card>
      </AppShell>
    );
  }

  if (!data) return null;

  const model = data.model;
  const evaluation = data.evaluation;
  const latency = data.latency;
  const overall = evaluation.overall;
  const classes = CLASS_KEYS.filter((c) => evaluation.per_class[c.key] != null);

  return (
    <AppShell>
      <PageHeader
        title="Model Performance"
        subtitle="Verified test-split evaluation and measured inference latency — served live from the training pipeline's own logs."
        chips={
          <>
            <MetaChip
              icon="memory"
              label="Model"
              value={`${model.name ?? '—'} ${model.version ?? ''}`}
              tone="primary"
            />
            <MetaChip icon="dataset" label="Split" value={evaluation.split ?? '—'} />
            <MetaChip
              icon="schedule"
              label="Latency p50"
              value={latency.p50_ms != null ? `${latency.p50_ms} ms` : '—'}
            />
          </>
        }
      />

      {/* Overall metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricTile label="Precision" value={fmt3(overall.precision)} sub="TP / (TP + FP)" />
        <MetricTile label="Recall" value={fmt3(overall.recall)} sub="TP / (TP + FN)" />
        <MetricTile label="mAP@50" value={fmt3(overall.mAP50)} sub="mean AP @ IoU 0.50" />
        <MetricTile label="mAP@50-95" value={fmt3(overall['mAP50-95'])} sub="multi-IoU 0.50:0.05:0.95" />
      </div>

      {/* Per-class performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
        <Card title="Per-class accuracy (mAP@50)">
          <div className="flex flex-col gap-4">
            {classes.map((c) => (
              <ClassBar
                key={c.key}
                label={c.key}
                value={evaluation.per_class[c.key].mAP50}
                color={c.color}
              />
            ))}
          </div>
          <p className="font-caption-data text-caption-data text-secondary leading-snug mt-4 pt-3 border-t border-surface-container-high/40">
            Known v1 limitation: Corrosion mAP@50 is 0.233 (recall 0.213) — corrosion findings are decision
            support for a human reviewer, not a cleared result.
          </p>
        </Card>

        <Card title="Per-class precision &amp; recall">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-secondary font-label-table-head text-label-table-head uppercase tracking-wider text-[11px] border-b border-surface-container-high/60">
                  <th className="py-2.5 px-3 font-bold">Class</th>
                  <th className="py-2.5 px-3 font-bold">Precision</th>
                  <th className="py-2.5 px-3 font-bold">Recall</th>
                  <th className="py-2.5 px-3 font-bold">mAP@50</th>
                  <th className="py-2.5 px-3 font-bold">mAP@50-95</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-low font-body-md text-body-md">
                {classes.map((c) => {
                  const m = evaluation.per_class[c.key];
                  return (
                    <tr key={c.key}>
                      <td className="py-2.5 px-3 font-semibold">
                        <span className="inline-flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c.color }} />
                          {c.key}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono">{fmt3(m.precision)}</td>
                      <td className="py-2.5 px-3 font-mono">{fmt3(m.recall)}</td>
                      <td className="py-2.5 px-3 font-mono">{fmt3(m.mAP50)}</td>
                      <td className="py-2.5 px-3 font-mono">{fmt3(m['mAP50-95'])}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="font-caption-data text-caption-data text-secondary mt-3">
            {evaluation.dataset.images.toLocaleString()} test images · {evaluation.dataset.annotations.toLocaleString()}{' '}
            annotations · run {evaluation.run ?? '—'}
          </p>
        </Card>
      </div>

      {/* Latency + model card */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
        <Card title="Inference latency (measured)">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-surface-container-low/60">
              <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary block">
                p50
              </span>
              <span className="font-metric-stat text-metric-stat text-tertiary">
                {latency.p50_ms != null ? `${latency.p50_ms} ms` : '—'}
              </span>
            </div>
            <div className="p-4 rounded-xl bg-surface-container-low/60">
              <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary block">
                p95
              </span>
              <span className="font-metric-stat text-metric-stat text-tertiary">
                {latency.p95_ms != null ? `${latency.p95_ms} ms` : '—'}
              </span>
            </div>
          </div>
          <p className="font-caption-data text-caption-data text-secondary mt-4">
            {latency.n_images ?? '—'} images · conf ≥ {latency.conf ?? '—'} · IoU {latency.iou ?? '—'} ·{' '}
            {latency.device ?? 'device not recorded'}
          </p>
        </Card>

        <Card title="Model card">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            {[
              { label: 'Name', value: model.name ?? '—' },
              { label: 'Architecture', value: model.type ?? '—' },
              { label: 'Version', value: model.version ?? '—' },
              { label: 'Input size', value: model.imgsz != null ? `${model.imgsz}px` : '—' },
              { label: 'Trained from', value: model.trained_from ?? '—' },
              {
                label: 'Exported',
                value: model.exported_at ? model.exported_at.slice(0, 10) : '—',
              },
            ].map((f) => (
              <div key={f.label} className="flex flex-col gap-0.5">
                <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
                  {f.label}
                </span>
                <span className="font-body-md text-body-md font-semibold text-on-surface break-words">{f.value}</span>
              </div>
            ))}
          </div>
          <p className="font-caption-data text-caption-data text-secondary mt-4 pt-3 border-t border-surface-container-high/40">
            Classes: {model.classes
              ? Object.entries(model.classes)
                  .map(([id, name]) => `${id} ${name}`)
                  .join(' · ')
              : '—'}
          </p>
        </Card>
      </div>
    </AppShell>
  );
};

export default ModelPerformance;
