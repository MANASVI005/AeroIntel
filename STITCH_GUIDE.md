# AeroIntel — STITCH MASTER FILE (prompts + real backend reference)

**This is the ONLY file you need.** It contains: ① how to feed Stitch, ② the master prompt, ③ all 11 screen prompts, ④ the complete real backend reference (every endpoint that actually exists in `backend/`, with exact request/response shapes from the code), ⑤ post-export wiring notes.

---

## 0. How to feed Stitch — one page at a time, NOT the whole file

**Send ONE prompt per message, in order.** Do not paste this whole file into Stitch.

1. **Message 1:** Master prompt (§1) + **attach the reference image** (sky-blue landing/dashboard mock).
2. **Message 2…12:** one screen prompt at a time (§2.1 → §2.11). Re-attach the reference image on the first 2–3 screens to lock the theme. Wait for each screen to finish before sending the next.
3. Keep everything in **one Stitch thread** — the master prompt's theme rules carry over to every later screen.
4. **Do not paste** §3 (backend reference) or §4 (wiring) into Stitch — those are for you and the frontend developer. Stitch only needs the master prompt + screen prompts + the image.
5. The values inside the screen prompts (48 inspections, 92% crack, 285 ms…) are already aligned with the real backend/data — no need to send Stitch anything else.

Stitch will render the 3D hero as a placeholder — that's expected; the real model gets wired in code (§4).

---

## 1. Master prompt — paste ONCE first (attach the reference image)

```
We are designing "AeroIntel", an AI-powered aircraft damage inspection web app
with a "longitudinal memory" called AeroMemory that tracks defects across
inspections.

THEME — FOLLOW THE ATTACHED REFERENCE IMAGE ONLY:
Use the attached reference image as the single source of truth for the entire
visual system: colors, gradients, background treatment, card style, rounding,
shadows, blur/glass effects, typography mood and spacing feel. Do NOT invent
or substitute any other palette or theme (in particular: keep it light and
airy like the image — no dark-mode dashboard). Recreate the look so closely
that the generated screens could be mistaken for the same product.

App structure:
- One public LANDING screen that matches the reference image top-to-bottom:
  slim glassy top navbar (logo "AeroIntel", links Dashboard, Inspection,
  Settings, hamburger "Menu" on the right), a large hero section, then the
  dashboard overview content scrolling directly below (exactly like the image).
- All other screens are in-app screens using a fixed left sidebar shell:
  logo "AeroIntel" with tagline "Smart Inspection. Safer Skies.", nav items
  Dashboard, New Inspection, Inspection History, AeroMemory, Reports,
  Model Performance, Settings (active item highlighted per the reference
  style), footer with version chip "v1.0.0" and a small status dot; top bar
  with global search, notification bell with dropdown, user avatar chip
  ("Aviation Engineer").

Damage classes used across the product: crack, corrosion, dent,
missing_fastener. Pick ONE accent color per class FROM THE REFERENCE IMAGE'S
PALETTE and reuse it identically everywhere (chips, bounding boxes, legends,
charts). Keep this mapping consistent on every screen.

Tone: clean aviation-industrial product, data-dense but breathable, soft
rounded cards, 8-pt spacing grid, tabular numerals for metrics.

I will send the screens one by one in this order:
Landing, Dashboard, New Inspection, Inspection Result, Inspection History,
AeroMemory, Reports, Inspection Report, Model Performance, Settings,
Mobile Capture.
```

---

## 2. Screen prompts — paste ONE PER MESSAGE, in this order

