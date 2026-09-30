import React from 'react';
import { Link } from 'react-router-dom';
import Hero3DAircraft from '../components/landing/Hero3DAircraft';
import { usePolling } from '../hooks/useApi';
import { api } from '../services/api';
import type { Inspection, ModelMetrics } from '../services/types';

/**
 * Landing — public hero page ported from stitch/aerointel_public_landing_overview.html.
 * NO-HOLLOW-UI RULE: the Stitch mockup's dashboard section (KPI counts, donut,
 * 2021-2025 trend chart, "Updated 10m ago" badge) was all invented data with no
 * backend behind it — replaced with what we actually have:
 *   - GET /api/inspections  → live record table (same data the Dashboard uses)
 *   - logs/eval_aerointel_v1_yolo11s_test.json → real v1.0.0 evaluation metrics
 *   - logs/latency_aerointel_v1_yolo11s.json  → real measured inference latency
 * The 3D hero and CTAs point at routes that exist.
 */

/* Class accent colors for per-class bars (backend class order). */
const CLASS_COLORS: Record<string, string> = {
  Crack: '#ba1a1a',
  Corrosion: '#8a4b12',
  Dent: '#7a5900',
  'Missing Fastener': '#6750a4',
};

const STATUS_PILL: Record<string, { label: string; cls: string }> = {
  completed: { label: 'Completed', cls: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
  pending: { label: 'Pending', cls: 'bg-amber-50 text-amber-600 border-amber-200' },
};
const statusPill = (s: string) =>
  STATUS_PILL[s] ?? { label: s, cls: 'bg-slate-50 text-slate-600 border-slate-200' };

const fmtDate = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
};

