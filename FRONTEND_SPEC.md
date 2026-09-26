# AeroIntel — Frontend Functional Spec

**What this is:** the complete functional reference for building the AeroIntel frontend — pages, layouts, endpoints, data shapes, interactions, and states. Visual theme is owned separately (Canva); this doc defines **what every page contains and where its data comes from**.

**Companion docs:** `VERIFICATION_GUIDE.md` (how to run the model), `docs/TECHNICAL_INTEGRATIONS.md` (system contracts).

---

## 1. Backend endpoints (the complete v1 surface)

Base URL: `http://localhost:8000` (dev). All responses are JSON.

| # | Method | Path | Purpose | Used by |
|---|---|---|---|---|
| E1 | `POST` | `/api/detect` | Run damage detection on one image | P2 → P3 |
| E2 | `GET` | `/api/health` | Service + model status | P1 status dot, all pages |
| E3 | `GET` | `/api/model` | Model identity + class registry | P1, P2, P7 |
| E4 | `GET` | `/api/metrics` | Verified test-split metrics + latency | P1, P7 |

### E1 · `POST /api/detect`
Request: `multipart/form-data` with field `image` (JPG/PNG, max 10 MB) + optional query params:
- `conf` (float, default `0.40`) — confidence threshold
- `iou` (float, default `0.50`) — NMS IoU threshold

Response `200`:
```json
{
  "model": { "name": "aerointel_v1", "version": "v1" },
  "inference_ms": 285.1,
  "detections": [
    {
      "class_id": 2,
      "class_name": "dent",
      "confidence": 0.858,
      "bbox": { "x1": 120, "y1": 340, "x2": 480, "y2": 610 }
    }
  ]
}
```
Rules:
- `bbox` is in **original image pixel coordinates** — the frontend draws the boxes (scale by `displayed_width / natural_width`).
- `detections` is sorted by `confidence` descending (frontend may re-sort/filter).
- The backend is **stateless**: images are not stored, nothing is saved server-side. Refresh = results gone.
- Errors: `400` bad request, `413` file > 10 MB, `422` unsupported type, `500` inference failure — shape: `{ "error": { "code": "...", "message": "..." } }`.

### E2 · `GET /api/health`
```json
{ "status": "ok", "model_loaded": true }
```
`status: "ok" | "degraded" | "down"`. Poll on app load and every 30 s for the sidebar status dot.

### E3 · `GET /api/model`
```json
{
  "name": "aerointel_v1",
  "type": "yolo11-onnx",
  "version": "v1",
  "imgsz": 640,
  "trained_from": "aerointel_v1_yolo11s",
  "exported_at": "2026-09-24T19:36:06",
  "classes": { "0": "crack", "1": "corrosion", "2": "dent", "3": "missing_fastener" }
}
```

### E4 · `GET /api/metrics`
```json
{
  "dataset": { "images": 8525, "annotations": 15225, "split": { "train": 6820, "valid": 852, "test": 853 } },
  "overall": { "precision": 0.769, "recall": 0.575, "mAP50": 0.613, "mAP50_95": 0.405 },
  "per_class": {
    "crack":            { "precision": 0.757, "recall": 0.619, "mAP50": 0.654, "mAP50_95": 0.447 },
    "corrosion":        { "precision": 0.565, "recall": 0.213, "mAP50": 0.233, "mAP50_95": 0.099 },
    "dent":             { "precision": 0.913, "recall": 0.861, "mAP50": 0.887, "mAP50_95": 0.688 },
    "missing_fastener": { "precision": 0.839, "recall": 0.607, "mAP50": 0.677, "mAP50_95": 0.388 }
  },
  "latency": { "p50_ms": 284.5, "p95_ms": 415.0, "n_images": 60, "device": "cpu" }
}
```

### Class ID contract (frozen — map by ID, never by string)
| ID | Name | Box/chip color token |
|---|---|---|
| 0 | crack | red |
| 1 | corrosion | orange |
| 2 | dent | yellow |
| 3 | missing_fastener | purple |

---

## 2. Pages

### P1 · Dashboard — `v1`
**Purpose:** landing overview + entry point to inspection.

