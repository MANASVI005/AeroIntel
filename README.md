# AeroIntel: Air-Gapped Intelligent Aircraft Inspection System

AeroIntel is an offline, edge-capable aircraft structural inspection and defect tracking system designed for air-gapped hangar environments. It combines high-speed local YOLO ONNX object detection with **AeroMemory**, a spatiotemporal defect lifecycle tracking engine that matches physical defects across repeated inspections over time.

---

## 🌟 Key Capabilities

- **Air-Gapped & Local**: Operates completely offline with zero internet, AWS, or cloud API dependencies.
- **Real-Time Local YOLO ONNX Inference**: Performs edge object detection using custom-trained YOLO ONNX models (`aerointel_v1.onnx`) running on ONNX Runtime CPU.
- **AeroMemory Spatiotemporal Tracking**:
  - Distinguishes persistent historical defects from newly emerging defects.
  - Monitors geometric defect progression (growth/shrinkage) across inspection series.
  - Handles disappeared, repaired, or unobserved defects cleanly.
  - Guarantees PostgreSQL transactional safety (ACID) with zero orphaned records or state corruption.
- **Technician Mobile Client**: Technician phone capture client connected over local Wi-Fi LAN to the laptop inspection hub.
- **Live Laptop Inspection Dashboard**: Real-time React inspection workspace with automated result polling and interactive bounding box displays.

---

## 🏗 System Architecture

```text
                  AIR-GAPPED LOCAL HANGAR LAN (Wi-Fi / Hotspot)
                                       
     📱 TECHNICIAN MOBILE CLIENT              💻 AEROINTEL EDGE LAPTOP HUB
   ┌─────────────────────────────┐         ┌─────────────────────────────────┐
   │ Native Mobile Camera / Input│         │  Vite React Dashboard (Port 3000)│
   │ Photo Capture               │         └────────────────┬────────────────┘
   └──────────────┬──────────────┘                          │
                  │ POST /api/inspections/{id}/images       │ GET /api/inspections/{id}/latest-result
                  └────────────────────┐                    │ (Polling every 2s)
                                       ▼                    ▼
                                 ┌──────────────────────────────────────────┐
                                 │          FastAPI Backend Server          │
                                 │               (Port 8000)                │
                                 └────────────────────┬─────────────────────┘
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
         ┌───────────────────────────┐                                 ┌───────────────────────────┐
         │   AeroIntel YOLO Service  │                                 │    AeroMemory Engine      │
         │  (aerointel_v1.onnx)     │                                 │ (Spatiotemporal Matcher)  │
         └─────────────┬─────────────┘                                 └─────────────┬─────────────┘
                       │                                                             │
                       └──────────────────────────────┬──────────────────────────────┘
                                                      ▼
                                       ┌────────────────────────────┐
                                       │   Local PostgreSQL Engine  │
                                       │ (Detections, Inspections,  │
                                       │  Tracked Defect Memory)    │
                                       └────────────────────────────┘
```

---

## 🚀 AeroMemory Defect Lifecycle Engine

AeroMemory is the core intelligence component of AeroIntel. It maintains continuous state for every physical defect on an aircraft panel across all inspections.

### Verified Validation Phases

- **Phase 1 — Transaction Safety**: Verified atomic rollbacks on network/inference faults, single-transaction commits for inspection image processing, and zero dangling DB records.
- **Phase 2 — New Defect Detection**: Proves that AeroMemory correctly distinguishes between existing tracked defects persisting into a new inspection and genuinely new physical defects appearing for the first time.
- **Phase 3 — Defect Progression**: Validates spatiotemporal matching when a defect's observed bounding box grows or changes geometry between inspections.
- **Phase 4 — Disappeared / Unmatched Defect Management**: Ensures that when a defect is not detected in a subsequent inspection (repaired or unobserved), historical records remain intact without creating false duplicates or deleting historical observations.

---

## 🛠 Technology Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy, PostgreSQL, OpenCV, ONNX Runtime (`onnxruntime`), Ultralytics YOLO.
- **Frontend**: React 18, TypeScript, Vite, Lucide Icons, React Router.
- **Machine Learning**: Custom YOLO object detection (`aerointel_v1.onnx`) supporting 4 key defect classes:
  - `0`: Crack
  - `1`: Corrosion
  - `2`: Dent
  - `3`: Missing Fastener

---

## 📁 Repository Structure

```text
AeroIntel/
├── aeromemory/              # Core AeroMemory matching & progression engine
│   ├── matcher.py           # IoU, centroid, and class-consistency matcher
│   ├── comparator.py        # Spatiotemporal defect progression comparator
│   └── service.py           # AeroMemory orchestration service
├── backend/                 # FastAPI REST API server
│   └── app/
│       ├── api/             # Inspection & image REST endpoints
│       ├── db/              # PostgreSQL database session configuration
│       ├── models/          # SQLAlchemy ORM models (Inspection, Detection, TrackedDefect)
│       └── services/        # AeroIntel YOLO service & AeroMemory Postgres repository
├── frontend/                # Vite + React TypeScript user interface
│   └── src/
│       ├── pages/
│       │   ├── DashboardPlaceholder.tsx  # Laptop Engineer Inspection Dashboard
│       │   └── MobileCapturePage.tsx     # Technician Mobile Capture Page
│       └── App.tsx
├── models/                  # Production ONNX models & registry
│   └── aerointel_v1.onnx    # Edge ONNX YOLO detection model
├── tools/                   # Validation, testing & diagnostic toolset
│   ├── test_phase1_transactions.py
│   ├── test_phase2_new_defect.py
│   ├── test_phase3_progression.py
│   ├── test_phase4_disappeared.py
│   └── diagnose_yolo_phone.py
├── REALTIME_IMAGE_CAPTURE.md # Detailed guide for mobile image capture & real-time workflow
├── PROGRESS.md              # Project status, dataset splits & validation milestones
└── README.md                # Project sitemap & architectural overview
```

---

## 🚦 Quick Start Guide

### 1. Backend Setup (Laptop)
```bash
# Install dependencies
pip install -r requirements.txt

# Launch local FastAPI server on LAN IP
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup (Laptop & Mobile LAN)
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```
- **Laptop Workspace**: Open `http://localhost:3000` (or `http://<LAPTOP_IP>:3000`)
- **Technician Mobile Client**: Open `http://<LAPTOP_IP>:3000/mobile` on phone connected to local Wi-Fi.

---

## 📖 Documentation Links

- [REALTIME_IMAGE_CAPTURE.md](file:///D:/AeroIntel/REALTIME_IMAGE_CAPTURE.md) — Real-time mobile capture workflow, camera input specs, resolution downscaling analysis, and framing best practices.
- [PROGRESS.md](file:///D:/AeroIntel/PROGRESS.md) — Complete history of dataset creation, AeroMemory validation phases, and testing reports.