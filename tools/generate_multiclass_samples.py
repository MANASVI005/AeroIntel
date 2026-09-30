from pathlib import Path
import cv2

DATASET_ROOT = Path(r"C:\Users\chanc\OneDrive\Desktop\AeroIntel\datasets\master_dataset_ABC")
VIS_DIR = Path(r"C:\Users\chanc\OneDrive\Desktop\AeroIntel\outputs\reports\visualizations")
VIS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = {
    0: "Crack",
    1: "Corrosion",
    2: "Dent",
    3: "Missing Fastener"
}

CLASS_COLORS = {
    0: (0, 0, 255),      # Red for Crack
    1: (0, 215, 255),    # Yellow/Gold for Corrosion
    2: (255, 100, 0),    # Blue for Dent
    3: (255, 0, 255)     # Magenta for Missing Fastener
}

target_counts_per_class = {0: 3, 1: 3, 2: 3, 3: 3}
collected_per_class = {0: 0, 1: 0, 2: 0, 3: 0}

train_img_dir = DATASET_ROOT / "train" / "images"
train_lbl_dir = DATASET_ROOT / "train" / "labels"

for lbl_path in sorted(train_lbl_dir.glob("*.txt")):
    with open(lbl_path, "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        continue

    # Check which classes are in this file
    file_classes = set()
    boxes = []
    for l in lines:
        parts = l.split()
        if len(parts) == 5:
            cid = int(parts[0])
            file_classes.add(cid)
            boxes.append((cid, float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])))

    # See if this file satisfies any class we still need
    needed = False
    for cid in file_classes:
        if collected_per_class[cid] < target_counts_per_class[cid]:
            needed = True
            break

    if not needed:
        continue

    # Find corresponding image
    img_candidates = list(train_img_dir.glob(f"{lbl_path.stem}.*"))
    if not img_candidates:
        continue
    img_path = img_candidates[0]

    img = cv2.imread(str(img_path))
    if img is None:
        continue

    h, w = img.shape[:2]
    vis_img = img.copy()

    for cid, xc, yc, bw, bh in boxes:
        x1 = max(0, int((xc - bw / 2.0) * w))
        y1 = max(0, int((yc - bh / 2.0) * h))
        x2 = min(w - 1, int((xc + bw / 2.0) * w))
        y2 = min(h - 1, int((yc + bh / 2.0) * h))

        cname = CLASS_NAMES[cid]
        color = CLASS_COLORS[cid]

        cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)
        tag = f"{cname} ({cid})"
        (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(vis_img, (x1, max(0, y1 - 18)), (x1 + tw + 4, max(0, y1)), color, -1)
        cv2.putText(vis_img, tag, (x1 + 2, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # Save
    primary_cls = list(file_classes)[0]
    out_name = f"vis_{CLASS_NAMES[primary_cls]}_{collected_per_class[primary_cls]+1:02d}_{img_path.stem[:20]}.jpg"
    cv2.imwrite(str(VIS_DIR / out_name), vis_img)

    for cid in file_classes:
        collected_per_class[cid] += 1

    if all(collected_per_class[c] >= target_counts_per_class[c] for c in range(4)):
        break

print(f"Multi-class visualizations successfully saved to: {VIS_DIR}")
for cid in range(4):
    print(f"  {CLASS_NAMES[cid]}: {collected_per_class[cid]} samples")
