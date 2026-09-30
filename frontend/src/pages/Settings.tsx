import React, { useEffect, useState } from 'react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeader, MetaChip, Card, Button,
  LoadingState, ErrorState, StatusPill,
} from '../components/common';
import { useHealth } from '../hooks/useHealth';
import { useApi } from '../hooks/useApi';
import { api, imageBaseUrl } from '../services/api';
import type { HealthResponse, ModelMetrics } from '../services/types';

/**
 * Settings (stitch/aerointel_settings_configuration.html).
 * NO-HOLLOW-UI RULE: the Stitch mockup is nearly all fiction — FAA/A&P
 * certification records, invented AeroMemory vector-storage stats
 * ("2.4 GB / 10 GB across 86 tail inspections"), airframe/hangar dropdowns
 * nothing consumes, sensor-quality selects, and Save/Reset buttons with no
 * settings API behind them. What we actually have:
 *   - GET /health      → real system status (API + database)
 *   - GET /api/metrics → real model identity + pipeline facts
 *   - Known constants from the backend code (conf 0.40 / IoU 0.50 / 640 px are
 *     fixed in model_service.py; SQLite via DATABASE_URL; images under data/).
 * So this page is read-only System Status + pipeline documentation. Preference
 * editing arrives only if/when a settings endpoint exists.
 */

export const Settings: React.FC = () => {
  const { health, online, dbConnected } = useHealth();

  // Manual health re-check with last-checked timestamp.
  const { run, loading: checking } = useApi<HealthResponse | null>(null);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  useEffect(() => {
    if (health) setLastCheck(new Date());
  }, [health]);

  const recheck = async () => {
    const h = await run(() => api.getHealth());
    if (h) setLastCheck(new Date());
  };

  // Model facts for the pipeline card (non-critical if it fails).
  const [metricsData, setMetricsData] = useState<ModelMetrics | null>(null);
  useEffect(() => {
    let cancelled = false;
    api
      .getMetrics()
      .then((m) => {
        if (!cancelled) setMetricsData(m);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell>
      <PageHeader
        title="Settings"
        subtitle="System status and pipeline information for this AeroIntel installation. Read-only — configuration endpoints don't exist yet."
        chips={
          <>
            <MetaChip
              icon={online ? 'cloud_done' : 'cloud_off'}
              label="Backend"
              value={online ? 'Online' : 'Offline'}
              tone={online ? 'primary' : 'neutral'}
            />
            <MetaChip
              icon="database"
              label="Database"
              value={dbConnected ? 'Connected' : 'Disconnected'}
            />
          </>
        }
      />

      {/* ── System Status — the real feature (GET /health) ── */}
      <Card
        title="System Status"
        actions={
          <Button variant="secondary" icon="refresh" onClick={recheck} disabled={checking}>
            {checking ? 'Checking…' : 'Re-check now'}
          </Button>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-surface-container-low/60 flex items-center justify-between gap-3">
            <div className="flex flex-col gap-0.5">
              <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
                API server
              </span>
              <span className="font-caption-data text-caption-data text-secondary break-all">
                {imageBaseUrl}
              </span>
            </div>
            <StatusPill tone={online ? 'positive' : 'error'}>
              {online ? 'Healthy' : 'Offline'}
            </StatusPill>
          </div>
          <div className="p-4 rounded-xl bg-surface-container-low/60 flex items-center justify-between gap-3">
            <div className="flex flex-col gap-0.5">
              <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
                Database
              </span>
              <span className="font-caption-data text-caption-data text-secondary">
                Local SQLite (DATABASE_URL)
              </span>
            </div>
            <StatusPill tone={dbConnected ? 'positive' : 'error'}>
              {dbConnected ? 'Connected' : 'Disconnected'}
            </StatusPill>
          </div>
        </div>
        <p className="font-caption-data text-caption-data text-secondary mt-3">
          Auto-refreshes every 30 s
          {lastCheck ? ` · last checked ${lastCheck.toLocaleTimeString()}` : ''}
          {health?.status ? ` · status "${health.status}"` : ''}
        </p>
      </Card>

      {/* ── Detection pipeline — real facts from /api/metrics + backend code ── */}
      {metricsData ? (
        <Card title="Detection pipeline">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-4">
            {[
              { label: 'Model', value: `${metricsData.model.name ?? '—'} ${metricsData.model.version ?? ''}` },
              { label: 'Architecture', value: metricsData.model.type ?? '—' },
              { label: 'Input size', value: metricsData.model.imgsz != null ? `${metricsData.model.imgsz} px` : '—' },
              {
                label: 'Classes',
                value: metricsData.model.classes
                  ? `${Object.keys(metricsData.model.classes).length} damage types`
                  : '—',
              },
              { label: 'Confidence threshold', value: '0.40 (fixed server-side)' },
              { label: 'IoU threshold', value: '0.50 (fixed server-side)' },
              { label: 'Latency p50 / p95', value: `${metricsData.latency.p50_ms} / ${metricsData.latency.p95_ms} ms` },
              { label: 'Eval split', value: metricsData.evaluation.split ?? '—' },
            ].map((f) => (
              <div key={f.label} className="flex flex-col gap-0.5">
                <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
                  {f.label}
                </span>
                <span className="font-body-md text-body-md font-semibold text-on-surface break-words">{f.value}</span>
              </div>
            ))}
          </div>
          <p className="font-caption-data text-caption-data text-secondary leading-snug mt-4 pt-3 border-t border-surface-container-high/40">
            Thresholds are constants in the backend model service — there is no settings endpoint to change them
            from the UI (client-side confidence filtering on the Result screen is display-only).
          </p>
        </Card>
      ) : (
        <Card>
          <LoadingState message="Loading pipeline facts from /api/metrics…" />
        </Card>
      )}

      {/* ── Storage — real locations ── */}
      <Card title="Storage">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          {[
            { label: 'Database', value: 'SQLite file (aerointel_test.db in the repo root for local runs)' },
            { label: 'Inspection images', value: 'data/inspections/{inspection_code}/ under the backend root' },
            { label: 'Image serving', value: 'Static mount /data → used by Result, AeroMemory and Report screens' },
            { label: 'Metrics sources', value: 'logs/eval_*.json · logs/latency_*.json · models/registry.json' },
          ].map((f) => (
            <div key={f.label} className="flex flex-col gap-0.5">
              <span className="font-caption-data text-caption-data uppercase tracking-wider font-bold text-secondary">
                {f.label}
              </span>
              <span className="font-body-md text-body-md text-on-surface">{f.value}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* ── Honest scope note ── */}
      <Card>
        <ErrorState
          message="No preference controls: the backend has no settings endpoint yet. Certification records, hangar/station pickers and storage quotas from the original mockup were removed because nothing backs them."
          action={
            <span className="font-caption-data text-caption-data text-secondary">
              Preferences arrive with Stage 2+ if a settings API is added.
            </span>
          }
        />
      </Card>
    </AppShell>
  );
};

export default Settings;
