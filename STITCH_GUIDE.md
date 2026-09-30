# AeroIntel — Stitch Prompts (copy-paste file)

**This is the ONLY file you need open while working in Stitch.** Give Stitch: ① the prompts below, ② the reference image (sky-blue AeroIntel dashboard) attached where indicated. That's all.

**Do NOT paste `mockApi.js` into Stitch** — it's data-layer code for the frontend developer, used after the Stitch code is exported (see §4).

**How to run (3 steps):**
1. Paste the **Master prompt** (§1) as the first message — **attach the reference image** (the sky-blue landing/dashboard mock).
2. For each page in the order below: paste its prompt. Attach the reference image again on the first 2–3 screens so the theme locks in.
3. Export the code → hand to the frontend dev with `mockApi.js` (§4).

**Theme rule (important):** No colors, fonts or theme are hard-coded anywhere in these prompts. Stitch must derive the ENTIRE visual system from the attached reference image.

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

## 2. Page prompts — paste in this order

### 2.1 Landing ▶ generate FIRST (hero with 3D rotating aircraft)
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

## 3. Screen → navigation map (for you, not for Stitch)

```
Landing — Start Detection → New Inspection
Dashboard — View / alert / thumbnail → Inspection Result
Dashboard — Start New Inspection → New Inspection
New Inspection — Use Photo → Processing → Inspection Result
Inspection Result — Compare with History / View AeroMemory → AeroMemory
Inspection Result — Generate Report → Inspection Report
Inspection History — View → Inspection Result · Compare → AeroMemory
AeroMemory — timeline node → Inspection Result · Generate Report → Reports
Reports — View → Inspection Report — Generate PDF → local PDF
```

## 4. After Stitch export — for the frontend dev (not for Stitch)

1. Add `mockApi.js` to the project (e.g. `src/services/`) and bind screens to
   it — field names used in the prompts (`class_name`, `confidence`,
   `inference_ms`, `bbox`, AeroMemory states) match the mock and the real
   backend.
2. **DEMO_MODE:** until the backend is wired, run against demo data
   (`DEMO-AC-001`, `DEMO-INS-001`…). Swap `mockApi` → real `api` with ONE
   import change (template at the bottom of `mockApi.js`).
3. **Golden rule:** the frontend visualizes backend intelligence, never
   recomputes it. Detection, confidence, matching, progression state,
   historical comparison and decision support all arrive from FastAPI /
   AeroMemory — React only displays them. Never fabricate mm values: show
   pixel deltas unless the backend sends a calibration.
4. Real endpoints already live in `backend/`:
   `POST /api/inspections/{id}/images` (upload → detect → compare),
   `GET /api/inspections/{id}/latest-result` (2-second polling),
   `GET /api/health` (drives the Settings → System Status card).
5. The 3D hero model ships in the repo:
   `frontend/public/models/G4_LARC_AIR_0824.glb`. Wire it with
   three.js / `@react-three/fiber` (auto-rotate + OrbitControls, no zoom
   limits UI). `frontend/public/videos/aircraft.mp4` is available as a
   fallback hero background.
6. The full functional specification (every page, state, transition) is in
   `docs/FRONTEND_PRODUCT_SPEC.md`.
