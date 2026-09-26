# AeroIntel — TECHNICAL_INTEGRATIONS.md

**How the pieces fit and talk to each other.** The canonical stack + interface reference, plus the append-only iteration log (`IT-xxx`) for every change to a version, format, or contract. Update whenever code changes what it consumes, produces, or exposes.

---

## 1. System overview (current)

```
[Raw sources A/B/C]
      │  local merge tools (dedupe, polygon→box, conflict resolution, split 80/10/10, seed 42)
      ▼
datasets/aerointel_dataset_v1_colab.zip ──upload──▶ Google Drive AeroIntel/datasets/
      │                                                    │
      │ unzip (colab cell 3)                               ▼
      ▼                                       runs/aerointel_v1_yolo11s/  (checkpoints, synced per chunk)
YOLO11s training (notebook 02, Colab T4)  ◀──resume from last.pt after any disconnect
      │
      ├─▶ runs/aerointel_v1_yolo11s/weights/best.pt ──▶ notebook 03
      │                                                    │
      │                                     per-class test eval · CPU latency · ONNX export
      ▼                                                    ▼
runs/... (metrics, plots, confusion matrix)          models/aerointel_v1.onnx + registry.json
                                                           │ (copied into repo models/)
                                                           ▼
                                                 Backend detector service /api/detect  (R2, spec A8)
```

## 2. Stack & versions

| Layer | Technology | Version / note | Where used |
|---|---|---|---|
| Detection framework | Ultralytics YOLO (D-002) | latest pip at run time; started from pretrained `yolo11s.pt` | notebooks 02, 03; backend |
| Training platform | Google Colab, free T4 GPU, AMP | ~2 min/epoch @ 640/16 | notebook 02 |
| Durable storage | Google Drive `MyDrive/AeroIntel/` | dataset zip, run folder, models, logs | all notebooks |
| Eval/plotting | Ultralytics val + matplotlib/pandas | per-epoch CSV + PNGs | notebooks 02, 03 |
| Export format | ONNX (opset 12, simplify=True, imgsz 640) | for the backend detector | notebook 03 |
| Dataset hashing | 8×8 grayscale aHash, Hamming ≤ 4 (near-dup grouping); SHA-256 (exact-dup conflicts) | in merge tooling | dataset build |

Environment pinning is **loose by design** (Colab installs latest at runtime). If a behavior change in a new ultralytics release breaks `resume=True`, notebook 02 falls back to a weights-only warm start from `best.pt` — record the incident as an `IT-xxx` entry.

## 3. Interfaces & data contracts

### 3.1 Class ID contract (B3.2) — **frozen** (D-001)

| ID | Canonical name | data.yaml display name |
|---|---|---|
| 0 | `crack` | `Crack` |
| 1 | `corrosion` | `Corrosion` |
| 2 | `dent` | `Dent` |
| 3 | `missing_fastener` | `Missing Fastener` |

Rules: map by **ID**, never by display string. Never reorder/rename. Sources remap into this schema or get dropped (logged).

### 3.2 Dataset zip contract — `aerointel_dataset_v1_colab.zip`

- Layout: `data.yaml` + `train/ valid/ test/` (each with `images/` + `labels/`) + `merge_report.txt` at the **zip root**; forward-slash paths (Linux/Colab-safe).
- `data.yaml`: `train: train/images`, `val: valid/images`, `test: test/images`, `nc: 4`, names as §3.1.
- Counts (verified): train 6,820 / valid 852 / test 853 — 8,525 images, 15,252 annotations.
- Notebook 02 auto-detects this layout and also accepts the older `merged/` nested layout + the legacy filename `aerointel_dataset_v1.zip`.
- **Change policy:** any new dataset version ships as a **new zip** (`..._v2.zip`) — never overwrite v1; runs must stay reproducible.

### 3.3 Run-folder contract (notebook 02 ↔ Drive)

- `Drive: AeroIntel/runs/<run_name>/` mirrors `/content/runs/<run_name>/` after **every chunk** (cell 6 sync; skips `.cache`/`.DS_Store`).
- Resume reads `args.yaml` + `weights/last.pt` from the run folder — it is **read-only for humans**; don't edit `TOTAL_EPOCHS` between chunks.
- Sidecar `runs/<run_name>_state.json` on Drive: `{"epochs_done": n, "chunk": k}` (written after each chunk; read before training).
- Run naming: `aerointel_v{n}_yolo11{size}` (e.g. `aerointel_v1_yolo11s`); a comparison `n`-model run gets its own folder automatically.

### 3.4 Model artifact contract (notebook 03 → backend)

