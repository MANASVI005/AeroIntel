import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeader, MetaChip, Card, Button, StatusPill,
  LoadingState, EmptyState, ErrorState,
} from '../components/common';
import { usePolling, useApi } from '../hooks/useApi';
import { useHealth } from '../hooks/useHealth';
import { api } from '../services/api';
import type { Inspection } from '../services/types';

/**
 * Inspection History (stitch/aerointel_inspection_history.html).
 * Data: GET /api/inspections — every row on screen is a real record.
 * NO-HOLLOW-UI notes vs the Stitch mockup:
 *   - "Detected Anomalies" chips, "Component STA", fake tail numbers → dropped
 *     (no per-inspection defect-count endpoint yet; real fields only).
 *   - Invented footer stats (3 critical flags / 87.4% pass rate / 1.4 s) →
 *     replaced with counts derived from the live rows.
 *   - "Edge Sync: Active" chip → real backend status from GET /health.
 *   - "Batch Report" button → dropped (no such feature); Export CSV is
 *     implemented client-side over the currently filtered rows.
 * Search / status / aircraft / date filters are real client-side filters over
 * the fetched list; filter options are derived from the data, never hardcoded.
 */

const fmtDateTime = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
};

const StatusCell: React.FC<{ status: string }> = ({ status }) => {
  const s = status.toLowerCase();
  if (s === 'completed')
    return <StatusPill tone="positive">Completed</StatusPill>;
  if (s === 'pending') return <StatusPill tone="primary">Pending</StatusPill>;
  return <StatusPill tone="neutral">{status || 'Unknown'}</StatusPill>;
};

const PER_PAGE_OPTIONS = [10, 25, 50];