### 2.1 Landing ▶ FIRST (hero with 3D rotating aircraft)
```
Screen: "Landing" — public hero page, match the attached reference image
exactly (top glassy pill navbar: "AeroIntel" logo left; Dashboard, Inspection,
Settings links; hamburger "Menu" right).

Hero section (full viewport height, sky gradient background like the image):
1. Left-aligned or centered headline block, styled like the image:
   small muted overline "An Edge AI Inspection Assistant" and bold main line
   "for Intelligent Aircraft Defect Detection".
2. PRIMARY NEW ELEMENT — 3D ROTATING AIRCRAFT: reserve a large hero area
   (right half on desktop, above/behind the headline on mobile) containing a
   3D aircraft model in a canvas, slowly auto-rotating on its vertical axis
   (idle rotation ~20s/turn), draggable to orbit, subtle vertical float, soft
   drop shadow beneath, no visible controls or chrome — just the model and
   generous sky around it. Render as a three.js-style placeholder (stylized
   low-poly passenger aircraft is fine; the real glTF model is wired later).
   The headline and the 3D plane must not overlap on desktop.
3. Below the headline: pill CTA button "Start Detection →" in the image's
   button style.

Directly below the hero (same scrolling page, like the image):
- Section header "Dashboard" with muted subtitle
  "Overview of your Aircraft Inspection", thin divider line.
- Row of 4 rounded white stat cards: Total Inspection 345, Defects Detected
  206, Resolved 24, Pending 11.
- "Recent Inspection" card: table with columns ID, Aircraft ID, Model,
  Component, Date, Status, Defects, Action (View link); show 5 example rows
  (e.g. INS-1042, VT-ALB, Boeing 737, Wing, 2025-09-14, Completed, 2, View).
- Two cards side by side: "Defect Overview" donut chart with legend
  (Crack, Dent, Corrosion, Missing Fastener — one palette color each) and
  "Inspection Performance" line chart with two series (Inspection, Defect)
  across years 2021–2025.
- One wide empty-content card at the bottom (alerts area placeholder).

Navbar interactions: Dashboard scrolls to the dashboard section; Inspection
and Menu are placeholder links.
```

### 2.2 Dashboard (in-app shell)
```
Screen: "Dashboard" — same content as the reference image's lower half, but
now inside the app shell (left sidebar + top bar per the master prompt).
Match the reference image theme.

1. Page header: H1 "Dashboard", subtitle "Overview of your aircraft
   inspections."
2. Row of 4 stat cards: "Total Inspections" 48, "Defects Detected" 27,
   "Resolved" 18, "Pending" 9.
3. "Recent Inspections" table card: columns Inspection ID | Aircraft |
   Model | Component | Date | Status | Defects | Action. 6 sample rows,
   statuses as soft pills (Completed, Pending, Flagged). Row action "View".
4. Two cards side by side: "Defect Overview" donut (crack, corrosion, dent,
   missing_fastener with class colors from the master mapping) and
   "Inspection Performance" trend chart (Inspections completed vs pending
   over time).
5. "Latest Alerts" list card: rows with small icons — "New crack detected —
   INS-1043", "Defect progression detected — INS-1038", "Defect marked
   repaired — INS-1029", "Missing fastener detected — INS-1041"; each row
   clickable (visual hover state).
6. "Recent Inspection Images" strip: 5 small rounded thumbnails.
7. "Quick Actions" card with 3 buttons: primary "Start New Inspection",
   secondary "Upload Inspection Image", ghost "View Reports".

Show one interaction state: the first alert row in hovered state.
```

