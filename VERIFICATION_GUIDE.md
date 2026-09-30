# AeroIntel — Collaborator Verification & Testing Guide

This guide is for any collaborator pulling this repository to verify that the model works, test inference, check training metrics, run AeroMemory temporal defect tracking, and reproduce or extend the pipeline.

---

## 1. Quick Checklist for Collaborators

| Objective | File / Location | How to verify |
|---|---|---|
| **Verify AeroMemory Engine** | `tools/test_aeromemory_on_dataset_e.py` | Run 30/30 automated state transition tests (Exit Code 0) |
| **Run AeroMemory Team Demo** | `tools/run_aeromemory_team_demo.py` | Generate 4 visual comparison panels + report in `outputs/team_demo/` |
| **Test Model Inference** | `tools/test_images.py` | Run local CLI test with ONNX weights |
| **Inspect Test Metrics** | `logs/eval_aerointel_v1_yolo11s_test.json` & `metrics_draft.md` | Verified held-out test split results (mAP50 = 0.613) |
| **Inspect CPU Latency** | `logs/latency_aerointel_v1_yolo11s.json` | CPU latency benchmark (p50 = 284.5 ms, p95 = 415.0 ms) |
| **Reproduce Training** | `ml/colab/02_train_yolo.ipynb` | Colab notebook with break-safe chunked training (T4 GPU) |
| **Run Test Eval & Export** | `ml/colab/03_eval_export.ipynb` | Colab notebook to evaluate test split and export to ONNX |
| **Frozen Class Schema** | `ml/class_map.yaml` & `models/registry.json` | 4 classes: `0 crack, 1 corrosion, 2 dent, 3 missing_fastener` |

---

## 2. Environment Setup

### 2.1 Python Virtual Environment
Requires Python 3.9+:

```bash
# Clone and checkout the branch
git clone https://github.com/MANASVI005/AeroIntel.git
cd AeroIntel
git checkout main

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate
```

*(Note for Windows users: ensure Git longpaths is enabled: `git config --global core.longpaths true`)*

### 2.2 Install Dependencies
Install Ultralytics and the inference runtimes:

```bash
pip install ultralytics onnx onnxruntime opencv-python matplotlib
```

---

## 3. Obtaining the Model Weights

- **`models/aerointel_v1.onnx` is bundled directly in this branch!**  
  As soon as you pull `main`, you have the model ready in `models/aerointel_v1.onnx` and can run inference immediately.

- **For PyTorch checkpoints (`best.pt` / `last.pt`):**  
  Raw training checkpoints are stored in Google Drive under `Drive/AeroIntel/runs/aerointel_v1_yolo11s/weights/best.pt` to keep the Git repo size manageable. You can also re-export or inspect them using `ml/colab/03_eval_export.ipynb`.

---

## 4. Running Local Inference (CLI)

Run inference on sample images using the ONNX model:

```bash
python tools/test_images.py --model models/aerointel_v1.onnx
```

---

## 5. Verifying Model Training & Evaluation Metrics

The model `aerointel_v1_yolo11s` was trained for 100 epochs on a Colab T4 GPU. You can verify the performance without re-training:

### 5.1 Held-Out Test Split Metrics (`logs/eval_aerointel_v1_yolo11s_test.json`)
The honest evaluation on the held-out test split (853 images):

| Class | Precision | Recall | mAP50 | mAP50-95 | Notes |
|---|---|---|---|---|---|
| **Overall** | **0.769** | **0.575** | **0.613** | **0.405** | **Passes project target (mAP50 ≥ 0.60)** |
| `Dent` | 0.913 | 0.861 | 0.887 | 0.688 | Strongest performing class |
| `Missing Fastener` | 0.839 | 0.607 | 0.677 | 0.388 | Reliable detection |
| `Crack` | 0.757 | 0.619 | 0.654 | 0.447 | Solid detection rate |
| `Corrosion` | 0.565 | 0.213 | 0.233 | 0.099 | Weakest class (comes solely from Dataset A; target for v2) |

### 5.2 CPU Latency Benchmark (`logs/latency_aerointel_v1_yolo11s.json`)
Measured on standard CPU (conf 0.40, IoU 0.50, imgsz 640):
- **p50:** `284.5 ms`
- **p95:** `415.0 ms`
- **Target:** `< 1,000 ms` (PASS)

---

## 6. Verifying AeroMemory™ Engine (Temporal Defect Tracking)

AeroMemory tracks defects over sequential inspections to answer whether a defect is `NEW`, `STABLE`, `INCREASED` (Progressing), or `RESOLVED` (Repaired).

