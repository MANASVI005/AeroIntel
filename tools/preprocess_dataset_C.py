"""Preprocess Dataset C Version 3 for AeroIntel."""

from __future__ import annotations

import ast
import math
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "datasets" / "dataset_C"
OUTPUT = SOURCE / "processed"
SPLITS = ("train", "valid", "test")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SOURCE_CLASS_NAMES = {0: "Dent", 1: "Fastener Damage", 2: "Rupture"}
CLASS_MAPPING = {0: 2, 1: 3, 2: 0}
FINAL_CLASS_NAMES = {0: "Crack", 1: "Corrosion", 2: "Dent", 3: "Missing Fastener"}


@dataclass
class SplitStats:
    original_images: int = 0
    processed_images: int = 0


def read_source_classes() -> dict[int, str]:
    text = (SOURCE / "data.yaml").read_text(encoding="utf-8")
    match = re.search(r"^names:\s*(\[.*\])\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError("Could not read class names from Dataset C data.yaml")
    names = ast.literal_eval(match.group(1))
    if not isinstance(names, list):
        raise ValueError("Dataset C data.yaml names must be a list")
    return {index: str(name) for index, name in enumerate(names)}


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


def parse_annotation(path: Path) -> tuple[list[str], list[str], Counter[int], Counter[str]]:
    valid_lines: list[str] = []
    problems: list[str] = []
    counts: Counter[int] = Counter()
    format_counts: Counter[str] = Counter()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return [], [f"could not read label: {error}"], counts, format_counts

    if not any(line.strip() for line in lines):
        return [], ["empty label file"], counts, format_counts

    for line_number, raw_line in enumerate(lines, start=1):
        text = raw_line.strip()
        if not text:
            continue
        fields = text.split()
        problem = None
        class_id: int | None = None
        try:
            class_value = float(fields[0])
            class_id = int(fields[0])
            values = [float(value) for value in fields[1:]]
            if not math.isfinite(class_value) or class_value != class_id:
                problem = "class ID is not an integer"
            elif class_id not in SOURCE_CLASS_NAMES:
                problem = f"unknown class ID {class_id}"
            elif any(not math.isfinite(value) for value in values):
                problem = "coordinates must be finite"
            elif len(fields) == 5:
                x, y, width, height = values
                format_counts["detection"] += 1
                if not all(0 <= value <= 1 for value in values):
                    problem = "bounding-box values must be normalized to [0, 1]"
                elif width <= 0 or height <= 0:
                    problem = "bounding-box width and height must be positive"
                elif x - width / 2 < 0 or x + width / 2 > 1 or y - height / 2 < 0 or y + height / 2 > 1:
                    problem = "bounding box extends outside image bounds"
            elif len(fields) >= 7 and len(values) % 2 == 0:
                format_counts["segmentation"] += 1
                points = list(zip(values[::2], values[1::2]))
                if len(points) < 3:
                    problem = "polygon requires at least three points"
                elif not all(0 <= value <= 1 for value in values):
                    problem = "polygon coordinates must be normalized to [0, 1]"
                elif min(x for x, _ in points) == max(x for x, _ in points) or min(y for _, y in points) == max(y for _, y in points):
                    problem = "polygon has zero area"
            else:
                problem = "expected YOLO detection (5 fields) or segmentation polygon (class plus coordinate pairs)"
        except (ValueError, OverflowError, IndexError):
            problem = "class ID and coordinates must be numeric"

        if problem:
            problems.append(f"line {line_number}: {problem}")
        else:
            fields[0] = str(CLASS_MAPPING[class_id])
            valid_lines.append(" ".join(fields))
            counts[CLASS_MAPPING[class_id]] += 1

    return valid_lines, problems, counts, format_counts


def write_report(
    source_classes: dict[int, str],
    stats: dict[str, SplitStats],
    original_counts: Counter[int],
    final_counts: Counter[int],
    final_image_counts: Counter[int],
    format_counts: Counter[str],
    details: list[str],
    excluded: int,
    corrupted: int,
    invalid: int,
    empty: int,
    missing_pairs: int,
    quarantined: int,
    warnings: list[str],
) -> None:
    total_original_images = sum(split.original_images for split in stats.values())
    lines = [
        "AeroIntel Dataset C processing report",
        "======================================",
        "Dataset name: Aircraft Defect Detection",
        "Dataset version: Version 3 (No Nulls)",
        f"Source folder: {SOURCE}",
        "",
        "Original image count:",
        *(f"  {split.title()}: {stats[split].original_images}" for split in SPLITS),
        f"  Total: {total_original_images}",
        "",
        "Original classes and IDs:",
        *(f"  {class_id}: {name}" for class_id, name in sorted(source_classes.items())),
        "",
        "Actual annotation counts by class:",
        *(f"  {class_id} ({source_classes.get(class_id, 'Unknown')}): {original_counts[class_id]}" for class_id in sorted(source_classes)),
        "",
        "Mapping performed:",
        "  Dent (0) -> Dent (2)",
        "  Fastener Damage (1) -> Missing Fastener (3)",
        "  Rupture (2) -> Crack (0)",
        "  Corrosion (1) -> no annotations created",
        "",
        "Rupture decision: mapped to Crack (0).",
        "Evidence: representative train, validation, and test images were inspected. They show visible crack-like surface fractures: a long rotor-seating fracture, fiberglass cracks radiating around a fastener, and a structural split. This is an evidence-based mapping, not an assumption from the class name alone.",
        "",
        "Annotation formats observed:",
        f"  YOLO detection records: {format_counts['detection']}",
        f"  YOLO segmentation polygon records preserved: {format_counts['segmentation']}",
        "",
        "Final class distribution:",
        f"  Crack: {final_counts[0]} annotations / {final_image_counts[0]} images",
        f"  Corrosion: {final_counts[1]} annotations / {final_image_counts[1]} images",
        f"  Dent: {final_counts[2]} annotations / {final_image_counts[2]} images",
        f"  Missing Fastener: {final_counts[3]} annotations / {final_image_counts[3]} images",
        "",
        f"Excluded files/images: {excluded}",
        f"Corrupted images: {corrupted}",
        f"Empty labels: {empty}",
        f"Invalid annotations: {invalid}",
        f"Missing image-label pairs: {missing_pairs}",
        f"Quarantine count: {quarantined}",
        "",
        "Warnings:",
    ]
    lines.extend(f"  {warning}" for warning in warnings) if warnings else lines.append("  None")
    lines.extend(["", "File actions:"])
    lines.extend(f"  {detail}" for detail in details) if details else lines.append("  None")
    (OUTPUT / "processing_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not SOURCE.is_dir():
        raise FileNotFoundError(f"Dataset C directory not found: {SOURCE}")
    source_classes = read_source_classes()
    if source_classes != SOURCE_CLASS_NAMES:
        raise ValueError(f"Unexpected Dataset C classes: {source_classes}")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    for split in SPLITS:
        (OUTPUT / split / "images").mkdir(parents=True, exist_ok=True)
        (OUTPUT / split / "labels").mkdir(parents=True, exist_ok=True)
    (OUTPUT / "quarantine").mkdir(parents=True, exist_ok=True)

    stats = {split: SplitStats() for split in SPLITS}
    original_counts: Counter[int] = Counter()
    final_counts: Counter[int] = Counter()
    final_image_counts: Counter[int] = Counter()
    format_counts: Counter[str] = Counter()
    details: list[str] = []
    warnings = ["Dataset C contains YOLO segmentation polygon records as well as five-field detection records; valid polygons were preserved."]
    excluded = corrupted = invalid = empty = missing_pairs = quarantined = 0

    for split in SPLITS:
        image_dir = SOURCE / split / "images"
        label_dir = SOURCE / split / "labels"
        image_paths = sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
        label_paths = sorted(path for path in label_dir.iterdir() if path.is_file() and path.suffix.lower() == ".txt")
        stats[split].original_images = len(image_paths)
        images_by_stem = {path.stem: path for path in image_paths}
        labels_by_stem = {path.stem: path for path in label_paths}
        missing_pairs += sum(1 for path in image_paths if path.stem not in labels_by_stem)
        missing_pairs += sum(1 for path in label_paths if path.stem not in images_by_stem)

        for image_path in image_paths:
            if image_path.stem not in labels_by_stem:
                quarantine_file(image_path, split, "missing-label")
                quarantined += 1
                details.append(f"quarantined missing label: {split}/{image_path.name}")
                continue
            label_path = labels_by_stem[image_path.stem]
            image_error = validate_image(image_path)
            if image_error:
                quarantine_file(image_path, split, "corrupted-image")
                quarantine_file(label_path, split, "corrupted-image")
                quarantined += 2
                corrupted += 1
                excluded += 1
                details.append(f"quarantined corrupted image and label: {split}/{image_path.name} ({image_error})")
                continue

            valid_lines, problems, counts, observed_formats = parse_annotation(label_path)
            format_counts.update(observed_formats)
            for line in label_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    fields = line.split()
                    try:
                        class_id = int(fields[0])
                        if class_id in source_classes:
                            original_counts[class_id] += 1
                    except (ValueError, IndexError):
                        pass
            if problems:
                invalid += sum("empty label file" not in problem for problem in problems)
                empty += sum("empty label file" in problem for problem in problems)
                quarantine_file(label_path, split, "invalid-label")
                quarantined += 1
                details.append(f"invalid label quarantined: {split}/{label_path.name}: {'; '.join(problems)}")
            if not valid_lines:
                quarantine_file(image_path, split, "excluded-no-valid-annotations")
                if not problems:
                    quarantine_file(label_path, split, "excluded-no-valid-annotations")
                    quarantined += 2
                else:
                    quarantined += 1
                excluded += 1
                details.append(f"excluded image with no valid annotations: {split}/{image_path.name}")
                continue

            shutil.copy2(image_path, OUTPUT / split / "images" / image_path.name)
            (OUTPUT / split / "labels" / f"{image_path.stem}.txt").write_text("\n".join(valid_lines) + "\n", encoding="utf-8")
            stats[split].processed_images += 1
            final_counts.update(counts)
            for class_id in counts:
                final_image_counts[class_id] += 1

        for label_path in label_paths:
            if label_path.stem not in images_by_stem:
                quarantine_file(label_path, split, "missing-image")
                quarantined += 1
                details.append(f"quarantined missing image: {split}/{label_path.name}")

    (OUTPUT / "data.yaml").write_text(
        """train: train/images
val: valid/images
test: test/images

nc: 4
names:
  0: Crack
  1: Corrosion
  2: Dent
  3: Missing Fastener
""",
        encoding="utf-8",
    )
    write_report(source_classes, stats, original_counts, final_counts, final_image_counts, format_counts, details, excluded, corrupted, invalid, empty, missing_pairs, quarantined, warnings)

    total_original = sum(split.original_images for split in stats.values())
    total_processed = sum(split.processed_images for split in stats.values())
    print("DATASET C PROCESSING COMPLETE")
    print("\nOriginal:")
    print(f"Train: {stats['train'].original_images}")
    print(f"Valid: {stats['valid'].original_images}")
    print(f"Test: {stats['test'].original_images}")
    print(f"Total: {total_original}")
    print("\nProcessed:")
    print(f"Train: {stats['train'].processed_images}")
    print(f"Valid: {stats['valid'].processed_images}")
    print(f"Test: {stats['test'].processed_images}")
    print(f"Total: {total_processed}")
    print("\nFinal classes:")
    for class_id in (0, 1, 2, 3):
        print(f"{FINAL_CLASS_NAMES[class_id]}: {final_counts[class_id]} annotations / {final_image_counts[class_id]} images")
    print("\nRupture:")
    print("Mapped to Crack (0) after inspecting representative train, valid, and test images showing crack-like surface fractures.")
    print(f"\nExcluded:\n{excluded}")
    print(f"\nCorrupted:\n{corrupted}")
    print(f"\nInvalid/empty annotations:\n{invalid + empty}")
    print(f"\nQuarantined:\n{quarantined}")


if __name__ == "__main__":
    main()
