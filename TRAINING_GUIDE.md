# AeroIntel - YOLO Training Guide

## 1. OFFICIAL DATASET

**TRAIN ONLY FROM:**

`datasets/master_dataset_ABC/`

Do NOT train from:

- `datasets/dataset_A/`
- `datasets/dataset_B/`
- `datasets/dataset_C/`
- `datasets/master_dataset/`
- `datasets/D/`
- `datasets/E/`
- `datasets/F/`

The old `master_dataset` is an older B+C dataset and must NOT be used for the final AeroIntel model.

## 2. Dataset Structure

```text
datasets/master_dataset_ABC/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
├── data.yaml
└── merge_report.txt
```

## 3. Dataset Roles

### Training

`datasets/master_dataset_ABC/train/`

Use this split to train the YOLO model.

### Validation

`datasets/master_dataset_ABC/valid/`

Use this split for model selection, hyperparameter monitoring, and validation metrics.

### Test

`datasets/master_dataset_ABC/test/`

Do NOT use this split during training or hyperparameter tuning. It is the final held-out evaluation set.

## 4. Classes

Use exactly this order:

```text
0 Crack
1 Corrosion
2 Dent
3 Missing Fastener
```

Do not rename, reorder, merge, or add classes.

## 5. data.yaml

Use:

`datasets/master_dataset_ABC/data.yaml`

Do not create a different class mapping manually.

## 6. Recommended First Training Run

Use this baseline for the first run:

- Model: YOLO small variant supported by the installed Ultralytics version
- Image size: 640
- Epochs: 50
- Batch: `auto`, or choose according to available GPU memory
- Device: GPU

The first run is a baseline. Do not immediately change many parameters.

## 7. What To Save

After training, save:

- `best.pt`
- `last.pt`
- `results.csv`
- `results.png`
- `confusion_matrix.png`

Also record:

- Precision
- Recall
- mAP50
- mAP50-95
- Per-class metrics for Crack, Corrosion, Dent, and Missing Fastener

## 8. Test Evaluation

After the model and training configuration are finalized, evaluate once on:

`datasets/master_dataset_ABC/test/`

The test set must remain untouched during training and tuning.

Record:

- Test Precision
- Test Recall
- Test mAP50
- Test mAP50-95
- Per-class metrics
- Confusion matrix

## 9. Important Rules

1. Do not move images between train, valid, and test.
2. Do not add external images into the final dataset without documenting them.
3. Do not modify labels after training has started without creating a new dataset version.
4. Do not use test images for training.
5. Do not tune the model using test metrics.
6. Keep the original `master_dataset` untouched.
7. Keep `merge_report.txt` with the dataset.
8. Record the exact model version and training parameters.
9. Record the date of each training run.
10. Keep `best.pt` for the best validation checkpoint.

## 10. Dataset Version

Dataset version: **AeroIntel-ABC-v1**

```text
AeroIntel-ABC-v1 = datasets/master_dataset_ABC/
```

Any future dataset modification should become v2, v3, etc. rather than silently replacing v1.

## 11. Final Workflow

```text
FINAL DATASET
    ↓
Train → train/
    ↓
Validate → valid/
    ↓
Select/finalize model
    ↓
ONE-TIME FINAL EVALUATION → test/
    ↓
best.pt
    ↓
AeroIntel FastAPI / Edge AI integration
```

## 12. Handoff Checklist

Before training, confirm:

- [ ] I am using `datasets/master_dataset_ABC/`
- [ ] I am using `data.yaml` from that folder
- [ ] I have 4 classes in the correct order
- [ ] Train = `train/`
- [ ] Validation = `valid/`
- [ ] Test = `test/`
- [ ] I will not train on `test/`
- [ ] I will save `best.pt`
- [ ] I will save training metrics
- [ ] I will record the model/version and training parameters

"THIS IS THE OFFICIAL AEROINTEL YOLO TRAINING DATASET. TRAIN FROM master_dataset_ABC ONLY."