### 2.3 New Inspection
```
Screen: "New Inspection" — capture + detection launch page. Match the
reference image theme, inside the app shell.

1. Page header: H1 "New Inspection", subtitle "Capture image, run AI
   detection and store in AeroMemory."
2. Horizontal step indicator with 4 steps: Capture → Save → Detect →
   Compare History (step 1 active, completed steps get a check style).
3. Card "Inspection information" — form grid: Inspection ID (prefilled
   INS-1043), Aircraft ID (VT-ALB), Aircraft Model (Boeing 737), Component
   (Wing dropdown), Panel / Area (Left Wing Panel), Engineer / Technician
   (A. Sharma). Primary button right-aligned: "Continue".
4. Two-column card below:
   LEFT = tabbed input panel: tab "Upload" (active) with large dashed
   drag-and-drop zone "Drop aircraft image here or browse — JPG/PNG,
   max 10 MB"; tab "Camera" with a live-capture placeholder frame and a
   round shutter button labeled "Capture Image".
   RIGHT = preview panel: selected image thumbnail, filename
   "wing_panel_sample.jpg", "1600 × 1200 px", "2.4 MB", with buttons
   "Retake Photo" (ghost) and "Use Photo" (primary).
5. Collapsible "Advanced settings" row: sliders "Confidence threshold" 0.40
   and "IoU threshold" 0.50.

Then show TWO additional states of the same screen as separate frames:
- PHOTO PREVIEW state: the LEFT panel replaced by the large captured photo
  with "Retake Photo" / "Use Photo" buttons beneath.
- PROCESSING state: the preview area replaced by a vertical checklist —
  "✓ Image uploaded", "✓ Image stored", "⟳ Running AI detection" (spinner),
  "○ Comparing with AeroMemory", "○ Preparing result".
```

### 2.4 Inspection Result
```
Screen: "Inspection Result" — the hero page. Match the reference image theme,
inside the app shell.

1. Page header: H1 "Inspection Result", subtitle "AI-detected defects,
   historical findings and decision support."
2. Two columns.
   LEFT (60%): image viewer card — aircraft wing photo with overlaid
   bounding boxes drawn in the class colors; each box has a small label chip
   pinned to its top-left ("crack · 92%", "dent · 76%"). Above the image:
   toggle pills "Boxes" and "Labels" (both on) and a neutral badge
   "Inference 285 ms".
   RIGHT (40%): "Detected Defects" list card — rows of colored class chip +
   class name + confidence % with a thin bar, sorted highest first
   (crack 92%, corrosion 87%, missing_fastener 81%, dent 76%). Under the
   list: "Confidence threshold" slider at 0.40 with caption
   "Showing 4 of 5 detections".
3. "Inspection Findings" table: Defect | Confidence | Location | Status —
   rows matching detections, status pill "Open".
4. "AeroMemory Analysis" strip card: one row per defect showing its
   historical state as a labeled badge — crack "NEW DEFECT", corrosion
   "EXISTING DEFECT", dent "PROGRESSING", missing_fastener "NO HISTORICAL
   MATCH". (Badge styles: new = info, existing = neutral, progressing =
   attention, no match = muted.)
5. "Decision Support" callout card with an attention icon: "Potential
   structural concern detected. Engineer Review Required." and the muted
   footnote line: "AI result is decision support only. Final decision must
   be made by a qualified maintenance engineer."
6. Footer action row: primary "Compare with History", secondary
   "Generate Report", secondary "View AeroMemory", ghost "Save Inspection".
```

### 2.5 Inspection History
```
Screen: "Inspection History" — searchable records table. Match the reference
image theme, inside the app shell.

1. Page header: H1 "Inspection History", subtitle "View and manage all
   inspection records."
2. Filter bar card: dropdowns Aircraft ID, Component, Defect Type (multi),
   Date range, Status + free-text search field "Search inspections…".
3. Dense results table: columns Inspection ID | Aircraft ID | Aircraft
   Model | Component | Date | Defects (class chips with counts) | Status
   pill | Actions. 8 sample rows with varied statuses (Completed, Pending,
   Flagged) and defect chips in class colors.
4. Row actions: "View" link and "Compare" link.
5. Pagination footer: "25 per page", page 1 of 6.

Show one empty state frame: same table with a centered muted message
"No inspections match the selected filters." and a "Clear filters" button.
```

