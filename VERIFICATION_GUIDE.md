# AeroIntel — Collaborator Verification & Testing Guide

This guide is for any collaborator pulling this repository to verify that the model works, test inference, check training metrics, and reproduce or extend the training pipeline.

---

## 1. Quick Checklist for Collaborators

| Objective | File / Location | How to verify |
|---|---|---|
| **Test Model Inference** | `tools/test_images.py` | Run local CLI test with ONNX or PyTorch weights |
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
git checkout model-training-and-eval

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate
```

### 2.2 Install Dependencies
Install Ultralytics and the inference runtimes:

```bash
pip install ultralytics onnx onnxruntime opencv-python matplotlib
```

*(Note for Windows users: ensure Git longpaths is enabled: `git config --global core.longpaths true`)*

---

## 3. Obtaining the Model Weights

- **`models/aerointel_v1.onnx` is already bundled directly in this branch!**  
  As soon as you pull `model-training-and-eval`, you have the model ready in `models/aerointel_v1.onnx` and can run inference immediately (see Section 4).

- **For PyTorch checkpoints (`best.pt` / `last.pt`):**  
  Raw training checkpoints are stored in Google Drive under `Drive/AeroIntel/runs/aerointel_v1_yolo11s/weights/best.pt` to keep the Git repo size manageable. You can also re-export or inspect them using `ml/colab/03_eval_export.ipynb`.

---

## 4. Testing Model Inference (Smoke Test)

### 4.1 CLI Image Test
Use `tools/test_images.py` to run detection on a single image or a folder of images:

```bash
# Test a single image using ONNX model (default threshold conf=0.40):
python tools/test_images.py path/to/aircraft_image.jpg --model models/aerointel_v1.onnx

# Test using a lower confidence threshold (e.g. 0.25):
python tools/test_images.py path/to/aircraft_image.jpg --model models/aerointel_v1.onnx --conf 0.25

# Test a folder of images using best.pt:
python tools/test_images.py path/to/image_folder/ --model runs/aerointel_v1_yolo11s/weights/best.pt --conf 0.25
```

**Expected output:**
- Prints each detected class and confidence score (e.g. `Dent: confidence=0.882`, `Missing Fastener: confidence=0.741`).
- Generates annotated bounding-box images under `runs/image_test/`.

### 4.2 Python Scripting / Code Snippet
To use the model in Python code or backend integration:

```python
from ultralytics import YOLO

# Load model (works with .onnx or .pt)
model = YOLO("models/aerointel_v1.onnx")

# Run prediction
results = model.predict("sample_aircraft_panel.jpg", imgsz=640, conf=0.25, iou=0.50)

for result in results:
    boxes = result.boxes
    for box, cls_id, conf in zip(boxes.xyxy, boxes.cls, boxes.conf):
        class_name = result.names[int(cls_id)]
        print(f"Found {class_name} ({float(conf):.1%}) at [{box.tolist()}]")
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

## 6. How to Reproduce or Re-Train the Model

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

## 7. Frozen Contracts & Golden Rules

1. **Class Schema is Frozen:** Do not reorder or renumber classes.
   ```yaml
   0: crack
   1: corrosion
   2: dent
   3: missing_fastener
   ```
2. **Never commit `.pt` or `.onnx` files to Git:** Keep them in Drive/storage as specified in `models/README.md`.
3. **Keep living docs updated:** If you change contracts, hyperparameters, or metrics, update `docs/DECISIONS.md`, `docs/PROGRESS.md`, and `docs/TECHNICAL_INTEGRATIONS.md`.
