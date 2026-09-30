# AeroIntel — DECISIONS.md

**Decision log.** Every technical decision with its rationale and alternatives considered. Append-only: new decisions get the next `D-xxx` number and are never rewritten or deleted. If a decision is reversed, add a new entry that supersedes the old one.

Status legend: `[accepted]` in force · `[superseded by D-xxx]` · `[proposed]` awaiting confirmation.

| ID | Date | Decision | Status |
|---|---|---|---|
| D-001 | week 1 | Freeze 4-class schema: 0 crack, 1 corrosion, 2 dent, 3 missing_fastener | accepted |
| D-002 | week 1 | Ultralytics YOLO as the detection framework | accepted |
| D-003 | week 1 | Google Colab (T4, free tier) as the training platform | accepted |
| D-004 | week 1 | Google Drive as the durable store (never rely on /content) | accepted |
| D-005 | week 1 | Break-safe chunked training (10-epoch chunks + Drive sync + auto-resume) | accepted |
| D-006 | training day | Build the official dataset from source Datasets A + B + C; exclude D, E, F | accepted |
| D-007 | training day | Dataset v1 = 8,525 images after exact-duplicate removal (530 excluded) | accepted |
| D-008 | training day | Leakage-safe split: near-duplicate groups kept as indivisible units, 80/10/10, seed 42 | accepted |
| D-009 | training day | Polygon annotations converted to enclosing YOLO boxes (715 boxes) | accepted |
| D-010 | training day | Cross-dataset annotation conflicts resolved case-by-case by visual inspection; unresolved ones excluded | accepted |
| D-011 | training day | Train YOLO11s (not n/m/l, not YOLOv8) as the v1 model | accepted |
| D-012 | training day | Hyperparameters: 100 epochs, patience 20, imgsz 640, batch 16, seed 42, deterministic, AMP | accepted |
| D-013 | training day | Default Ultralytics augmentation (mosaic, fliplr 0.5, HSV, scale 0.5, erasing 0.4) | accepted |
| D-014 | 2026-09-24 | Run completed all 100 epochs without early stopping; v1 is final unless test eval fails | accepted |
| D-015 | 2026-09-24 | Docs system: README + DECISIONS + PROGRESS + TECHNICAL_INTEGRATIONS updated after every change | accepted |

---

## D-001 — Freeze the 4-class schema `[accepted]`

Class IDs are a contract between dataset, model and every downstream consumer. Renumbering after training silently corrupts all predictions.

- **Decision:** `0 crack · 1 corrosion · 2 dent · 3 missing_fastener`, recorded in `ml/class_map.yaml` and in every `data.yaml`.
- **Alternatives:** dynamic schema grown per dataset (rejected: breaks the backend/frontend contract); separate binary detectors per class (rejected: 4× inference cost, no shared learning).
- **Consequence:** dataset sources must remap (or drop) their classes to this schema; drops are logged. `data.yaml` display names are capitalized (`Crack`, …) — map by **ID**, not string.

## D-002 — Ultralytics YOLO as the detection framework `[accepted]`

- **Why:** best-documented small-object detector ecosystem, single-command train/val/export, first-class ONNX export for the backend detector service, works on free Colab.
- **Alternatives:** Detectron2 / MMDetection (heavier setup on Colab, slower iteration), TensorFlow Object Detection API (aging), custom pipeline (out of scope for the timeline).

## D-003 — Google Colab free T4 as the training platform `[accepted]`

- **Why:** no local GPU needed; T4 is enough for YOLO11s @ 640 / batch 16; measured ~2 min/epoch → ~3.5 h for the full 100-epoch run.
- **Cost:** runtimes disconnect (idle timeouts, 12 h cap) → drove D-004 and D-005.

## D-004 — Google Drive as the single durable store `[accepted]`

- **Decision:** everything that must survive a disconnect lives in `Drive → AeroIntel/` (dataset zip, run folder, checkpoints, logs, exported models). Nothing lives only in `/content`.
- **Consequence:** after any disconnect, *Runtime → Run all* restores state; worst case loses the current unsynced chunk.

## D-005 — Break-safe chunked training `[accepted]`

- **Decision:** training runs in `EPOCHS_PER_CHUNK = 10` chunks; after each chunk the run folder is synced to Drive (notebook 02 cell 6). Re-running cell 5 resumes via `resume=True` (optimizer state + epoch counter from `last.pt`).
- **Fallback:** if `resume` fails after an ultralytics version change or early stop (optimizer stripped from `last.pt`), cell 5 falls back to a **weights-only warm start from `best.pt`** and the epoch counter restarts — note it here when it happens. *(Has not been needed so far — the v1 run completed cleanly.)*
- **Rule:** do not change `TOTAL_EPOCHS` between chunks; do not edit anything inside the run folder.

## D-006 — Dataset composition: A + B + C only `[accepted]`