### 2.6 AeroMemory
```
Screen: "AeroMemory" — historical comparison, the key differentiator page.
Match the reference image theme, inside the app shell.

1. Page header: H1 "AeroMemory", subtitle "Compare current inspections with
   historical aircraft records."
2. Selector card: dropdowns Aircraft ID (VT-ALB), Aircraft Model
   (Boeing 737), Component (Wing), Previous Inspection (INS-1008 · Sep 10),
   Current Inspection (INS-1043 · Sep 24).
3. Side-by-side comparison: two image cards labeled "PREVIOUS INSPECTION"
   and "CURRENT INSPECTION" with bounding boxes overlaid in class colors,
   and a circular "VS" badge between them.
4. "Detection Comparison" card: per-defect rows —
   crack: "Previous +0 px → Current +42 px" with a red change chip "+42 px ·
   PROGRESSING"; corrosion: "existing · area −6%" with a neutral chip.
   Include the muted caption: "Physical measurement unavailable — no
   calibration for this camera. Deltas shown in pixels."
5. "Historical Timeline" card: horizontal timeline with 4 clickable nodes
   (INS-1005 Aug 26 · STABLE, INS-1008 Sep 10 · EXISTING, INS-1012 Sep 14 ·
   PROGRESSING, INS-1043 Sep 24 · PROGRESSING), each node colored by state.
6. "Progression Analysis" summary card: current state badge "PROGRESSING"
   with a small rising trend icon, and one-line explanation
   "Defect has grown across the last 2 inspections."
7. Action row: primary "Compare", secondary "Overlay", secondary
   "View Timeline", ghost "Generate Report".

Show one overlay state frame: the previous image with the current
inspection's bounding boxes ghosted on top at 50% opacity.
```

### 2.7 Reports
```
Screen: "Reports" — report list. Match the reference image theme, inside the
app shell.

1. Page header: H1 "Reports", subtitle "Generate and manage inspection
   reports."
2. Table card "Inspection Reports": columns Inspection ID | Aircraft | Date
   | Status | Report Status (Generated / Not generated pills) | Action
   (View, Generate, Download links). 6 sample rows.
3. Empty state frame: "No reports generated yet." with primary button
   "Generate first report".
```

### 2.8 Inspection Report
```
Screen: "Inspection Report" — printable one-inspection report. Match the
reference image theme, inside the app shell (slightly wider content column).

1. Report header block: title "Inspection Report", metadata grid —
   Inspection ID INS-1043, Aircraft ID VT-ALB, Model Boeing 737, Component
   Wing, Inspector A. Sharma, Date 2025-09-24, Model Version aerointel_v1.
2. "Detected Defects" table: Defect Type | Confidence | Location |
   Measurement | Status.
3. Two image cards side by side: "Original" photo and "Annotated" photo with
   class-colored boxes.
4. "Historical Comparison" section: compact table — Previous Inspection
   INS-1012, Current Inspection INS-1043, Change "+42 px", AeroMemory State
   "PROGRESSING".
5. "Decision Support" callout: "Potential structural concern detected.
   Maintenance action may require review." followed by an "Engineer Review"
   sign-off block (name, signature line, date) with the footnote
   "Final decision must be made by a qualified maintenance engineer."
6. Footer actions: "Generate PDF" (primary), "Export Report", "Print".
```

### 2.9 Model Performance
```
Screen: "Model Performance" — YOLO model metrics dashboard. Match the
reference image theme, inside the app shell.

1. Page header: H1 "Model Performance", subtitle "Performance metrics and
   model details." Badge next to title: "aerointel_v1 · YOLO11s · ONNX ·
   640 px".
2. KPI row of 5 cards: Precision 0.769, Recall 0.575, mAP50 0.613,
   mAP50-95 0.405, Inference Time "p50 285 ms · p95 415 ms (CPU)".
3. "Per-class performance" grouped bar chart: Precision vs Recall for
   crack, corrosion, dent, missing_fastener (class colors).
4. "Detection Distribution" donut card labeled clearly
   "Detections recorded in operational inspections" — crack, corrosion,
   dent, missing_fastener.
5. "Model information" card: rows — Model "YOLO11s (aerointel_v1)", Version
   "v1", Training Dataset "AeroIntel-ABC (8,525 images · 15,252
   annotations)", Last Evaluated "2026-09-24", Deployment Status "Deployed"
   with green dot.
6. Small footnote card: "Metrics from the held-out test split (853 images).
   Corrosion is single-source data — targeted for v2."
```

