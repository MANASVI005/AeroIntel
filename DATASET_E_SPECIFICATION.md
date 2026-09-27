# Dataset E — AeroMemory Synthetic Longitudinal Dataset

## Purpose

Dataset E validates AeroIntel's **AeroMemory**, historical comparison,
progression analysis, and prototype decision-support workflow.

It is **not a YOLO training dataset**.

## Fixed v1.0

- 12 aircraft histories
- 5 inspections per aircraft
- 60 inspection images
- 1024 × 1024 PNG
- Seed: 42
- Synthetic calibration: 10 pixels/mm
- 30-day inspection interval
- Classes: Crack, Corrosion, Dent, Missing Fastener

## Scenarios

1. AI-001 — crack progression
2. AI-002 — faster crack progression
3. AI-003 — stable crack
4. AI-004 — corrosion progression
5. AI-005 — accelerating corrosion
6. AI-006 — stable corrosion
7. AI-007 — dent depth progression
8. AI-008 — dent dimension progression
9. AI-009 — stable dent
10. AI-010 — missing fastener appears
11. AI-011 — new crack appears and progresses
12. AI-012 — mixed defects and repair/resolution

## Output

```text
datasets/dataset_E_aeromemory/
├── aircraft/
│   ├── AI-001/
│   │   ├── INS-001/
│   │   │   ├── image.png
│   │   │   └── image.json
│   │   └── ...
│   └── ...
├── index.json
├── progression_cases.json
├── generation_config.json
└── dataset_E_report.txt
```

The metadata stores aircraft ID, inspection date, panel/region IDs,
stable defect IDs, bounding boxes, measurements, severity, lifecycle status,
and expected comparison results.

## Comparison states

Dataset E explicitly covers:

- matched
- stable
- increased
- decreased
- new
- resolved

## Source-image policy

The generator reads existing images from:

```text
datasets/master_dataset_ABC/
```

as read-only base panel context.

It does not modify the source dataset, download anything, scrape the web,
or generate replacement annotations for Dataset A/B/C.

The generated images contain controlled synthetic defect changes while
retaining the same base panel context across an aircraft's five inspections.

## Important

Do not add Dataset E to `datasets/master_dataset_ABC/`.

Do not use Dataset E for YOLO training.

The synthetic severity and decision-support rules are demonstration logic
only and are not certified aircraft maintenance thresholds.
