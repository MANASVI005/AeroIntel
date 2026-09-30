"""
AeroIntel - YOLOv8 Model Evaluation & Validation Script
Evaluates best.pt on validation or held-out test split.
Outputs overall and per-class Precision, Recall, mAP50, and mAP50-95.

Usage:
    python scripts/validate.py --weights models/best.pt --data datasets/master_dataset_ABC/data.yaml --split val
    python scripts/validate.py --weights models/best.pt --data datasets/master_dataset_ABC/data.yaml --split test
"""

import argparse
from pathlib import Path
from ultralytics import YOLO

CLASS_NAMES = {
    0: "Crack",
    1: "Corrosion",
    2: "Dent",
    3: "Missing Fastener"
}


def evaluate(weights_path: str, data_yaml: str, split: str = "val", batch: int = 16, imgsz: int = 640):
    weights = Path(weights_path)
    data = Path(data_yaml)

    if not weights.exists():
        raise FileNotFoundError(f"Model weights not found at: {weights}")
    if not data.exists():
        raise FileNotFoundError(f"data.yaml not found at: {data}")

    print("=" * 70)
    print(f"AEROINTEL MODEL EVALUATION [{split.upper()} SET]")
    print("=" * 70)
    print(f"Evaluating Model : {weights}")
    print(f"Dataset YAML     : {data}")
    print(f"Target Split     : {split}")
    print("-" * 70)

    model = YOLO(str(weights))

    # Run validation
    metrics = model.val(
        data=str(data),
        split=split,
        batch=batch,
        imgsz=imgsz,
        conf=0.001,             # Standard benchmark confidence threshold
        iou=0.6,                # Standard IoU threshold
        save_json=True,
        plots=True
    )

    # Extract overall metrics
    precision = metrics.box.mp
    recall = metrics.box.mr
    map50 = metrics.box.map50
    map50_95 = metrics.box.map

    print("\n" + "=" * 70)
    print(f"OVERALL PERFORMANCE METRICS ({split.upper()} SET)")
    print("=" * 70)
    print(f"  Precision (P)    : {precision:.4f} ({precision * 100:.2f}%)")
    print(f"  Recall (R)       : {recall:.4f} ({recall * 100:.2f}%)")
    print(f"  mAP@0.50         : {map50:.4f} ({map50 * 100:.2f}%)")
    print(f"  mAP@0.50:0.95    : {map50_95:.4f} ({map50_95 * 100:.2f}%)")
    print("-" * 70)

    # Per-class breakdown
    print(f"\nPER-CLASS METRICS BREAKDOWN ({split.upper()} SET):")
    print("-" * 70)
    header = f"{'Class ID':<10} | {'Defect Name':<18} | {'Precision':<10} | {'Recall':<10} | {'mAP@0.50':<10} | {'mAP@0.50:0.95':<12}"
    print(header)
    print("-" * len(header))

    for cid in range(len(CLASS_NAMES)):
        cname = CLASS_NAMES[cid]
        try:
            p_cls = metrics.box.p[cid] if hasattr(metrics.box, "p") and len(metrics.box.p) > cid else float("nan")
            r_cls = metrics.box.r[cid] if hasattr(metrics.box, "r") and len(metrics.box.r) > cid else float("nan")
            map50_cls = metrics.box.ap50[cid] if hasattr(metrics.box, "ap50") and len(metrics.box.ap50) > cid else float("nan")
            map_cls = metrics.box.ap[cid] if hasattr(metrics.box, "ap") and len(metrics.box.ap) > cid else float("nan")
            print(f"{cid:<10} | {cname:<18} | {p_cls:<10.3f} | {r_cls:<10.3f} | {map50_cls:<10.3f} | {map_cls:<12.3f}")
        except Exception:
            print(f"{cid:<10} | {cname:<18} | Class metric unavailable")

    print("-" * len(header))
    print(f"\nEvaluation plots (confusion matrix, PR curve) saved to:")
    print(f"--> {metrics.save_dir}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AeroIntel YOLOv8 Model")
    parser.add_argument("--weights", type=str, default="models/best.pt", help="Path to weights file")
    parser.add_argument("--data", type=str, default="datasets/master_dataset_ABC/data.yaml", help="Path to data.yaml")
    parser.add_argument("--split", type=str, default="val", choices=["val", "test"], help="Dataset split to evaluate")
    parser.add_argument("--batch", type=int, default=16, help="Evaluation batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    args = parser.parse_args()

    evaluate(args.weights, args.data, args.split, args.batch, args.imgsz)
