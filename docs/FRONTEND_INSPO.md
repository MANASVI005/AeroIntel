# AeroIntel — Frontend Inspiration Board

**Companion to:** `docs/UI_DESIGN_BRIEF.md` (page map + data slots). This file is the *visual* inspiration reference for designing the theme in Canva and building pages in Stitch. Pair them: Brief = *what*, Inspo = *how it feels*.

---

## 1. Vibe keywords (paste into Canva/Stitch mood boards)

> "Aviation hangar meets clean SaaS" — technical, trustworthy, calm, data-dense but breathable.

- ✈️ Avionics / cockpit instrumentation: crisp readouts, tabular numbers, status dots
- 🔍 Inspection-grade clarity: high contrast on data, neutral chrome around it
- 🧊 Clean SaaS dashboard: rounded cards, soft shadows, generous spacing

---

## 2. Products worth studying (and what to steal from each)

| Product | Steal this |
|---|---|
| **Linear** (linear.app) | dark navy chrome, keyboard-clean layout, pill badges, restrained color |
| **Vercel Dashboard** | status dots, deploy-card rhythm, mono details, empty/loading states |
| **Stripe Dashboard** | metric cards with delta arrows, tables that breathe, chart polish |
| **Grafana** | metrics-grid layout for Model Performance, per-series color legends |
| **Flightradar24 / ADS-B Exchange** | aviation data aesthetics: map/table toggle, aircraft metadata chips |
| **Roboflow (annotate & result views)** | bounding-box overlay UX, class-colored boxes, confidence labels on boxes |
| **Label Studio / CVAT** | box overlay patterns, zoom-pan on annotated images |
| **Ultralytics demo (docs.ultralytics.com)** | detection result cards: thumbnail + class + confidence rows |

Aviation-industrial concept searches (Dribbble/Behance tags): `aviation dashboard`, `aircraft inspection app`, `MRO software`, `hangar management`, `drone inspection dashboard`, `object detection ui`, `defect detection dashboard`, `computer vision results`.

---

## 3. Page-by-page inspo map (matches UI_DESIGN_BRIEF §2)

| Page | Mood reference | Key visual pattern |
|---|---|---|
| 01 Dashboard | Stripe + Vercel | 4 stat cards row → CTA card → legend strip |
| 02 New Inspection | mobile-check apps, upload heroes | huge dashed drop-zone, flow chips (Capture→Detect→Result) |
| 03 Inspection Result | Roboflow result view | image left w/ colored boxes + labels, right rail list w/ confidence bars |
| 04 History *(v2)* | Linear tables + Stripe filters | filter bar, zebra-free dense table, status pills |
| 05 AeroMemory *(v2)* | "compare" split-screen patterns | before/after slider, timeline dots |
| 06 Report *(v2)* | print-first docs | A4-ish card, sections, signature blocks |
| 07 Model Performance | Grafana / Tremor dashboards | KPI row, per-class bar chart, confusion matrix card |
| 08 Settings | Linear/Vercel settings | two-column: nav list left, form right, save bar |

---

## 4. Component inspo (design once, reuse)

- **Bounding box overlay:** 2px solid class color, class chip pinned top-left of box, confidence % inside chip; dimmed style for `confidence < 0.30`
- **Class chips:** 4 frozen colors — crack `#ef4444` · corrosion `#f97316` · dent `#eab308` · missing_fastener `#a855f7`
- **Confidence bar:** tiny horizontal bar inside detection list rows (0–100%)
- **Latency badge:** mono font pill, e.g. `285 ms`, green if < 1000 ms
- **Stat card:** label (small caps) + big tabular number + delta arrow
- **Status dot system:** green `online/completed` · amber `pending/loading` · red `offline/flagged`
- **Empty state:** thin-line illustration (plane silhouette), one sentence, one action
- **Loading:** skeleton shimmer on image + result list (detection takes ~300 ms CPU)

UI kit shortcuts for Stitch output styling: **shadcn/ui** (cards, tables, dialogs), **Tremor** (KPI/chart blocks), **Recharts** or **Chart.js** for the metrics charts, **react-webcam** for capture, **konva** or plain absolutely-positioned divs for box overlays.

---

## 5. Color & type tokens (freeze in Canva first)

```
Canvas        #F6F8FB   (light blue-gray)
Card          #FFFFFF
Sidebar       #0B1F3A   (deep navy)
Sidebar text  #E6EDF7
Primary CTA   #1D6FE0   (aviation blue)
Success       #16A34A   Warning #F59E0B   Danger #DC2626
Class colors  crack #ef4444 · corrosion #f97316 · dent #eab308 · missing_fastener #a855f7
Borders       #E3E8F0   (1px)
Shadow        0 1px 3px rgba(11,31,58,0.08)

Font UI       Inter (400/500/600/700)
Font numbers  tabular-nums (Inter feature) or JetBrains Mono for IDs/latency
Radius        xl (16px) cards · lg (12px) inputs · full pills
Spacing       8-pt grid
```

Dark-mode variant (optional, do after light locks): same hues, canvas `#0A0F1A`, cards `#111827`, borders `#1F2937`.

---

## 6. Do / Don't

- ✅ Draw boxes on the frontend from `bbox` coords (server returns JSON only)
- ✅ Show **test-split** metrics: mAP50 **0.613**, P 0.769, R 0.575 (never the val 0.623)
- ✅ Design every page's empty / loading / error / no-detections states
- ❌ Don't show server-annotated images (no such endpoint)
- ❌ Don't label the model "YOLOv8" — it's **YOLO11s** (`aerointel_v1`, ONNX, 640px)
- ❌ Don't invent numbers — Corrosion mAP50 0.233 stays visible and honest
- ❌ Don't wire v2 pages (History, AeroMemory, Reports) in v1 — tag them "Phase 2"

---

## 7. Footer / brand touches

- Logo: paper-plane / shield motif (navy + aviation blue)
- Tagline: **"AeroIntel · Smarter Inspections, Safer Skies"**
- Version chip in sidebar footer: `AI-Powered Aircraft Inspection · v1.0.0`
- Pipeline strip for About/landing: Capture → AI Detection → Storage → Comparison → Decision Support → Engineer Review → Report
