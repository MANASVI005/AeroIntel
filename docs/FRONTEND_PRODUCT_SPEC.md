# AeroIntel Frontend — Complete Screen & Navigation Specification

> Functional source of truth for the frontend. The reference image (sky-blue AeroIntel landing/dashboard mock) is the **visual direction**; this document is the **functional specification**. Copy-paste prompts for Stitch live in `STITCH_GUIDE.md`.

**Final product message:** AI detects. AeroMemory compares. Decision Engine assists. Engineer decides.

---

## 1. Overall frontend structure

The frontend should feel like one complete aviation inspection application.

### Main navigation

The left sidebar remains visible on desktop:

```text
AeroIntel
Smart Inspection. Safer Skies.

Dashboard
New Inspection
Inspection History
AeroMemory
Reports
Model Performance
Settings
```

At the top: global search, notification bell, engineer profile. The currently selected page is highlighted in the sidebar.

## 2. Overall application flow

The most important flow:

```text
                DASHBOARD
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
New Inspection  History       AeroMemory
    │               │               │
    ▼               ▼               ▼
 Capture        View Result     Compare
    │               │               │
    ▼               │               │
AI Detection ──────┘               │
    │                               │
    ▼                               ▼
Inspection Result ◄──────── Historical Comparison
    │
    ├──► AeroMemory
    ├──► Generate Report
    └──► Engineer Review
```

The user should **not feel they are navigating disconnected pages**. Every inspection leads naturally to: **Capture → Detect → Result → Compare → Decision Support → Report**.

## 3. PAGE 01 — DASHBOARD

Landing page after opening AeroIntel. Header: "Dashboard — Overview of your aircraft inspections."

**Top summary cards (4):** Total Inspections (48), Defects Detected (27), Resolved (18), Pending (9). Values come from the backend later; demo data for now.

**Recent Inspections table:** Inspection ID | Aircraft | Model | Component | Date | Status | Defects | Action. Example row: INS-1042, VT-ALB, Boeing 737, Wing, 2025-09-14, Completed, 2, View. Clicking "View" → `/inspection/{id}` (Inspection Result).

**Defect Overview:** distribution of crack, corrosion, dent, missing_fastener (eventually real backend counts).

**Inspection Performance:** trend chart (date, inspections completed/pending). System usage, not model accuracy.

**Latest Alerts:** e.g. "⚠ New crack detected", "⚠ Defect progression detected", "✓ Defect marked repaired", "⚠ Missing fastener detected". Clicking an alert → the relevant Inspection Result.

**Recent Inspection Images:** small thumbnails → clicking opens Inspection Result.

**Quick Actions:** "Start New Inspection" → New Inspection; "Upload Inspection Image" → New Inspection; "View Reports" → Reports.

## 4. PAGE 02 — NEW INSPECTION

Header: "New Inspection — Capture image, run AI detection and store in AeroMemory."

**Step 1 — Inspection information form:** Inspection ID, Aircraft ID, Aircraft Model, Component, Panel/Area, Engineer/Technician. Example: INS-1043, VT-ALB, Boeing 737, Wing, Left Wing Panel. "Continue" activates the capture area.

**Progress indicator:** Capture → Save → Detect → Compare History.

**Camera section:** laptop shows "Upload Image"; phone shows "Capture Image" (native `<input capture="environment">` flow is preserved — see `REALTIME_IMAGE_CAPTURE.md`). Phone flow: New Inspection → Capture Image → native camera → photo captured → Preview.

## 5. PHOTO PREVIEW

After capturing: large aircraft image with `[ Retake Photo ] [ Use Photo ]`.
- Retake → back to camera.
- Use Photo → `POST /api/inspections/{id}/images` → Processing.

## 6. PROCESSING STATE

Do NOT jump straight to the result page. Show:

```text
Processing Inspection
✓ Image uploaded
✓ Image stored
⟳ Running AI detection
○ Comparing with AeroMemory
○ Preparing result
```

## 7. DETECTION COMPLETE

Backend finishes: Image → YOLO → AeroMemory → Result. Frontend navigates automatically to `/inspection/{id}/result`.

## 8. PAGE 03 — INSPECTION RESULT

Header: "Inspection Result — AI-detected defects, historical findings and decision support."

**Main image (left, ~60%):** large inspection photo with actual YOLO bounding boxes overlaid. Boxes come from the backend — the frontend must NOT generate them.

**Detected Defects panel (right):** class chip + name + confidence (e.g. Crack 92%, Corrosion 87%, Dent 76%, Missing Fastener 81%). Only show defects that actually exist. If none: "No active defects detected."