| Key | Value (v1) |
|---|---|
| `registry.json` fields | `name: aerointel_v1`, `type: yolo11-onnx`, `path: models/aerointel_v1.onnx`, `classes` (map §3.1), `version: v1`, `imgsz: 640`, `trained_from: aerointel_v1_yolo11s`, `exported_at` |
| Inference params | `imgsz=640`, latency tests at `conf=0.40`, `iou=0.50` |
| Weights policy | `.pt`/`.onnx` **never committed to git** (B4) — they live in Drive/shared storage; repo keeps `models/README.md` with fetch instructions |
| Backend endpoint | `/api/detect` (R2, spec A8) — to be smoke-tested with the ONNX (⬜ pending) |

### 3.5 Colab notebook interfaces

| Notebook | Inputs | Outputs |
|---|---|---|
| `01_data_prep.ipynb` | Drive raw sources, `ROBOFLOW_API_KEY`, `REMAP` dict | `datasets/merged/` + `data.yaml`, audit JSON + contact sheets, drop log |
| `02_train_yolo.ipynb` | dataset zip from Drive, `MODEL_SIZE`, `TOTAL_EPOCHS=100`, `EPOCHS_PER_CHUNK=10`, `IMGSZ=640`, `BATCH=16`, `PATIENCE=20` | run folder (weights, CSV, plots) synced to Drive, `*_state.json` |
| `03_eval_export.ipynb` | Drive run folder + dataset zip | `eval_*_test.json`, `latency_*.json`, `models/aerointel_v{v}.onnx`, `registry.json`, `metrics_draft.md` |

## 4. Iteration log (`IT-xxx`) — append-only

| ID | Date | Change | Impact / notes |
|---|---|---|---|
| IT-001 | pre-v1 | Local merge tooling built: audit → exact-dup removal (530) → polygon→box (715) → conflict resolution → group-safe 80/10/10 split → v1 zip with `data.yaml` at root + `merge_report.txt`. | Notebook 01's Colab flow superseded for v1 but kept for v2 (D-006). |
| IT-002 | pre-v1 | Notebook 02 switched dataset input to the root-layout zip; auto-detects root vs `merged/` layout; accepts legacy zip name. | Decouples notebooks from notebook-01's `merged/` layout. |
| IT-003 | pre-v1 | Notebook 02 model default set to YOLO11**s** (was YOLOv8n in the original plan); run name `aerointel_v1_yolo11s`. | D-011. `MODEL_SIZE='n'` still available for a lighter comparison run. |
| IT-004 | pre-v1 | Break-safe training hardened: state file `*_state.json`, Drive sync cell, `resume=True` auto-resume, weights-only warm-start fallback if resume errors. | Makes free-Colab disconnects a non-event; fallback not needed so far. |
| IT-005 | pre-v1 | Notebook 02 cell 3 sed display fixed (`sed -n 1,10p "{DATA_YAML}\\"`) — cosmetic; trailing backslash in the quoted path. | No functional impact; clean up next time the cell is touched. |
| IT-006 | 2026-09-24 | v1 training executed to 100/100 epochs; run folder synced to Drive and mirrored to `runs/aerointel_v1_yolo11s/`. | Val mAP50 0.623 / mAP50-95 0.410; ~3.5 h T4. |
| IT-007 | 2026-09-25 | Living-docs system created (README + DECISIONS + PROGRESS + TECHNICAL_INTEGRATIONS); update protocol defined in README §5. | All four docs now authoritative; every change must be reflected. |
| IT-008 | 2026-09-25 | Notebooks 02/03 observed to pass `data.yaml`-root zip paths and legacy `merged/` layout through the same restore logic; `args.yaml` shows `cls_remap: true` (non-standard key, ignored by ultralytics). | Harmless extra key logged for the record; remove from the train call if it ever warns. |

## 5. Risks & open integration issues

- **Loose ultralytics pinning** — a future release may change `resume`/export behavior; the warm-start fallback covers training, but re-verify notebook 03 export after any major upgrade.
- **Val vs test gap** — 0.623 mAP50 is a validation number; the test split may be lower. Don't quote val numbers in the report as if they were test numbers.
- **Recall 0.579** — the model misses ~42% of defects at default threshold; for a safety-adjacent demo consider lowering the deployed `conf` and documenting the trade-off.
- **Corrosion class depends on a single source (A)** — diversity risk; v2 should broaden corrosion data.
- **`runs/` currently not git-ignored** — add `.gitignore` (`runs/**`, `*.pt`, `*.onnx`) before the first commit (B4).
