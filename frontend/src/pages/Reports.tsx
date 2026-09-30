import React from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeader, MetaChip, Card, Button,
  LoadingState, EmptyState, ErrorState,
} from '../components/common';
import { useApi } from '../hooks/useApi';
import { useHealth } from '../hooks/useHealth';
import { api } from '../services/api';
import type { Inspection } from '../services/types';

/**
 * Reports hub (stitch/aerointel_reports.html).
 * NO-HOLLOW-UI RULE: the backend has NO report entity — no stored PDFs, no
 * "38 reports / 6 awaiting / 32 certified" counters, no FAA/EASA compliance
 * states, no file sizes. What we actually have: recorded inspections whose
 * data can be rendered into a printable report on demand.
 * So this screen is an honest launchpad: pick a completed inspection →
 * /reports/{id} renders a printable report live from stored data
 * (InspectionReport.tsx). Stitch's invented KPI cards, report-status column,
 * "PDF · 4.2 MB" rows and compliance badges are dropped.
 */

const fmtDateTime = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
};

export const Reports: React.FC = () => {
  const { data, loading, error, run } = useApi<Inspection[] | null>(null);
  const { online } = useHealth();

  React.useEffect(() => {
    run(() => api.listInspections());
    const t = setInterval(() => run(() => api.listInspections()), 8000);
    return () => clearInterval(t);
  }, [run]);

  const rows = data ?? [];
  const reportReady = rows.filter((r) => r.status.toLowerCase() === 'completed').length;

  return (
    <AppShell>
      <PageHeader
        title="Reports"
        subtitle="Generate a printable inspection report from any recorded inspection — rendered live from stored data."
        chips={
          <>
            <MetaChip icon="summarize" label="Inspections" value={String(rows.length)} tone="primary" />
            <MetaChip icon="verified" label="Report-ready" value={String(reportReady)} />
            <MetaChip
              icon={online ? 'cloud_done' : 'cloud_off'}
              label="Backend"
              value={online ? 'Online' : 'Offline'}
            />
          </>
        }
      />

      {/* How reports work — honest explainer (no server-side PDF entity exists) */}
      <Card title="How reports work here">
        <ol className="flex flex-col gap-2 font-body-md text-body-md text-on-surface list-decimal pl-5">
          <li>Pick a completed inspection from the list below.</li>
          <li>The report renders live from the stored record: inspection details, latest scan, detections and AeroMemory tracking.</li>
          <li>Print it or save as PDF from your browser; Export JSON downloads the raw backend payload.</li>
        </ol>
        <p className="font-caption-data text-caption-data text-secondary leading-snug mt-3">
          Reports are generated on demand — the backend stores no PDF/report entity yet (that, plus signed-off
          report records, arrives with Stage 2+).
        </p>
      </Card>

      {/* Inspection list */}
      <Card className="!p-0 overflow-hidden">
        {loading && rows.length === 0 ? (
          <LoadingState message="Loading inspections…" />
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
            icon="summarize"
            message="No inspections recorded yet — run one to generate its report."
            action={
              <Link to="/inspections/new">
                <Button icon="add_circle">New Inspection</Button>
              </Link>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[760px]">
              <thead>
                <tr className="bg-surface-container-low/60 text-secondary font-label-table-head text-label-table-head uppercase tracking-wider text-[11px] border-b border-surface-container-high/60">
                  <th className="py-3.5 px-5 font-bold">Inspection</th>
                  <th className="py-3.5 px-4 font-bold">Aircraft</th>
                  <th className="py-3.5 px-4 font-bold">Panel</th>
                  <th className="py-3.5 px-4 font-bold">Date</th>
                  <th className="py-3.5 px-5 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-low font-body-md text-body-md text-on-surface">
                {rows.map((r) => (
                  <tr key={r.id} className="hover:bg-surface-container-low/50 transition-colors">
                    <td className="py-3.5 px-5">
                      <span className="font-mono font-bold text-primary">{r.inspection_code}</span>
                    </td>
                    <td className="py-3.5 px-4">{r.aircraft_code ?? <span className="text-secondary">—</span>}</td>
                    <td className="py-3.5 px-4">{r.panel_code ?? `Panel #${r.panel_id}`}</td>
                    <td className="py-3.5 px-4 font-caption-data text-caption-data text-secondary">
                      {fmtDateTime(r.inspection_date)}
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      {r.status.toLowerCase() === 'completed' ? (
                        <Link
                          to={`/reports/${r.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-primary hover:bg-surface-container font-caption-data text-caption-data font-bold transition-colors"
                        >
                          <span className="material-symbols-outlined text-[16px]">summarize</span>
                          Open report
                        </Link>
                      ) : (
                        <span className="font-caption-data text-caption-data text-secondary">
                          Awaiting completion
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </AppShell>
  );
};

export default Reports;
