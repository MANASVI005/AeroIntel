/**
 * AeroIntel service layer — the ONLY place the app talks to the backend.
 *
 * Real backend first, DEMO_MODE fallback. Set VITE_DEMO_MODE=1 (or leave the
 * backend offline) and every call resolves with realistic mock data instead.
 * Components never import fetch — they call these functions.
 */
import type {
  HealthResponse,
  Inspection,
  InspectionCreate,
  LatestResult,
  UploadResult,
  DecisionSupport,
  DetectResult,
  ModelMetrics,
} from './types';

const BASE: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const DEMO: boolean =
  import.meta.env.VITE_DEMO_MODE === '1' || import.meta.env.VITE_DEMO_MODE === 'true';

export const isDemoMode = () => DEMO;

/** Base URL for static files served by the backend (uploaded inspection images). */
export const imageBaseUrl = BASE;

/** Thrown by every service call on failure — components catch this. */
export class ApiServiceError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

/* ── low-level helpers ─────────────────────────────────────────────── */

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* keep statusText */
    }
    throw new ApiServiceError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  return fetch(`${BASE}${path}`).then((r) => json<T>(r));
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  return fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then((r) => json<T>(r));
}

async function postForm<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append('file', file); // backend field name is "file" — never "image"
  return fetch(`${BASE}${path}`, { method: 'POST', body: form }).then((r) => json<T>(r));
}

/* ── DEMO fixtures (realistic shapes, clearly fake IDs) ────────────── */

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const DEMO_DETECTIONS = [
  { id: 101, class_id: 0, class_name: 'Crack', confidence: 0.92, bbox: { x: 512, y: 640, width: 384, height: 172 } },
  { id: 102, class_id: 1, class_name: 'Corrosion', confidence: 0.87, bbox: { x: 180, y: 830, width: 280, height: 180 } },
  { id: 103, class_id: 3, class_name: 'Missing Fastener', confidence: 0.81, bbox: { x: 1180, y: 700, width: 52, height: 52 } },
  { id: 104, class_id: 2, class_name: 'Dent', confidence: 0.76, bbox: { x: 1020, y: 210, width: 325, height: 52 } },
];

const DEMO_AEROMEMORY = {
  matched_count: 2,
  new_count: 2,
  comparisons: [
    { defect_id: 'DEF-010', defect_type: 'Crack', state: 'increased', severity: 'High', match_confidence: 0.91 },
    { defect_id: 'DEF-011', defect_type: 'Corrosion', state: 'stable', severity: 'Medium', match_confidence: 0.84 },
    { defect_id: 'DEF-012', defect_type: 'Missing Fastener', state: 'new', severity: 'High', match_confidence: 0 },
    { defect_id: 'DEF-013', defect_type: 'Dent', state: 'new', severity: 'Medium', match_confidence: 0 },
  ],
};

const DEMO_INSPECTION: Inspection = {
  id: 42,
  panel_id: 1,
  inspection_code: 'DEMO-INS-1043',
  inspection_date: new Date().toISOString(),
  inspector_name: 'A. Sharma',
  status: 'completed',
  panel_code: 'PNL-LW-01',
  aircraft_code: 'DEMO-VT-ALB',
};

const DEMO_INSPECTIONS: Inspection[] = [
  DEMO_INSPECTION,
  { ...DEMO_INSPECTION, id: 41, inspection_code: 'DEMO-INS-1042', panel_code: 'PNL-LW-02', aircraft_code: 'DEMO-VT-ALB' },
  { ...DEMO_INSPECTION, id: 40, inspection_code: 'DEMO-INS-1041', panel_code: 'PNL-RW-01', aircraft_code: 'DEMO-VT-ALB' },
  { ...DEMO_INSPECTION, id: 39, inspection_code: 'DEMO-INS-1040', panel_code: 'PNL-FS-01', aircraft_code: 'DEMO-VT-AXP' },
];

function demoUpload(): UploadResult {
  return {
    inspection_id: 42,
    inspection_code: 'DEMO-INS-1043',
    inspection_image_id: 34,
    original_filename: 'wing_panel_sample.jpg',
    stored_path: 'data/inspections/DEMO-INS-1043/demo.jpg',
    image_width: 1600,
    image_height: 1200,
    count: DEMO_DETECTIONS.length,
    detections: DEMO_DETECTIONS,
    aeromemory: DEMO_AEROMEMORY,
  };
}

