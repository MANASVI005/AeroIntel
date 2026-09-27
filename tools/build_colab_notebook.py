import json
from pathlib import Path

notebook_path = Path(r"C:\Users\chanc\OneDrive\Desktop\AeroIntel\notebooks\aircraft_defect_training.ipynb")
notebook_path.parent.mkdir(parents=True, exist_ok=True)

cells = []

def add_md(text):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    })

def add_code(code):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    })

# Title
add_md("""# AeroIntel - Aircraft Defect Detection using YOLOv8
### Automated End-to-End Google Colab T4 Workflow

Defect Classes:
* **0: Crack**
* **1: Corrosion**
* **2: Dent**
* **3: Missing Fastener**

This notebook is configured for **Google Colab with a free T4 GPU**.""")

# Cell 1: GPU check
add_md("## Step 1: Hardware & GPU Verification")
add_code("""# CELL 1: Hardware & GPU Verification
import torch
import sys

print(f"Python Version: {sys.version.split()[0]}")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    device_name = torch.cuda.get_device_name(0)
    device_count = torch.cuda.device_count()
    memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"Active GPU: {device_name}")
    print(f"GPU Count: {device_count}")
    print(f"Total VRAM: {memory_gb:.2f} GB")
else:
    print("WARNING: CUDA is NOT available. In Colab, go to Runtime -> Change runtime type -> T4 GPU.")
""")

# Cell 2: Install Ultralytics
add_md("## Step 2: Install Ultralytics YOLOv8 & Dependencies")
add_code("""# CELL 2: Install and check Ultralytics
!pip install -U ultralytics

import ultralytics
from ultralytics import YOLO

print(f"Ultralytics version: {ultralytics.__version__}")
ultralytics.checks()
""")

# Cell 3: Clone GitHub
add_md("## Step 3: Clone AeroIntel Repository & Define Global Paths")
add_code("""# CELL 3: Clone AeroIntel and setup paths
import os
from pathlib import Path

REPO_DIR = Path("/content/AeroIntel")
DATASET_DIR = REPO_DIR / "datasets" / "master_dataset_ABC"
DATA_YAML = DATASET_DIR / "data.yaml"

if not REPO_DIR.exists():
    print("Cloning AeroIntel repository...")
    !git clone https://github.com/MANASVI005/AeroIntel.git {REPO_DIR}
else:
    print("Repository already exists. Pulling latest commit...")
    !git -C {REPO_DIR} pull

print("Installing git-lfs and fetching binary images (311 MB)...")
!apt-get update -qq
!apt-get install -y -qq git-lfs
!git -C {REPO_DIR} lfs install
!git -C {REPO_DIR} lfs pull

print("\\n--- Verifying Paths ---")
print(f"REPO_DIR    : {REPO_DIR} (Exists: {REPO_DIR.exists()})")
print(f"DATASET_DIR : {DATASET_DIR} (Exists: {DATASET_DIR.exists()})")
print(f"DATA_YAML   : {DATA_YAML} (Exists: {DATA_YAML.exists()})")
""")