Layout blocks (top → bottom):
1. **Page header:** "Dashboard" + subtitle "Overview of your aircraft inspections."
2. **Stat card row (4):**
   - Inspections this session (client-side counter)
   - Defects detected this session (client-side counter)
   - Model mAP50 — from E4 `overall.mAP50` (0.613)
   - Avg latency — from E4 `latency.p50_ms` (284.5 ms)
3. **CTA card:** "New Inspection" primary button → P2.
4. **Class legend strip:** 4 class chips with counts from the current session (0 if none).
5. **Model card:** name/version/type from E3 + service status dot from E2.
6. *(v2 placeholder, collapsed)* Recent inspections table — hidden in v1, needs DB.

Data: E2, E3, E4. States: service down (red banner, disable CTA), model loading (amber).

### P2 · New Inspection — `v1` (core page)
**Purpose:** provide an image and run detection.

Layout blocks:
1. Header: "New Inspection" + subtitle "Capture an image, run AI detection."
2. **Flow indicator:** `Capture → Detect → Result` (3 steps, current highlighted).
3. **Metadata inputs (optional, client-side only in v1):** Aircraft ID, Aircraft Model, Component (text/dropdown).
4. **Input panel (two tabs):**
   - *Upload:* drag-and-drop zone + "Browse files" (JPG/PNG, ≤ 10 MB)
   - *Camera:* live capture via `getUserMedia`, snap button, retake
5. **Preview panel:** selected image thumbnail + filename, dimensions (W×H px), file size.
6. **Detection settings (collapsible "Advanced"):** confidence slider 0.05–1.00 (default 0.40), IoU slider 0.10–0.90 (default 0.50).
7. **Primary CTA:** "Run Detection" — disabled until a valid image is set.
8. **Recent captures strip (session):** last 4 thumbnails from this browser session, click to reload.

Interactions: validate type/size before enabling CTA; show upload progress; on submit → E1 with chosen `conf`/`iou`; on success navigate to P3 with the response.
States: empty (no image), invalid type, file too large (show 10 MB limit), detecting (~300 ms skeleton overlay on preview), API error (banner + retry).

### P3 · Inspection Result — `v1` (hero page)
**Purpose:** show detections on the image + actionable list.

Layout blocks:
1. Header: "Inspection Result" + subtitle "Review detected defects and take action."
2. **Left: annotated image viewer**
   - Original image, overlay boxes from `detections[].bbox` scaled to display size
   - Each box: 2px class-color border + label chip `class_name · confidence%` (toggleable)
   - Click a box ⇄ highlights the matching list row (both directions)
   - Toggle buttons: show/hide boxes, show/hide labels
   - Zoom/pan on the image
3. **Right rail: Detected Defects list**
   - One row per detection: class chip, `class_name`, `confidence` as % + mini bar
   - Sorted by confidence desc; per-class filter checkboxes; row click → flash box
4. **Confidence slider (result-level):** live client-side re-filter of returned detections; rows below slider render dimmed with "below threshold"; counter shows `X shown / Y total`.
5. **Inspection Findings table (compact):** Defect Type · Confidence · Location (bbox as `WxH px`) · Status (`Open` for v1).
6. **Meta badges:** `inference_ms` (e.g. "285 ms"), model name/version.
7. **Actions:** "New Inspection" (→ P2), "Download annotated image" (client-side canvas render — no API).
8. *(v2 placeholders, disabled)* Save to AeroMemory · Generate Report · Decision Support card.

States: zero detections (empty state + "try lowering the confidence threshold" + button that sets slider to 0.25), low-confidence-only results (info banner), API error.

### P4 · Inspection History — `v2` (design now, wire later)
**Purpose:** browse/search all stored inspections. **Requires DB + `GET /api/inspections` (not built).**

Layout: filter bar (Aircraft ID, Component, Defect Type multi-select, Date range, Status) · results table (Inspection ID, Date, Aircraft, Model, Component, Defects count + chips, Status pill, Actions → View) · pagination (25/page) · free-text search.

### P5 · AeroMemory — `v2` (design now, wire later)
**Purpose:** compare current inspection vs historical records for the same aircraft/component.