**Inspection Findings table:** Defect | Confidence | Location | Status (e.g. Crack, 92%, Wing – Front Left, Open).

**AeroMemory Analysis:** what happened versus history — states: `NEW DEFECT`, `EXISTING DEFECT`, `PROGRESSING`, `STABLE`, `REPAIRED`, `DISAPPEARED`, `NO HISTORICAL MATCH`.

**Decision Support:** "Potential structural concern detected. Engineer Review Required."

**Hard rule:** the frontend must never say "Aircraft unsafe" or "Aircraft approved". Always: *"AI result is decision support only. Final decision must be made by a qualified maintenance engineer."*

**Buttons:** Compare with History → AeroMemory · Generate Report → Inspection Report · View AeroMemory → AeroMemory · Save Inspection → History.

## 9. PAGE 04 — INSPECTION HISTORY

Header: "Inspection History — View and manage all inspection records."

**Filters:** Aircraft ID, Component, Defect Type, Date Range, Status + "Search inspections…".

**Table:** Inspection ID | Aircraft ID | Aircraft Model | Component | Date | Defects | Status | Action.

- View → Inspection Result.
- Compare → AeroMemory (selected inspection becomes the current one).

## 10. PAGE 05 — AEROMEMORY

The key differentiator. Header: "AeroMemory — Compare current inspections with historical aircraft records."

**Selection:** Aircraft ID, Aircraft Model, Component, then Previous Inspection + Current Inspection.

**Side-by-side comparison:** PREVIOUS image | VS | CURRENT image, bounding boxes on both.

**Detection Comparison:** e.g. Crack → "Change: Progressing"; "Previous measurement: 11 mm → Current: 18 mm, Change: +7 mm" — **only if real physical calibration exists**. Otherwise: "Pixel change: +X px — Physical measurement unavailable." **Never fabricate mm values.**

**Historical Timeline:** vertical/horizontal nodes per inspection (INS-1005 Aug 26 · INS-1008 Sep 10 · INS-1012 Sep 14 · INS-1043 Sep 24), each labeled Stable / Existing / Progressing / Repaired. Clicking a node opens that inspection.

**Progression Analysis:** current state (Stable / Improving / Progressing / Repaired) comes from AeroMemory. **Do not implement the calculation in React — backend calculates, frontend visualizes.**

**Actions:** Compare · Overlay (previous image + current boxes) · View Timeline · Generate Report.

## 11. PAGE 06 — REPORTS / INSPECTION REPORT

Sidebar label: "Reports"; inside: "Inspection Report".

**Report list:** Inspection ID | Aircraft | Date | Status | Report Status | Action (View / Generate / Download).

**Report detail:** metadata block (Inspection ID, Aircraft ID, Model, Component, Inspector, Date, Model Version) → Detected defects table (Type, Confidence, Location, Measurement, Status) → Historical comparison (Previous, Current, Change, AeroMemory State) → Decision support ("Potential structural concern detected. Maintenance action may require review.") → Engineer Review sign-off ("Final decision must be made by a qualified maintenance engineer.").

**Report buttons:** Generate PDF · Export · Print. Flow: Frontend → `POST /report` → FastAPI → ReportLab → PDF → download/view. PDF is generated locally.

## 12. PAGE 07 — MODEL PERFORMANCE

About the YOLO model — not inspection usage. Header: "Model Performance — Performance metrics and model details."

**Model information:** Model, Version (`aerointel_v1`), Training Dataset, Last Evaluated, Deployment Status. Use actual backend info.

**Metric cards:** Precision, Recall, mAP50, mAP50-95, Inference Time. **Rule — don't copy screenshot numbers:** without real evaluation data show "Not evaluated". Inference time can be measured from actual local inference.

**Per-class chart:** Precision/Recall for crack, corrosion, dent, missing_fastener (real data only).

**Confusion matrix:** display if backend provides it; otherwise "Confusion matrix unavailable. Model evaluation has not been performed."

**Detection distribution:** clearly label it as *detections recorded in operational inspections* — do not confuse with model evaluation performance.

## 13. PAGE 08 — SETTINGS

Header: "Settings — Manage your preferences and application configuration."

- **Profile:** Name, Role (Aviation Engineer), Email.
- **Aircraft:** Aircraft ID, Model, Default Component.
- **Inspection:** Image Quality, Detection Confidence Threshold (editable only with confirmation — affects production detection), Auto-save to AeroMemory.
- **AeroMemory:** Storage (e.g. 2.4 GB / 10 GB), Historical Retention (12 months), Comparison Settings, Auto Compare (ON). Real values from backend/config.
- **Model:** Model Version, Model Path, Detection Threshold, Inference Configuration. Do not allow casual replacement of the production model.
- **Application:** Notifications, Theme, Language, Offline Mode, Local Server Status. For this project: Network Mode LOCAL, Internet Not Required.

