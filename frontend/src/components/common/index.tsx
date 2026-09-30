import React from 'react';

/**
 * Small shared UI primitives, traced from the Stitch screens.
 * All class names reference the token config in index.html — never raw hex.
 */

/* ── StatusPill ─────────────────────────────────────────────────────── */
export type PillTone = 'primary' | 'neutral' | 'attention' | 'positive' | 'error';

const PILL_TONES: Record<PillTone, string> = {
  primary: 'bg-primary-container text-on-primary-container',
  neutral: 'bg-secondary-fixed text-on-secondary-fixed-variant',
  attention: 'bg-error-container text-on-error-container',
  positive: 'bg-tertiary-container text-on-tertiary-container',
  error: 'bg-error text-on-error',
};

export const StatusPill: React.FC<{
  tone?: PillTone;
  children: React.ReactNode;
  className?: string;
}> = ({ tone = 'neutral', children, className = '' }) => (
  <span
    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-caption-data text-caption-data font-semibold ${PILL_TONES[tone]} ${className}`}
  >
    {children}
  </span>
);

/* ── ClassChip ──────────────────────────────────────────────────────── */
import { classMeta } from '../../types/classes';

export const ClassChip: React.FC<{ classId: number; count?: number }> = ({ classId, count }) => {
  const meta = classMeta(classId);
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-container-low text-on-surface font-caption-data text-caption-data font-semibold">
      <span className={`w-2 h-2 rounded-full ${meta.dot}`} />
      {meta.name}
      {count !== undefined && <span className="text-secondary">× {count}</span>}
    </span>
  );
};

/* ── StatCard ───────────────────────────────────────────────────────── */
export const StatCard: React.FC<{
  label: string;
  value: string | number;
  icon?: string;
  sub?: string;
}> = ({ label, value, icon, sub }) => (
  <div className="rounded-3xl bg-surface-container-lowest/90 backdrop-blur-xl p-5 card-shadow flex flex-col gap-1">
    <div className="flex items-center justify-between">
      <span className="font-caption-data text-caption-data text-on-surface-variant">{label}</span>
      {icon && <span className="material-symbols-outlined text-primary text-[18px]">{icon}</span>}
    </div>
    <span className="font-metric-stat text-metric-stat text-primary leading-none">{value}</span>
    {sub && <span className="font-caption-data text-caption-data text-secondary">{sub}</span>}
  </div>
);

/* ── PageHeader ─────────────────────────────────────────────────────── */
export const PageHeader: React.FC<{
  title: string;
  subtitle?: string;
  /** trailing metadata chips cluster (right side) */
  chips?: React.ReactNode;
  actions?: React.ReactNode;
}> = ({ title, subtitle, chips, actions }) => (
  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
    <div>
      <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">{title}</h1>
      {subtitle && <p className="font-body-md text-body-md text-secondary mt-0.5">{subtitle}</p>}
    </div>
    {(chips || actions) && (
      <div className="flex flex-wrap items-center gap-2">
        {chips}
        {actions}
      </div>
    )}
  </div>
);

/** Metadata chip used in PageHeader clusters (Airframe / Component / status). */
export const MetaChip: React.FC<{
  icon: string;
  label: string;
  value: React.ReactNode;
  tone?: 'glass' | 'primary' | 'neutral';
}> = ({ icon, label, value, tone = 'glass' }) => {
  const tones = {
    glass: 'bg-surface-container-lowest/90 backdrop-blur-md shadow-sm',
    primary: 'bg-primary-container text-on-primary-container',
    neutral: 'bg-secondary-fixed text-on-secondary-fixed-variant',
  } as const;
  const isSolid = tone !== 'glass';
  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${tones[tone]} ${isSolid ? 'shadow-sm' : ''}`}
    >
      {!isSolid && (
        <span className="material-symbols-outlined text-primary text-[18px]">{icon}</span>
      )}
      <div className="flex flex-col">
        <span
          className={`font-caption-data text-[10px] leading-none ${isSolid ? 'opacity-80' : 'text-secondary'}`}
        >
          {label}
        </span>
        <span
          className={`font-caption-data text-caption-data font-bold ${isSolid ? '' : 'text-on-surface'}`}
        >
          {value}
        </span>
      </div>
    </div>
  );
};

