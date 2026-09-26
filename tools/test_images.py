"""Run the exported AeroIntel detector on one image or a folder."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from ultralytics import YOLO


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Image file or folder of images")
    parser.add_argument("--model", type=Path, default=Path("models/aerointel_v1.onnx"))
    parser.add_argument("--conf", type=float, default=0.40)
    parser.add_argument("--iou", type=float, default=0.50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--save-dir", type=Path, default=Path("runs/image_test"))
    return parser.parse_args()


def image_paths(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(
            path for path in source.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS
        )
    raise FileNotFoundError(f"Source does not exist: {source}")


def main() -> int:
    args = parse_args()
    save_dir = args.save_dir.resolve()
    images = image_paths(args.source)
    if not images:
        raise FileNotFoundError(f"No image files found in: {args.source}")

    model = YOLO(str(args.model))
    class_counts: Counter[str] = Counter()
    images_with_detections = 0
    total_detections = 0

    for image_path in images:
        results = model.predict(
            str(image_path),
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            save=True,
            project=str(save_dir.parent),
            name=save_dir.name,
            exist_ok=True,
            verbose=False,
        )
        result = results[0]
        detections = len(result.boxes)
        total_detections += detections
        images_with_detections += detections > 0

        print(f"{image_path}: {detections} detection(s)")
        for class_id, confidence in zip(result.boxes.cls, result.boxes.conf):
            class_name = result.names[int(class_id)]
            class_counts[class_name] += 1
            print(f"  - {class_name}: confidence={float(confidence):.3f}")

    print("\nSummary")
    print(f"Images tested: {len(images)}")
    print(f"Images with detections: {images_with_detections}")
    print(f"Total detections: {total_detections}")
    print(f"Detections by class: {dict(class_counts)}")
    print(f"Annotated images: {save_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())