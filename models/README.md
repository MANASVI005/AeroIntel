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

## Storage Location
Model weights and exported ONNX binaries are stored in Google Drive under:
`Drive/AeroIntel/models/aerointel_v1.onnx`
and training checkpoints in:
`Drive/AeroIntel/runs/aerointel_v1_yolo11s/weights/{best.pt, last.pt}`

To generate or export a new ONNX binary, run `ml/colab/03_eval_export.ipynb`.
