# AeroIntel — Aircraft Damage Detection

Vision ML project that detects visible aircraft surface damage (crack, corrosion, dent, missing fastener) from photos, using an Ultralytics YOLO11 detector trained on Google Colab.

**Current status: `aerointel_v1_yolo11s` trained (100/100 epochs). Test-split evaluation, ONNX export, and backend integration are the next milestones.**

---

## 1. Status snapshot

| Item | Value |
|---|---|
| Model | YOLO11s (`runs/aerointel_v1_yolo11s/`) |
| Dataset | AeroIntel-ABC-v1 (`datasets/aerointel_dataset_v1_colab.zip`) — 8,525 images, 15,252 annotations |
| Classes | 4 frozen: `0 crack, 1 corrosion, 2 dent, 3 missing_fastener` |
| Training result (val split) | best **mAP50 0.623** / **mAP50-95 0.410**, P 0.787, R 0.579 |
| A6 target (mAP50 ≥ 0.60) | **PASS at val level** — test split still to be measured honestly |
| Train time | ~3.5 h on a free Colab T4 |
| Exported model | ❌ not yet (notebook 03 pending) |
| Field test set (≥ 50 unseen images) | ❌ not yet collected |

## 2. Repository structure

```
├── README.md                        # this file
├── docs/
│   ├── DECISIONS.md                 # every technical decision + rationale (append-only)
│   ├── PROGRESS.md                  # status dashboard, milestones, changelog
│   └── TECHNICAL_INTEGRATIONS.md    # stack, contracts, integration iteration log
├── datasets/
│   └── aerointel_dataset_v1_colab.zip   # official v1 dataset (data.yaml at zip root + merge_report.txt)
├── ml/
│   ├── 01_download.md               # dataset provenance / license record (partially filled)
│   ├── class_map.yaml               # frozen class schema + per-source remap table
│   └── colab/
│       ├── README.md                # how to run the Colab pipeline
│       ├── 01_data_prep.ipynb       # audit → remap → dedupe → split → zip (A6 steps 2–4)
│       ├── 02_train_yolo.ipynb      # break-safe chunked training with auto-resume (A6 step 5)
│       └── 03_eval_export.ipynb     # per-class test eval → CPU latency → ONNX export (A6 steps 6–7)
└── runs/
    └── aerointel_v1_yolo11s/
        ├── weights/{best.pt, last.pt}
        ├── args.yaml                # exact hyperparameters used
        ├── results.csv              # full 100-epoch metric history
        ├── results.png, confusion_matrix(.png), BoxP/R/PR/F1 curves, labels.jpg
        └── train_batch*.jpg, val_batch*_labels/pred.jpg
```

> `runs/**` (weights, plots, CSVs) is experiment output — do **not** commit `.pt` files to git (rule B4). Keep weights in Drive / shared storage and reference them here.

## 3. The frozen class contract (B3.2)

These IDs are **frozen forever** — never rename, reorder or renumber after training:

| ID | Class | Train imgs | Ann. | Valid+test notes |
|---|---|---|---|---|
| 0 | `crack` | 3,791 | 5,192 | largest class |
| 1 | `corrosion` | 1,148 | 2,597 | from Dataset A only |
| 2 | `dent` | 2,588 | 3,869 | |
| 3 | `missing_fastener` | 1,571 | 3,594 | |

The dataset `data.yaml` uses display names (`Crack`, `Corrosion`, `Dent`, `Missing Fastener`) at the same IDs. Downstream consumers (backend detector service, frontend) must map by **ID**, not by string.

## 4. Reproduce / use

**Re-run training (Colab):** upload `datasets/aerointel_dataset_v1_colab.zip` to `Drive → AeroIntel/datasets/`, open `ml/colab/02_train_yolo.ipynb` with a T4 GPU runtime, then *Runtime → Run all*. Training is break-safe: it runs in 10-epoch chunks, syncs checkpoints to Drive after each chunk, and auto-resumes from `last.pt` after a disconnect.

**Evaluate + export:** `ml/colab/03_eval_export.ipynb` — per-class metrics on the **test** split, CPU latency benchmark, ONNX export to `models/aerointel_v1.onnx` + `registry.json`.

**Local inference (after export):**

```python
from ultralytics import YOLO
model = YOLO("runs/aerointel_v1_yolo11s/weights/best.pt")   # or models/aerointel_v1.onnx
results = model.predict("image.jpg", imgsz=640, conf=0.40, iou=0.50)
```

**Test whether the model detects damage in images:**

```powershell
python tools/test_images.py path\to\image.jpg
python tools/test_images.py final_visual_test\predictions --conf 0.25
```

The script prints each detected class and confidence, then saves annotated images under `runs/image_test/`. A folder smoke test confirms that inference runs; accuracy requires images with trusted YOLO label files and should be measured with the test split or notebook 03.

## 5. Documentation system — how this repo stays honest

Four living documents. **After every change to this project, update them** (protocol below):

| File | Owns | Update when |
|---|---|---|
| `README.md` | What the project is + current status snapshot | Any change visible from the outside (new artifacts, new metrics, new structure) |
| `docs/DECISIONS.md` | The *why* — every technical decision with rationale and alternatives considered | Every time a choice is made (append `D-xxx`, never rewrite old entries) |
| `docs/PROGRESS.md` | The *when* — milestone status + dated changelog | Every work session (append a changelog entry) |
| `docs/TECHNICAL_INTEGRATIONS.md` | The *how* — stack, interfaces, contracts, integration iterations | Every change to stack versions, data formats, or component contracts |

**Update protocol (every change):**
1. Do the work.
2. Add a dated bullet to `docs/PROGRESS.md → Changelog`.
3. If a decision was made → append `D-xxx` to `docs/DECISIONS.md`.
4. If a contract/format/version changed → new `IT-xxx` entry in `docs/TECHNICAL_INTEGRATIONS.md`.
5. Refresh the tables in `README.md §1` and `docs/PROGRESS.md §1`.

Never fabricate numbers: leave `?` / `TODO` until the value is verified from an artifact.

## 6. Immediate next steps

1. Run `ml/colab/03_eval_export.ipynb` → per-class **test** metrics, CPU latency, `models/aerointel_v1.onnx`.
2. Copy `metrics_draft.md` → `docs/metrics.md`; copy ONNX + registry into the repo `models/`.
3. Collect the ≥ 50-image field test set (spec A6) and evaluate on it.
4. Backend `/api/detect` smoke test with the exported ONNX (R2 detector service, spec A8).
5. Record license verification for Dataset A in `ml/01_download.md` (CC BY 4.0 credit in all reports).

See `docs/PROGRESS.md` for the full picture.