### 2.10 Settings
```
Screen: "Settings" — preferences and system configuration. Match the
reference image theme, inside the app shell.

1. Page header: H1 "Settings", subtitle "Manage your preferences and
   application configuration."
2. Two-column layout.
   LEFT column, stacked cards:
   - "Profile": Name, Role "Aviation Engineer", Email.
   - "Aircraft": Aircraft ID VT-ALB, Aircraft Model Boeing 737, Default
     Component Wing.
   - "Inspection": Image Quality select, "Detection Confidence Threshold"
     slider 0.40 with a warning hint "Changing this affects live
     detection — confirmation required", toggle "Auto-save to AeroMemory"
     (on).
   - "AeroMemory": Storage "2.4 GB / 10 GB" with a slim progress bar,
     Historical Retention "12 months", Comparison Settings link, toggle
     "Auto Compare" (on).
   - "Model": Model Version aerointel_v1 (read-only), Model Path
     models/aerointel_v1.onnx (read-only), Inference Configuration link —
     visually locked with a small lock icon and caption "Managed by the
     local server".
   RIGHT column, top card "System Status" — one row per line, each with a
   status dot: Backend "Connected" (green), PostgreSQL "Connected" (green),
   YOLO Model "Loaded" (green), AeroMemory "Ready" (green), Storage
   "Available" (green), Network "LOCAL" (green), Internet "Not Required"
   (neutral).
   Below it "Application" card: Notifications toggle, Theme select showing
   "System", Language select, Offline Mode toggle, and a "Local Server
   Status" row "http://localhost:8000 — running".
```

### 2.11 Mobile Capture
```
Screen: "Mobile Capture" — phone-sized flow (generate as a 390 × 844 mobile
frame). Match the reference image theme, simplified for a technician's phone.

1. Compact header: "AeroIntel Mobile" + tagline "New Inspection".
2. Context card: Aircraft "VT-ALB", Component "Wing" (small read-only chips).
3. Large rounded capture area: camera viewfinder placeholder with a round
   shutter button "Capture Image".
4. Preview state frame: captured photo with "Retake" (ghost) and
   "Use Photo" (primary) buttons.
5. Processing state frame: stacked status rows — "Uploading…", "AI
   Detecting…", "Comparing with AeroMemory…" with a spinner.
6. Result state frame: success check, "Inspection Complete",
   "2 Defects Detected", rows "Crack 92%" and "Corrosion 87%" with class
   color chips, primary button "View Full Result".
```

---

## 3. REAL BACKEND REFERENCE (for you + the frontend dev — do NOT paste into Stitch)

Everything below is extracted from the actual FastAPI code in `backend/` (verified running 2026-09-30). Base URL: `http://localhost:8000`.

Run locally:
```bash
export DATABASE_URL="sqlite:///./aerointel_test.db"   # or postgres URL
PYTHONPATH=backend python -m app.db.init_db           # create tables (first time)
cd backend && uvicorn app.main:app --reload --port 8000
```

### 3.1 Endpoint map

| # | Method | Path | Purpose | Used by screen |
|---|---|---|---|---|
| A | `GET` | `/` | API info ping | — |
| B | `GET` | `/health` | DB + service health | Dashboard dot, Settings → System Status |
| C | `POST` | `/api/detect` | Stateless one-shot detection (no save) | quick-try tools |
| D | `POST` | `/api/inspections` | Create an inspection record | New Inspection step 1 |
| E | `GET` | `/api/inspections` | List inspections (desc) | Dashboard, History tables |
| F | `POST` | `/api/inspections/{id}/images` | **THE core endpoint**: upload → save → YOLO → AeroMemory, one atomic commit | New Inspection (Use Photo) |
| G | `GET` | `/api/inspections/{id}/latest-result` | Latest image + detections + AeroMemory states | Result page, dashboard 2 s polling, mobile |
| H | `POST` | `/api/decisions/{detection_id}` | Run decision engine on one detection | Result → Decision Support card |

