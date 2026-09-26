# AeroIntel — UI/UX Design Brief (Canva theme → Stitch code)

**Purpose:** single reference for the UI designer. Page map, user flow, per-page data slots (with **exact API field names**), states to design, and theme direction.

**Golden rule:** use the **exact API field names** from "Data slots" (e.g. `class_name`, `confidence`, `inference_ms`) in the design. Then the Stitch-exported frontend wires to the real backend by just swapping mock JSON for `fetch()` calls — zero renaming.

---

## 0. Scope split — CRITICAL for the team

| Phase | Pages | Backend status |
|---|---|---|
| **v1 — buildable today** | Dashboard, New Inspection, Inspection Result, Model Performance, Settings (partial) | ✅ Works with the 4 planned endpoints, no DB needed |
| **v2 — needs a database first** | Inspection History, AeroMemory, Reports, Alerts, historical comparison | ⬜ Stateless inference backend only; needs inspection storage (DB + `POST /api/inspections`) |

Design all 8 pages (they define the product vision), but **mark v2 pages as "Phase 2"** in handoff so nobody expects them wired to the backend in v1.

---

## 1. User flow (v1 happy path)

```
Login/landing (optional) → Dashboard → New Inspection → [Capture/Upload image]
      → Detect (loading ~300 ms) → Inspection Result (boxes + list)
      → [Adjust confidence slider → live re-filter] → Model Performance
```

v2 adds: Result → Save to AeroMemory → History / Compare / Report.

---

## 2. Page-by-page reference

### P1 · Dashboard (v1 ✅)
Purpose: at-a-glance overview.
- **Data slots:** `model.name`, `model.version` (badge), status dot ← `GET /api/health` → `{ status, model_loaded }`; stats cards ← `GET /api/metrics` (overall mAP50 0.613, latency p50 285 ms); defect-legend chips (4 classes + colors).
- **States:** backend down (red dot + "service offline"), model loading (amber dot).
- ⚠️ Donut chart "defects overview" and "recent inspections" table are **v2** (need DB). For v1 replace with: per-class mAP50 bar strip from `/api/metrics` + "Start inspection" CTA.

### P2 · New Inspection (v1 ✅ — the core page)
Purpose: capture/upload → detect.
- **Elements:** big drag-and-drop zone (JPG/PNG, max 10 MB), camera capture (mobile), preview thumbnail, primary CTA "Run Detection".
- **Flow chips:** Capture → Detect → Result (nice for orientation; it's client-side only, no API).
- **Data slots (pre-fill):** `model.name`, `model.version`, `imgsz` ← `GET /api/model`.
- **States:** empty, invalid file type, file > 10 MB (413), uploading, detecting (~300 ms skeleton/spinner — design it, it matters).

### P3 · Inspection Result (v1 ✅ — hero page)
Purpose: image with boxes + detection list.
- **Data slots:** ← `POST /api/detect` response, field names **exactly**:
  - `detections[]` → `class_id`, `class_name`, `confidence`, `bbox.x1/y1/x2/y2` (original image pixels — **frontend draws the boxes**; that's why class colors live in the theme)
  - `inference_ms` → latency badge ("285 ms")
  - `model.name`, `model.version` → small badge
- **Confidence slider** (0.05–1.0, default 0.40): re-filters detections client-side; results below threshold shown dimmed.
- **States:** no detections found (empty state with "try lowering confidence" hint), low-confidence results, very many boxes (list scrolls).
- **v2 zone (mark it):** Decision Support card, "Compare with AeroMemory", "Generate Report".

### P4 · Inspection History (v2 ⬜ — design fully, mark Phase 2)
Purpose: searchable table of past inspections. Needs `GET /api/inspections` (DB). Filters: aircraft ID, defect type, date range, status.

### P5 · AeroMemory (v2 ⬜)
Purpose: side-by-side current vs historical comparison, progression timeline, "change ±mm". Needs stored inspections + image storage. This is the "wow" page — design it richly, flag as Phase 2.

### P6 · Inspection Report (v2 ⬜ for persistence; ⬜ PDF export)
Purpose: one-inspection summary → PDF. v1 could render a print-friendly result page client-side (no API needed) — nice intermediate win.

### P7 · Model Performance (v1 ✅)
Purpose: metrics dashboard.
- **Data slots:** ← `GET /api/metrics`:
  - overall: `precision` 0.769, `recall` 0.575, `mAP50` 0.613, `mAP50-95` 0.405
  - per-class table (Crack / Corrosion / Dent / Missing Fastener × same 4 columns)
  - latency card: `p50` 284.5 ms, `p95` 415.0 ms
  - model info: name `aerointel_v1`, type `yolo11-onnx`, imgsz 640
- ⚠️ Mockup shows "YOLOv8" — actual model is **YOLO11s**. And show **test** numbers (mAP50 0.613), never val (0.623).
- **Honesty note:** keep Corrosion's weak row visible (mAP50 0.233) — the project rule is "never fabricate numbers".

### P8 · Settings (v1 partial ✅)
v1-able: confidence default slider, theme light/dark, class color legend.
v2: aircraft profile, storage, notifications, historical retention.

---

## 3. Global components to design once, reuse everywhere
- Sidebar nav: Dashboard · New Inspection · Inspection History · AeroMemory · Reports · Model Performance · Settings (v2 items get a "Phase 2" dot)
- Top bar: search, notification bell, user chip
- **Class chip system** (4 colors, same chips used in legend, lists, tables, boxes)
- Status pills: Completed / Pending / Flagged (v2), Online / Offline (v1)
- Stat card, table row, empty state, loading skeleton, error banner

---

## 4. Theme direction (from the approved mockup)
- **Light, clean aviation-industrial:** white cards, very light blue-gray canvas, **deep navy sidebar** (#0B1F3A-ish) with white text
- Primary accent: **aviation blue** (#1D6FE0-ish) for CTAs and links
- **Class colors (freeze these — used for boxes + chips):** crack `#ef4444` red · corrosion `#f97316` orange · dent `#eab308` yellow · missing_fastener `#a855f7` purple
- Status: green = success/completed, amber = pending, red = flagged/error
- Type: Inter for UI; tabular numerals for metrics; JetBrains Mono or IBM Plex Mono for IDs/latency badges
- Cards: rounded-xl, soft shadow, 1px light border; data-dense but breathable (8-pt spacing grid)
- Footer tagline: "AeroIntel · Smarter Inspections, Safer Skies"

---

## 5. Handoff checklist (before Stitch)
- [ ] All detection UI labels use API field names (`class_name`, `confidence`, `inference_ms`, `bbox`)
- [ ] Class colors match the 4 frozen IDs exactly
- [ ] Every page has: empty, loading, error, no-data states
- [ ] v2-only features visually tagged "Phase 2" in handoff notes
- [ ] Numbers shown = test-split values from `/api/metrics`, not invented ones
