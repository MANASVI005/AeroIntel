"""
AeroIntel - YOLOv8 ONNX Model Export Script
Exports best.pt to ONNX format for edge deployment, OpenCV DNN, and cross-platform serving.

Usage:
    python scripts/export.py --weights models/best.pt --imgsz 640
"""

import argparse
from pathlib import Path
from ultralytics import YOLO


def export_onnx(weights_path: str = "models/best.pt", imgsz: int = 640, opset: int = 12):
    weights = Path(weights_path)
    if not weights.exists():
        raise FileNotFoundError(f"Model weights not found at: {weights}")

    print("=" * 65)
    print("AEROINTEL MODEL EXPORT TO ONNX")
    print("=" * 65)
    print(f"Source Model : {weights}")
    print(f"Export Format: ONNX (opset {opset})")
    print(f"Input Shape  : (1, 3, {imgsz}, {imgsz})")
    print("-" * 65)

    model = YOLO(str(weights))
    onnx_path = model.export(
        format="onnx",
        imgsz=imgsz,
        opset=opset,
        simplify=True,
        dynamic=False  # fixed shape optimized for TensorRT and standard OpenCV DNN
    )

    print("\n" + "=" * 65)
    print("EXPORT COMPLETED SUCCESSFULLY ✅")
    print(f"Exported ONNX file: {onnx_path}")
    print("\nNote: Your original PyTorch model 'best.pt' remains intact as")
    print("the primary checkpoint. The ONNX model is ideal for C++, C#,")
    print("OpenCV dnn, TensorRT, or edge runtime deployments.")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export AeroIntel model to ONNX")
    parser.add_argument("--weights", type=str, default="models/best.pt", help="Path to best.pt")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset version")
    args = parser.parse_args()

    export_onnx(args.weights, args.imgsz, args.opset)