# Cell 4: Verify structure
add_md("## Step 4: Verify Dataset Structure & 1:1 Image-Label Pairing")
add_code("""# CELL 4: Verify Dataset Structure and 1:1 Pairing
from pathlib import Path

splits = ["train", "valid", "test"]
supported_img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

print("=" * 60)
print("AEROINTEL DATASET INTEGRITY CHECK")
print("=" * 60)

all_passed = True

for split in splits:
    img_dir = DATASET_DIR / split / "images"
    lbl_dir = DATASET_DIR / split / "labels"
    
    if not img_dir.exists() or not lbl_dir.exists():
        print(f"ERROR: Missing directory in split '{split}':")
        print(f"  images dir exists: {img_dir.exists()}")
        print(f"  labels dir exists: {lbl_dir.exists()}")
        all_passed = False
        continue
    
    img_files = {f.stem: f for f in img_dir.iterdir() if f.suffix.lower() in supported_img_exts}
    lbl_files = {f.stem: f for f in lbl_dir.iterdir() if f.suffix.lower() == ".txt"}
    
    missing_labels = set(img_files.keys()) - set(lbl_files.keys())
    orphan_labels = set(lbl_files.keys()) - set(img_files.keys())
    
    print(f"[{split.upper()}] Images: {len(img_files):>5} | Labels: {len(lbl_files):>5} | Missing: {len(missing_labels)} | Orphan: {len(orphan_labels)}")
    if len(missing_labels) > 0 or len(orphan_labels) > 0:
        all_passed = False

print("=" * 60)
if all_passed:
    print("STATUS: PASSED ✅ All splits have perfect 1:1 image-label pairings!")
else:
    print("STATUS: FAILED ❌ Discrepancies detected.")
""")

# Cell 5: Read data.yaml
add_md("## Step 5: Verify & Ensure Exact data.yaml Configuration")
add_code("""# CELL 5: Read and Validate data.yaml
import yaml

with open(DATA_YAML, "r") as f:
    config = yaml.safe_load(f)

print("Current data.yaml:")
print(yaml.dump(config, sort_keys=False))

# Standardize path to avoid relative path ambiguity in YOLO
config["path"] = str(DATASET_DIR)
config["train"] = "train/images"
config["val"] = "valid/images"
config["test"] = "test/images"
config["nc"] = 4
config["names"] = {
    0: "Crack",
    1: "Corrosion",
    2: "Dent",
    3: "Missing Fastener"
}

with open(DATA_YAML, "w") as f:
    yaml.dump(config, f, sort_keys=False)

print("Validated and standardized data.yaml successfully!")
""")

# Cell 6: Image readability & Quality Check
add_md("## Step 6: OpenCV Image Readability & Annotation Audit")
add_code("""# CELL 6: OpenCV Readability and YOLO Label Quality Check
import cv2

corrupted_images = 0
invalid_annotations = 0
total_boxes = 0

for split in ["train", "valid", "test"]:
    img_dir = DATASET_DIR / split / "images"
    lbl_dir = DATASET_DIR / split / "labels"
    
    for img_path in img_dir.iterdir():
        if img_path.suffix.lower() not in supported_img_exts:
            continue
        
        # OpenCV check
        img = cv2.imread(str(img_path))
        if img is None:
            corrupted_images += 1
            continue
        
        lbl_path = lbl_dir / f"{img_path.stem}.txt"
        if lbl_path.exists():
            with open(lbl_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        invalid_annotations += 1
                        continue
                    try:
                        cls_id, xc, yc, bw, bh = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                        if cls_id not in (0, 1, 2, 3) or not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 < bw <= 1 and 0 < bh <= 1):
                            invalid_annotations += 1
                        else:
                            total_boxes += 1
                    except ValueError:
                        invalid_annotations += 1

print("=" * 55)
print(f"Corrupted Images (cv2.imread failed) : {corrupted_images}")
print(f"Invalid Annotations                  : {invalid_annotations}")
print(f"Total Valid Bounding Boxes Checked   : {total_boxes}")
print("STATUS: " + ("PERFECT ✅" if corrupted_images == 0 and invalid_annotations == 0 else "WARNING ⚠️"))
print("=" * 55)
""")

