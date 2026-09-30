import os
import sys
import json
from pathlib import Path
import cv2

DATASET_ROOT = Path(r"C:\Users\chanc\OneDrive\Desktop\AeroIntel\datasets\master_dataset_ABC")
OUTPUT_DIR = Path(r"C:\Users\chanc\OneDrive\Desktop\AeroIntel\outputs\reports")
VIS_DIR = OUTPUT_DIR / "visualizations"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = {
    0: "Crack",
    1: "Corrosion",
    2: "Dent",
    3: "Missing Fastener"
}

CLASS_COLORS = {
    0: (0, 0, 255),     # Red for Crack (BGR)
    1: (0, 215, 255),   # Gold/Yellow for Corrosion
    2: (255, 100, 0),   # Blue for Dent
    3: (255, 0, 255)    # Magenta for Missing Fastener
}

supported_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
splits = ["train", "valid", "test"]

stats = {
    "counts": {},
    "missing_labels": {},
    "orphan_labels": {},
    "corrupted_images": 0,
    "corrupted_files": [],
    "invalid_annotations": 0,
    "invalid_annotation_details": [],
    "empty_label_files": 0,
    "class_counts": {s: {c: 0 for c in range(4)} for s in splits},
    "total_boxes": {s: 0 for s in splits},
    "dimensions_summary": {}
}

print("=" * 70)
print("STARTING FULL AEROINTEL DATASET AUDIT (OPENCV & YOLO LABELS)")
print(f"Dataset root: {DATASET_ROOT}")
print("=" * 70)

vis_samples_saved = 0
MAX_VIS_SAMPLES = 12

