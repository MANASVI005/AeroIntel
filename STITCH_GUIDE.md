# AeroIntel — Stitch Prompts (copy-paste file)

**This is the ONLY file you need open while working in Stitch.** Give Stitch: ① the prompts below, ② the matching Canva image attached to each page. That's all.

**Do NOT paste `mockApi.js` into Stitch** — it's data-layer code for the frontend developer, used after the Stitch code is exported (see footer).

**How to run (3 steps):**
1. Paste the **Master prompt** (§1) as the first message — no image attached.
2. For each page in the order below: **attach that page's Canva image** + paste its prompt.
3. Export the code → hand to the frontend dev with `mockApi.js`.

---

## 1. Master prompt — paste ONCE first (no image)

```
We are designing "AeroIntel", an AI-powered aircraft damage inspection web app.
App type: responsive web dashboard with a fixed left sidebar and top bar.
Global layout for every screen: left sidebar (logo "AeroIntel" with a paper-plane
mark, nav items: Dashboard, New Inspection, Inspection History, AeroMemory,
Reports, Model Performance, Settings; footer shows version chip "v1.0.0" and a
small status dot), top bar (search field, notification bell, user avatar chip).
Content area: white rounded cards on a very light blue-gray canvas, soft shadows,
8-pt spacing grid, Inter-style UI font, tabular numerals for metrics.
Status colors: green = online/completed, amber = pending/loading, red = error.
Damage-class color coding used everywhere (chips, table rows, legend, chart bars):
crack = red, corrosion = orange, dent = yellow, missing_fastener = purple.
Tone: clean aviation-industrial SaaS, data-dense but breathable.
Match the theme of the reference images I will attach to the next messages.
```

---

## 2. Page prompts — paste in this order, each with its Canva image attached

### 2.1 New Inspection ▶ generate FIRST (core page)
📎 Attach: Canva image of New Inspection.
```
Screen: "New Inspection" — image upload and detection launch page.
Match the attached reference image for theme and layout.
Layout top-to-bottom:
1. Page header: H1 "New Inspection", subtitle "Capture an image, run AI detection.",
   primary button on the right.
2. Horizontal step indicator with 3 steps: Capture → Detect → Result
   (step 1 active).
3. Two-column card: LEFT = tabbed input panel with two tabs "Upload" (active,
   large dashed-border drag-and-drop zone with upload icon and text
   "Drop aircraft image here or browse — JPG/PNG, max 10 MB") and "Camera"
   (placeholder for live capture with a snap button). RIGHT = preview panel
   showing the selected image thumbnail, filename "wing_panel_sample.jpg",
   dimensions "1600 × 1200 px", size "2.4 MB".
4. Collapsible "Advanced settings" row with two labeled sliders:
   "Confidence threshold" value 0.40 and "IoU threshold" value 0.50.
5. Bottom: primary CTA button "Run Detection", secondary link "Reset".
Below the card: "Recent captures" strip with 4 small image thumbnails.
Also show the detecting state: same screen but the preview area covered by a
skeleton shimmer with a small spinner and text "Running detection…".
```

### 2.2 Inspection Result ▶ the hero page
📎 Attach: Canva image of Inspection Result.
```
Screen: "Inspection Result" — detection review page.
Match the attached reference image for theme and layout.
Layout: two columns.
LEFT (60%): image viewer card with an aircraft wing photo, overlaid bounding
boxes drawn in class colors (red crack, orange corrosion, yellow dent, purple
missing_fastener). Each box has a small label chip pinned to its top-left like
"dent · 91%" or "crack · 85%". Above the image: toggle buttons "Boxes" and
"Labels" (both on), and a badge "285 ms" showing inference_ms.
RIGHT (40%): "Detected Defects" list card. Each row: colored class chip, class
name (dent, crack, missing_fastener, corrosion), confidence as a percentage
with a thin horizontal bar, sorted highest first (91%, 85%, 78%, 66%, 55%).
One row at 31% is rendered dimmed with a "below threshold" tag.
Under the list: a "Confidence threshold" slider at 0.40 with caption
"Showing 5 of 6 detections".
Below the image: "Inspection Findings" table with columns
Defect Type | Confidence | Location | Status — rows matching the detections,
location shown as pixel sizes like "384 × 172 px", status pill "Open".
Footer actions: primary "New Inspection", secondary "Download annotated image".
```

### 2.3 Dashboard
📎 Attach: Canva image of Dashboard.
```
Screen: "Dashboard" — landing overview.
Match the attached reference image for theme and layout.
Top-to-bottom:
1. Header: H1 "Dashboard", subtitle "Overview of your aircraft inspections."
2. Row of 4 stat cards: "Inspections" (12, small up-arrow), "Defects detected"
   (27), "Model mAP50" (0.613), "Avg latency" (285 ms, green "fast" chip).
3. Wide CTA card: "Start a new inspection" text + primary button
   "New Inspection".
4. "Damage classes" legend card: 4 chips with class colors — crack, corrosion,
   dent, missing_fastener — each with a session count number.
5. "Model" card: rows "aerointel_v1 · yolo11-onnx · 640 px", "Exported
   2026-09-24", and a green status dot labeled "Service online".
```