- **Decision:** v1 is built from Dataset A (corrosion), Dataset B (crack/missing-fastener ambiguity set) and Dataset C (crack/dent/missing-fastener). Datasets D, E, F and the pre-existing master dataset are excluded; sources are never modified in place.
- **Why:** A/B/C passed the audit (0 missing pairs, 0 corrupted, 0 invalid annotations); D/E/F were not cleaned/verified in time for v1.
- **Alternative for v2:** re-audit D/E/F and grow the dataset (tracked in PROGRESS.md as a future milestone).

## D-007 — Exact-duplicate removal policy `[accepted]`

- **Decision:** 486 exact-duplicate groups → 530 duplicate images removed; identical annotations keep one copy; conflicting annotations are resolved individually (D-010) or the whole group is excluded.
- **Why:** duplicates inflate metrics and leak between splits if unhandled.

## D-008 — Leakage-safe split `[accepted]`

- **Decision:** fresh split from A+B+C after dedup, target 80/10/10, seed 42. Near-duplicate groups (8×8 aHash, Hamming ≤ 4; 1,945 groups covering 7,216 images; 693 groups span datasets) are assigned to a **single split as indivisible units** so augmented variants of one source image can't straddle train/test.
- **Result:** train 6,820 / valid 852 / test 853 = 8,525 images, 15,252 annotations.

## D-009 — Polygon → enclosing YOLO box `[accepted]`

- **Decision:** 715 polygon annotations converted to their enclosing axis-aligned boxes; no polygons remain in v1.
- **Trade-off:** enclosing boxes slightly over-cover the defect; accepted because the detector schema is box-only.

## D-010 — Conflict resolution by visual inspection `[accepted]`

- **Decision:** where the same physical image carried different class labels in different sources (e.g. Dataset B "crack" vs Dataset C "dent" on the same fastener region), each conflict was inspected individually; the visually better-supported label was kept, the conflicting copy excluded, and the decision (with SHA-256) recorded in the zip's `merge_report.txt`. Images with genuinely ambiguous ground truth were excluded **without** inventing a label.
- **Why:** silently favoring one dataset would bake label noise into the contract classes.

## D-011 — YOLO11s as the v1 model `[accepted]`

- **Why:** current Ultralytics generation with better accuracy per GPU-hour than YOLOv8 at the same size; `s` fits the free T4 at 640/16 with AMP; exports cleanly to ONNX. `n` is kept as a documented lighter baseline (`MODEL_SIZE = 'n'` creates a separate run).
- **Alternatives:** v8n baseline (older generation), v8s/v11m (too slow / OOM risk on free T4).

## D-012 — Training hyperparameters `[accepted]`

Frozen in `runs/aerointel_v1_yolo11s/args.yaml`: pretrained `yolo11s.pt`, epochs 100, patience 20 (early stopping), imgsz 640, batch 16, workers 2, optimizer auto, lr0 0.01, seed 42, deterministic True, AMP True, cos_lr False, close_mosaic 10.

- **Why these:** spec A6 (100 epochs + early stopping, imgsz 640); `workers 2` and batch 16 are Colab-T4-safe; seed+deterministic for reproducibility.

## D-013 — Augmentation policy `[accepted]`

- **Decision:** Ultralytics defaults (mosaic 1.0, mixup 0, fliplr 0.5, flipud 0, HSV h0.015/s0.7/v0.4, scale 0.5, translate 0.1, erasing 0.4, close_mosaic 10). No extra augmentation on top.
- **Why:** defaults are well-tuned for small-object detection; dataset already has scale variety. Rotate/flipud were deliberately left off — vertical orientation matters for aircraft surfaces.

## D-014 — v1 training declared complete `[accepted]`

- **Evidence:** `results.csv` has all 100 epochs (early stopping never fired; patience 20 not reached because val mAP50-95 kept creeping up to 0.410 @ epoch 89).
- **Val-split result:** best mAP50 **0.623** / mAP50-95 **0.410** / P 0.787 / R 0.579 (epoch 89 for mAP50-95; mAP50 peaked 0.623 @ epoch 76).
- **Caveat:** these are **validation** numbers. The honest number is the test split in notebook 03 — until that runs, "PASS vs A6 target 0.60" is provisional.
- **Read of the curves:** precision is strong (0.77–0.79) but recall plateaus ~0.56–0.58 → recall is v2's main lever (more/diverse corrosion + crack data, possibly higher-res tiles).

## D-015 — Living documentation system `[accepted]`

- **Decision:** four living docs — `README.md` (status snapshot), `docs/DECISIONS.md` (this file, append-only), `docs/PROGRESS.md` (milestones + dated changelog), `docs/TECHNICAL_INTEGRATIONS.md` (stack + contracts + integration iterations). After **every** change, update all that apply (protocol in `README.md §5`).
- **Why:** the Colab pipeline is easy to re-run but hard to reconstruct from memory; decisions and numbers must be written down the moment they exist, and never fabricated.
