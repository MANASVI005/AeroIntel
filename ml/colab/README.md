# AeroIntel — YOLO training on Google Colab (R1 / spec A6)

Three notebooks, run in order. Everything durable lives in **Google Drive → `AeroIntel/`**, so runtime disconnects never lose work.

| Notebook | Spec step | What it does |
|---|---|---|
| `01_data_prep.ipynb` | A6 steps 2–4 | Download/upload sources → audit (counts, class balance, contact sheets) → remap to the 4 frozen classes → dedupe + leakage-safe split → `aerointel_dataset_v1.zip` in Drive |
| `02_train_yolo.ipynb` | A6 step 5 | YOLOv8n (then `s` for comparison) at imgsz=640, trained in **break-safe chunks** with auto-resume from Drive |
| `03_eval_export.ipynb` | A6 steps 6–7 | Per-class metrics on the test split, CPU latency benchmark, ONNX export to `models/aerointel_v{n}.onnx`, draft `metrics.md` |

Upload them to Colab (or open from Drive) and run top-to-bottom. Notebook 02 needs the GPU runtime: **Runtime → Change runtime type → T4 GPU**.

> **Current dataset flow (AeroIntel-ABC-v1):** the official dataset is `datasets/master_dataset_ABC/` in the repo, built by the `tools/` scripts. `tools/_tmp_rebuild_zip.py` repacks it into **`aerointel_dataset_v1_colab.zip`** (Linux-safe forward-slash paths, `train/ valid/ test/ data.yaml` at the root). Upload that zip to **Drive → `AeroIntel/datasets/`** and start at notebook 02. Notebook 01 is only needed if you rebuild the dataset from raw sources on Colab instead.

## Drive layout (created automatically)

```
MyDrive/AeroIntel/
  datasets/
    raw/<source>/                # untouched downloads
    raw_uploads/                 # you put non-Roboflow zips here
    audit/                       # audit_summary.json + contact sheets (LOOK AT THEM)
    merged/                      # the 4-class dataset + data.yaml + summary
    field_test/                  # >=50 unseen images for the field test (A6)
    aerointel_dataset_v1_colab.zip   # master_dataset_ABC repacked (upload this)
  runs/aerointel_v1_yolo11s/     # checkpoints synced here after EVERY chunk
  runs/aerointel_v1_yolo11s_state.json
  models/aerointel_v1.onnx + registry.json
  logs/eval_*.json, latency_*.json
  metrics_draft.md
```

## Break-safe training (notebook 02) — the important part

- Training runs in chunks of `EPOCHS_PER_CHUNK` (default 10). After each chunk, **run the sync cell** — that copies `last.pt`/`best.pt` + logs to Drive.
- If the runtime disconnects (free Colab idle-timeouts, 12h limits, browser closed): reopen the notebook, **Runtime → Run all**. Cells 1–4 restore the dataset and the run folder from Drive; cell 5 resumes the next chunk via `resume=True` (optimizer state and epoch count are restored from `last.pt`).
- Worst case you lose the current (unsynced) chunk only.
- Notebook 02 trains **YOLO11s** (current Ultralytics generation, best accuracy/speed on the T4). For a lighter/faster baseline, change `MODEL_SIZE = 'n'` in cell 2 and rerun — it creates a separate run (`aerointel_v1_yolo11n`) so the `s` run is preserved.

## Before you can train — week-1 checklist (spec A6 / B10)

1. Fill the source table in `ml/01_download.md` (licenses, counts, splits — verify the Roboflow CC BY 4.0 figures).
2. Put the sources in Drive (Roboflow API key or zip uploads) and set `ml/class_map.yaml` + the `REMAP` dict in notebook 01 cell 5.
3. Audit every source and **look at the contact sheets** — reject bad-label datasets.
4. Keep the class IDs frozen: `0 crack, 1 corrosion, 2 dent, 3 missing_fastener` (contract B3.2).

## After training — back into the repo

1. Copy `models/aerointel_v1.onnx` + `registry.json` from Drive into the repo `models/` (never commit weights to git — B4; keep them in shared storage and note how to fetch in `models/README.md`).
2. Copy `metrics_draft.md` → `docs/metrics.md` and fill the TODOs (field test, experimental classes).
3. Record the exact training command/hyperparameters in `docs/DECISIONS.md` (A6 step 5).
4. Run the backend `/api/detect` smoke test with the exported ONNX (R2's detector service, spec A8).