### 2.4 Model Performance
📎 Attach: Canva image of Model Performance.
```
Screen: "Model Performance" — metrics dashboard.
Match the attached reference image for theme and layout.
1. Header: H1 "Model Performance", badge "aerointel_v1 · ONNX · 640 px".
2. KPI row of 5 cards: Precision 0.769, Recall 0.575, mAP50 0.613,
   mAP50-95 0.405, Latency "p50 285 ms · p95 415 ms".
3. "Per-class performance" table: columns Class | Precision | Recall | mAP50
   | mAP50-95; rows crack (0.757/0.619/0.654/0.447), corrosion
   (0.565/0.213/0.233/0.099), dent (0.913/0.861/0.887/0.688), missing_fastener
   (0.839/0.607/0.677/0.388). Keep the low corrosion row visible and neutral —
   no error styling.
4. Two chart cards side by side: bar chart "mAP50 by class" (4 bars in class
   colors), grouped bar chart "Precision vs Recall".
5. Bottom row: "Dataset" card (8,525 images · 15,252 annotations · split
   6,820/852/853) and a "Notes" card with the text "Metrics from the held-out
   test split (853 images). Corrosion is single-source data — targeted for v2."
```

### 2.5 Settings (v1 subset only)
📎 Attach: Canva image of Settings.
```
Screen: "Settings" — preferences page, two-column layout.
Match the attached reference image for theme and layout.
LEFT: settings nav list (Preferences active, Aircraft profile, Storage,
Notifications — last three show a small "Phase 2" tag and are disabled).
RIGHT: "Preferences" card with:
- "Default confidence threshold" slider 0.40
- Toggle "Show box labels by default" (on)
- Segmented control "Default input tab": Upload | Camera
- "Reset to defaults" ghost button
Below: read-only "Model info" card (aerointel_v1, yolo11-onnx, 640 px,
exported 2026-09-24) and a service status row with green dot.
```

### 2.6 Inspection History (Phase 2 — design only)
📎 Attach: Canva image of Inspection History.
```
Screen: "Inspection History" — searchable records table (Phase 2 feature).
Match the attached reference image for theme and layout.
1. Header + filter bar: dropdowns Aircraft ID, Component, Defect Type (multi),
   Date range, Status; free-text search field.
2. Dense results table: columns Inspection ID | Date | Aircraft | Model |
   Component | Defects (class chips with counts) | Status pill | Actions (View
   link). 8 sample rows with varied statuses (Completed green, Pending amber,
   Flagged red).
3. Pagination footer: "25 per page", page 1 of 6.
Add a "Phase 2" tag chip next to the page title.
```

### 2.7 AeroMemory (Phase 2 — design only)
📎 Attach: Canva image of AeroMemory.
```
Screen: "AeroMemory" — historical comparison (Phase 2 feature).
Match the attached reference image for theme and layout.
1. Header + selector row of 3 dropdowns: Aircraft ID (VT-ALB), Aircraft Model
   (Boeing 737), Component (Wing).
2. Two image cards side by side labeled "PREVIOUS INSPECTION" and "CURRENT
   INSPECTION", each with a bounding box overlay in the same class colors, a
   "VS" badge between them.
3. "Detection Comparison" card: rows like "Crack — 11 mm → 18 mm" with a red
   "+7 mm" change chip.
4. "Historical Timeline" card: horizontal timeline with 4 clickable inspection
   ID nodes.
5. "Progression" badge card: "Worsening" in amber with a small trend icon.
Add a "Phase 2" tag chip next to the page title.
```

### 2.8 Inspection Report (Phase 2 — design only)
📎 Attach: Canva image of Inspection Report.
```
Screen: "Inspection Report" — printable one-inspection summary (Phase 2).
Match the attached reference image for theme and layout.
1. Report header block: Inspection ID INS-0143, Aircraft ID VT-ALB, Model
   Boeing 737, Component Wing, Date 2025-09-24, model badge
   "aerointel_v1 v1".
2. "Detected Defects" table: Type | Confidence | Location | Measurement.
3. Two image cards: original photo and annotated photo with boxes.
4. "Historical Comparison" section (collapsed placeholder).
5. "Decision Support" callout card with amber icon and text "Potential
   structural stress detected…", and an "Engineer Review" sign-off block.
6. Footer actions: "Generate PDF", "Export", "Print".
Add a "Phase 2" tag chip next to the page title.
```

---

## 3. After Stitch export — for the frontend dev (not for Stitch)

1. Add `mockApi.js` to the project (e.g. `src/services/`).
2. Re-export it as the app's `api` and bind screens to it — the binding
   table and state-testing commands are in the header comment of
   `mockApi.js` itself.
3. Field names in the generated UI (`class_name`, `confidence`,
   `inference_ms`, `bbox`) already match the mock — no renaming needed.
4. When the real backend exists, swap one import (template at the bottom
   of `mockApi.js`).
