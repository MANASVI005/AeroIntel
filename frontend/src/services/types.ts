/**
 * AeroIntel API types — match the REAL FastAPI backend (verified 2026-09-30).
 * Source of truth: backend/app/api/*.py + STITCH_GUIDE.md §3.
 *
 * Key facts baked in here:
 *   - bbox is {x, y, width, height} (top-left + size), NOT x1y1x2y2
 *   - upload form field is "file"
 *   - GET /health returns {status, database}
 *   - classes map by ID: 0 crack, 1 corrosion, 2 dent, 3 missing_fastener
 *   - AeroMemory states: new | stable | increased | decreased | resolved
 */

export interface Bbox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Detection {
  id?: number;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: Bbox;
}

export interface AeroMemoryComparison {
  defect_id: string;
  defect_type: string;
  state: string; // new | stable | increased | decreased | resolved
  severity: string; // Low | Medium | High | Critical
  match_confidence: number;
}

export interface AeroMemorySummary {
  matched_count: number;
  new_count: number;
  comparisons: AeroMemoryComparison[];
}

/* ── /health ── */
export interface HealthResponse {
  status: string; // "healthy" | "unhealthy"
  database: string; // "connected" | ...
}

/* ── POST /api/inspections ── */
export interface InspectionCreate {
  panel_id: number;
  inspection_code: string;
  inspector_name?: string;
  notes?: string;
}

export interface Inspection {
  id: number;
  panel_id: number;
  inspection_code: string;
  inspection_date: string;
  inspector_name: string | null;
  status: string;
  panel_code: string | null;
  aircraft_code: string | null;
}

/* ── POST /api/inspections/{id}/images  (the core pipeline) ── */
export interface UploadResult {
  inspection_id: number;
  inspection_code: string;
  inspection_image_id: number;
  original_filename: string;
  stored_path: string;
  image_width: number;
  image_height: number;
  count: number;
  detections: Detection[];
  aeromemory: AeroMemorySummary;
}

/* ── GET /api/inspections/{id}/latest-result ── */
export interface LatestResult extends UploadResult {
  has_result: boolean;
  message?: string;
}

/* ── POST /api/decisions/{detection_id} ── */
export interface DecisionSupport {
  id: number;
  detection_id: number;
  severity: string;
  progression_status: string;
  recommended_action: string;
  reasoning: string;
}

/* ── POST /api/detect (stateless) ── */
export interface DetectResult {
  filename: string;
  count: number;
  detections: Detection[];
}

/* ── GET /api/metrics ── */
export interface ModelInfo {
  name: string | null;
  type: string | null;
  version: string | null;
  imgsz: number | null;
  trained_from: string | null;
  exported_at: string | null;
  classes: Record<string, string> | null;
}

export interface ClassMetrics {
  precision: number;
  recall: number;
  mAP50: number;
  'mAP50-95': number;
}

export interface ModelMetrics {
  model: ModelInfo;
  evaluation: {
    run: string | null;
    split: string | null;
    overall: { precision: number; recall: number; mAP50: number; 'mAP50-95': number };
    per_class: Record<string, ClassMetrics>;
    dataset: { images: number; annotations: number };
  };
  latency: {
    device: string | null;
    n_images: number | null;
    p50_ms: number | null;
    p95_ms: number | null;
    conf: number | null;
    iou: number | null;
  };
}

/** API error shape from FastAPI HTTPException */
export interface ApiError {
  status: number;
  detail: string;
}