### 6.1 Automated Strict Verification on Dataset E

Run the test suite against sequential ground truth in Dataset E:

```bash
python tools/test_aeromemory_on_dataset_e.py
```

**Key Verification Features:**
- **Evaluates 30 inspections** across 5 representative scenarios: `AI-001` (crack steady growth), `AI-002` (crack accelerated growth), `AI-003` (stable defect surveillance), `AI-006` (maintenance repair and resolution), and `AI-019` (multi-defect panel with newly emerged missing fastener).
- **Exact Dictionary State Matching:** Compares `{defect_id: state}` defect-by-defect, detecting missed or unexpected defects.
- **Empty Ground-Truth Validation:** Specifically validates inspections with no active defects (such as `AI-006` `INS-006` post-repair).
- **Exit Code:** Returns `0` on 100% pass and `1` on any mismatch.
- **Database Isolation:** Harness isolates SQLite databases per aircraft run to avoid `defect_id` collision across the fleet.

### 6.2 Live Team Demonstration & Artifact Generation

Run the comprehensive team demonstration:

```bash
python tools/run_aeromemory_team_demo.py
```

This script:
1. Runs the 4 core maintenance scenarios through the full `AeroMemoryService` pipeline.
2. Generates high-clarity side-by-side engineer visual comparison panels with bounding boxes, baseline deltas ($\Delta\text{mm}$), growth rates ($\%$), and decision-support text.
3. Writes the formal summary report to `outputs/team_demo/AEROMEMORY_TEAM_REPORT.md`.

Visual artifacts produced:
- `outputs/team_demo/CASE-1_AI-001_Inspection_Comparison.png`
- `outputs/team_demo/CASE-2_AI-003_Inspection_Comparison.png`
- `outputs/team_demo/CASE-3_AI-006_Inspection_Comparison.png`
- `outputs/team_demo/CASE-4_AI-019_Inspection_Comparison.png`

### 6.3 Synthetic Benchmark Boundary & Disclaimer

> [!IMPORTANT]
> Dataset E fixtures are synthetic benchmark datasets with simulated defect geometries, progression steps, and repair events (10 px/mm synthetic calibration).
> These tests validate state-machine transitions, IoU/centroid matching, delta tracking, and database persistence logic within the AeroMemory engine.
> They do **not** establish certified production airworthiness or real-aircraft reliability, which requires physical NDT inspection calibration, regulatory compliance, and independent evaluation on unseen real-aircraft imagery (Dataset D).

---

## 7. How to Reproduce or Re-Train the Model

If you want to re-run training from scratch or fine-tune with new data:

1. **Dataset:**
   - Official training archive is `datasets/aerointel_dataset_v1_colab.zip` (326 MB, 8,525 images).
   - Upload it to your Google Drive under `AeroIntel/datasets/aerointel_dataset_v1_colab.zip`.
2. **Open Notebook 02:**
   - Open `ml/colab/02_train_yolo.ipynb` in [Google Colab](https://colab.research.google.com/).
   - Set runtime to **T4 GPU** (*Runtime → Change runtime type → T4 GPU*).
   - Mount Google Drive and run all cells.
   - **Break-safe:** Notebook runs training in 10-epoch chunks and syncs checkpoints to Drive. If Colab disconnects, re-running cell 5 automatically resumes from `last.pt`.
3. **Open Notebook 03 for Evaluation & Export:**
   - Open `ml/colab/03_eval_export.ipynb`.
   - Run all cells to compute per-class test metrics, plot confusion matrix, benchmark CPU latency, and export `models/aerointel_v1.onnx`.

---

## 8. Frozen Contracts & Golden Rules

1. **Class Schema is Frozen:** Do not reorder or renumber classes.
   ```yaml
   0: crack
   1: corrosion
   2: dent
   3: missing_fastener
   ```
2. **Never commit raw training `.pt` checkpoints to Git:** Keep them in Drive/storage as specified in `models/README.md`.
3. **Defect Lifecycle Statuses:**
   - `New`: First detection of defect.
   - `Monitored`: Defect re-detected and stable within tolerance.
   - `Progressing`: Defect dimension or area has increased beyond tolerance.
   - `Repaired` / `Closed`: Defect no longer active; excluded from future active defect queries (`status NOT IN ('Closed', 'Repaired')`).
4. **Keep living docs updated:** If you change contracts, hyperparameters, or metrics, update `docs/DECISIONS.md`, `docs/PROGRESS.md`, and `docs/TECHNICAL_INTEGRATIONS.md`.
