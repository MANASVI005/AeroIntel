# AeroIntel: Aircraft Defect Detection & Longitudinal Memory System

> **⭐ THIS IS THE INTEGRATED MAIN — use this branch for all further work.**
> It consolidates **everything** from `model-training-and-eval`, `AEROMEMORY`, and `feature/aeromemory`: the YOLO v1 training pipeline + ONNX model, the AeroMemory™ engine, the FastAPI backend, the React frontend scaffold, phase 1–4 test suites, and all three datasets (`master_dataset_ABC`, `dataset_D`, `dataset_E_aeromemory` via LFS). The old feature branches are retained only for history — **do not start new work from them.**
> Quick start: backend — `PYTHONPATH=backend python -m app.db.init_db` then `uvicorn app.main:app` (see `STITCH_GUIDE.md` §3); frontend — `cd frontend && npm install && npm run dev`; Stitch UI — `STITCH_GUIDE.md`.

AeroIntel is an intelligent aircraft structural inspection system that combines edge-optimized deep learning defect detection (YOLO11) with a longitudinal memory engine (**AeroMemory™**) to track defect evolution, compute growth metrics, and generate automated airworthiness decision support.

**Current status:** `aerointel_v1` YOLO11s trained (100/100 epochs, test-split mAP50 = 0.613) and bundled as `models/aerointel_v1.onnx`. AeroMemory engine implemented and verified on Dataset E (30/30 automated checks pass).

> 💡 **Collaborator Quickstart:** Pulling this branch to test or train the model? Follow the step-by-step instructions in [VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md).

---

## 1. Status snapshot

| Item | Value |
|---|---|
| Detector | YOLO11s (`runs/aerointel_v1_yolo11s/`), exported `models/aerointel_v1.onnx` |
| Dataset (training) | Merged ABC dataset — 8,525 images, 15,252 annotations, 4 classes |
| Training result (val split) | best **mAP50 0.623** / **mAP50-95 0.410**, P 0.787, R 0.579 |
| Test result (held-out test split) | **mAP50 0.613** / **mAP50-95 0.405**, P 0.769, R 0.575 (PASS vs A6 target ≥ 0.60) |
| Train time | ~3.5 h on a free Colab T4 |
| AeroMemory engine | ✅ implemented (`aeromemory/` package), verified on Dataset E — 30/30 PASS |
| Dataset E (synthetic benchmark) | ✅ complete & verified — 1,200 sequential inspection images with temporal ground truth |
| Dataset D (unseen field images) | ⬜ not yet collected (independent task) |

## 2. System architecture

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
                     (ORB Registration + Rule-Based Matching)
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                  Spatial Delta /           Temporal State
                 Centroid Distance             Machine
                         │                         │
                         ▼                         ▼
               Growth Metrics (Δmm, rate)   NEW / STABLE / PROGRESSING /
                         │                  DECREASED / RESOLVED
                         └────────────┬────────────┘
                                      ▼
                     Relational Storage & Timeline (SQLite/PostgreSQL)
                                      │
                                      ▼
                     Automated Decision Support Advisory
