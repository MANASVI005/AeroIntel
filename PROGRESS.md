# AeroIntel — Project Progress

## 1. Current Status

- **Dataset Preparation (A+B+C):** COMPLETE (8,525 images, 15,252 annotations)
- **YOLO11s Model Training:** COMPLETE (100 epochs, mAP50 = 0.613 on test split)
- **Model Export:** COMPLETE (`models/aerointel_v1.onnx` ready for CPU/edge inference)
- **AeroMemory™ Engine:** COMPLETE & FULLY IMPLEMENTED
- **Dataset E Automated Verification:** 30/30 INSPECTIONS PASS (`tools/test_aeromemory_on_dataset_e.py`, Exit Code 0)
- **Team Demonstration & Visual Artifacts:** COMPLETE (`outputs/team_demo/`, 4 comparative panels + report)
- **FastAPI Backend:** COMPLETE (`backend/` — detection, inspection, decision APIs, `latest-result` polling)
- **Frontend Scaffold:** COMPLETE (`frontend/` — Vite + React 18 + TS, dashboard + mobile capture pages)
- **Branch Integration:** COMPLETE — `model-training-and-eval`, `AEROMEMORY`, and the unique parts of `feature/aeromemory` are consolidated on `main`

---

## 2. AeroMemory™ Implementation & Hardening

The AeroMemory module (`aeromemory/`) implements rule-based defect tracking across inspection cycles without introducing a secondary machine learning model:

### 2.1 Core Modules
- **`aeromemory.models`:** Domain records (`Aircraft`, `Component`, `DefectRecord`, `ObservationRecord`, `InspectionRecord`, `ProgressionState`, `DefectComparison`).
- **`aeromemory.repository`:** Relational abstraction (`AeroMemoryRepository` ABC) and persistent SQLite implementation (`SQLiteAeroMemoryRepository`).
- **`aeromemory.registration`:** OpenCV ORB keypoint detector + RANSAC homography estimation (`compute_alignment`, `transform_bbox`) to align image pairs under camera shift.
- **`aeromemory.matcher`:** Bipartite matching combining transformed bounding box IoU ($\ge 0.30$) and normalized centroid Euclidean distance ($< 15\%$ image width).
- **`aeromemory.comparator`:** Measurement delta ($\Delta\text{mm}$ / $\Delta\text{px}^2$) and percentage growth rate calculation.
- **`aeromemory.progression`:** State-machine classification into `NEW`, `STABLE`, `INCREASED` (Progressing), `DECREASED`, and `RESOLVED` (Repaired), generating deterministic maintenance decision support.
- **`aeromemory.severity`:** Dynamic defect severity categorization (`Low`, `Medium`, `High`, `Critical`).
- **`aeromemory.service`:** `AeroMemoryService.process_inspection()` orchestrating the end-to-end inspection lifecycle.

### 2.2 Key Fixes & Verification Hardening
1. **AI-006 Duplicate Resolution Bug Resolved:**
   - Previously, `get_active_defects` filtered only `status != 'Closed'`. When defect `D01` was marked `'Repaired'` at `INS-005`, `INS-006` re-queried it as active, found no detection, and reported it as `RESOLVED` again.
   - Updated query to `status NOT IN ('Closed', 'Repaired')`. At `INS-006`, active defects evaluate to empty, resulting in 0 comparisons and matching `comparison_ground_truth: []`.
2. **Dataset E Verification Harness Hardened:**
   - Updated `tools/test_aeromemory_on_dataset_e.py` to compare exact dictionary mappings `{defect_id: state}` defect-by-defect.
   - Accurately checks multi-defect panels (e.g. `AI-019`) and empty ground-truth inspections (e.g. `AI-006` `INS-006`).
   - Returns non-zero exit code (`sys.exit(1)`) on any mismatch and `sys.exit(0)` on 100% pass across all 30/30 inspections.
   - Runs each aircraft against an isolated SQLite database to eliminate `defect_id` cross-contamination.
3. **Synthetic Benchmark Boundary Declared:**
   - Prominently documented that Dataset E fixtures are synthetic benchmark datasets designed for algorithmic state-machine verification, not for physical aircraft airworthiness certification. Dataset D remains reserved for unseen real-aircraft validation.

### 2.3 Phase 1–4 Validation Status

