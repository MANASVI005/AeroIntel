# AeroIntel: Aircraft Defect Detection & Longitudinal Memory System

AeroIntel is an intelligent aircraft structural inspection system that combines edge-optimized deep learning defect detection (YOLO11) with a longitudinal memory engine (**AeroMemory™**) to track defect evolution, compute growth metrics, and generate automated airworthiness decision support.

---

## 1. System Architecture

```text
       INSPECTION 1 (Previous)                   INSPECTION 2 (Current)
             [ Image ]                                 [ Image ]
                 │                                         │
                 ▼                                         ▼
         aerointel_v1.onnx                         aerointel_v1.onnx
      (YOLO11s Defect Detector)                 (YOLO11s Defect Detector)
                 │                                         │
       [ Defect Bounding Boxes ]                 [ Defect Bounding Boxes ]
                 └────────────────────┬────────────────────┘
                                      ▼
                                 AEROMEMORY™
                     (Homography Registration + Matcher)
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                  IoU Overlap /             Temporal State
                 Centroid Distance             Machine
                         │                         │
                         ▼                         ▼
               Measurement Delta (Δmm)       NEW / STABLE /
               & Growth Rate (%)             PROGRESSING / RESOLVED
                         │                         │
                         └────────────┬────────────┘
                                      ▼
                        Relational Storage & Timeline
                         (SQLite / PostgreSQL Schema)
                                      │
                                      ▼
                     Automated Decision Support Advisory
```

---

## 2. Core Capabilities

1. **Defect Detection (YOLO11s):**
   - 4 frozen classes: `0: crack`, `1: corrosion`, `2: dent`, `3: missing_fastener`.
   - Trained on official merged dataset (`datasets/master_dataset_ABC`, 8,525 images).
   - Exported model: `models/aerointel_v1.onnx` (mAP50 = 0.613 on held-out test split, CPU latency p50 = 284.5 ms).

2. **Longitudinal Memory (AeroMemory™):**
   - **Computer Vision Alignment:** OpenCV ORB feature matching with RANSAC homography estimation to align sequential inspection frames under viewpoint and camera angle shifts.
   - **Rule-Based Temporal Matching:** Spatio-temporal bipartite matching using IoU ($\ge 0.30$) and normalized centroid proximity ($< 15\%$ image width) alongside class consistency. No secondary ML model required.
   - **Progression State Classification:** Categorizes defect history into `NEW`, `STABLE`, `INCREASED` (Progressing), `DECREASED`, and `RESOLVED` (Repaired).
   - **Engineering Decision Support:** Deterministic, rule-based maintenance recommendations mapped directly to defect severity and dimensional growth rate.
   - **Lifecycle Persistence:** Relational repository pattern (`AeroMemoryRepository`, `SQLiteAeroMemoryRepository`) tracking defects across inspection timelines with repair status filtering.

---

## 3. Dataset Inventory & Roles

| Dataset | Scope & Contents | Role in AeroIntel | Status |
|---|---|---|---|
| **Dataset A, B, C** (`master_dataset_ABC`) | 8,525 aircraft surface images; 15,252 annotations across 4 classes. | Official training, validation, and held-out test set for YOLO11s. | Complete & Verified |
| **Dataset D** | Unseen real-world aircraft inspection images. | Held-out validation of YOLO11s model generalization. | Independent / Handled separately |
| **Dataset E** (`dataset_E_aeromemory`) | 200 aircraft histories, 1,200 sequential inspection PNGs with temporal ground truth (10 px/mm synthetic calibration). | Synthetic benchmark dataset for verifying AeroMemory state transitions, delta calculations, and DB persistence. | Complete & Verified (30/30 PASS) |

> [!NOTE]
> **Synthetic Benchmark Notice:** Dataset E fixtures are synthetic benchmark datasets with simulated defect geometries, progression steps, and repair events. These tests validate state-machine transitions, IoU/centroid matching, delta tracking, and database persistence logic. They do **not** establish certified production airworthiness or real-aircraft reliability, which requires physical NDT inspection calibration and Dataset D evaluation on unseen real-aircraft imagery.

---

## 4. Verification & Testing

### 4.1 Test Model Inference (YOLO11s ONNX)
Run inference on sample aircraft images using the exported ONNX model:
```bash
python tools/test_images.py --model models/aerointel_v1.onnx
```

### 4.2 Run AeroMemory Automated Verification on Dataset E
Executes strict defect-by-defect ground truth comparisons across key aircraft progression scenarios (`AI-001`, `AI-002`, `AI-003`, `AI-006`, `AI-019`):
```bash
python tools/test_aeromemory_on_dataset_e.py
```
*Returns exit code `0` on 100% pass, `1` on any mismatch or unexpected detection.*

### 4.3 Run AeroMemory Live Team Demonstration & Artifact Generation
Processes 4 representative MRO maintenance scenarios, outputs side-by-side visual comparison panels, and writes the formal engineering report:
```bash
python tools/run_aeromemory_team_demo.py
```
Generated evidence artifacts are saved in:
- `outputs/team_demo/CASE-1_AI-001_Inspection_Comparison.png` (Crack Progression)
- `outputs/team_demo/CASE-2_AI-003_Inspection_Comparison.png` (Stable Defect Surveillance)
- `outputs/team_demo/CASE-3_AI-006_Inspection_Comparison.png` (Maintenance Repair & Resolution)
- `outputs/team_demo/CASE-4_AI-019_Inspection_Comparison.png` (Multi-Defect Emergence)
- `outputs/team_demo/AEROMEMORY_TEAM_REPORT.md` (Full Engineering Report)

---

## 5. Repository Structure

```text
Aero/
├── aeromemory/                  # AeroMemory Core Engine
│   ├── models.py                # Domain entities (InspectionRecord, DefectRecord, ProgressionState)
│   ├── repository.py            # Repository interface & SQLite implementation
│   ├── registration.py          # OpenCV ORB + RANSAC homography alignment
│   ├── matcher.py               # Rule-based bipartite defect matcher
│   ├── comparator.py            # Measurement delta & growth rate calculation
│   ├── progression.py           # Progression state classifier & decision support
│   ├── severity.py              # Defect severity scoring
│   ├── service.py               # High-level AeroMemoryService facade
│   └── __init__.py
├── datasets/
│   ├── master_dataset_ABC/      # Merged YOLO training dataset (8,525 images)
│   └── dataset_E_aeromemory/    # Synthetic benchmark dataset (1,200 inspections)
├── docs/                        # Architecture, decisions, and integration specs
│   ├── DECISIONS.md             # Append-only architectural decision log (D-001 to D-019)
│   ├── PROGRESS.md              # Milestones and project changelog
│   └── TECHNICAL_INTEGRATIONS.md# Technical contracts and interface specifications
├── models/
│   ├── aerointel_v1.onnx        # Exported YOLO11s model
│   └── registry.json            # Model metadata and class mapping
├── outputs/
│   └── team_demo/               # Visual comparison artifacts and demonstration report
├── tools/                       # Testing, benchmarking, and dataset utilities
│   ├── test_aeromemory_on_dataset_e.py  # Strict verification test suite
│   ├── run_aeromemory_team_demo.py      # Demonstration runner and artifact generator
│   └── test_images.py                   # ONNX inference runner
├── README.md
├── PROGRESS.md
└── VERIFICATION_GUIDE.md
```