### 3.2 Endpoint details (exact shapes from code)

**B — `GET /health`** →
```json
{ "status": "healthy", "database": "connected" }
```
(503 with `status: "unhealthy"` when DB is down. Poll on load + every 30 s.)

**C — `POST /api/detect`** — multipart form, field name **`file`** (not `image`). JPG/JPEG/PNG/BMP/WEBP only (else 400). Stateless: nothing stored.
```json
{
  "filename": "wing.jpg",
  "count": 2,
  "detections": [
    { "class_id": 0, "class_name": "Crack", "confidence": 0.92,
      "bbox": { "x": 120, "y": 340, "width": 360, "height": 270 } }
  ]
}
```

**D — `POST /api/inspections`** — JSON body:
```json
{ "panel_id": 1, "inspection_code": "INSP-1043", "inspector_name": "A. Sharma", "notes": "" }
```
→ returns the created record `{id, panel_id, inspection_code, inspection_date, inspector_name, status: "completed", notes}`. **409** if `inspection_code` already exists.

**E — `GET /api/inspections`** → array, newest first:
```json
[ { "id": 12, "panel_id": 1, "inspection_code": "INSP-1043",
    "inspection_date": "2026-09-30T14:53:29", "inspector_name": "A. Sharma",
    "status": "completed",
    "panel_code": "PNL-01", "aircraft_code": "VT-ALB" } ]
```

**F — `POST /api/inspections/{id}/images`** — multipart form, field name **`file`**. This is the whole pipeline in one call: saves image to `data/inspections/{inspection_code}/`, validates with OpenCV, runs YOLO, stores image + detections, runs AeroMemory matching, single atomic commit (rollback deletes the file on failure).

Response `200`:
```json
{
  "inspection_id": 12,
  "inspection_code": "INSP-1043",
  "inspection_image_id": 34,
  "original_filename": "wing.jpg",
  "stored_path": "data/inspections/INSP-1043/3cb5a043….jpg",
  "image_width": 1600,
  "image_height": 1200,
  "count": 2,
  "detections": [
    { "id": 101, "class_id": 0, "class_name": "Crack", "confidence": 0.92,
      "bbox": { "x": 120, "y": 340, "width": 360, "height": 270 } }
  ],
  "aeromemory": {
    "matched_count": 1,
    "new_count": 1,
    "comparisons": [
      { "defect_id": "DEF-010", "defect_type": "Crack",
        "state": "increased", "severity": "High",
        "match_confidence": 0.87 },
      { "defect_id": "DEF-011", "defect_type": "Corrosion",
        "state": "new", "severity": "Medium",
        "match_confidence": 0.0 }
    ]
  }
}
```
Errors: 404 unknown inspection · 400 bad/empty/unreadable image or unsupported format · 500 processing failure (rolled back).

**G — `GET /api/inspections/{id}/latest-result`** → same shape as F, plus:
```json
{ "has_result": true, … }
```
No image yet → `{ "has_result": false, "message": "No inspection image uploaded yet…" }` (not an error — mobile shows "waiting" state). Poll every ~2 s from the dashboard.

**H — `POST /api/decisions/{detection_id}`** →
```json
{
  "id": 7,
  "detection_id": 101,
  "severity": "High",
  "progression_status": "New / Baseline",
  "recommended_action": "…deterministic maintenance recommendation…",
  "reasoning": "…rule-based explanation…"
}
```
Errors: 404 unknown detection · 409 decision already exists (records are immutable — read the existing one instead of re-POSTing).

### 3.3 Enum / string contracts (display EXACTLY these — never translate in the UI)

| Field | Possible values (exact strings) |
|---|---|
| `class_id` / `class_name` | `0` Crack · `1` Corrosion · `2` Dent · `3` Missing Fastener (map by **ID**, never by string) |
| AeroMemory `state` (comparisons) | `new` · `stable` · `increased` · `decreased` · `resolved` |
| TrackedDefect `status` | `New` · `Monitored` · `Progressing` · `Repaired` · `Closed` |
| `severity` | `Low` · `Medium` · `High` · `Critical` |
| Inspection `status` | `completed` (v1; extend later) |