/* ── public API ────────────────────────────────────────────────────── */

export const api = {
  /** GET /health */
  async getHealth(): Promise<HealthResponse> {
    if (DEMO) {
      await delay(120);
      return { status: 'healthy', database: 'connected' };
    }
    return getJson<HealthResponse>('/health');
  },

  /** POST /api/inspections */
  async createInspection(data: InspectionCreate): Promise<Inspection> {
    if (DEMO) {
      await delay(200);
      return { ...DEMO_INSPECTION, inspection_code: data.inspection_code, inspector_name: data.inspector_name ?? null };
    }
    return postJson<Inspection>('/api/inspections', data);
  },

  /** GET /api/inspections — newest first */
  async listInspections(): Promise<Inspection[]> {
    if (DEMO) {
      await delay(200);
      return DEMO_INSPECTIONS;
    }
    return getJson<Inspection[]>('/api/inspections');
  },

  /**
   * POST /api/inspections/{id}/images — the core pipeline:
   * save → YOLO detect → AeroMemory compare, one atomic commit.
   */
  async uploadInspectionImage(inspectionId: number, file: File): Promise<UploadResult> {
    if (DEMO) {
      // simulate the real pipeline stages (~2.4 s total)
      await delay(2400);
      return { ...demoUpload(), inspection_id: inspectionId };
    }
    return postForm<UploadResult>(`/api/inspections/${inspectionId}/images`, file);
  },

  /** GET /api/inspections/{id}/latest-result — 2s dashboard polling */
  async getLatestResult(inspectionId: number): Promise<LatestResult> {
    if (DEMO) {
      await delay(150);
      return { has_result: true, ...demoUpload() };
    }
    return getJson<LatestResult>(`/api/inspections/${inspectionId}/latest-result`);
  },

  /** POST /api/decisions/{detection_id} */
  async createDecisionSupport(detectionId: number): Promise<DecisionSupport> {
    if (DEMO) {
      await delay(300);
      return {
        id: 7,
        detection_id: detectionId,
        severity: 'High',
        progression_status: 'New / Baseline',
        recommended_action:
          'Schedule detailed NDT inspection of the affected area within the next maintenance cycle.',
        reasoning:
          'High-confidence Crack detection on a primary structure zone requires engineer review before further flight operation.',
      };
    }
    return postJson<DecisionSupport>(`/api/decisions/${detectionId}`, {});
  },

  /** GET /api/metrics — verified eval + latency served by the backend */
  async getMetrics(): Promise<ModelMetrics> {
    if (DEMO) {
      await delay(150);
      return {
        model: {
          name: 'aerointel_v1',
          type: 'yolo11-onnx',
          version: 'v1',
          imgsz: 640,
          trained_from: 'aerointel_v1_yolo11s',
          exported_at: '2026-09-24T19:36:06.967545',
          classes: { '0': 'crack', '1': 'corrosion', '2': 'dent', '3': 'missing_fastener' },
        },
        evaluation: {
          run: 'aerointel_v1_yolo11s',
          split: 'test',
          overall: { precision: 0.769, recall: 0.575, mAP50: 0.613, 'mAP50-95': 0.405 },
          per_class: {
            Crack: { precision: 0.757, recall: 0.619, mAP50: 0.654, 'mAP50-95': 0.447 },
            Corrosion: { precision: 0.565, recall: 0.213, mAP50: 0.233, 'mAP50-95': 0.099 },
            Dent: { precision: 0.913, recall: 0.861, mAP50: 0.887, 'mAP50-95': 0.688 },
            'Missing Fastener': { precision: 0.839, recall: 0.607, mAP50: 0.677, 'mAP50-95': 0.388 },
          },
          dataset: { images: 8525, annotations: 15252 },
        },
        latency: {
          device: 'colab cpu (proxy for laptop cpu)',
          n_images: 60,
          p50_ms: 284.5,
          p95_ms: 415.0,
          conf: 0.4,
          iou: 0.5,
        },
      };
    }
    return getJson<ModelMetrics>('/api/metrics');
  },

  /** POST /api/detect — stateless quick detection (no save) */
  async detectImage(file: File): Promise<DetectResult> {
    if (DEMO) {
      await delay(800);
      return { filename: file.name, count: DEMO_DETECTIONS.length, detections: DEMO_DETECTIONS };
    }
    return postForm<DetectResult>('/api/detect', file);
  },
};

export default api;