Layout: selector row (Aircraft ID → Model → Component) · two panes "Previous Inspection" vs "Current Inspection" with box overlays · **Detection Comparison** cards (type, previous mm → current mm, change delta colored) · **Historical Timeline** (inspection IDs as clickable nodes) · **Progression** badge (Stable / Improving / Worsening) · view toggles: Compare / Overlay / View Timeline.

### P6 · Inspection Report — `v2` (v1 fallback: print view)
**Purpose:** printable/exportable one-inspection summary.

Layout: report header (Inspection ID, Aircraft ID/Model, Component, Date, Inspector, Model + version used) · Detected Defects table (Type, Confidence, Location, Measurement) · original + annotated images · Historical Comparison section (v2) · Decision Support block (v2) · Engineer Review sign-off (v2) · actions: Generate PDF / Export / Print.

**v1 fallback:** a print-friendly stylesheet for P3 (browser print → PDF), no new API needed.

### P7 · Model Performance — `v1`
**Purpose:** transparent, honest model metrics dashboard.

Layout blocks:
1. Header + model badge (E3: name, type `yolo11-onnx`, imgsz 640, exported date).
2. **KPI row (5 cards):** Precision 0.769 · Recall 0.575 · mAP50 0.613 · mAP50-95 0.405 · Latency "p50 284.5 ms / p95 415 ms".
3. **Per-class performance table:** rows = 4 classes (with chips), cols = Precision / Recall / mAP50 / mAP50-95.
4. **Charts:** per-class mAP50 bar chart · Precision vs Recall grouped bars.
5. **Dataset card:** 8,525 images · 15,252 annotations · split 6,820 / 852 / 853 (train/valid/test).
6. **Notes card (fixed text):** "Metrics are from the held-out **test** split (853 images). Corrosion performance is low (single-source data) — targeted for v2. Detection threshold in production defaults to 0.40."

Data: E4 + E3. Rules: show test numbers only (never val 0.623); do not hide the weak Corrosion row.

### P8 · Settings — `v1 subset`
**v1 (all client-side, `localStorage`):**
- Default confidence threshold slider (syncs P2's default)
- Toggle: box labels on/off by default
- Default tab: Upload / Camera
- Reset to defaults
- Model info (read-only from E3) + service status (E2)

**v2 (design, don't build):** aircraft profiles, storage quota, notifications, auto-save toggle, historical retention, model version pinning.

---

## 3. Global layout (all pages)

- **Sidebar (fixed left):** logo → nav: Dashboard · New Inspection · Inspection History `v2` · AeroMemory `v2` · Reports `v2` · Model Performance · Settings → footer: version chip `v1.0.0` + service status dot (E2).
- **Topbar:** global search (v2, hidden in v1), notification bell (v2), user chip.
- **Page header pattern:** H1 title + one-line subtitle + primary action on the right.
- **v2 nav items:** visible but badged "Phase 2"; clicking shows a "Coming in Phase 2" placeholder page (keeps the sitemap stable).

## 4. Frontend behavior rules

1. **Boxes are drawn client-side** from `bbox` pixel coords: `left = x1 * (display_w / natural_w)`, same for all edges. Store `naturalWidth/Height` at upload.
2. **Confidence slider = client-side filter** of the E1 response; the `conf` query param is only the server-side floor. Never re-call E1 on slider change.
3. **No persistence in v1:** session stats live in memory; refresh resets. Settings persist via `localStorage`.
4. **Health polling:** E2 on app load + every 30 s; down → disable detection CTAs, show banner.
5. **Error mapping:** 413 → "Image exceeds 10 MB" · 422 → "Unsupported file type" · 5xx/network → "Detection service unavailable, retry".
6. **Mock-first development:** the JSON shapes in §1 are the fixtures — frontend can build fully against them before the backend exists, then swap `fetch()` in one service layer (`api.ts` / `api.js`).
7. **Numbers policy:** display metrics only from E4; never hardcode numbers elsewhere; never show val-split values.

## 5. Build order

| Sprint | Deliverable |
|---|---|
| 1 | P2 + P3 (full inspect loop, mock → real E1) + service layer |
| 2 | P7 (metrics dashboard, real E4) + P8 v1 subset |
| 3 | P1 dashboard + global layout + states/errors polish |
| 4+ | v2: DB-backed P4/P5/P6 (needs backend storage endpoints — separate spec) |
