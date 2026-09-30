# AeroIntel Model Artifacts

Per project rule B4 (documented in `docs/DECISIONS.md`), large binary weights (`.pt` and `.onnx`) are not committed to Git to keep the repository lightweight.

## Model Registry
The metadata for current models is stored in `models/registry.json`.

- Current default model: `aerointel_v1`
- Type: `yolo11-onnx`
- Base model: `aerointel_v1_yolo11s` (YOLO11s, 640px input)
- Target defect classes:
  - 0: Crack
  - 1: Corrosion
  - 2: Dent
  - 3: Missing Fastener

## Availability in this Branch
- **`models/aerointel_v1.onnx`** (37.9 MB) is committed directly to this branch (`model-training-and-eval`) so collaborators can test inference immediately upon `git pull` without manual downloads.
- Raw training checkpoints (`best.pt`, `last.pt`) remain in Google Drive under:
  `Drive/AeroIntel/runs/aerointel_v1_yolo11s/weights/{best.pt, last.pt}`

To generate or export a new ONNX binary, run `ml/colab/03_eval_export.ipynb`.