```

### Core capabilities

1. **Defect detection (YOLO11s):** 4 frozen classes — `0 crack, 1 corrosion, 2 dent, 3 missing_fastener`. Class IDs are **frozen forever** — downstream consumers (backend, frontend) must map by ID, never by display string (see `ml/class_map.yaml`).
2. **AeroMemory™ longitudinal engine:**
   - **Registration:** OpenCV ORB feature matching with RANSAC homography to align inspection frames across viewpoint shifts (`aeromemory/registration.py`).
   - **Rule-based matching:** deterministic spatio-temporal bipartite matcher using IoU (≥ 0.30) + centroid proximity — no secondary re-identification ML model (`aeromemory/matcher.py`).
   - **Progression classification:** defect lifecycle states `NEW / STABLE / INCREASED / DECREASED / RESOLVED` (`aeromemory/progression.py`).
   - **Severity & decision support:** deterministic maintenance recommendations mapped to severity and growth rate (`aeromemory/severity.py`).
   - **Persistence:** relational repository pattern with SQLite (`aeromemory/repository.py`, `aeromemory/database.py`).

## 3. Repository structure

```text
AeroIntel/
├── aeromemory/                      # AeroMemory longitudinal engine
│   ├── registration.py              # ORB + RANSAC homography alignment
│   ├── matcher.py                   # rule-based defect matching
│   ├── progression.py               # lifecycle state classification
│   ├── severity.py                  # severity scoring
│   ├── comparator.py                # growth-metric computation
│   ├── repository.py / database.py  # SQLite persistence
│   └── service.py                   # AeroMemoryService facade
├── ml/
│   ├── class_map.yaml               # frozen class schema
│   └── colab/                       # 01_data_prep / 02_train_yolo / 03_eval_export notebooks
├── models/
│   ├── aerointel_v1.onnx            # exported YOLO11s detector
│   └── registry.json                # model metadata + class mapping
├── runs/                            # training artifacts (weights NOT committed — rule B4)
├── scripts/                         # train / detect / validate / export CLI
├── tools/
│   ├── test_images.py               # ONNX inference smoke test
│   ├── test_aeromemory_on_dataset_e.py   # strict 30/30 verification suite
│   ├── run_aeromemory_team_demo.py  # demo runner + report generator
│   └── audit_dataset.py             # dataset audit utility
├── outputs/team_demo/               # 4 visual comparison panels + engineering report
├── datasets/                        # master_dataset_ABC (training), dataset_D (held-out field), dataset_E_aeromemory (synthetic benchmark, LFS)
├── docs/
│   ├── DECISIONS.md                 # append-only architectural decision log
│   ├── PROGRESS.md                  # milestone dashboard + changelog
│   └── TECHNICAL_INTEGRATIONS.md    # stack, contracts, integration log
└── FRONTEND_SPEC.md / UI_DESIGN_BRIEF.md / STITCH_GUIDE.md / mockApi.js
```

## 4. Verification & testing

**Test detector inference (ONNX):**

```bash
python tools/test_images.py path/to/image.jpg
python tools/test_images.py final_visual_test/predictions --conf 0.25
```

**Run AeroMemory automated verification (Dataset E):** strict defect-by-defect comparison across progression scenarios; exits `0` on 100% pass:

```bash
python tools/test_aeromemory_on_dataset_e.py
```

**Run the AeroMemory team demo** (4 MRO scenarios → comparison panels + report in `outputs/team_demo/`):

```bash
python tools/run_aeromemory_team_demo.py
```

**Re-run training (Colab):** open `ml/colab/02_train_yolo.ipynb` with a T4 GPU runtime and *Runtime → Run all*. Training is checkpoint-safe: it runs in chunks, syncs to Drive, and auto-resumes from `last.pt`.

## 5. Documentation system — how this repo stays honest

Four living documents. **After every change, update them**:

| File | Owns | Update when |
|---|---|---|
| `README.md` | What the project is + status snapshot | Any externally visible change |
| `docs/DECISIONS.md` | The *why* — every technical decision + rationale | Every choice made (append `D-xxx`, never rewrite) |
| `docs/PROGRESS.md` | The *when* — milestones + dated changelog | Every work session |
| `docs/TECHNICAL_INTEGRATIONS.md` | The *how* — stack, contracts, integration iterations | Every contract/format/version change |

**Update protocol:** do the work → add a dated bullet to `docs/PROGRESS.md` → append `D-xxx` if a decision was made → add `IT-xxx` if a contract changed → refresh the snapshot tables. Never fabricate numbers: leave `?` / `TODO` until verified from an artifact.

## 6. Immediate next steps

1. **Frontend via Stitch** — generate the UI from `FRONTEND_SPEC.md` + `UI_DESIGN_BRIEF.md` + `STITCH_GUIDE.md`, wiring to `mockApi.js` until the backend lands.
2. ~~Backend `/api/detect` smoke test~~ ✅ done — FastAPI backend in `backend/` runs the ONNX end-to-end; phase 1 & 3 suites pass locally (see `docs/PROGRESS.md`).
3. Collect the ≥ 50-image field test set (Dataset D) and evaluate on it.
4. Record license verification for the merged ABC dataset in `ml/01_download.md` (CC BY 4.0 credit in all reports).

See `docs/PROGRESS.md` for the full picture.