**System Status (global, especially Settings):** Backend Connected · PostgreSQL Connected · YOLO Model Loaded · AeroMemory Ready · Storage Available · Network Local · Internet Not Required. Values from `GET /api/health` — never hardcoded.

## 14. GLOBAL SEARCH & NOTIFICATIONS

**Search** (top bar) over Inspection ID, Aircraft ID, Component, Defect Type. Typing "INS-1042" → dropdown "Inspection INS-1042 · Boeing 737 · Wing · 2 defects · Completed" → click opens Inspection Result.

**Notifications** (bell): dropdown with "New crack detected — INS-1043", "Defect progression detected — INS-1038", "Inspection completed — INS-1040". Click → relevant Inspection Result.

## 15. GLOBAL TRANSITIONS (exact map)

```text
DASHBOARD
├── Start New Inspection → NEW INSPECTION → Capture → Preview → Upload → Processing → INSPECTION RESULT
├── Recent Inspection → View → INSPECTION RESULT
├── Alert → INSPECTION RESULT
├── Recent Image → INSPECTION RESULT
└── Reports → REPORTS

NEW INSPECTION: details → Capture/Upload → Preview → Upload → Processing → AI Detection → AeroMemory Comparison → INSPECTION RESULT

INSPECTION RESULT
├── Compare with History → AEROMEMORY
├── View AeroMemory → AEROMEMORY
├── Generate Report → INSPECTION REPORT
└── Save Inspection → INSPECTION HISTORY

INSPECTION HISTORY: View → RESULT · Compare → AEROMEMORY · Report → REPORT

AEROMEMORY: select aircraft/component/inspections → side-by-side → detection comparison → timeline → progression → Generate Report → REPORT

REPORTS: select inspection → INSPECTION REPORT → Generate PDF → local PDF
```

## 16. MOBILE FLOW (`/mobile`)

The phone must NOT show the entire desktop app. Simplified flow:

```text
AeroIntel Mobile — New Inspection
Aircraft: VT-ALB · Component: Wing
[ Capture Image ] → Camera → Preview → [ Retake ] [ Use Photo ]
→ Uploading… → AI Detecting… → Detection Complete
→ Inspection Complete: 2 Defects Detected (Crack 92%, Corrosion 87%)
→ [ View Full Result ]
```

"View Full Result" can open the full dashboard/result interface.

## 17. REQUIRED UI STATES (every page)

| State | Copy |
|---|---|
| Loading | "Loading inspection…" |
| Empty | "No inspections available." |
| No defects | "No active defects detected." |
| Processing | "AI detection in progress…" |
| Error | "Unable to load inspection. Please check the local AeroIntel server." |
| Backend unavailable | "AeroIntel backend is unavailable. Check that the laptop server is running and connected to the same local network." |
| Success | "Inspection completed successfully." |

## 18. DEMO MODE

Don't wait for the finished backend. Build against the expected API structure using `DEMO_MODE` data (`DEMO-AC-001`, `DEMO-INS-001`, `DEMO-INS-002`), clearly kept as demo data. Later: DEMO API → REAL API with **no component rewrites** — only the data source changes (`mockApi.js` swap).

## 19. Component structure

```text
frontend/src/
├── components/
│   ├── layout/      # Sidebar, Topbar, PageHeader, SystemStatus
│   ├── dashboard/
│   ├── inspection/
│   ├── aeromemory/
│   ├── reports/
│   ├── model/
│   └── common/
├── pages/           # Dashboard, NewInspection, InspectionResult,
│                    # InspectionHistory, AeroMemory, Reports,
│                    # InspectionReport, ModelPerformance, Settings,
│                    # MobileCapture
├── services/        # api, inspectionApi, aeromemoryApi, reportApi, healthApi
├── hooks/
├── types/
└── routes/
```

Avoid one giant `App.jsx`.

## 20. Golden rule

> **Frontend should visualize backend intelligence, not recreate it.**

React must not calculate "Progressing" — FastAPI/AeroMemory computes the state, React displays it. Same for detection, confidence, matching, progression, repaired state, historical comparison, decision support, and model metrics. The frontend is the **interface**, not the AI engine.

## 21. Final user journey

```text
Dashboard → Start Inspection → New Inspection → Capture/Upload → Preview
→ Upload → AI Detection → AeroMemory Compare → Inspection Result
   ├── Compare → AeroMemory → Historical Comparison → Progression Analysis
   │                → Decision Support → Engineer Review
   ├── Report → PDF Report
   └── History → All Records
```