# Cell 7: Class Distribution
add_md("## Step 7: Class Bounding Box Distribution")
add_code("""# CELL 7: Class Distribution Table
class_names = {0: "Crack", 1: "Corrosion", 2: "Dent", 3: "Missing Fastener"}
counts = {s: {c: 0 for c in range(4)} for s in ["train", "valid", "test"]}

for split in ["train", "valid", "test"]:
    lbl_dir = DATASET_DIR / split / "labels"
    for lbl_path in lbl_dir.glob("*.txt"):
        with open(lbl_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    cls_id = int(parts[0])
                    if cls_id in counts[split]:
                        counts[split][cls_id] += 1

print(f"{'Class':<20} | {'Train':<8} | {'Valid':<8} | {'Test':<8} | {'Total':<8}")
print("-" * 60)
for cid in range(4):
    cname = class_names[cid]
    tr, val, ts = counts['train'][cid], counts['valid'][cid], counts['test'][cid]
    tot = tr + val + ts
    print(f"{cname} (Class {cid})".ljust(20) + f" | {tr:<8} | {val:<8} | {ts:<8} | {tot:<8}")
""")

# Cell 8: Visualize Samples
add_md("## Step 8: Visualize Training Images with Bounding Boxes")
add_code("""# CELL 8: Visual Inspection of Defect Bounding Boxes
import cv2
import matplotlib.pyplot as plt
import random

train_img_dir = DATASET_DIR / "train" / "images"
train_lbl_dir = DATASET_DIR / "train" / "labels"

sample_imgs = random.sample(list(train_img_dir.glob("*.jpg")), 6)
colors = {0: (255, 0, 0), 1: (255, 215, 0), 2: (0, 165, 255), 3: (255, 0, 255)}

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, img_p in enumerate(sample_imgs):
    img = cv2.imread(str(img_p))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    
    lbl_p = train_lbl_dir / f"{img_p.stem}.txt"
    if lbl_p.exists():
        with open(lbl_p, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    cid = int(parts[0])
                    xc, yc, bw, bh = [float(v) for v in parts[1:]]
                    x1 = int((xc - bw/2) * w)
                    y1 = int((yc - bh/2) * h)
                    x2 = int((xc + bw/2) * w)
                    y2 = int((yc + bh/2) * h)
                    cv2.rectangle(img, (x1, y1), (x2, y2), colors.get(cid, (0, 255, 0)), 2)
                    cv2.putText(img, class_names[cid], (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors.get(cid, (0, 255, 0)), 1)
    
    axes[idx].imshow(img)
    axes[idx].set_title(img_p.name[:20])
    axes[idx].axis("off")

plt.tight_layout()
plt.show()
""")

# Cell 9: Model Selection
add_md("""## Step 9: Select YOLOv8 Model Architecture
We recommend **YOLOv8s** (`yolov8s.pt`):
* **Parameters**: 11.2M (Lightweight yet expressive enough for fine surface cracks and small fasteners).
* **Speed vs Accuracy**: Excellent balance; trains on T4 GPU in ~1.5 hours for 60 epochs.
* **Comparison**:
  * `yolov8n`: Too small (3.2M params), frequently misses subtle hairline cracks.
  * `yolov8m`: High accuracy (25.9M params) but 2.5x slower training with risk of OOM at batch 16 on T4.""")
add_code("""# CELL 9: Load Pre-trained YOLOv8s Model
from ultralytics import YOLO

model = YOLO("yolov8s.pt")
print("Loaded YOLOv8s model successfully.")
""")

# Cell 10: Training
add_md("## Step 10: Train YOLOv8 on T4 GPU")
add_code("""# CELL 10: Launch Training
results = model.train(
    data=str(DATA_YAML),
    epochs=60,
    imgsz=640,
    batch=16,           # Optimal for 15GB T4 GPU
    patience=15,        # Early stopping if no mAP improvement
    device=0,           # T4 GPU
    workers=2,
    project="/content/runs/detect",
    name="aircraft_defect_yolov8s",
    exist_ok=True,
    save=True,
    save_period=10,
    pretrained=True,
    optimizer="auto",
    verbose=True,
    degrees=10.0,
    fliplr=0.5,
    flipud=0.2,
    hsv_s=0.5,
    mosaic=1.0
)

# Save best.pt into AeroIntel/models/
import shutil
shutil.copy("/content/runs/detect/aircraft_defect_yolov8s/weights/best.pt", "/content/AeroIntel/models/best.pt")
print("Copied best.pt to /content/AeroIntel/models/best.pt")
""")

