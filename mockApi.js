/**
 * AeroIntel — Mock API (THE one file the frontend needs)
 * ========================================================
 * Single-file fixture + mock service implementing FRONTEND_SPEC.md §1.
 * Build every screen against `mockApi` — loading states, empty states and
 * errors all work. When the real backend lands, swap ONE import (see
 * "GOING LIVE" at the bottom). No other file changes.
 *
 * Fixtures are plain objects — if you need raw JSON, copy them as-is.
 */

/** Simulated latency (ms) so skeletons/spinners get exercised */
const MOCK_LATENCY_MS = 300;

/**
 * Image the detect fixtures assume — for testing bbox scaling.
 * bboxes are in ORIGINAL image pixels; scale by displayed/natural size.
 */
export const FIXTURE_IMAGE = {
  filename: "wing_panel_sample.jpg",
  width: 1600,
  height: 1200,
};

/** E2 — GET /api/health */
export const MOCK_HEALTH = { status: "ok", model_loaded: true };

/** E3 — GET /api/model */
export const MOCK_MODEL = {
  name: "aerointel_v1",
  type: "yolo11-onnx",
  version: "v1",
  imgsz: 640,
  trained_from: "aerointel_v1_yolo11s",
  exported_at: "2026-09-24T19:36:06",
  classes: { 0: "crack", 1: "corrosion", 2: "dent", 3: "missing_fastener" },
};

/** E4 — GET /api/metrics (verified test-split numbers — do not edit) */
export const MOCK_METRICS = {
  dataset: {
    images: 8525,
    annotations: 15252,
    split: { train: 6820, valid: 852, test: 853 },
  },
  overall: { precision: 0.769, recall: 0.575, mAP50: 0.613, mAP50_95: 0.405 },
  per_class: {
    crack:            { precision: 0.757, recall: 0.619, mAP50: 0.654, mAP50_95: 0.447 },
    corrosion:        { precision: 0.565, recall: 0.213, mAP50: 0.233, mAP50_95: 0.099 },
    dent:             { precision: 0.913, recall: 0.861, mAP50: 0.887, mAP50_95: 0.688 },
    missing_fastener: { precision: 0.839, recall: 0.607, mAP50: 0.677, mAP50_95: 0.388 },
  },
  latency: { p50_ms: 284.5, p95_ms: 415.0, n_images: 60, device: "cpu" },
};

/**
 * E1 — POST /api/detect (full result: all 4 classes, 6 detections).
 * NOTE: one detection sits at conf 0.31 on purpose — it demos the
 * "below threshold" dimmed state of the result-page slider.
 */
export const MOCK_DETECT_FULL = {
  model: { name: "aerointel_v1", version: "v1" },
  inference_ms: 285.1,
  detections: [
    { class_id: 2, class_name: "dent", confidence: 0.913,
      bbox: { x1: 512, y1: 640, x2: 896, y2: 812 } },
    { class_id: 0, class_name: "crack", confidence: 0.847,
      bbox: { x1: 1020, y1: 210, x2: 1345, y2: 262 } },
    { class_id: 3, class_name: "missing_fastener", confidence: 0.782,
      bbox: { x1: 1180, y1: 700, x2: 1232, y2: 752 } },
    { class_id: 1, class_name: "corrosion", confidence: 0.656,
      bbox: { x1: 180, y1: 830, x2: 460, y2: 1010 } },
    { class_id: 3, class_name: "missing_fastener", confidence: 0.548,
      bbox: { x1: 240, y1: 380, x2: 286, y2: 426 } },
    { class_id: 0, class_name: "crack", confidence: 0.31,
      bbox: { x1: 700, y1: 150, x2: 960, y2: 184 } },
  ],
};

/** E1 — zero-detection result (empty state) */
export const MOCK_DETECT_EMPTY = {
  model: { name: "aerointel_v1", version: "v1" },
  inference_ms: 271.4,
  detections: [],
};

/** Error shapes (FRONTEND_SPEC.md §1) — trigger via `force` option */
export const MOCK_ERRORS = {
  too_large:    { status: 413, body: { error: { code: "IMAGE_TOO_LARGE",       message: "Image exceeds the 10 MB limit." } } },
  bad_type:     { status: 422, body: { error: { code: "UNSUPPORTED_MEDIA_TYPE", message: "Only JPG and PNG images are supported." } } },
  server_error: { status: 500, body: { error: { code: "INFERENCE_FAILED",      message: "Detection service unavailable, retry." } } },
};

const delay = (ms) => new Promise((r) => setTimeout(r, ms));
const clone = (x) => structuredClone(x);
const throwLike = (e) => { const err = new Error(e.body.error.message); err.status = e.status; err.body = e.body; throw err; };

/**
 * Mock API — same signatures the real client will have.
 * detectImage(file, { conf, iou, force })
 *   force: undefined      → normal full result (filtered by conf)
 *          'empty'        → zero-detection result
 *          'too_large' | 'bad_type' | 'server_error' → error
 */
export const mockApi = {
  async getHealth() {
    await delay(80);
    return clone(MOCK_HEALTH);
  },

  async getModel() {
    await delay(80);
    return clone(MOCK_MODEL);
  },

  async getMetrics() {
    await delay(120);
    return clone(MOCK_METRICS);
  },

  async detectImage(file, { conf = 0.4, iou = 0.5, force } = {}) {
    if (force && MOCK_ERRORS[force]) {
      await delay(200);
      throwLike(MOCK_ERRORS[force]);
    }
    await delay(MOCK_LATENCY_MS);
    const result = force === "empty" ? MOCK_DETECT_EMPTY : MOCK_DETECT_FULL;
    const out = clone(result);
    out.detections = out.detections.filter((d) => d.confidence >= conf);
    return out;
  },
};

export default mockApi;

/* =========================== GOING LIVE ===========================
 * When the backend exists, replace ONLY the api import in your
 * service layer (e.g. src/services/api.js):

   const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

   export const api = {
     getHealth:  () => fetch(`${BASE}/api/health`).then((r) => r.json()),
     getModel:   () => fetch(`${BASE}/api/model`).then((r) => r.json()),
     getMetrics: () => fetch(`${BASE}/api/metrics`).then((r) => r.json()),
     detectImage: (file, { conf = 0.4, iou = 0.5 } = {}) => {
       const form = new FormData();
       form.append("image", file);
       return fetch(`${BASE}/api/detect?conf=${conf}&iou=${iou}`, {
         method: "POST",
         body: form,
       }).then(async (r) => {
         if (!r.ok) throw Object.assign(new Error("detect failed"), { status: r.status, body: await r.json() });
         return r.json();
       });
     },
   };

 * Before: import { mockApi as api } from "./mockApi";
 * After:  import { api } from "./api";
 * Every component keeps calling api.detectImage(...) unchanged.
 * ================================================================== */
