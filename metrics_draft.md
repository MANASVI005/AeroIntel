# AeroIntel model metrics — aerointel_v1_yolo11s (draft)

## Overall (held-out test split)
- precision: 0.769 | recall: 0.575 | mAP50: 0.613 | mAP50-95: 0.405

## Per class (never hide a weak class behind the average)
- **Crack**: P=0.757 R=0.619 mAP50=0.654 mAP50-95=0.447
- **Corrosion**: P=0.565 R=0.213 mAP50=0.233 mAP50-95=0.099
- **Dent**: P=0.913 R=0.861 mAP50=0.887 mAP50-95=0.688
- **Missing Fastener**: P=0.839 R=0.607 mAP50=0.677 mAP50-95=0.388

## Latency (CPU)
- p50: 284.5 ms | p95: 415.0 ms (conf 0.40, IoU 0.50, imgsz 640) — re-measure on the demo laptop before final submission.

## Field test set (spec A6 — fill in after collecting >=50 unseen images)
- TODO: same table on the field set. Expect a drop vs the dataset metrics; state it honestly.

## Known weaknesses / experimental classes
- TODO: list classes below usable level and mark them experimental per A6.
