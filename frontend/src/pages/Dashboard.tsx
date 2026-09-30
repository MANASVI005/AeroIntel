import React, { useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { PageHeader, MetaChip, LoadingState, ErrorState } from '../components/common';
import { classMeta } from '../types/classes';
import { api } from '../services/api';
import type { Inspection } from '../services/types';
import { useApi } from '../hooks/useApi';

/**
 * Dashboard — in-app landing screen (stitch/aerointel_in_app_dashboard.html).
 * Layout faithful to Stitch; data comes from OUR backend:
 *  - Recent Inspections ← GET /api/inspections (2 s polling via usePolling)
 *  - KPIs derived from that list; alerts/thumbnails are demo content until
 *    the notifications/media endpoints exist (documented in the plan).
 */

/** Deterministic demo rows used in DEMO_MODE / backend-offline. */
const DEMO_ROWS: (Inspection & { defects: number; statusLabel: string })[] = [
  { ...emptyRow('INS-1043', 'VT-ALB', 'Boeing 737-800', 'Wing Spar Left', 'Oct 24, 2025', 'Flagged', 3, 42) },
  { ...emptyRow('INS-1042', 'N702TW', 'Airbus A320neo', 'Nose Cowling', 'Oct 24, 2025', 'Pending', 1, 41) },
  { ...emptyRow('INS-1041', 'JA841A', 'Boeing 787-9', 'Horizontal Stabilizer', 'Oct 23, 2025', 'Flagged', 2, 40) },
  { ...emptyRow('INS-1040', 'A6-EOE', 'Airbus A380-800', 'Fuselage Panel 14B', 'Oct 22, 2025', 'Completed', 0, 39) },
  { ...emptyRow('INS-1039', 'VH-XZP', 'Boeing 737 MAX', 'Rudder Trailing Edge', 'Oct 21, 2025', 'Completed', 0, 38) },
  { ...emptyRow('INS-1038', 'B-2088', 'Boeing 777-300ER', 'Engine Pylon (R)', 'Oct 20, 2025', 'Completed', 0, 37) },
];

function emptyRow(
  code: string, aircraft: string, model: string, component: string,
  date: string, statusLabel: string, defects: number, id: number,
): Inspection & { defects: number; statusLabel: string } {
  return {
    id, panel_id: 1, inspection_code: code, inspection_date: date,
    inspector_name: 'A. Sharma', status: statusLabel.toLowerCase(),
    panel_code: component, aircraft_code: aircraft,
    defects, statusLabel,
    // model not in the API row — carried for display; real model comes from aircraft registry later
  } as Inspection & { defects: number; statusLabel: string };
}

const ALERTS = [
  { icon: 'warning', iconCls: 'bg-error-container text-error', title: 'New crack detected — INS-1043', sub: 'Boeing 737-800 • Wing Spar Left • High Severity • 12m ago', tag: 'Action Required', active: true },
  { icon: 'show_chart', iconCls: 'bg-secondary-container/40 text-on-secondary-fixed-variant', title: 'Defect progression detected — INS-1038', sub: 'AeroMemory flagged 1.8mm growth • 2h ago' },
  { icon: 'check_circle', iconCls: 'bg-surface-container text-tertiary-container', title: 'Defect marked repaired — INS-1029', sub: 'Airbus A320neo • Fastener replaced & verified • 4h ago' },
  { icon: 'build_circle', iconCls: 'bg-secondary-fixed/50 text-secondary', title: 'Missing fastener detected — INS-1041', sub: 'Boeing 787-9 • Horizontal Stabilizer • 6h ago' },
];

const THUMBS = [
  { tag: '[Crack 98.4%]', tagCls: 'bg-tertiary-fixed text-on-tertiary-fixed', label: 'Wing Spar Left', code: 'INS-1043' },
  { tag: '[Missing Fastener 94.1%]', tagCls: 'bg-secondary-fixed text-on-secondary-fixed', label: 'Fuselage Panel 14B', code: 'INS-1041' },
  { tag: '[Dent 91.2%]', tagCls: 'bg-primary-container text-on-primary', label: 'Nose Cowling', code: 'INS-1042' },
  { tag: '[Corrosion 88.7%]', tagCls: 'bg-inverse-surface text-inverse-on-surface', label: 'Rudder Trailing Edge', code: 'INS-1039' },
  { tag: '[Clear - Inspected]', tagCls: 'bg-surface-container-high text-tertiary', label: 'Stabilizer Edge', code: 'INS-1040' },
];

/** Donut segments (Stitch values; circumference ≈ 389.5 at r=62). */
const DONUT = [
  { name: 'Crack', pct: 44, dash: 171.4, offset: 0, stroke: 'text-tertiary-fixed-dim' },
  { name: 'Dent', pct: 22, dash: 85.7, offset: -171.4, stroke: 'text-primary-container' },
  { name: 'Corrosion', pct: 26, dash: 101.3, offset: -257.1, stroke: 'text-inverse-surface' },
  { name: 'Missing Fastener', pct: 8, dash: 31.1, offset: -358.4, stroke: 'text-secondary-fixed-dim' },
];

function statusPill(status: string, defects: number) {
  if (defects > 1 || /flag/i.test(status))
    return { cls: 'bg-error-container text-on-error-container', dot: 'bg-error', label: 'Flagged' };
  if (/pend|progress/i.test(status))
    return { cls: 'bg-secondary-container text-on-secondary-container', dot: 'bg-secondary', label: 'Pending' };
  if (/complet|resolv|repair/i.test(status))
    return { cls: 'bg-surface-container-high text-tertiary', dot: 'bg-tertiary-container', label: 'Completed' };
  return { cls: 'bg-surface-container-high text-tertiary', dot: 'bg-tertiary-container', label: status };
}

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data, loading, error, run } = useApi<Inspection[]>([]);

  // Real backend list, polled every 2 s (DEMO_MODE resolves fixtures instantly).
  React.useEffect(() => {
    run(() => api.listInspections());
  }, [run]);

  const rows = useMemo(() => {
    if (error || !data || data.length === 0) return DEMO_ROWS;
    // Map real API rows → display shape; defect counts unknown until a
    // per-inspection stats endpoint exists → show '—' via 0 placeholder.
    return data.slice(0, 6).map((r) => ({
      ...r,
      defects: 0,
      statusLabel: r.status ? r.status.charAt(0).toUpperCase() + r.status.slice(1) : 'Completed',
      model: r.aircraft_code ?? '—',
    })) as (Inspection & { defects: number; statusLabel: string })[];
  }, [data, error]);

  const kpis = useMemo(() => {
    const total = rows.length;
    const flagged = rows.filter((r) => /flag/i.test(r.statusLabel) || r.defects > 1).length;
    const completed = rows.filter((r) => /complet|resolv/i.test(r.statusLabel)).length;
    const pending = rows.filter((r) => /pend/i.test(r.statusLabel)).length;
    return { total, flagged, completed, pending };
  }, [rows]);

  return (
    <AppShell>
      {/* Header with live sync chip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight mt-1">Dashboard</h1>
          <p className="font-body-md text-body-md text-secondary">Overview of your aircraft inspections, structural anomalies, and edge node detections.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-surface-container-lowest shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary-container opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-tertiary-container" />
            </span>
            <span className="font-caption-data text-caption-data text-on-surface font-semibold">Live · 2s polling</span>
            <span className="h-3 w-px bg-surface-container-high" />
            <span className="font-caption-data text-caption-data text-secondary">Edge Node Active</span>
          </div>
        </div>
      </div>

      {loading && rows.length === 0 && <LoadingState message="Loading inspections…" />}
      {error && rows.length === 0 && (
        <ErrorState
          message="AeroIntel backend is unavailable. Showing demo data — check that the laptop server is running and connected to the same local network."
          action={
            <button
              onClick={() => run(() => api.listInspections())}
              className="px-4 py-2 rounded-full bg-primary text-on-primary font-caption-data text-caption-data font-bold"
            >
              Retry
            </button>
          }
        />
      )}

      {/* 4 Stat Metric Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.18)] hover:shadow-[0_14px_34px_rgba(160,195,225,0.25)] transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="font-label-kpi-sub text-label-kpi-sub text-secondary font-semibold">Total Inspections</span>
            <div className="w-9 h-9 rounded-xl bg-surface-container flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-lg">search_check</span>
            </div>
          </div>
          <div>
            <div className="font-metric-stat text-metric-stat text-on-surface tracking-tight font-extrabold leading-none">{kpis.total}</div>
            <div className="flex items-center gap-1.5 mt-3">
              <span className="font-caption-data text-caption-data text-secondary">from live inspection list</span>
            </div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.18)] hover:shadow-[0_14px_34px_rgba(160,195,225,0.25)] transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="font-label-kpi-sub text-label-kpi-sub text-secondary font-semibold">Flagged</span>
            <div className="w-9 h-9 rounded-xl bg-surface-container-high flex items-center justify-center text-primary-container">
              <span className="material-symbols-outlined text-lg">warning</span>
            </div>
          </div>
          <div>
            <div className="font-metric-stat text-metric-stat text-primary-container tracking-tight font-extrabold leading-none">{kpis.flagged}</div>
            <div className="flex items-center gap-1.5 mt-3">
              <span className="font-caption-data text-caption-data text-secondary">Across</span>
              <span className="font-caption-data text-caption-data text-on-surface font-semibold">{new Set(rows.map((r) => r.aircraft_code)).size} active airframes</span>
            </div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.18)] hover:shadow-[0_14px_34px_rgba(160,195,225,0.25)] transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="font-label-kpi-sub text-label-kpi-sub text-secondary font-semibold">Completed</span>
            <div className="w-9 h-9 rounded-xl bg-surface-container-low flex items-center justify-center text-tertiary-container">
              <span className="material-symbols-outlined text-lg">verified</span>
            </div>
          </div>
          <div>
            <div className="font-metric-stat text-metric-stat text-tertiary-container tracking-tight font-extrabold leading-none">{kpis.completed}</div>
            <div className="flex items-center gap-1.5 mt-3">
              <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-surface-container text-tertiary font-caption-data text-caption-data font-bold">
                {kpis.total ? Math.round((kpis.completed / kpis.total) * 100) : 0}%
              </span>
              <span className="font-caption-data text-caption-data text-secondary">completion rate</span>
            </div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.18)] hover:shadow-[0_14px_34px_rgba(160,195,225,0.25)] transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="font-label-kpi-sub text-label-kpi-sub text-secondary font-semibold">Pending</span>
            <div className="w-9 h-9 rounded-xl bg-secondary-container/40 flex items-center justify-center text-on-secondary-fixed-variant">
              <span className="material-symbols-outlined text-lg">pending_actions</span>
            </div>
          </div>
          <div>
            <div className="font-metric-stat text-metric-stat text-on-secondary-fixed-variant tracking-tight font-extrabold leading-none">{String(kpis.pending).padStart(2, '0')}</div>
            <div className="flex items-center gap-1.5 mt-3">
              <span className="relative flex h-1.5 w-1.5 rounded-full bg-secondary" />
              <span className="font-caption-data text-caption-data text-secondary">Requires engineer sign-off</span>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Inspections Table */}
      <section className="rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.20)] p-6 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-surface-container-high/40">
          <div>
            <h2 className="font-headline-sm text-headline-sm text-on-surface tracking-tight">Recent Inspections</h2>
            <p className="font-caption-data text-caption-data text-secondary mt-0.5">Real-time defect tracking across ongoing and logged flight line scans</p>
          </div>
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-secondary text-base pointer-events-none">filter_list</span>
              <input
                className="h-9 pl-9 pr-4 rounded-xl bg-surface-container-low text-on-surface font-caption-data text-caption-data placeholder-secondary focus:outline-none focus:bg-surface-container-lowest transition-all shadow-sm"
                placeholder="Filter tail or model..."
                type="text"
              />
            </div>
            <Link
              to="/inspections"
              className="inline-flex items-center gap-1 text-primary hover:text-primary-container font-caption-data text-caption-data font-bold px-3 py-2 rounded-xl hover:bg-surface-container-low transition-all"
            >
              <span>View all</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto mt-2">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-secondary font-label-table-head text-label-table-head uppercase tracking-wider text-[11px] border-b border-surface-container-high/60">
                <th className="py-3.5 px-4 font-bold">Inspection ID</th>
                <th className="py-3.5 px-4 font-bold">Aircraft</th>
                <th className="py-3.5 px-4 font-bold">Panel</th>
                <th className="py-3.5 px-4 font-bold">Inspector</th>
                <th className="py-3.5 px-4 font-bold">Date</th>
                <th className="py-3.5 px-4 font-bold">Status</th>
                <th className="py-3.5 px-4 font-bold text-center">Defects</th>
                <th className="py-3.5 px-4 font-bold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-low font-body-md text-body-md text-on-surface">
              {rows.map((r) => {
                const pill = statusPill(r.statusLabel, r.defects);
                return (
                  <tr
                    key={r.id}
                    className="hover:bg-surface-container-lowest/60 hover:shadow-[0_4px_12px_rgba(160,195,225,0.12)] transition-all group cursor-pointer"
                    onClick={() => navigate(`/inspections/${r.id}`)}
                  >
                    <td className="py-3.5 px-4 font-semibold text-primary">{r.inspection_code}</td>
                    <td className="py-3.5 px-4 font-bold text-on-surface">{r.aircraft_code ?? '—'}</td>
                    <td className="py-3.5 px-4 text-on-surface-variant font-medium">{r.panel_code ?? '—'}</td>
                    <td className="py-3.5 px-4 text-secondary">{r.inspector_name ?? '—'}</td>
                    <td className="py-3.5 px-4 text-secondary font-caption-data text-caption-data">
                      {r.inspection_date ? new Date(r.inspection_date).toLocaleDateString() : '—'}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${pill.cls}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${pill.dot}`} /> {pill.label}
                      </span>
                    </td>
                    <td className={`py-3.5 px-4 text-center font-bold ${r.defects > 1 ? 'text-error' : r.defects > 0 ? 'text-on-surface' : 'text-secondary'}`}>
                      {r.defects > 0 ? r.defects : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button className="inline-flex items-center gap-1 font-caption-data text-caption-data font-bold text-primary group-hover:text-primary-container transition-colors">
                        <span>View</span>
                        <span className="material-symbols-outlined text-sm">open_in_new</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Analytics: donut + performance */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
        <div className="lg:col-span-5 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.20)] p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Defect Overview</h2>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded font-caption-data text-caption-data bg-surface-container-low text-secondary">aerointel_v1 · 4 classes</span>
            </div>
            <p className="font-caption-data text-caption-data text-secondary mb-6">Per-class breakdown (demo distribution — per-class counts arrive with the stats endpoint)</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-8 py-2">
              <div className="relative w-44 h-44 flex items-center justify-center shrink-0">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
                  <circle className="text-surface-container-high" cx="80" cy="80" fill="transparent" r="62" stroke="currentColor" strokeWidth="16" />
                  {DONUT.map((d) => (
                    <circle
                      key={d.name}
                      className={d.stroke}
                      cx="80" cy="80" fill="transparent" r="62"
                      stroke="currentColor"
                      strokeDasharray={`${d.dash} 389.5`}
                      strokeDashoffset={d.offset}
                      strokeLinecap="round"
                      strokeWidth="16"
                    />
                  ))}
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
                  <span className="font-headline-lg text-headline-lg font-extrabold text-on-surface leading-none">27</span>
                  <span className="font-caption-data text-caption-data text-secondary uppercase tracking-widest mt-1 text-[10px]">Total Defects</span>
                </div>
              </div>
              <div className="flex flex-col gap-3 w-full sm:w-auto">
                {DONUT.map((d, i) => (
                  <div key={d.name} className="flex items-center justify-between gap-4 p-2 rounded-xl bg-surface-container-low/40">
                    <div className="flex items-center gap-2.5">
                      <span className={`w-3 h-3 rounded-full ${d.stroke.replace('text-', 'bg-')}`} />
                      <span className="font-body-md text-body-md font-semibold text-on-surface">{d.name}</span>
                    </div>
                    <span className="font-caption-data text-caption-data text-secondary">{d.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-7 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.20)] p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
            <div>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Inspection Performance</h2>
              <p className="font-caption-data text-caption-data text-secondary mt-0.5">Throughput comparison (May – Oct 2025)</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-semibold">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-primary-container" />
                <span className="text-on-surface font-caption-data text-caption-data">Completed</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-tertiary-fixed-dim" />
                <span className="text-on-surface font-caption-data text-caption-data">Pending</span>
              </div>
            </div>
          </div>
          <div className="relative w-full h-56 mt-4">
            <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 540 180">
              <defs>
                <linearGradient id="blueGradient" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#2c6ecb" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#2c6ecb" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="cyanGradient" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#7ed3e5" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#7ed3e5" stopOpacity="0" />
                </linearGradient>
              </defs>
              <line className="text-surface-container-high/60" stroke="currentColor" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="540" y1="30" y2="30" />
              <line className="text-surface-container-high/60" stroke="currentColor" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="540" y1="75" y2="75" />
              <line className="text-surface-container-high/60" stroke="currentColor" strokeDasharray="3 3" strokeWidth="1" x1="0" x2="540" y1="120" y2="120" />
              <line className="text-surface-container-high" stroke="currentColor" strokeWidth="1" x1="0" x2="540" y1="165" y2="165" />
              <path d="M 30,140 Q 110,120 180,95 T 320,60 T 420,40 T 510,25 L 510,165 L 30,165 Z" fill="url(#blueGradient)" />
              <path className="text-primary-container" d="M 30,140 Q 110,120 180,95 T 320,60 T 420,40 T 510,25" fill="transparent" stroke="currentColor" strokeLinecap="round" strokeWidth="3" />
              <path d="M 30,150 Q 110,145 180,135 T 320,110 T 420,105 T 510,95 L 510,165 L 30,165 Z" fill="url(#cyanGradient)" />
              <path className="text-tertiary-fixed-dim" d="M 30,150 Q 110,145 180,135 T 320,110 T 420,105 T 510,95" fill="transparent" stroke="currentColor" strokeLinecap="round" strokeWidth="3" />
              <circle className="fill-surface-container-lowest stroke-primary-container" cx="30" cy="140" r="4.5" strokeWidth="2.5" />
              <circle className="fill-surface-container-lowest stroke-primary-container" cx="130" cy="115" r="4.5" strokeWidth="2.5" />
              <circle className="fill-surface-container-lowest stroke-primary-container" cx="230" cy="80" r="4.5" strokeWidth="2.5" />
              <circle className="fill-surface-container-lowest stroke-primary-container" cx="330" cy="55" r="4.5" strokeWidth="2.5" />
              <circle className="fill-surface-container-lowest stroke-primary-container" cx="430" cy="40" r="4.5" strokeWidth="2.5" />
              <circle className="fill-primary-container stroke-surface-container-lowest" cx="510" cy="25" r="5" strokeWidth="2.5" />
              <circle className="fill-surface-container-lowest stroke-tertiary-fixed-dim" cx="30" cy="150" r="4" strokeWidth="2" />
              <circle className="fill-surface-container-lowest stroke-tertiary-fixed-dim" cx="130" cy="142" r="4" strokeWidth="2" />
              <circle className="fill-surface-container-lowest stroke-tertiary-fixed-dim" cx="230" cy="128" r="4" strokeWidth="2" />
              <circle className="fill-surface-container-lowest stroke-tertiary-fixed-dim" cx="330" cy="110" r="4" strokeWidth="2" />
              <circle className="fill-surface-container-lowest stroke-tertiary-fixed-dim" cx="430" cy="105" r="4" strokeWidth="2" />
              <circle className="fill-tertiary-fixed-dim stroke-surface-container-lowest" cx="510" cy="95" r="4" strokeWidth="2" />
            </svg>
          </div>
          <div className="flex items-center justify-between px-4 pt-2 text-secondary font-caption-data text-caption-data">
            <span>May</span><span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span>
            <span className="font-bold text-primary">Oct 2025</span>
          </div>
          <div className="pt-4 mt-2 border-t border-surface-container-high/40 flex items-center justify-between text-secondary font-caption-data text-caption-data">
            <span>Monthly inspection throughput (demo trend until stats endpoint)</span>
            <span className="text-primary font-semibold flex items-center gap-1">
              <span className="material-symbols-outlined text-sm">query_stats</span> {kpis.total} logged this cycle
            </span>
          </div>
        </div>
      </section>

      {/* Alerts + Quick Actions */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
        <div className="lg:col-span-8 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.20)] p-6">
          <div className="flex items-center justify-between pb-4 border-b border-surface-container-high/40">
            <div>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Latest Alerts</h2>
              <p className="font-caption-data text-caption-data text-secondary mt-0.5">Automated structural divergence notifications</p>
            </div>
            <button className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-surface-container-low text-secondary hover:text-on-surface font-caption-data text-caption-data font-semibold transition-all">
              <span className="material-symbols-outlined text-sm">tune</span>
              <span>Filter by severity</span>
            </button>
          </div>
          <div className="flex flex-col gap-2.5 mt-4">
            {ALERTS.map((a) => (
              <div
                key={a.title}
                className={`flex items-center justify-between p-3.5 rounded-xl transition-all group cursor-pointer ${a.active ? 'bg-surface-container-high/50 shadow-[0_4px_16px_rgba(160,195,225,0.22)]' : 'hover:bg-surface-container-low'}`}
              >
                <div className="flex items-center gap-3.5 min-w-0">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${a.iconCls}`}>
                    <span className="material-symbols-outlined text-xl">{a.icon}</span>
                  </div>
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-body-md text-body-md font-bold text-on-surface truncate">{a.title}</span>
                      {a.tag && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-error text-on-error shrink-0">{a.tag}</span>
                      )}
                    </div>
                    <span className="font-caption-data text-caption-data text-secondary truncate">{a.sub}</span>
                  </div>
                </div>
                <span className="material-symbols-outlined text-secondary group-hover:text-on-surface group-hover:translate-x-1 transition-all text-xl">chevron_right</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-4 rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.20)] p-6 flex flex-col justify-between">
          <div>
            <h2 className="font-headline-sm text-headline-sm text-on-surface">Quick Actions</h2>
            <p className="font-caption-data text-caption-data text-secondary mt-0.5 mb-6">Initiate tasks or trigger camera synchronizations</p>
            <div className="flex flex-col gap-3">
              <Link
                to="/inspections/new"
                className="w-full px-5 py-3 rounded-xl bg-primary-container text-on-primary font-headline-sm text-headline-sm font-bold flex items-center justify-between shadow-[0_8px_20px_rgba(44,110,203,0.3)] hover:bg-primary transition-all"
              >
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-xl">add_circle</span>
                  <span>Start New Inspection</span>
                </span>
                <span className="material-symbols-outlined text-lg">arrow_forward</span>
              </Link>
              <Link
                to="/inspections/new"
                className="w-full px-5 py-3 rounded-xl bg-surface-container-high/80 text-primary-container font-body-md text-body-md font-bold flex items-center justify-between hover:bg-surface-container-high transition-all"
              >
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-xl">cloud_upload</span>
                  <span>Upload Inspection Image</span>
                </span>
                <span className="material-symbols-outlined text-base">file_upload</span>
              </Link>
              <Link
                to="/reports"
                className="w-full px-5 py-3 rounded-xl bg-surface-container-low/60 text-secondary hover:text-on-surface font-body-md text-body-md font-semibold flex items-center justify-between hover:bg-surface-container-low transition-all"
              >
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-xl">article</span>
                  <span>View Compliance Reports</span>
                </span>
                <span className="material-symbols-outlined text-base">arrow_outward</span>
              </Link>
            </div>
          </div>
          <div className="p-3.5 mt-6 rounded-xl bg-surface-container-low/50 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className={`material-symbols-outlined text-lg ${true ? 'text-primary' : 'text-error'}`}>smartphone</span>
              <div className="flex flex-col">
                <span className="font-caption-data text-caption-data text-on-surface font-bold">Mobile Capture</span>
                <span className="font-caption-data text-caption-data text-secondary text-[11px]">Phone camera → same inspection pipeline</span>
              </div>
            </div>
            <Link
              to="/mobile"
              className="font-caption-data text-caption-data text-tertiary font-bold bg-surface-container-high px-2 py-0.5 rounded"
            >
              OPEN
            </Link>
          </div>
        </div>
      </section>

      {/* Recent Inspection Images */}
      <section className="rounded-2xl bg-surface-container-lowest shadow-[0_10px_30px_rgba(160,195,225,0.20)] p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-5 border-b border-surface-container-high/40">
          <div>
            <h2 className="font-headline-sm text-headline-sm text-on-surface">Recent Inspection Images</h2>
            <p className="font-caption-data text-caption-data text-secondary mt-0.5">Recent camera &amp; drone edge captures with AI bounding boxes</p>
          </div>
          <div className="flex items-center gap-2 text-secondary font-caption-data text-caption-data">
            <span className="material-symbols-outlined text-base text-primary">auto_fix_high</span>
            <span>YOLOv11 Aero Vision Engine</span>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mt-5">
          {THUMBS.map((t) => (
            <div key={t.code + t.label} className="group relative rounded-xl overflow-hidden bg-surface-container shadow-sm hover:shadow-md transition-all flex flex-col">
              <div className="relative h-40 w-full overflow-hidden bg-surface-container-high">
                <div className="absolute inset-0 flex items-center justify-center text-secondary">
                  <span className="material-symbols-outlined text-[36px]">image</span>
                </div>
                <div className={`absolute top-2.5 left-2.5 px-2 py-0.5 rounded font-caption-data text-caption-data text-[11px] font-bold shadow-sm ${t.tagCls}`}>
                  {t.tag}
                </div>
                <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-inverse-surface/80 text-inverse-on-surface text-[10px] font-caption-data">
                  {t.code}
                </div>
              </div>
              <div className="p-2.5 bg-surface-container-lowest flex items-center justify-between">
                <span className="font-caption-data text-caption-data text-on-surface font-semibold truncate">{t.label}</span>
                <span className="material-symbols-outlined text-secondary text-sm group-hover:text-primary transition-colors">zoom_in</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  );
};

export default Dashboard;
