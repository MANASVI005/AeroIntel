# AeroIntel - Project Progress

## 1. Current Status

- DATASET PREPARATION: COMPLETE
- FINAL TRAINING DATASET: READY
- INDEPENDENT VALIDATION: PASSED
- MODEL TRAINING: NOT STARTED

The final training dataset is:

`datasets/master_dataset_ABC/`

## 2. Final Dataset

- Total images: 8,525
- Train: 6,820
- Valid: 852
- Test: 853
- Total annotations: 15,252

Classes:

- `0 = Crack`
- `1 = Corrosion`
- `2 = Dent`
- `3 = Missing Fastener`

Class statistics:

- Crack: 5,192 annotations / 3,791 images
- Corrosion: 2,597 annotations / 1,148 images
- Dent: 3,869 annotations / 2,588 images
- Missing Fastener: 3,594 annotations / 1,571 images

## 3. Dataset Sources

### Dataset A

- Aircraft Corrosion YOLO
- 1,148 final images
- 2,597 annotations
- Contributes Corrosion

### Dataset B

- Aircraft Skin Defects
- 1,078 final images
- 1,630 annotations

### Dataset C

- Aircraft Defect Detection
- 6,299 final images
- 11,025 annotations
- 715 polygon annotations converted to YOLO bounding boxes

Datasets D, E, and F were NOT used for YOLO training.

## 4. Final Split

- 80% train
- 10% validation
- 10% test

The split was freshly generated with seed `42`.

The final dataset is leakage-controlled. Exact duplicate images do not cross train, validation, and test splits. Near-duplicate groups were also prevented from crossing splits.

## 5. Validation Status

Independent validation passed with 0 errors.

- Dataset structure: PASS
- Image/label pairing: PASS
- Orphan/missing labels: PASS
- YOLO 5-field labels: PASS
- Valid class IDs: PASS
- Valid normalized coordinates: PASS
- Bounding boxes inside images: PASS
- Empty labels: PASS
- Corrupt images: PASS
- Exact cross-split leakage: PASS
- Near-duplicate split leakage: PASS
- `data.yaml`: PASS
- Ultralytics-compatible structure: PASS

## 6. Conflict Curation

Several exact-image annotation conflicts were identified during the A+B+C merge. Approved conflicts were handled using narrowly guarded rules. Unresolved ambiguous conflicts were excluded rather than assigning unsupported labels.

All decisions are recorded in:

`datasets/master_dataset_ABC/merge_report.txt`

## 7. Important Dataset Rule

Do NOT train directly from Dataset A, Dataset B, Dataset C, the old `master_dataset`, Dataset D, Dataset E, or Dataset F.

The official AeroIntel training dataset is:

`datasets/master_dataset_ABC/`
