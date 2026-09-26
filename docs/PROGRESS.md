# AeroIntel — PROGRESS.md

**Status dashboard + changelog.** Update after every work session: refresh §1, move milestones, and append a dated changelog entry at the bottom. Numbers only from verified artifacts — `?` until then.

---

## 1. Status dashboard

**Last updated: 2026-09-25**

| Area | Status | Notes |
|---|---|---|
| Dataset provenance record (`ml/01_download.md`) | 🟡 partial | Dataset A recorded; licenses/URLs still `[CONFIRM]`; B/C not yet added |
| Class schema (4 frozen classes) | ✅ done | `ml/class_map.yaml`; contract B3.2 |
| Dataset build (A+B+C → v1) | ✅ done | 8,525 images / 15,252 ann.; merge report inside the zip |
| Notebook 01 — data prep | ✅ done (superseded by local merge for v1) | audit → remap → dedupe → split pipeline kept for v2 |
| Notebook 02 — training | ✅ done | 100/100 epochs, no early stop, ~3.5 h T4 |
| Notebook 03 — eval + export | ✅ done | per-class **test** eval, CPU latency, ONNX export |
| ONNX model (`models/aerointel_v1.onnx`) | ✅ done | exported to `models/aerointel_v1.onnx` + `registry.json` |
| `docs/metrics.md` / `metrics_draft.md` | ✅ done | verified test-split metrics (mAP50 = 0.613) |
| Field test set (≥ 50 unseen images) | ⬜ not started | spec A6 |
| Backend `/api/detect` smoke test | ⬜ not started | R2 detector service, spec A8 |
| Repo hygiene (`.gitignore` for weights) | ✅ done | `.pt`, `.onnx`, `datasets/*.zip`, `eval_workspace/` ignored |

## 2. Milestones

### ✅ M1 — Setup & data provenance
- Repo skeleton, class schema frozen, provenance record started.
- Three Colab notebooks written: data prep, break-safe training, eval/export.

### ✅ M2 — Dataset v1 (AeroIntel-ABC-v1)
- Sources audited: A (1,148 img / 2,597 ann), B (1,104 / 1,662), C (6,803 / 11,786) — 0 missing pairs, 0 corrupted, 0 invalid.
- Merged + deduped (530 exact duplicates removed, 715 polygons → boxes, cross-dataset label conflicts resolved by visual inspection).
- Leakage-safe 80/10/10 split (seed 42): **train 6,820 / valid 852 / test 853**.
- Packed as `datasets/aerointel_dataset_v1_colab.zip` (Linux-safe paths, `data.yaml` at zip root + `merge_report.txt`).

### ✅ M3 — Model v1 trained (`aerointel_v1_yolo11s`)
- YOLO11s, imgsz 640, batch 16, 100 epochs, patience 20 (never triggered), seed 42, AMP.
- **Validation-split results:** best mAP50 **0.623**, mAP50-95 **0.410**, P 0.787, R 0.579 (epoch 89).
- A6 target mAP50 ≥ 0.60 → **provisional PASS at val level**.
- Checkpoints + full run artifacts synced to Drive and mirrored in `runs/aerointel_v1_yolo11s/`.

### ✅ M4 — Evaluate & export v1
- [x] Notebook 03: per-class metrics on the **test** split: **mAP50 0.613**, mAP50-95 0.405, P 0.769, R 0.575 (PASS vs target ≥ 0.60)
- [x] CPU latency benchmark: p50 = 284.5 ms, p95 = 415.0 ms (< 1,000 ms target)
- [x] Export `models/aerointel_v1.onnx` + `registry.json` + `models/README.md`
- [x] Test evaluation log in `logs/eval_aerointel_v1_yolo11s_test.json`, latency in `logs/latency_aerointel_v1_yolo11s.json`

### 🔜 M5 — Field validation & integration
- [ ] Collect ≥ 50-image field test set, evaluate on it
- [ ] Backend `/api/detect` smoke test with the ONNX
- [ ] Fill remaining provenance/licensing gaps in `ml/01_download.md`; add B/C rows

### 🔮 M6 — v2 ideas (not started)
- Recall improvement: more corrosion/crack diversity (recall is the weak spot at ~0.58)
- Re-audit Datasets D/E/F for inclusion
- Per-class confusion analysis → targeted data collection
- Optional YOLO11n comparison run for speed baseline

## 3. Key metrics (verified from artifacts)

| Metric | Value | Source |
|---|---|---|
| Val mAP50 (best, epoch 76) | 0.623 | `results.csv` |
| Val mAP50-95 (best, epoch 89) | 0.410 | `results.csv` |
| Val precision (best ckpt) | 0.787 | `results.csv` |
| Val recall (best ckpt) | 0.579 | `results.csv` |
| Test-split mAP50 | 0.613 | `logs/eval_aerointel_v1_yolo11s_test.json` |
| Test-split mAP50-95 | 0.405 | `logs/eval_aerointel_v1_yolo11s_test.json` |
| Test-split Precision | 0.769 | `logs/eval_aerointel_v1_yolo11s_test.json` |
| Test-split Recall | 0.575 | `logs/eval_aerointel_v1_yolo11s_test.json` |
| CPU latency p50 | 284.5 ms | `logs/latency_aerointel_v1_yolo11s.json` |
| CPU latency p95 | 415.0 ms | `logs/latency_aerointel_v1_yolo11s.json` |
| Per-class mAP50 | Dent 0.887, Fastener 0.677, Crack 0.654, Corrosion 0.233 | `logs/eval_aerointel_v1_yolo11s_test.json` |

## 4. Changelog

### 2026-09-24 — Model v1 training completed
- Trained `aerointel_v1_yolo11s` for the full 100 epochs (early stopping never fired). Best val mAP50 0.623 / mAP50-95 0.410 @ epoch 89; ~3.5 h on a free Colab T4.
- Run artifacts (weights, `args.yaml`, `results.csv`, plots, confusion matrix) synced to Drive and copied into `runs/aerointel_v1_yolo11s/`.

### 2026-09-25 — Project documentation created
- Analysed the whole folder: dataset zip (+ `merge_report.txt`), three Colab notebooks, class map, provenance record, and the full training run.
- Created the living-docs system: `README.md` (status snapshot), `docs/DECISIONS.md` (D-001…D-015), `docs/PROGRESS.md` (this file), `docs/TECHNICAL_INTEGRATIONS.md` (stack, contracts, IT log).
- Logged the v1 dataset merge and training decisions; flagged val-vs-test caveat and recall as the v2 lever.

### 2026-09-26 — Frontend functional spec added (`FRONTEND_SPEC.md`)
- Added repo-root `FRONTEND_SPEC.md`: complete v1 frontend functional reference — 4 API endpoints (E1–E4) with exact request/response shapes, 8 pages with layouts/data slots/states, frontend behavior rules, and build order. Supersedes the earlier frontend inspo doc (visual theme now owned by the design track in Canva/Stitch).

### 2026-09-26 — Model evaluation, export & collaborator guide
- Verified test-split evaluation (mAP50 = 0.613) and CPU latency benchmarks.
- Created `VERIFICATION_GUIDE.md` for collaborators to test inference and re-run training.
- Created `model-training-and-eval` branch and pushed verified artifacts to remote.