# Cell 11: Training Curves
add_md("## Step 11: Inspect Training Loss and Metric Curves")
add_code("""# CELL 11: Display Training Progress Curves
from IPython.display import Image, display

results_png = Path("/content/runs/detect/aircraft_defect_yolov8s/results.png")
if results_png.exists():
    display(Image(filename=str(results_png)))
else:
    print("results.png not found.")
""")

# Cell 12: Validation
add_md("## Step 12: Validation on Held-Out Validation Split")
add_code("""# CELL 12: Model Validation
best_model = YOLO("/content/runs/detect/aircraft_defect_yolov8s/weights/best.pt")

metrics = best_model.val(
    data=str(DATA_YAML),
    split="val",
    imgsz=640,
    batch=16,
    plots=True
)

print("\\n" + "=" * 50)
print(f"Overall Precision (P) : {metrics.box.mp:.4f}")
print(f"Overall Recall (R)    : {metrics.box.mr:.4f}")
print(f"Overall mAP@0.50      : {metrics.box.map50:.4f}")
print(f"Overall mAP@0.50:0.95 : {metrics.box.map:.4f}")
print("=" * 50)
""")

# Cell 13: Confusion Matrix
add_md("## Step 13: Display Confusion Matrix")
add_code("""# CELL 13: Display Confusion Matrix
cm_path = Path("/content/runs/detect/aircraft_defect_yolov8s/confusion_matrix.png")
if cm_path.exists():
    display(Image(filename=str(cm_path)))
""")

# Cell 14: Final Test Evaluation
add_md("## Step 14: Final Evaluation on Completely Unseen Test Split")
add_code("""# CELL 14: Unseen Test Set Evaluation
test_metrics = best_model.val(
    data=str(DATA_YAML),
    split="test",
    imgsz=640,
    batch=16
)

print("\\n" + "=" * 50)
print(f"TEST Precision (P)    : {test_metrics.box.mp:.4f}")
print(f"TEST Recall (R)       : {test_metrics.box.mr:.4f}")
print(f"TEST mAP@0.50         : {test_metrics.box.map50:.4f}")
print(f"TEST mAP@0.50:0.95    : {test_metrics.box.map:.4f}")
print("=" * 50)
""")

# Cell 15: Run Inference
add_md("## Step 15: Single & Batch Prediction on Test Images")
add_code("""# CELL 15: Inference on a Sample Test Image
sample_test_img = list((DATASET_DIR / "test" / "images").glob("*.jpg"))[0]

preds = best_model.predict(source=str(sample_test_img), conf=0.25, save=True)
print(f"Inference on: {sample_test_img.name}")
for box in preds[0].boxes:
    cid = int(box.cls[0].item())
    conf = float(box.conf[0].item())
    xyxy = [int(v) for v in box.xyxy[0].tolist()]
    print(f"Defect: {class_names[cid]} | Confidence: {conf:.2f} | Bounding Box: {xyxy}")
""")

# Cell 16: Export ONNX
add_md("## Step 16: Export best.pt to ONNX Format")
add_code("""# CELL 16: Export to ONNX
onnx_path = best_model.export(format="onnx", imgsz=640, opset=12, simplify=True)
print(f"ONNX Model saved to: {onnx_path}")
""")

# Cell 17: Download best.pt
add_md("## Step 17: Download Model Checkpoints to Local Machine")
add_code("""# CELL 17: Download Trained Weights
from google.colab import files

print("Downloading best.pt...")
files.download("/content/runs/detect/aircraft_defect_yolov8s/weights/best.pt")
""")

notebook_json = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {
            "gpuType": "T4",
            "provenance": []
        },
        "kernelspec": {
            "display_name": "Python 3",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.12"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 0
}

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook_json, f, indent=2)

print(f"Created complete Google Colab notebook at: {notebook_path}")
