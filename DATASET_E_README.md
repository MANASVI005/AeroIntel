# Dataset E Generator

## Install

From the AeroIntel repository:

```bash
pip install pillow numpy
```

## Install script

Copy `generate_aeromemory_dataset.py` into:

```text
tools/generate_aeromemory_dataset.py
```

## Run

From the repository root:

```bash
python tools/generate_aeromemory_dataset.py
```

The generator expects the existing final Dataset A+B+C at:

```text
datasets/master_dataset_ABC/
```

It creates only:

```text
datasets/dataset_E_aeromemory/
```

## Result

- 12 aircraft
- 5 inspections each
- 60 images
- per-image ground-truth metadata
- longitudinal comparison ground truth
- progression cases
- deterministic generation with seed 42
- validation report

Dataset E is for AeroMemory validation, not YOLO training.