export const InspectionHistory: React.FC = () => {
  const { data, loading, error, run } = useApi<Inspection[] | null>(null);
  const { online } = useHealth();

  // Initial load + 5 s refresh (dashboard already polls the same endpoint at 2 s).
  React.useEffect(() => {
    run(() => api.listInspections());
    const t = setInterval(() => run(() => api.listInspections()), 5000);
    return () => clearInterval(t);
  }, [run]);

  /* ── filters (all client-side over the fetched rows) ── */
  const [query, setQuery] = useState('');
  const [aircraft, setAircraft] = useState('all');
  const [status, setStatus] = useState('all');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [perPage, setPerPage] = useState(10);
  const [page, setPage] = useState(1);

  const rows = data ?? [];

  const aircraftOptions = useMemo(
    () => Array.from(new Set(rows.map((r) => r.aircraft_code).filter((a): a is string => !!a))).sort(),
    [rows]
  );
  const statusOptions = useMemo(
    () => Array.from(new Set(rows.map((r) => r.status).filter(Boolean))).sort(),
    [rows]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const from = fromDate ? new Date(fromDate).setHours(0, 0, 0, 0) : null;
    const to = toDate ? new Date(toDate).setHours(23, 59, 59, 999) : null;
    return rows.filter((r) => {
      if (q) {
        const hay = `${r.inspection_code} ${r.aircraft_code ?? ''} ${r.panel_code ?? ''} ${r.inspector_name ?? ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (aircraft !== 'all' && r.aircraft_code !== aircraft) return false;
      if (status !== 'all' && r.status !== status) return false;
      const t = new Date(r.inspection_date).getTime();
      if (from !== null && t < from) return false;
      if (to !== null && t > to) return false;
      return true;
    });
  }, [rows, query, aircraft, status, fromDate, toDate]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  const safePage = Math.min(page, totalPages);
  const pageRows = filtered.slice((safePage - 1) * perPage, safePage * perPage);

  const resetFilters = () => {
    setQuery('');
    setAircraft('all');
    setStatus('all');
    setFromDate('');
    setToDate('');
    setPage(1);
  };
  const activeFilters =
    (query ? 1 : 0) +
    (aircraft !== 'all' ? 1 : 0) +
    (status !== 'all' ? 1 : 0) +
    (fromDate ? 1 : 0) +
    (toDate ? 1 : 0);

  /* ── derived stats (real counts from the live rows — nothing invented) ── */
  const completedCount = rows.filter((r) => r.status.toLowerCase() === 'completed').length;
  const pendingCount = rows.length - completedCount;
  const airframeCount = aircraftOptions.length;

  /* ── CSV export of the currently filtered rows (client-side, real) ── */
  const exportCsv = () => {
    if (filtered.length === 0) return;
    const esc = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const header = ['inspection_code', 'aircraft_code', 'panel_code', 'panel_id', 'inspector_name', 'status', 'inspection_date'];
    const lines = filtered.map((r) =>
      [r.inspection_code, r.aircraft_code ?? '', r.panel_code ?? '', r.panel_id, r.inspector_name ?? '', r.status, r.inspection_date]
        .map(esc)
        .join(',')
    );
    const blob = new Blob([[header.join(','), ...lines].join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aerointel-inspections-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const inputCls =
    'w-full h-11 px-4 rounded-xl bg-surface-container-low text-on-surface font-body-md text-body-md placeholder:text-secondary focus:outline-none focus:bg-surface-container transition-all';

  return (
    <AppShell>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <PageHeader
          title="Inspection History"
          subtitle="Every inspection recorded by this AeroIntel server — search, filter and audit."
          chips={
            <>
              <MetaChip icon="inventory_2" label="Total logs" value={String(rows.length)} tone="primary" />
              <MetaChip
                icon={online ? 'cloud_done' : 'cloud_off'}
                label="Backend"
                value={online ? 'Online' : 'Offline'}
              />
            </>
          }
        />
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="ghost" icon="download" onClick={exportCsv} disabled={filtered.length === 0}>
            Export CSV
          </Button>
          <Link to="/inspections/new">
            <Button icon="add_circle">New Inspection</Button>
          </Link>
        </div>
      </div>

      {/* Filter card */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3">
          <div className="lg:col-span-4 relative flex items-center">
            <span className="material-symbols-outlined absolute left-3 text-secondary text-[20px] pointer-events-none">
              search
            </span>
            <input
              className={`${inputCls} pl-11`}
              placeholder="Search by ID, airframe, panel, inspector…"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <div className="lg:col-span-3 relative">
            <select
              className={`${inputCls} appearance-none cursor-pointer`}
              value={aircraft}
              onChange={(e) => {
                setAircraft(e.target.value);
                setPage(1);
              }}
            >
              <option value="all">All aircraft{aircraftOptions.length ? ` (${aircraftOptions.length})` : ''}</option>
              {aircraftOptions.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div className="lg:col-span-2 relative">
            <select
              className={`${inputCls} appearance-none cursor-pointer`}
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
            >
              <option value="all">All statuses</option>
              {statusOptions.map((s) => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
          </div>
          <div className="lg:col-span-3 grid grid-cols-2 gap-3">
            <input
              type="date"
              className={inputCls}
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setPage(1);
              }}
              aria-label="From date"
            />
            <input
              type="date"
              className={inputCls}
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setPage(1);
              }}
              aria-label="To date"
            />
          </div>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 mt-4">
          <span className="font-caption-data text-caption-data text-secondary">
            {activeFilters > 0 ? `${activeFilters} filter${activeFilters > 1 ? 's' : ''} applied · ` : ''}
            {filtered.length} of {rows.length} inspections match
          </span>
          {activeFilters > 0 && (
            <button
              onClick={resetFilters}
              className="inline-flex items-center gap-1 text-primary hover:text-primary-container font-caption-data text-caption-data font-bold transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">restart_alt</span>
              Reset filters
            </button>
          )}
        </div>
      </Card>

      {/* Table */}
      <Card className="!p-0 overflow-hidden">
        {loading && rows.length === 0 ? (
          <LoadingState message="Loading inspection history…" />
        ) : error && rows.length === 0 ? (
          <ErrorState
            message="Unable to reach the local AeroIntel server. Start it on port 8000 and retry."
            action={
              <Button variant="secondary" icon="refresh" onClick={() => run(() => api.listInspections())}>
                Retry
              </Button>
            }
          />
        ) : rows.length === 0 ? (
          <EmptyState
            icon="manage_search"
            message="No inspections recorded yet — create the first one."
            action={
              <Link to="/inspections/new">
                <Button icon="add_circle">New Inspection</Button>
              </Link>
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[900px]">
                <thead>
                  <tr className="bg-surface-container-low/60 text-secondary font-label-table-head text-label-table-head uppercase tracking-wider text-[11px] border-b border-surface-container-high/60">
                    <th className="py-3.5 px-5 font-bold">Inspection</th>
                    <th className="py-3.5 px-4 font-bold">Aircraft</th>
                    <th className="py-3.5 px-4 font-bold">Panel</th>
                    <th className="py-3.5 px-4 font-bold">Inspector</th>
                    <th className="py-3.5 px-4 font-bold">Date</th>
                    <th className="py-3.5 px-4 font-bold">Status</th>
                    <th className="py-3.5 px-5 font-bold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container-low font-body-md text-body-md text-on-surface">
                  {pageRows.map((r) => (
                    <tr key={r.id} className="hover:bg-surface-container-low/50 transition-colors">
                      <td className="py-3.5 px-5">
                        <span className="font-mono font-bold text-primary">{r.inspection_code}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        {r.aircraft_code ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-surface-container-high text-on-surface font-caption-data text-caption-data font-bold">
                            <span className="material-symbols-outlined text-[14px] text-primary">flight</span>
                            {r.aircraft_code}
                          </span>
                        ) : (
                          <span className="text-secondary">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">{r.panel_code ?? `Panel #${r.panel_id}`}</td>
                      <td className="py-3.5 px-4">{r.inspector_name ?? <span className="text-secondary">—</span>}</td>
                      <td className="py-3.5 px-4 font-caption-data text-caption-data text-secondary">
                        {fmtDateTime(r.inspection_date)}
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusCell status={r.status} />
                      </td>
                      <td className="py-3.5 px-5 text-right">
                        {r.status.toLowerCase() === 'completed' ? (
                          <Link
                            to={`/inspections/${r.id}`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-primary hover:bg-surface-container font-caption-data text-caption-data font-bold transition-colors"
                          >
                            <span className="material-symbols-outlined text-[16px]">visibility</span>
                            View results
                          </Link>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-secondary font-caption-data text-caption-data">
                            <span className="material-symbols-outlined text-[16px]">hourglass_empty</span>
                            Awaiting images
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {pageRows.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-8 px-4 text-center text-secondary">
                        No inspections match the current filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination — real, over the filtered set */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-5 py-3 bg-surface-container-low/40 border-t border-surface-container-high/40">
              <div className="flex items-center gap-4">
                <span className="font-caption-data text-caption-data text-secondary">
                  Showing{' '}
                  <span className="text-on-surface font-bold">
                    {filtered.length === 0 ? 0 : (safePage - 1) * perPage + 1}–
                    {Math.min(safePage * perPage, filtered.length)}
                  </span>{' '}
                  of <span className="text-on-surface font-bold">{filtered.length}</span>
                </span>
                <select
                  className="px-2 py-1 rounded-lg bg-surface-container-low text-on-surface font-caption-data text-caption-data cursor-pointer focus:outline-none"
                  value={perPage}
                  onChange={(e) => {
                    setPerPage(parseInt(e.target.value, 10));
                    setPage(1);
                  }}
                  aria-label="Rows per page"
                >
                  {PER_PAGE_OPTIONS.map((n) => (
                    <option key={n} value={n}>{n} per page</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  disabled={safePage <= 1}
                  onClick={() => setPage(safePage - 1)}
                  className="px-2.5 py-1 rounded-lg text-secondary font-caption-data text-caption-data flex items-center disabled:opacity-40 enabled:hover:bg-surface-container transition-colors"
                >
                  <span className="material-symbols-outlined text-[18px]">chevron_left</span>
                  Previous
                </button>
                <span className="w-8 h-8 rounded-lg bg-primary text-on-primary font-caption-data text-caption-data font-bold flex items-center justify-center">
                  {safePage}
                </span>
                <span className="px-1 font-caption-data text-caption-data text-secondary">
                  of {totalPages}
                </span>
                <button
                  disabled={safePage >= totalPages}
                  onClick={() => setPage(safePage + 1)}
                  className="px-2.5 py-1 rounded-lg text-secondary font-caption-data text-caption-data flex items-center disabled:opacity-40 enabled:hover:bg-surface-container transition-colors"
                >
                  Next
                  <span className="material-symbols-outlined text-[18px]">chevron_right</span>
                </button>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* Derived stat cards — real counts from the live rows */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-2">
        <div className="p-5 rounded-2xl bg-surface-container-lowest/90 backdrop-blur-xl card-shadow flex items-center justify-between">
          <div className="flex flex-col">
            <span className="font-caption-data text-caption-data text-secondary uppercase tracking-wider font-semibold">
              Completed
            </span>
            <span className="font-metric-stat text-metric-stat text-primary mt-0.5">{completedCount}</span>
            <span className="font-caption-data text-caption-data text-secondary">with detection results</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-primary-container text-on-primary-container flex items-center justify-center">
            <span className="material-symbols-outlined text-[28px]">verified</span>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-surface-container-lowest/90 backdrop-blur-xl card-shadow flex items-center justify-between">
          <div className="flex flex-col">
            <span className="font-caption-data text-caption-data text-secondary uppercase tracking-wider font-semibold">
              Awaiting images
            </span>
            <span className="font-metric-stat text-metric-stat text-tertiary mt-0.5">{pendingCount}</span>
            <span className="font-caption-data text-caption-data text-secondary">records with no captures yet</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-secondary-container text-on-secondary-container flex items-center justify-center">
            <span className="material-symbols-outlined text-[28px]">hourglass_empty</span>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-surface-container-lowest/90 backdrop-blur-xl card-shadow flex items-center justify-between">
          <div className="flex flex-col">
            <span className="font-caption-data text-caption-data text-secondary uppercase tracking-wider font-semibold">
              Airframes inspected
            </span>
            <span className="font-metric-stat text-metric-stat text-on-surface mt-0.5">{airframeCount}</span>
            <span className="font-caption-data text-caption-data text-secondary">distinct registrations on record</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-surface-container text-secondary flex items-center justify-center">
            <span className="material-symbols-outlined text-[28px]">flight</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
};

export default InspectionHistory;
