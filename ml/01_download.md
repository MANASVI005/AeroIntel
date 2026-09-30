# 01_download.md — Dataset provenance record

Per spec A6 step 1: a written record of where each dataset came from, its version and license.
Update this file the moment a dataset is downloaded. Never fabricate numbers — leave `?` until verified.

## How to download

### Roboflow datasets (recommended path)
1. Create/find the dataset page on Roboflow Universe, verify image count, split structure, augmentation and license **[CONFIRM]**.
2. In Colab notebook `ml/colab/01_data_prep.ipynb`, cell "Download Roboflow dataset", set:
   - `ROBOFLOW_API_KEY` (get from Roboflow account settings; do NOT commit it)
   - `RF_WORKSPACE`, `RF_PROJECT`, `RF_VERSION`
3. The notebook downloads the YOLOv8-format export into Drive `AeroIntel/datasets/raw/<name>/` and records the version in `download_log.txt`.

### Manual upload fallback
1. Download the dataset zip on your machine.
2. Upload to Google Drive under `AeroIntel/datasets/raw_uploads/` (raw, do not extract or rename).
3. Add a row to the table below.

## Source table (fill in week 1 — all [CONFIRM])

| Source | Origin / URL | Version | License | Original classes | Maps to | Images | Split structure | Augmented? |
|---|---|---|---|---|---|---|---|---|
| roboflow_aircraft_corrosion | Roboflow Universe (Aircraft Corrosion YOLO) | ? (v2 export) | CC BY 4.0 (verify) | corrosion | corrosion | reported 1,148 — verify | ? | reported yes — prefer unaugmented export |
| dataset_b (crack / missing_fastener) | ? | ? | ? | ? | ? | ? | ? | ? |
| dataset_c (dent) | ? | ? | ? | ? | ? | ? | ? | ? |
| dataset_d (mixed) | ? | ? | ? | ? | ? | ? | ? | ? |

## Field test set (spec A6)
- Collect >= 50 images never used in training (photos of printed/on-screen aircraft images, or real metal surfaces).
- Store under `AeroIntel/datasets/field_test/` with labels in YOLO format. Evaluated separately in `03_eval_export.ipynb`.

## Attribution to carry into reports/slides
- Roboflow Aircraft Corrosion dataset: CC BY 4.0 — include credit line in every PDF report and slide deck.