UI badge mapping suggestion: `new`→"NEW DEFECT" (info), `stable`→"STABLE" (neutral), `increased`→"PROGRESSING" (attention), `decreased`→"IMPROVING" (positive), `resolved`→"REPAIRED" (positive), no row → "NO HISTORICAL MATCH" (muted).

### 3.4 Verified model facts (safe to hardcode in the Model Performance screen copy)

- Model: `aerointel_v1` · YOLO11s · ONNX · imgsz 640 · exported 2026-09-24
- Test split (853 images): Precision **0.769** · Recall **0.575** · mAP50 **0.613** · mAP50-95 **0.405**
- Per class (P / R / mAP50): Crack 0.757/0.619/0.654 · Corrosion 0.565/0.213/0.233 · Dent 0.913/0.861/0.887 · Missing Fastener 0.839/0.607/0.677
- CPU latency (60 images): p50 **284.5 ms** · p95 **415 ms**
- Dataset: 8,525 images · 15,252 annotations · split 6,820 / 852 / 853

### 3.5 Known data-shape discrepancies (frontend dev must reconcile)

1. **bbox format:** the real backend returns `{x, y, width, height}` (top-left + size). The pre-backend `mockApi.js` fixtures use `{x1, y1, x2, y2}`. When binding to the real API, convert once in the service layer: `x2 = x + width`, `y2 = y + height` (or update the mock to match).
2. **Upload field name:** real endpoints take the file as form field **`file`**; `mockApi.js`'s "GOING LIVE" template says `image`. Use `file`.
3. **Health shape:** real `/health` returns `{status, database}`, not `{status, model_loaded}` — bind the Settings status card to the real shape.
4. **Metrics source:** there is no `GET /api/metrics` endpoint in the backend yet — the numbers in §3.4 come from `logs/eval_aerointel_v1_yolo11s_test.json` and `logs/latency_aerointel_v1_yolo11s.json`. Serve them statically or add the endpoint later.

### 3.6 Golden rules

1. **Frontend visualizes backend intelligence, never recomputes it.** Progression state, matching, severity, decision support: computed by FastAPI/AeroMemory — React displays.
2. **Never fabricate mm values.** Backend v1 has no physical calibration → show pixel deltas; if a calibration exists later, the backend will send it.
3. Boxes are drawn client-side by scaling bbox coords: `left = x * display_w / image_width` (image dims come in the response).
4. The confidence slider on Result is a **client-side filter** of returned detections — do not re-call the API on slider change.
5. Decision-support wording is fixed: *"AI result is decision support only. Final decision must be made by a qualified maintenance engineer."* Never "aircraft unsafe/approved".

---

## 4. After Stitch export — wiring notes for the frontend dev

1. Bind screens to `mockApi.js` first (field names align with §3; see §3.5 for the 3 shape fixes), then swap `mockApi` → real `api` with one import change (template at the bottom of `mockApi.js`).
2. Endpoints already live and tested: F (upload pipeline) and G (polling) power the entire New Inspection → Result → AeroMemory loop; B powers the System Status card; E fills Dashboard/History tables; H fills the Decision Support card.
3. **3D hero:** use `frontend/public/models/G4_LARC_AIR_0824.glb` with three.js / `@react-three/fiber` — auto-rotate + OrbitControls (damping on, no zoom UI), gentle vertical float, soft shadow. `frontend/public/videos/aircraft.mp4` is the fallback hero background.
4. Mobile capture keeps the native `<input type="file" accept="image/*" capture="environment">` bridge (see `REALTIME_IMAGE_CAPTURE.md`) — phones POST to the same endpoint F.
5. Full functional spec (every page, state, transition): `docs/FRONTEND_PRODUCT_SPEC.md`.
