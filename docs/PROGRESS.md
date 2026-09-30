# AeroIntel — PROGRESS.md

**Status dashboard + changelog.** Update after every work session: refresh §1, move milestones, and append a dated changelog entry at the bottom. Numbers only from verified artifacts — `?` until then.

---

## 1. Status dashboard

**Last updated: 2026-09-27**

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
| **AeroMemory™ Engine Core** | ✅ done | rule-based matching, ORB alignment, SQLite repo, progression states |
| **Dataset E Automated Verification** | ✅ done | 30/30 inspections PASS (`tools/test_aeromemory_on_dataset_e.py`, Exit 0) |
| **AeroMemory Team Demo & Visuals** | ✅ done | 4 visual comparison panels + report in `outputs/team_demo/` |
| Field test set (Dataset D, unseen images) | 🔄 in progress | Handled independently by teammate |
| Backend `/api/detect` smoke test | ⬜ not started | R2 detector service, spec A8 |
| Repo hygiene (`.gitignore` for weights) | ✅ done | `.pt`, `.onnx`, `datasets/*.zip`, `eval_workspace/` ignored |

---

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

### ✅ M5 — AeroMemory™ Longitudinal Tracking Engine
- [x] Package structure in `aeromemory/` with repository pattern (`AeroMemoryRepository`, `SQLiteAeroMemoryRepository`).
- [x] OpenCV ORB feature alignment and RANSAC homography estimation (`registration.py`).
- [x] Bipartite defect matcher using bounding box IoU ($\ge 0.30$) and normalized centroid proximity ($< 15\%$ width).
- [x] Progression engine classifying defects into `NEW`, `STABLE`, `INCREASED`, `DECREASED`, and `RESOLVED` with dynamic decision support.
- [x] Fixed AI-006 repair status filtering bug: `get_active_defects` excludes `'Closed'` and `'Repaired'` defects.
- [x] Hardened `tools/test_aeromemory_on_dataset_e.py` with dictionary state mapping and non-zero exit codes.
- [x] Verified 30/30 sequential inspections across Dataset E benchmark scenarios (Exit Code 0).
- [x] Built `tools/run_aeromemory_team_demo.py` generating side-by-side comparison panels in `outputs/team_demo/`.

