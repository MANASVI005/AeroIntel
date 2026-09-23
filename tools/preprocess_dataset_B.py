"""Create the cleaned AeroIntel YOLO dataset from Dataset B v2."""

from __future__ import annotations

import math
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "datasets" / "dataset_B"
OUTPUT = SOURCE / "processed"
SPLITS = {"train": "train", "valid": "val", "test": "test"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
CLASS_MAPPING = {0: 0, 2: 2, 3: 3}


@dataclass
class SplitStats:
    original_images: int = 0
    processed_images: int = 0


def quarantine_file(path: Path, split: str, category: str) -> None:
    destination = OUTPUT / "quarantine" / split / category / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        shutil.copy2(path, destination)


def validate_image(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
    except (OSError, UnidentifiedImageError) as error:
        return f"{type(error).__name__}: {error}"
    return None


def parse_label(path: Path) -> tuple[list[str], list[str], Counter[int], Counter[int]]:
    valid_lines: list[str] = []
    problems: list[str] = []
    counts: Counter[int] = Counter()
    removed: Counter[int] = Counter()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return [], [f"could not read label: {error}"], counts, removed

    for line_number, raw_line in enumerate(lines, start=1):
        text = raw_line.strip()
        if not text:
            continue
        fields = text.split()
        problem = None
        class_id: int | None = None
        if len(fields) != 5:
            problem = f"line {line_number}: expected 5 fields, found {len(fields)}"
        else:
            try:
                class_value = float(fields[0])
                class_id = int(fields[0])
                values = [float(value) for value in fields[1:]]
                if not math.isfinite(class_value) or class_value != class_id:
                    problem = f"line {line_number}: class ID is not an integer"
                elif any(not math.isfinite(value) for value in values):
                    problem = f"line {line_number}: coordinates must be finite"
                else:
                    x, y, width, height = values
                    if class_id not in range(5):
                        problem = f"line {line_number}: unknown class ID {class_id}"
                    elif not all(0 <= value <= 1 for value in (x, y, width, height)):
                        problem = f"line {line_number}: values must be normalized to [0, 1]"
                    elif width <= 0 or height <= 0:
                        problem = f"line {line_number}: width and height must be positive"
                    elif x - width / 2 < 0 or x + width / 2 > 1 or y - height / 2 < 0 or y + height / 2 > 1:
                        problem = f"line {line_number}: bounding box extends outside image bounds"
            except (ValueError, OverflowError):
                problem = f"line {line_number}: class ID and coordinates must be numeric"

        if problem:
            problems.append(problem)
        elif class_id in CLASS_MAPPING:
            fields[0] = str(CLASS_MAPPING[class_id])
            valid_lines.append(" ".join(fields))
            counts[CLASS_MAPPING[class_id]] += 1
        elif class_id in (1, 4):
            removed[class_id] += 1

    if not lines:
        problems.append("empty label file")
    return valid_lines, problems, counts, removed


def collect_duplicate_filenames() -> list[str]:
    occurrences: defaultdict[str, list[str]] = defaultdict(list)
    for source_split in SPLITS:
        for kind in ("images", "labels"):
            directory = SOURCE / source_split / kind
            for path in sorted(directory.iterdir() if directory.is_dir() else []):
                if path.is_file():
                    occurrences[f"{kind}/{path.name.lower()}"].append(f"{source_split}/{kind}/{path.name}")
    return [f"{key}: {', '.join(values)}" for key, values in sorted(occurrences.items()) if len(values) > 1]


def write_report(
    stats: dict[str, SplitStats],
    details: list[str],
    totals: Counter[int],
    image_counts: Counter[int],
    excluded: int,
    quarantined: int,
    corrupted: int,
    invalid: int,
    duplicate_entries: list[str],
    removed: Counter[int],
) -> None:
    lines = [
        "AeroIntel Dataset B v2 preprocessing report",
        "=" * 48,
        f"Source: {SOURCE}",
        f"Output: {OUTPUT}",
        "Source data.yaml declares one generic class; the requested Dataset B mapping was applied to label IDs.",
        "",
        "Class mapping:",
        "  crack -> Crack (0)",
        "  scratch -> removed",
        "  dent -> Dent (2)",
        "  missing-head -> Missing Fastener (3)",
        "  paint-off -> removed",
        "  Corrosion (1) -> no annotations created",
        "",
        "Split statistics:",
    ]
    for source_split, output_split in SPLITS.items():
        split = stats[source_split]
        lines.append(f"  {source_split} -> {output_split}: {split.original_images} original images, {split.processed_images} processed images")
    lines.extend(
        [
            "",
            f"Excluded images: {excluded}",
            f"Quarantined files: {quarantined}",
            f"Corrupted images: {corrupted}",
            f"Invalid annotations: {invalid}",
            "",
            "Class totals:",
            f"  Crack images: {image_counts[0]}",
            f"  Dent images: {image_counts[2]}",
            f"  Missing Fastener images: {image_counts[3]}",
            f"  Total Crack annotations: {totals[0]}",
            f"  Total Dent annotations: {totals[2]}",
            f"  Total Missing Fastener annotations: {totals[3]}",
            f"  Removed scratch annotations: {removed[1]}",
            f"  Removed paint-off annotations: {removed[4]}",
            "",
            "Duplicate filenames:",
        ]
    )
    lines.extend(f"  {entry}" for entry in duplicate_entries) if duplicate_entries else lines.append("  None")
    lines.extend(["", "File actions:"])
    lines.extend(f"  {detail}" for detail in details) if details else lines.append("  None")
    (OUTPUT / "processing_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not SOURCE.is_dir():
        raise FileNotFoundError(f"Dataset B directory not found: {SOURCE}")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    for output_split in SPLITS.values():
        (OUTPUT / "images" / output_split).mkdir(parents=True, exist_ok=True)
        (OUTPUT / "labels" / output_split).mkdir(parents=True, exist_ok=True)
    (OUTPUT / "quarantine").mkdir(parents=True, exist_ok=True)

    stats = {split: SplitStats() for split in SPLITS}
    details: list[str] = []
    totals: Counter[int] = Counter()
    image_counts: Counter[int] = Counter()
    removed: Counter[int] = Counter()
    excluded = quarantined = corrupted = invalid = 0
    duplicate_entries = collect_duplicate_filenames()
    for entry in duplicate_entries:
        details.append(f"duplicate filename detected (split-specific copies retained): {entry}")

    for source_split, output_split in SPLITS.items():
        image_dir = SOURCE / source_split / "images"
        label_dir = SOURCE / source_split / "labels"
        image_paths = sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
        label_paths = sorted(path for path in label_dir.iterdir() if path.is_file() and path.suffix.lower() == ".txt")
        stats[source_split].original_images = len(image_paths)
        images_by_stem = {path.stem: path for path in image_paths}
        labels_by_stem = {path.stem: path for path in label_paths}

        for image_path in image_paths:
            if image_path.stem not in labels_by_stem:
                quarantine_file(image_path, source_split, "missing-label")
                quarantined += 1
                details.append(f"quarantined missing label: {source_split}/{image_path.name}")
                continue
            label_path = labels_by_stem[image_path.stem]
            image_error = validate_image(image_path)
            if image_error:
                quarantine_file(image_path, source_split, "corrupted-image")
                quarantine_file(label_path, source_split, "corrupted-image")
                quarantined += 2
                corrupted += 1
                details.append(f"quarantined corrupted image and label: {source_split}/{image_path.name} ({image_error})")
                continue
            valid_lines, problems, label_counts, removed_counts = parse_label(label_path)
            removed.update(removed_counts)
            if problems:
                invalid += len(problems)
                quarantine_file(label_path, source_split, "invalid-label")
                quarantined += 1
                details.append(f"invalid label retained as quarantine copy: {source_split}/{label_path.name}: {'; '.join(problems)}")
            if not valid_lines:
                quarantine_file(image_path, source_split, "excluded-no-valid-annotations")
                if not problems:
                    quarantine_file(label_path, source_split, "excluded-no-valid-annotations")
                    quarantined += 2
                else:
                    quarantined += 1
                excluded += 1
                details.append(f"excluded image with no valid wanted annotations: {source_split}/{image_path.name}")
                continue

            shutil.copy2(image_path, OUTPUT / "images" / output_split / image_path.name)
            (OUTPUT / "labels" / output_split / f"{image_path.stem}.txt").write_text("\n".join(valid_lines) + "\n", encoding="utf-8")
            stats[source_split].processed_images += 1
            totals.update(label_counts)
            for class_id in label_counts:
                image_counts[class_id] += 1

        for label_path in label_paths:
            if label_path.stem not in images_by_stem:
                quarantine_file(label_path, source_split, "missing-image")
                quarantined += 1
                details.append(f"quarantined missing image: {source_split}/{label_path.name}")

    data_yaml = """train: images/train
val: images/val
test: images/test

nc: 4
names:
  0: Crack
  1: Corrosion
  2: Dent
  3: Missing Fastener
"""
    (OUTPUT / "data.yaml").write_text(data_yaml, encoding="utf-8")
    write_report(stats, details, totals, image_counts, excluded, quarantined, corrupted, invalid, duplicate_entries, removed)

    print(f"Original train images: {stats['train'].original_images}")
    print(f"Original validation images: {stats['valid'].original_images}")
    print(f"Original test images: {stats['test'].original_images}")
    print(f"Processed train images: {stats['train'].processed_images}")
    print(f"Processed validation images: {stats['valid'].processed_images}")
    print(f"Processed test images: {stats['test'].processed_images}")
    print(f"Excluded images: {excluded}")
    print(f"Quarantined files: {quarantined}")
    print(f"Corrupted images: {corrupted}")
    print(f"Invalid annotations: {invalid}")
    print(f"Crack images: {image_counts[0]}")
    print(f"Dent images: {image_counts[2]}")
    print(f"Missing Fastener images: {image_counts[3]}")
    print(f"Total Crack annotations: {totals[0]}")
    print(f"Total Dent annotations: {totals[2]}")
    print(f"Total Missing Fastener annotations: {totals[3]}")
    print("\nClass mapping:")
    print("crack -> Crack (0)")
    print("scratch -> removed")
    print("dent -> Dent (2)")
    print("missing-head -> Missing Fastener (3)")
    print("paint-off -> removed")


if __name__ == "__main__":
    main()