export const Landing: React.FC = () => {
  const scrollTo = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  // Same live sources the Dashboard uses — 10 s is plenty for a public page.
  const { data: inspections, error } = usePolling<Inspection[]>(() => api.listInspections(), 10000);
  const { data: metrics } = usePolling<ModelMetrics>(() => api.getMetrics(), 60000);
  const recent = (inspections ?? []).slice(0, 6);
  const latest = inspections?.[0] ?? null;
  const backendOnline = !error || !!inspections;

  return (
    <div className="sky-canvas min-h-screen text-aero-navy relative overflow-x-hidden">
      {/* ── Floating Navigation ── */}
      <header className="w-full sticky top-0 z-50 bg-[#E8F3FA]/70 backdrop-blur-md border-b border-white/50 transition-all">
        <div className="max-w-[1280px] mx-auto px-6 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 group">
            <img
              src="/brand/aerointel-logo.png"
              alt="AeroIntel"
              className="h-10 w-auto object-contain transition-transform group-hover:scale-[1.02]"
            />
          </Link>
          <nav className="hidden md:flex items-center space-x-12">
            <a className="text-[15px] font-semibold text-aero-navy hover:text-aero-ocean transition-colors" href="#live-record" onClick={scrollTo('live-record')}>
              Live Record
            </a>
            <a className="text-[15px] font-medium text-[#465E73] hover:text-aero-navy transition-colors" href="#model" onClick={scrollTo('model')}>
              Model
            </a>
            <Link className="text-[15px] font-medium text-[#465E73] hover:text-aero-navy transition-colors" to="/inspections/new">
              New Inspection
            </Link>
          </nav>
          <Link
            to="/inspections/new"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-aero-darkblue text-white text-[14px] font-bold shadow-aero-button hover:bg-aero-navy transition-colors"
          >
            Start Detection
          </Link>
        </div>
      </header>

      {/* ── Hero Section with 3D aircraft ── */}
      <section className="relative pt-20 pb-24 md:pt-28 md:pb-32 px-4 overflow-hidden">
        <div className="absolute inset-0 cloud-overlay pointer-events-none" />
        <div className="absolute inset-0 hero-cloud-mist" />

        {/* Desktop: text left, plane right. Mobile: stacked. */}
        <div className="relative z-10 max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 items-center gap-6">
          <div className="flex flex-col items-center md:items-start text-center md:text-left max-w-xl mx-auto md:mx-0">
            <h2 className="text-2xl md:text-[34px] font-bold tracking-tight text-[#748C9E] mb-2 leading-tight">
              An Edge AI Inspection Assistant
            </h2>
            <h1 className="text-3xl md:text-[44px] font-extrabold text-[#050D18] tracking-tight mb-6 leading-tight">
              for Intelligent Aircraft Defect Detection
            </h1>
            <p className="text-[15px] font-medium text-[#465E73] mb-9 max-w-md">
              YOLOv11 inference and longitudinal defect tracking, running entirely on your local server
              — every number on this page comes from the real model and the live inspection record.
            </p>
            <Link
              to="/inspections/new"
              className="inline-flex items-center justify-center gap-3 bg-white/95 hover:bg-white text-[#6E889D] hover:text-aero-darkblue text-[19px] font-bold px-10 py-4 rounded-full shadow-aero-button border border-white/70 backdrop-blur-sm transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0"
            >
              <span>Start Detection</span>
              <svg className="w-5 h-5 text-[#6E889D]" fill="currentColor" viewBox="0 0 20 20">
                <path
                  clipRule="evenodd"
                  fillRule="evenodd"
                  d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                />
              </svg>
            </Link>
          </div>

          {/* 3D rotating aircraft (drag to orbit, auto-rotates ~20 s/turn) */}
          <div className="relative h-[340px] md:h-[520px]">
            <Hero3DAircraft />
          </div>
        </div>
      </section>

      {/* ── Live record (real GET /api/inspections — same data the Dashboard uses) ── */}
      <main className="max-w-[1240px] mx-auto px-6 pb-24 relative z-10" id="live-record">
        <section className="mb-10">
          <h3 className="text-3xl font-extrabold text-[#091523] tracking-tight">Live Inspection Record</h3>
          <p className="text-[17px] font-medium text-[#7A90A2] mt-1">
            Straight from your local AeroIntel backend — no sample data.
          </p>
          <hr className="mt-5 border-t border-[#8BA2B5]/40" />
        </section>

        {/* Real-at-a-glance strip */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-5 md:gap-7 mb-10">
          <div className="bg-white/95 rounded-[28px] py-7 px-6 text-center shadow-aero-card border border-white/80">
            <span className="block text-base font-bold text-[#2A4359] mb-1">Inspections recorded</span>
            <span className="block text-4xl lg:text-5xl font-extrabold text-[#235882] tracking-tight">
              {inspections ? inspections.length : '—'}
            </span>
          </div>
          <div className="bg-white/95 rounded-[28px] py-7 px-6 text-center shadow-aero-card border border-white/80">
            <span className="block text-base font-bold text-[#2A4359] mb-1">Latest inspection</span>
            <span className="block text-xl lg:text-2xl font-extrabold text-[#235882] tracking-tight break-all pt-2">
              {latest ? latest.inspection_code : '—'}
            </span>
          </div>
          <div className="bg-white/95 rounded-[28px] py-7 px-6 text-center shadow-aero-card border border-white/80">
            <span className="block text-base font-bold text-[#2A4359] mb-1">Detection model</span>
            <span className="block text-xl lg:text-2xl font-extrabold text-[#235882] tracking-tight pt-2">
              {metrics?.model.name ?? '—'}
            </span>
            <span className="block text-xs font-semibold text-[#7A90A2] mt-1">
              {metrics ? `${metrics.model.type} · ${metrics.model.version}` : 'live from /api/metrics'}
            </span>
          </div>
          <div className="bg-white/95 rounded-[28px] py-7 px-6 text-center shadow-aero-card border border-white/80">
            <span className="block text-base font-bold text-[#2A4359] mb-1">Inference latency</span>
            <span className="block text-xl lg:text-2xl font-extrabold text-[#235882] tracking-tight pt-2">
              {metrics?.latency.p50_ms != null ? `${metrics.latency.p50_ms} ms` : '—'}
            </span>
            <span className="block text-xs font-semibold text-[#7A90A2] mt-1">
              p50 CPU · p95 {metrics?.latency.p95_ms ?? '—'} ms
            </span>
          </div>
        </section>

        {/* Recent inspections — real rows */}
        <section className="bg-white/95 rounded-[32px] p-8 shadow-aero-card border border-white/80 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xl font-bold text-aero-navy">Recent Inspections</h4>
            <Link to="/dashboard" className="text-xs font-bold text-aero-ocean hover:text-aero-navy transition">
              Open Dashboard →
            </Link>
          </div>
          {!backendOnline && !inspections ? (
            <p className="py-10 text-center text-[15px] font-medium text-[#7A90A2]">
              Backend offline — start the FastAPI server (port 8000) to see the live record.
            </p>
          ) : recent.length === 0 ? (
            <div className="py-10 text-center">
              <p className="text-[15px] font-semibold text-aero-darkblue">No inspections recorded yet.</p>
              <Link
                to="/inspections/new"
                className="mt-3 inline-flex items-center gap-2 text-sm font-bold text-aero-ocean hover:text-aero-navy transition"
              >
                Create the first one →
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#EEF2F6] text-[14px] font-bold text-[#21384E]">
                    <th className="pb-4 pl-3">Inspection</th>
                    <th className="pb-4">Aircraft</th>
                    <th className="pb-4">Panel</th>
                    <th className="pb-4">Date</th>
                    <th className="pb-4">Inspector</th>
                    <th className="pb-4 text-center">Status</th>
                    <th className="pb-4 text-right pr-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F1F5F9] text-[14px] font-medium text-[#465E73]">
                  {recent.map((r) => {
                    const pill = statusPill(r.status);
                    return (
                      <tr key={r.id} className="hover:bg-[#F8FBFE] transition-colors">
                        <td className="py-4 pl-3 font-semibold text-aero-navy">{r.inspection_code}</td>
                        <td className="py-4 font-mono font-bold text-aero-darkblue">{r.aircraft_code ?? '—'}</td>
                        <td className="py-4">{r.panel_code ?? `Panel #${r.panel_id}`}</td>
                        <td className="py-4 text-[#6A8196]">{fmtDate(r.inspection_date)}</td>
                        <td className="py-4">{r.inspector_name ?? '—'}</td>
                        <td className="py-4 text-center">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${pill.cls}`}>
                            {pill.label}
                          </span>
                        </td>
                        <td className="py-4 text-right pr-4">
                          {r.status === 'completed' ? (
                            <Link
                              to={`/inspections/${r.id}`}
                              className="text-xs font-bold text-aero-ocean hover:text-aero-navy transition"
                            >
                              View Results
                            </Link>
                          ) : (
                            <span className="text-xs text-[#9DB0C0]">Awaiting images</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* ── Model evaluation — LIVE from GET /api/metrics (verified eval logs) ── */}
        <section id="model" className="grid grid-cols-1 lg:grid-cols-12 gap-7 mb-8">
          {!metrics ? (
            <div className="lg:col-span-12 bg-white/95 rounded-[32px] p-8 shadow-aero-card border border-white/80 text-center">
              <p className="text-[15px] font-semibold text-aero-darkblue">Model metrics unavailable right now.</p>
              <p className="text-xs font-medium text-[#7A90A2] mt-1">
                Metrics load from the AeroIntel backend (GET /api/metrics) — start the server and refresh.
              </p>
            </div>
          ) : (
            <>
              <article className="lg:col-span-5 bg-white/95 rounded-[32px] p-7 shadow-aero-card border border-white/80 flex flex-col">
                <h4 className="text-lg font-bold text-aero-navy mb-1">
                  {metrics.model.name} · {metrics.model.type}
                </h4>
                <p className="text-xs font-semibold text-[#7A90A2] mb-5">
                  {metrics.evaluation.split} split · {metrics.evaluation.dataset.images.toLocaleString()} images ·{' '}
                  {metrics.evaluation.dataset.annotations.toLocaleString()} annotations
                </p>
                <div className="grid grid-cols-2 gap-4 mb-5">
                  <div className="rounded-2xl bg-[#F1F7FB] p-4">
                    <span className="block text-xs font-bold text-[#7A90A2] uppercase tracking-wider">mAP@50</span>
                    <span className="block text-3xl font-black text-aero-navy mt-1">{metrics.evaluation.overall.mAP50.toFixed(3)}</span>
                  </div>
                  <div className="rounded-2xl bg-[#F1F7FB] p-4">
                    <span className="block text-xs font-bold text-[#7A90A2] uppercase tracking-wider">mAP@50-95</span>
                    <span className="block text-3xl font-black text-aero-navy mt-1">{metrics.evaluation.overall['mAP50-95'].toFixed(3)}</span>
                  </div>
                  <div className="rounded-2xl bg-[#F1F7FB] p-4">
                    <span className="block text-xs font-bold text-[#7A90A2] uppercase tracking-wider">Precision</span>
                    <span className="block text-3xl font-black text-aero-navy mt-1">{metrics.evaluation.overall.precision.toFixed(3)}</span>
                  </div>
                  <div className="rounded-2xl bg-[#F1F7FB] p-4">
                    <span className="block text-xs font-bold text-[#7A90A2] uppercase tracking-wider">Recall</span>
                    <span className="block text-3xl font-black text-aero-navy mt-1">{metrics.evaluation.overall.recall.toFixed(3)}</span>
                  </div>
                </div>
                <p className="text-xs font-medium text-[#7A90A2] leading-relaxed mt-auto">
                  Latency measured on CPU: p50 {metrics.latency.p50_ms} ms · p95 {metrics.latency.p95_ms} ms per image
                  ({metrics.latency.n_images}-image run).
                </p>
              </article>

              <article className="lg:col-span-7 bg-white/95 rounded-[32px] p-7 shadow-aero-card border border-white/80 flex flex-col">
                <h4 className="text-lg font-bold text-aero-navy mb-1">Per-class accuracy (mAP@50)</h4>
                <p className="text-xs font-semibold text-[#7A90A2] mb-6">Where the v1 model is strong — and where it isn't.</p>
                <div className="flex flex-col gap-5 my-auto">
                  {Object.entries(metrics.evaluation.per_class)
                    .sort((a, b) => b[1].mAP50 - a[1].mAP50)
                    .map(([name, m]) => (
                      <div key={name}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="flex items-center gap-2 text-sm font-bold text-[#21384E]">
                            <span
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: CLASS_COLORS[name] ?? '#8BA2B5' }}
                            />
                            {name}
                          </span>
                          <span className="text-sm font-black text-aero-navy">{m.mAP50.toFixed(3)}</span>
                        </div>
                        <div className="h-3 rounded-full bg-[#F1F5F9] overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${m.mAP50 * 100}%`, backgroundColor: CLASS_COLORS[name] ?? '#8BA2B5' }}
                          />
                        </div>
                      </div>
                    ))}
                </div>
                <p className="text-xs font-medium text-[#7A90A2] leading-relaxed mt-6">
                  Known v1 limitation: Corrosion recall is {metrics.evaluation.per_class.Corrosion?.recall.toFixed(3) ?? '—'} on the
                  test split — treat corrosion results as decision support for a human reviewer, not a cleared finding.
                </p>
              </article>
            </>
          )}
        </section>

        {/* Start-inspection card — points at the real flow */}
        <section className="bg-white/80 rounded-[32px] min-h-[200px] shadow-aero-card border border-white/70 p-8 flex items-center justify-center">
          <div className="flex flex-col items-center justify-center text-center py-4">
            <div className="w-12 h-12 rounded-2xl bg-sky-100 flex items-center justify-center text-aero-ocean mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M12 4v16m8-8H4" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
              </svg>
            </div>
            <p className="text-base font-bold text-aero-darkblue">Run a detection now</p>
            <p className="text-xs text-[#7A90A2] mt-1 max-w-md">
              Upload an aircraft panel image or capture one with a device camera — inference runs on the
              local server and every defect is written to AeroMemory.
            </p>
            <Link
              to="/inspections/new"
              className="mt-4 inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-aero-darkblue text-white text-sm font-bold shadow-aero-button hover:bg-aero-navy transition-colors"
            >
              New Inspection
            </Link>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="w-full py-8 text-center text-xs font-medium text-[#7C93A6]">
        <div className="max-w-[1240px] mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 AeroIntel. Edge AI for Aerospace Maintenance &amp; Defect Detection.</p>
          <div className="flex items-center space-x-6">
            <Link to="/inspections/new" className="hover:text-aero-navy transition">New Inspection</Link>
            <Link to="/dashboard" className="hover:text-aero-navy transition">Dashboard</Link>
            <Link to="/model-performance" className="hover:text-aero-navy transition">Model Performance</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
