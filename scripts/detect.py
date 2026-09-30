"""
AeroIntel - Aircraft Defect Detection Inference Script
Usage:
    python scripts/detect.py --source "path/to/aircraft_image.jpg" --weights "models/best.pt" --conf 0.25
"""

import argparse
import sys
from pathlib import Path
import cv2
from ultralytics import YOLO

# Class mapping and distinct visual colors (BGR format for OpenCV)
CLASS_NAMES = {
    0: "Crack",
    1: "Corrosion",
    2: "Dent",
    3: "Missing Fastener"
}

CLASS_COLORS = {
    0: (0, 0, 255),      # Red for Crack
    1: (0, 215, 255),    # Gold/Yellow for Corrosion
    2: (255, 100, 0),    # Blue for Dent
    3: (255, 0, 255)     # Magenta for Missing Fastener
}


def run_inference(image_path: str, weights_path: str, conf_threshold: float = 0.25, output_dir: str = "outputs/predictions"):
    img_path = Path(image_path)
    weights = Path(weights_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not img_path.exists():
        print(f"ERROR: Image not found at {img_path}")
        sys.exit(1)

    # Check if local weight file exists or if it is a standard ultralytics weight name
    if not weights.exists() and not str(weights_path).startswith("yolo"):
        print(f"ERROR: Model weights not found at {weights}")
        print("Please train the model first or provide a valid .pt checkpoint.")
        sys.exit(1)

    print("=" * 65)
    print("AEROINTEL AIRCRAFT DEFECT DETECTION SYSTEM")
    print("=" * 65)
    print(f"Loading Model : {weights}")
    print(f"Input Image   : {img_path}")
    print(f"Confidence    : {conf_threshold}")
    print("-" * 65)

    # 1. Load trained YOLOv8 model
    model = YOLO(str(weights))

    # 2. Run inference
    results = model.predict(source=str(img_path), conf=conf_threshold, verbose=False)
    result = results[0]

    # Read original image for custom OpenCV drawing
    orig_img = cv2.imread(str(img_path))
    if orig_img is None:
        print(f"ERROR: OpenCV could not read image at {img_path}")
        sys.exit(1)

    h, w = orig_img.shape[:2]
    boxes = result.boxes

    print(f"\nDetection Results (Found {len(boxes)} defect(s)):")
    print("-" * 65)

    if len(boxes) == 0:
        print("No defects detected above the confidence threshold.")
    else:
        for idx, box in enumerate(boxes):
            cls_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            x1, y1, x2, y2 = [int(v) for v in xyxy]

            defect_name = CLASS_NAMES.get(cls_id, f"Class_{cls_id}")
            color = CLASS_COLORS.get(cls_id, (0, 255, 0))

            print(f"[{idx + 1}] Defect       : {defect_name}")
            print(f"    Confidence   : {confidence:.2f} ({confidence * 100:.1f}%)")
            print(f"    Bounding Box : [{x1}, {y1}, {x2}, {y2}] (x1, y1, x2, y2)")
            print(f"    Box Size     : width={x2 - x1}px, height={y2 - y1}px")
            print("-" * 40)

            # Draw bounding box
            cv2.rectangle(orig_img, (x1, y1), (x2, y2), color, 2)

            # Draw defect tag banner
            label = f"{defect_name}: {confidence:.2f}"
            (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(orig_img, (x1, max(0, y1 - 22)), (x1 + text_w + 6, max(0, y1)), color, -1)
            cv2.putText(orig_img, label, (x1 + 3, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    # 3. Save predicted output
    output_filename = out_dir / f"pred_{img_path.name}"
    cv2.imwrite(str(output_filename), orig_img)
    print(f"\nAnnotated image saved successfully to:\n--> {output_filename}")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AeroIntel YOLOv8 Defect Detection")
    parser.add_argument("--source", type=str, required=True, help="Path to input image")
    parser.add_argument("--weights", type=str, default="models/best.pt", help="Path to best.pt weights")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold (0.0 to 1.0)")
    parser.add_argument("--output", type=str, default="outputs/predictions", help="Directory to save output")
    args = parser.parse_args()

    run_inference(args.source, args.weights, args.conf, args.output)