### 🔜 M6 — Field validation (Dataset D) & Integration
- [ ] Evaluate YOLO11s on unseen Dataset D images (teammate's task).
- [ ] Smoke-test end-to-end integration between `/api/detect` and AeroMemory pipeline.
- [ ] Complete license/provenance documentation for source datasets.

### 🔮 M7 — v2 ideas (not started)
- Recall improvement: more corrosion/crack diversity (recall is the weak spot at ~0.58).
- Multi-camera 3D defect coordinate mapping.
- Per-class confusion analysis → targeted data collection.

---

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
| AeroMemory Test Pass Rate | 30/30 (100%) | `tools/test_aeromemory_on_dataset_e.py` |

---

## 4. Changelog

### 2026-09-24 — Model v1 training completed
- Trained `aerointel_v1_yolo11s` for the full 100 epochs (early stopping never fired). Best val mAP50 0.623 / mAP50-95 0.410 @ epoch 89; ~3.5 h on a free Colab T4.
- Run artifacts (weights, `args.yaml`, `results.csv`, plots, confusion matrix) synced to Drive and copied into `runs/aerointel_v1_yolo11s/`.

### 2026-09-25 — Project documentation created
- Analysed the whole folder: dataset zip (+ `merge_report.txt`), three Colab notebooks, class map, provenance record, and the full training run.
- Created the living-docs system: `README.md` (status snapshot), `docs/DECISIONS.md` (D-001…D-015), `docs/PROGRESS.md` (this file), `docs/TECHNICAL_INTEGRATIONS.md` (stack, contracts, IT log).

### 2026-09-26 — Model evaluation, export & collaborator guide
- Verified test-split evaluation (mAP50 = 0.613) and CPU latency benchmarks.
- Created `VERIFICATION_GUIDE.md` for collaborators to test inference and re-run training.
- Created `model-training-and-eval` branch and pushed verified artifacts to remote.

### 2026-09-27 — AeroMemory Engine Implemented & Verified on Dataset E
- Implemented full `aeromemory` package (models, repository, homography registration, matcher, comparator, progression, severity, and high-level service).
- Fixed AI-006 duplicate resolution bug: updated `get_active_defects` to filter `status NOT IN ('Closed', 'Repaired')`, eliminating phantom re-resolution on subsequent clean inspections.
- Upgraded `tools/test_aeromemory_on_dataset_e.py` with dictionary-based ground-truth matching, empty comparison validation, synthetic benchmark disclaimers, and strict non-zero exit codes.
- Achieved 100% test pass (30/30 inspections) across benchmark scenarios AI-001, AI-002, AI-003, AI-006, and AI-019.
- Generated 4 high-clarity visual comparison panels and formal engineering report in `outputs/team_demo/`.

### 2026-09-30 — Branch integration & full local verification
- Integrated all branches into `main`: merged `model-training-and-eval` (YOLO v1 pipeline, ONNX, Stitch docs) and `AEROMEMORY` (AeroMemory engine, Dataset E docs, team demo outputs), resolving 6 conflicts; grafted the unique, unrelated-history parts of `feature/aeromemory` directly (FastAPI `backend/`, Vite React `frontend/` scaffold, phase 1–4 test suites, `requirements.txt`, `REALTIME_IMAGE_CAPTURE.md`). `feature/aeromemory`'s LFS datasets and duplicate tree were intentionally left out.
- Unified docs: combined README (training narrative + AeroMemory architecture), union `.gitignore`, root `PROGRESS.md` gained the Phase 1–4 table, Phase 5 LAN/mobile-capture section, and independent dataset validation from `feature/aeromemory`.
- Fixed SQLite autoincrement: all 9 backend PK columns now use `BigInteger().with_variant(Integer, "sqlite")` — Postgres behavior unchanged; phases 1 & 3 went from hard failure to full pass on a fresh local SQLite DB.
- Added `python-dotenv` and `httpx` to `requirements.txt` (backend import crash and TestClient dependency were missing).
- Verified locally: ONNX loads and detects (Corrosion @ 0.656 on a real test image), FastAPI `/` + `/health` return 200 with DB connected, frontend `tsc --noEmit` + `vite build` pass, phase 1 & 3 exit 0, `mockApi.js` contracts match the backend routes.
- Not runnable locally (LFS-only data): Dataset E 30/30 suite and phase 2; phase 4 additionally expects a pre-populated dev database (hardcoded `DEF-010`) — flagged for follow-up.
- Brought all branch data into `main`: checked out `datasets/dataset_D` (1,493 files, plain git) and `datasets/dataset_E_aeromemory` (2,404 files) from `feature/aeromemory`; added an LFS tracking rule for Dataset E PNGs and pulled all 1,200 objects (~1.1 GB, verified as valid PNGs). `main` now fully contains every branch's content, datasets included.

### 2026-09-30 — Stitch prompt workbook v2 (landing + 3D hero + full spec)
- Rewrote `STITCH_GUIDE.md` as the single copy-paste file: new public Landing screen matching the sky-blue reference image (glassy pill navbar, hero, dashboard section scrolling below) with a dedicated **3D rotating aircraft hero slot** (auto-rotate, draggable, no chrome; wires to `frontend/public/models/G4_LARC_AIR_0824.glb` via three.js/@react-three/fiber), plus all 11 screens from the product brief (Dashboard, New Inspection with preview/processing states, Inspection Result with AeroMemory Analysis + decision-support wording, History, AeroMemory with timeline/overlay, Reports, Inspection Report, Model Performance, Settings with System Status, Mobile Capture).
- Theme is **not hard-coded anywhere**: the master prompt delegates the entire visual system (colors, gradients, glass, typography mood, per-class accent mapping) to the attached reference image.
- Saved the collaborator's full functional specification as `docs/FRONTEND_PRODUCT_SPEC.md`; marked root `FRONTEND_SPEC.md` as superseded (kept as the v1 data-contract reference).

### 2026-09-30 — Main declared the single integrated branch; pushed
- `main` pushed to origin as the consolidated integration of all former branches (training/eval, AeroMemory engine, backend, frontend scaffold, datasets). README now carries an explicit "integrated main — use this" banner with quick-start commands; stale branch references removed from `VERIFICATION_GUIDE.md` and `models/README.md`.
- Stitch UI work continues from `STITCH_GUIDE.md` (master prompt + 11 screen prompts + real backend reference). A collaborator has a pre-merge branch in progress — will be rebased/integrated onto this main when ready.

### 2026-09-30 — Frontend integration complete (Stitch UI → real app, Stages 0–1)
- Built the full real frontend on the Stitch design system (Tailwind CDN tokens, Material Symbols, Plus Jakarta Sans/Inter): Landing with 3D hero + live inspection record + real model metrics, Dashboard, New Inspection (create → upload/camera → processing → result), Inspection Result (bbox overlay, AeroMemory, per-detection decision support via POST /api/decisions), Inspection History (search/filter/CSV/pagination), AeroMemory (tracked-defect review), Reports + printable Inspection Report (print CSS + JSON export), Model Performance, read-only Settings. Logo applied site-wide.
- Governing rules: step-gated workflow, no mid-work pushes, session-carrying plan doc, and the user's NO-HOLLOW-UI rule — every Stitch element without a backend was removed or replaced with real data (invented KPIs/charts/telemetry/compliance badges stripped; demo data only where explicitly labeled).
- New backend endpoint: GET /api/metrics serving logs/eval + logs/latency + models/registry verbatim (9 endpoints total).
- Key backend facts documented: bbox {x,y,width,height}; upload field "file"; inspection.status always "completed" at create (upload never flips it); thresholds conf 0.40 / IoU 0.50 fixed server-side; /data static mount serves stored images.
- Verified: tsc --noEmit clean, vite build clean, all 11 routes HTTP 200, /health + /api/metrics + /api/inspections 200, E2E flow previously verified (inspection 11 → Corrosion 0.656 + AeroMemory DEF-001 stable/High; inspection 10 → DEF-004 Progressing/Critical).
- Deferred by user: Step 1.10 mobile-capture restyle (route + page exist), Stage 2.2 seed script (panel_id=1 hardcode), Stage 2.3 AeroMemory compare endpoint, GLTF hero model swap.
- Session-carrying details: docs/FRONTEND_INTEGRATION_PLAN.md (checklist + 16-entry session log + discovered facts).
- Commit hygiene: at the user's request, "Generated with Codebuff / Co-Authored-By: Codebuff" attribution trailers were removed from all main-branch commit messages before pushing (history rewritten, force-push); all commits remain authored solely by their real human authors.

### 2026-09-30 — GLTF hero swap + docs refresh (frontend wrap-up)
- Replaced the procedural 3D hero plane with the team's `G4_LARC_AIR_0824.glb` (glTF 2.0, embedded textures, already tracked in the repo) via three.js r147 `GLTFLoader`; model normalized and camera auto-framed from its real size + canvas aspect (no clipping at any rotation angle), slow delta-time auto-rotation, procedural plane kept as automatic fallback. License/provenance recorded in `frontend/public/models/CREDITS.md` (confirm before public distribution).
- User-review iterations: aligned beside hero text (camera lookAt), slowed rotation to ~45 s/turn, fixed 120 Hz double-speed spin (delta-time), removed float/wave motion, zoomed to the geometric max fill (margin 1.0).
- Sidebar logo now links back to the landing page from every screen.
- Docs refreshed for the frontend-complete state: README (status snapshot row + next steps), this file, `docs/FRONTEND_INTEGRATION_PLAN.md` (hero swap logged, 3.2 checked).
- Remaining backlog: seed script (panel hardcode), mobile-capture restyle, AeroMemory compare endpoint, dataset/model license verifications.
