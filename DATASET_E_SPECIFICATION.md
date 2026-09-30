# Dataset E — AeroMemory Synthetic Longitudinal Dataset

## Purpose

Dataset E validates AeroIntel's **AeroMemory**, historical comparison,
progression analysis, and prototype decision-support workflow.

It is **not a YOLO training dataset**.

## Specifications

- 200 aircraft histories (v2.0, 1,200 images; v1.0 had 12 aircraft)
- 6 inspections per aircraft
- 1024 × 1024 PNG
- Seed: 42
- Synthetic calibration: 10 pixels/mm
- 30-day inspection interval
- Classes: Crack, Corrosion, Dent, Missing Fastener

## Scenarios

1. AI-001 — crack progression (slow growth)
2. AI-002 — faster crack progression (accelerated growth)
3. AI-003 — stable crack (tolerance monitoring)
4. AI-004 — corrosion progression
5. AI-005 — accelerating corrosion
6. AI-006 — crack repair / resolution scenario (stable for cycles 1-4, repaired at cycle 5, clean panel at cycle 6)
7. AI-007 — dent depth progression
8. AI-008 — dent dimension progression
9. AI-009 — stable dent
10. AI-010 — missing fastener appears
11. AI-011 — new crack appears and progresses
12. AI-012 — mixed defects and repair/resolution
13. AI-019 — multi-defect panel with concurrent growth, stability, and new emergence

## Output Structure

```text
datasets/dataset_E_aeromemory/
├── aircraft/
│   ├── AI-001/
│   │   ├── INS-001/
│   │   │   ├── INS-001.png
│   │   │   └── INS-001.json
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

## Comparison States

Dataset E explicitly covers:

- `new`
- `stable`
- `increased`
- `decreased`
- `resolved`

### Repair and Post-Resolution Lifecycle Handling
- In the cycle where a defect is resolved (e.g. `INS-005` in `AI-006`), the defect is omitted from detections, and `comparison_ground_truth` records `{"defect_id": "D01", "state": "resolved"}`. AeroMemory updates the defect status to `Repaired`.
- In subsequent clean inspection cycles (e.g. `INS-006` in `AI-006`), `defects: []` and `comparison_ground_truth: []`. AeroMemory filters `status NOT IN ('Closed', 'Repaired')`, ensuring 0 active defects and 0 spurious comparisons are reported.

## Source-Image Policy

The generator reads existing images from:

```text
datasets/master_dataset_ABC/
```

as read-only base panel context.

It does not modify the source dataset, download anything, scrape the web,
or generate replacement annotations for Dataset A/B/C.

The generated images contain controlled synthetic defect changes while
retaining the same base panel context across an aircraft's sequential inspections.

## Synthetic Benchmark Boundary & Disclaimer

> [!IMPORTANT]
> - Do not add Dataset E to `datasets/master_dataset_ABC/`.
> - Do not use Dataset E for YOLO training.
> - The synthetic severity, measurement calibration (10 px/mm), and decision-support rules are demonstration logic only and are not certified aircraft maintenance thresholds.
> - Dataset E validates algorithmic state-machine transitions and persistence. Physical aircraft airworthiness requires independent validation on real-aircraft imagery (Dataset D).
