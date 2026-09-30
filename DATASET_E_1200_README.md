# AeroIntel Dataset E v2 — 1,200 images

- 200 aircraft histories
- 6 inspections per aircraft
- exactly 1,200 images
- 30-day inspection interval
- 1024×1024 PNG
- deterministic seed 42
- Crack, Corrosion, Dent, Missing Fastener
- historical progression, new, stable, resolved, mixed and camera-variation scenarios
- JSON metadata for every inspection

This dataset is for AeroMemory validation only. It is **not for YOLO training**.

Copy the generator to:
`tools/generate_aeromemory_dataset.py`

Run:
`python tools/generate_aeromemory_dataset.py`

The generator reads `datasets/master_dataset_ABC` as read-only visual context and writes only to `datasets/dataset_E_aeromemory/`.