| Phase | Milestone Description | Status | Verification Tool |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Transaction Safety & Atomicity** — Single-transaction commits for image upload, detection insertion, and AeroMemory state update. Zero dangling records on rollback. | **PASS** | `tools/test_phase1_transactions.py` |
| **Phase 2** | **New Defect Detection** — Distinguishes persisting historical defects from newly emerging physical defects on aircraft panels. | **PASS** | `tools/test_phase2_new_defect.py` |
| **Phase 3** | **Defect Progression** — Matches physical defects across sequential inspections when bounding boxes grow or alter geometry. | **PASS** | `tools/test_phase3_progression.py` |
| **Phase 4** | **Disappeared / Unmatched Defects** — Preserves historical observations when a defect is unobserved or repaired in a subsequent inspection without creating duplicate records. | **PASS** | `tools/test_phase4_disappeared.py` |

> Phases 1 and 3 re-verified locally on 2026-09-30 against a fresh SQLite database (exit 0). Phases 2 and 4 depend on Git LFS fixtures (`datasets/dataset_B/`) and a pre-populated dev database respectively, and require the full dataset checkout to run.

---

## 3. YOLO Training Dataset (master_dataset_ABC)

- Total images: 8,525 (Train: 6,820 | Valid: 852 | Test: 853)
- Total annotations: 15,252
- Classes (frozen contract):
  - `0 = Crack` (5,192 annotations / 3,791 images)
  - `1 = Corrosion` (2,597 annotations / 1,148 images)
  - `2 = Dent` (3,869 annotations / 2,588 images)
  - `3 = Missing Fastener` (3,594 annotations / 1,571 images)

### Dataset Sources
- **Dataset A:** Aircraft Corrosion YOLO (1,148 images, 2,597 annotations).
- **Dataset B:** Aircraft Skin Defects (1,078 images, 1,630 annotations).
- **Dataset C:** Aircraft Defect Detection (6,299 images, 11,025 annotations; 715 polygon annotations converted to bounding boxes).
- *Datasets D, E, and F were NOT used for YOLO training.*

### Independent Dataset Validation

Independent validation passed with 0 errors:
- Dataset structure: PASS
- Image/label pairing: PASS
- Orphan/missing labels: PASS
- YOLO 5-field labels: PASS
- Valid class IDs & normalized coordinates: PASS
- Zero cross-split or near-duplicate leakage: PASS

---

## 4. Model Training & Test Evaluation Metrics

Trained on Google Colab (T4 GPU, 100 epochs, imgsz 640, batch 16):
- **Test-split mAP50:** `0.613` (exceeds project target $\ge 0.60$)
- **Test-split mAP50-95:** `0.405`
- **Test-split Precision:** `0.769`
- **Test-split Recall:** `0.575`
- **Per-class mAP50:**
  - `Dent`: 0.887
  - `Missing Fastener`: 0.677
  - `Crack`: 0.654
  - `Corrosion`: 0.233
- **CPU Latency (p50):** `284.5 ms` (target $< 1,000\text{ ms}$, PASS)

---

## 5. Live Demonstration & Verification Evidence

All 4 maintenance scenarios execute deterministically in `tools/run_aeromemory_team_demo.py`:
- `CASE-1` (AI-001): Fatigue Crack Progression (+1.5 mm / +12.5% per cycle, `PROGRESSING`)
- `CASE-2` (AI-003): Stable Defect Surveillance (0.0 mm change, `STABLE`, `MONITORED`)
- `CASE-3` (AI-006): Maintenance Repair & Resolution (Defect repaired at INS-005 `RESOLVED`; 0 defects at INS-006)
- `CASE-4` (AI-019): Multi-Defect Panel (Simultaneous tracking of Crack growth, Stable corrosion, and newly emerged Fastener)

Evidence artifacts available in `outputs/team_demo/` and documented in `outputs/team_demo/AEROMEMORY_TEAM_REPORT.md`.

---

## 6. Phase 5 & Real-Time Mobile Capture Progress

- **Air-Gapped LAN Workflow**: Technician phone connects to laptop local Wi-Fi LAN (`http://<LAPTOP_IP>:3000/mobile`) without internet access or external cloud services.
- **Native HTML5 Camera Integration**: Replaced `getUserMedia()` with native `<input type="file" accept="image/*" capture="environment">` to bypass HTTP webview security restrictions on mobile browsers.
- **State Preservation**: Resolved UI unmounting and element hidden state issues by positioning the file input off-screen (`top: -9999px`) while retaining DOM tree references for seamless photo capture and preview.
- **Laptop Auto-Polling**: The laptop React dashboard (`http://localhost:3000`) continuously polls `GET /api/inspections/{id}/latest-result` every 2 seconds, instantly presenting YOLO detections and AeroMemory defect progression comparisons.
- **Image Resolution Analysis**: Diagnosed 4K phone camera resolution downscaling behavior (3072x4096 reduced to 640x640 by YOLO), establishing close-up framing guidelines for field technicians and documenting the sliding-window tiling solution in `REALTIME_IMAGE_CAPTURE.md`.
