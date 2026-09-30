"""
AeroIntel - YOLOv8 Aircraft Defect Detection Training Script
Trains YOLOv8 on master_dataset_ABC with 4 defect classes:
  0: Crack, 1: Corrosion, 2: Dent, 3: Missing Fastener

Usage:
    python scripts/train.py --data datasets/master_dataset_ABC/data.yaml --model yolov8s.pt --epochs 60 --imgsz 640 --batch 16
"""

import argparse
import shutil
from pathlib import Path
from ultralytics import YOLO


def train(data_yaml: str, model_type: str = "yolov8s.pt", epochs: int = 60,
          imgsz: int = 640, batch: int = 16, patience: int = 15,
          device: str = "0", project: str = "runs/detect", name: str = "aircraft_defect_yolov8s"):

    yaml_path = Path(data_yaml).resolve()
    if not yaml_path.exists():
        raise FileNotFoundError(f"data.yaml not found at: {yaml_path}")

    print("=" * 70)
    print("AEROINTEL YOLOV8 MODEL TRAINING")
    print("=" * 70)
    print(f"Data Config      : {yaml_path}")
    print(f"Base Model       : {model_type} (pre-trained on COCO)")
    print(f"Epochs           : {epochs}")
    print(f"Image Resolution : {imgsz}x{imgsz}")
    print(f"Batch Size       : {batch}")
    print(f"Early Stopping   : patience={patience} epochs")
    print(f"Target Device    : {device}")
    print(f"Output Project   : {project}/{name}")
    print("=" * 70)

    # 1. Initialize YOLOv8 model with pre-trained weights
    model = YOLO(model_type)

    # 2. Start training with optimized parameters for aircraft defects
    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=patience,
        device=device,
        workers=2,              # Colab has 2 vCPUs
        project=project,
        name=name,
        exist_ok=True,
        save=True,
        save_period=10,         # checkpoint every 10 epochs
        pretrained=True,
        optimizer="auto",
        verbose=True,
        # Augmentations tailored for aircraft surface defects:
        degrees=10.0,           # slight rotation
        fliplr=0.5,             # horizontal reflection
        flipud=0.2,             # minor vertical flip
        hsv_h=0.015,            # subtle hue variation
        hsv_s=0.5,              # saturation variation (helps corrosion detection)
        hsv_v=0.4,              # exposure/contrast variation
        mosaic=1.0,             # multi-scale mosaic composition (critical for small defects)
    )

    # 3. Copy best.pt to models/ directory
    run_dir = Path(project) / name
    best_weights = run_dir / "weights" / "best.pt"
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    if best_weights.exists():
        target_pt = models_dir / "best.pt"
        shutil.copy(best_weights, target_pt)
        print("\n" + "=" * 70)
        print("TRAINING FINISHED SUCCESSFULLY ✅")
        print(f"Best checkpoint saved to: {best_weights}")
        print(f"Copied to primary model : {target_pt}")
        print(f"Curves & metrics saved to: {run_dir / 'results.png'}")
        print("=" * 70)
    else:
        print(f"Warning: weights not found at {best_weights}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AeroIntel YOLOv8 Defect Detector")
    parser.add_argument("--data", type=str, default="datasets/master_dataset_ABC/data.yaml", help="Path to data.yaml")
    parser.add_argument("--model", type=str, default="yolov8s.pt", help="YOLOv8 base model (e.g. yolov8s.pt, yolov8m.pt)")
    parser.add_argument("--epochs", type=int, default=60, help="Total training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (reduce to 8 if OOM occurs)")
    parser.add_argument("--patience", type=int, default=15, help="Patience for early stopping")
    parser.add_argument("--device", type=str, default="0", help="CUDA device index or 'cpu'")
    parser.add_argument("--project", type=str, default="runs/detect", help="Project output folder")
    parser.add_argument("--name", type=str, default="aircraft_defect_yolov8s", help="Run folder name")
    args = parser.parse_args()

    train(args.data, args.model, args.epochs, args.imgsz, args.batch, args.patience, args.device, args.project, args.name)
