/**
 * Frozen damage-class contract (backend `models/aerointel_v1.onnx` classes).
 * Map by class_id — NEVER by string (class names vary: "Crack"/"crack").
 */
export interface ClassMeta {
  id: number;
  /** Canonical display name */
  name: string;
  /** Tailwind dot/chip token from the Stitch palette (defined in index.html) */
  dot: string;
  /** Chip bg for solid chips */
  chip: string;
}

export const CLASS_META: Record<number, ClassMeta> = {
  0: { id: 0, name: 'Crack', dot: 'bg-class-crack', chip: 'bg-class-crack' },
  1: { id: 1, name: 'Corrosion', dot: 'bg-class-corrosion', chip: 'bg-class-corrosion' },
  2: { id: 2, name: 'Dent', dot: 'bg-class-dent', chip: 'bg-class-dent' },
  3: { id: 3, name: 'Missing Fastener', dot: 'bg-class-fastener', chip: 'bg-class-fastener' },
};

/** Safe lookup for unknown class_ids arriving from the backend. */
export const classMeta = (id: number): ClassMeta =>
  CLASS_META[id] ?? { id, name: `Class ${id}`, dot: 'bg-outline', chip: 'bg-outline' };

/** AeroMemory comparison states — exact strings the backend sends. */
export type AeroMemoryState = 'new' | 'stable' | 'increased' | 'decreased' | 'resolved';

export const AEROMEMORY_STATE_META: Record<
  AeroMemoryState,
  { label: string; pill: string }
> = {
  new: { label: 'NEW DEFECT', pill: 'bg-primary-container text-on-primary-container' },
  stable: { label: 'STABLE', pill: 'bg-secondary-fixed text-on-secondary-fixed-variant' },
  increased: { label: 'PROGRESSING', pill: 'bg-error-container text-on-error-container' },
  decreased: { label: 'IMPROVING', pill: 'bg-tertiary-container text-on-tertiary-container' },
  resolved: { label: 'REPAIRED', pill: 'bg-tertiary-fixed text-on-tertiary-fixed-variant' },
};

export const aeromemoryStateMeta = (s: string) =>
  AEROMEMORY_STATE_META[s as AeroMemoryState] ?? {
    label: 'NO HISTORICAL MATCH',
    pill: 'bg-surface-container text-secondary',
  };