/* ── Card ───────────────────────────────────────────────────────────── */
export const Card: React.FC<{
  title?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}> = ({ title, actions, children, className = '' }) => (
  <div
    className={`rounded-3xl bg-surface-container-lowest/90 backdrop-blur-xl p-6 card-shadow ${className}`}
  >
    {(title || actions) && (
      <div className="flex items-center justify-between mb-4">
        {title && (
          <h2 className="font-headline-sm text-headline-sm text-on-surface tracking-tight">
            {title}
          </h2>
        )}
        {actions}
      </div>
    )}
    {children}
  </div>
);

/* ── Buttons ────────────────────────────────────────────────────────── */
type BtnVariant = 'primary' | 'secondary' | 'ghost';

const BTN: Record<BtnVariant, string> = {
  primary:
    'bg-primary text-on-primary hover:bg-primary-container shadow-sm',
  secondary:
    'bg-secondary-container text-on-secondary-container hover:bg-surface-container-high',
  ghost: 'border border-outline-variant text-on-surface-variant hover:bg-surface-container-low',
};

export const Button: React.FC<{
  variant?: BtnVariant;
  icon?: string;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
}> = ({ variant = 'primary', icon, onClick, disabled, className = '', children }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-body-md text-body-md font-semibold transition-all disabled:opacity-40 disabled:pointer-events-none ${BTN[variant]} ${className}`}
  >
    {icon && <span className="material-symbols-outlined text-[18px]">{icon}</span>}
    {children}
  </button>
);

/* ── UI states ──────────────────────────────────────────────────────── */
export const LoadingState: React.FC<{ message?: string }> = ({
  message = 'Loading…',
}) => (
  <div className="flex flex-col items-center justify-center gap-3 py-16">
    <span className="material-symbols-outlined text-primary text-[36px] animate-spin">
      progress_activity
    </span>
    <span className="font-body-md text-body-md text-secondary">{message}</span>
  </div>
);

export const EmptyState: React.FC<{
  icon?: string;
  message: string;
  action?: React.ReactNode;
}> = ({ icon = 'inbox', message, action }) => (
  <div className="flex flex-col items-center justify-center gap-3 py-16">
    <span className="material-symbols-outlined text-outline text-[40px]">{icon}</span>
    <span className="font-body-md text-body-md text-secondary">{message}</span>
    {action}
  </div>
);

export const ErrorState: React.FC<{ message?: string; action?: React.ReactNode }> = ({
  message = 'Unable to load data. Please check the local AeroIntel server.',
  action,
}) => (
  <div className="flex flex-col items-center justify-center gap-3 py-16">
    <span className="material-symbols-outlined text-error text-[40px]">cloud_off</span>
    <span className="font-body-md text-body-md text-on-surface-variant text-center max-w-md">
      {message}
    </span>
    {action}
  </div>
);

/* ── ProcessingChecklist (New Inspection processing state) ──────────── */
export type StepStatus = 'done' | 'active' | 'pending';

export const ProcessingChecklist: React.FC<{
  steps: { label: string; status: StepStatus }[];
}> = ({ steps }) => (
  <div className="flex flex-col gap-3">
    {steps.map((s) => (
      <div key={s.label} className="flex items-center gap-3">
        {s.status === 'done' && (
          <span className="material-symbols-outlined text-tertiary text-[20px]">check_circle</span>
        )}
        {s.status === 'active' && (
          <span className="material-symbols-outlined text-primary text-[20px] animate-spin">
            progress_activity
          </span>
        )}
        {s.status === 'pending' && (
          <span className="w-5 h-5 rounded-full border-2 border-outline-variant" />
        )}
        <span
          className={`font-body-md text-body-md ${
            s.status === 'pending' ? 'text-secondary' : 'text-on-surface'
          }`}
        >
          {s.label}
        </span>
      </div>
    ))}
  </div>
);