for split in splits:
    img_dir = DATASET_ROOT / split / "images"
    lbl_dir = DATASET_ROOT / split / "labels"

    if not img_dir.exists() or not lbl_dir.exists():
        print(f"ERROR: Directory missing for split {split}")
        continue

    images = sorted([f for f in img_dir.iterdir() if f.suffix.lower() in supported_exts])
    labels = sorted([f for f in lbl_dir.iterdir() if f.suffix.lower() == ".txt"])

    img_map = {f.stem: f for f in images}
    lbl_map = {f.stem: f for f in labels}

    missing_lbl = set(img_map.keys()) - set(lbl_map.keys())
    orphan_lbl = set(lbl_map.keys()) - set(img_map.keys())

    stats["counts"][split] = {"images": len(images), "labels": len(labels)}
    stats["missing_labels"][split] = len(missing_lbl)
    stats["orphan_labels"][split] = len(orphan_lbl)

    print(f"\nChecking split [{split.upper()}]: {len(images)} images, {len(labels)} labels...")

    for i, (stem, img_path) in enumerate(img_map.items()):
        # 1. OpenCV integrity check
        img = cv2.imread(str(img_path))
        if img is None:
            stats["corrupted_images"] += 1
            stats["corrupted_files"].append(str(img_path))
            continue

        h, w, c = img.shape
        dim_key = f"{w}x{h}"
        stats["dimensions_summary"][dim_key] = stats["dimensions_summary"].get(dim_key, 0) + 1

        # 2. Annotation check
        lbl_path = lbl_map.get(stem)
        if not lbl_path or not lbl_path.exists():
            continue

        with open(lbl_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) == 0:
            stats["empty_label_files"] += 1

        drawn_boxes = []

        for line_idx, line in enumerate(lines):
            parts = line.split()
            if len(parts) != 5:
                stats["invalid_annotations"] += 1
                stats["invalid_annotation_details"].append(f"{lbl_path.name} L{line_idx+1}: {line} (parts!=5)")
                continue

            try:
                cls_id = int(parts[0])
                xc = float(parts[1])
                yc = float(parts[2])
                bw = float(parts[3])
                bh = float(parts[4])
            except ValueError as e:
                stats["invalid_annotations"] += 1
                stats["invalid_annotation_details"].append(f"{lbl_path.name} L{line_idx+1}: {e}")
                continue

            if cls_id not in (0, 1, 2, 3):
                stats["invalid_annotations"] += 1
                stats["invalid_annotation_details"].append(f"{lbl_path.name} L{line_idx+1}: invalid class_id {cls_id}")
                continue

            if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < bw <= 1.0 and 0.0 < bh <= 1.0):
                stats["invalid_annotations"] += 1
                stats["invalid_annotation_details"].append(f"{lbl_path.name} L{line_idx+1}: coordinates out of [0, 1]")
                continue

            stats["class_counts"][split][cls_id] += 1
            stats["total_boxes"][split] += 1

            # Convert YOLO normalized (xc, yc, bw, bh) to pixel (x1, y1, x2, y2)
            x1 = int((xc - bw / 2.0) * w)
            y1 = int((yc - bh / 2.0) * h)
            x2 = int((xc + bw / 2.0) * w)
            y2 = int((yc + bh / 2.0) * h)

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            drawn_boxes.append((cls_id, x1, y1, x2, y2))

        # 3. Create visual inspection sample for train split
        if split == "train" and vis_samples_saved < MAX_VIS_SAMPLES and len(drawn_boxes) > 0:
            # We want a sample representing defects
            vis_img = img.copy()
            for cls_id, x1, y1, x2, y2 in drawn_boxes:
                cname = CLASS_NAMES[cls_id]
                color = CLASS_COLORS[cls_id]
                cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)
                label_text = f"{cname} ({cls_id})"
                (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(vis_img, (x1, max(0, y1 - 20)), (x1 + tw + 4, max(0, y1)), color, -1)
                cv2.putText(vis_img, label_text, (x1 + 2, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            out_vis_path = VIS_DIR / f"sample_{vis_samples_saved+1:02d}_{stem[:25]}.jpg"
            cv2.imwrite(str(out_vis_path), vis_img)
            vis_samples_saved += 1

        if (i + 1) % 1500 == 0 or (i + 1) == len(images):
            print(f"  Processed {i+1}/{len(images)} images...")

# Print Summary Tables
print("\n" + "=" * 70)
print("DATASET INTEGRITY & PAIRING SUMMARY")
print("=" * 70)
print(f"{'Split':<10} | {'Images':<8} | {'Labels':<8} | {'Missing Lbl':<12} | {'Orphan Lbl':<12}")
print("-" * 60)
for s in splits:
    c = stats["counts"].get(s, {})
    print(f"{s.upper():<10} | {c.get('images', 0):<8} | {c.get('labels', 0):<8} | {stats['missing_labels'].get(s, 0):<12} | {stats['orphan_labels'].get(s, 0):<12}")

print("\n" + "=" * 70)
print("IMAGE READABILITY & ANNOTATION QUALITY")
print("=" * 70)
print(f"Corrupted Images (cv2.imread failed) : {stats['corrupted_images']}")
print(f"Invalid Annotations                  : {stats['invalid_annotations']}")
print(f"Empty Label Files (0 defects)        : {stats['empty_label_files']}")
print(f"Image Dimensions Distribution        : {stats['dimensions_summary']}")

print("\n" + "=" * 70)
print("CLASS BOUNDING BOX DISTRIBUTION")
print("=" * 70)
header = f"{'Class':<20} | {'Train':<8} | {'Valid':<8} | {'Test':<8} | {'Total':<8} | {'Share %':<8}"
print(header)
print("-" * len(header))

grand_total_boxes = sum(stats["total_boxes"].values())

for cid in range(4):
    cname = CLASS_NAMES[cid]
    tr = stats["class_counts"]["train"][cid]
    val = stats["class_counts"]["valid"][cid]
    ts = stats["class_counts"]["test"][cid]
    tot = tr + val + ts
    share = (tot / grand_total_boxes * 100) if grand_total_boxes > 0 else 0
    print(f"{cname} (Class {cid})".ljust(20) + f" | {tr:<8} | {val:<8} | {ts:<8} | {tot:<8} | {share:6.2f}%")

print("-" * len(header))
print(f"{'TOTAL BOXES':<20} | {stats['total_boxes']['train']:<8} | {stats['total_boxes']['valid']:<8} | {stats['total_boxes']['test']:<8} | {grand_total_boxes:<8} | 100.00%")
print("=" * 70)

# Save JSON and Text report
report_json_path = OUTPUT_DIR / "dataset_audit_report.json"
with open(report_json_path, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2)

report_txt_path = OUTPUT_DIR / "dataset_audit_report.txt"
with open(report_txt_path, "w", encoding="utf-8") as f:
    f.write("AeroIntel master_dataset_ABC Audit Report\n")
    f.write(f"Total Images: {sum(c.get('images', 0) for c in stats['counts'].values())}\n")
    f.write(f"Corrupted Images: {stats['corrupted_images']}\n")
    f.write(f"Invalid Annotations: {stats['invalid_annotations']}\n")
    f.write(f"Total Bounding Boxes: {grand_total_boxes}\n")
    f.write(f"Class Breakdown: {stats['class_counts']}\n")

print(f"\nVisualizations saved: {vis_samples_saved} images to {VIS_DIR}")
print(f"Reports saved to {report_json_path} and {report_txt_path}")
