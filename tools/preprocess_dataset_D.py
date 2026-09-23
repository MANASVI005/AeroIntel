"""Preprocess Dataset D Version 20 for AeroIntel."""

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
SOURCE = ROOT / "datasets" / "dataset_D"
OUTPUT = SOURCE / "processed"
SPLITS = ("train", "valid", "test")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SOURCE_CLASS_NAMES = {
    0: "crack",
    1: "dent",
    2: "missing-head",
    3: "paint-peel-off",
    4: "scratch",
}
CLASS_MAPPING = {0: 0, 1: 2, 2: 3}
FINAL_CLASS_NAMES = {0: "Crack", 1: "Corrosion", 2: "Dent", 3: "Missing Fastener"}
UNWANTED_CLASS_NAMES = {3: "paint-peel-off", 4: "scratch"}


@dataclass
class SplitStats:
    original_images: int = 0
    processed_images: int = 0


def read_source_classes() -> dict[int, str]:
    text = (SOURCE / "data.yaml").read_text(encoding="utf-8")
    match = re.search(r"^names:\s*(\[.*\])\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError("Could not read class names from Dataset D data.yaml")
    names = ast.literal_eval(match.group(1))
    if not isinstance(names, list):
        raise ValueError("Dataset D data.yaml names must be a list")
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


def parse_label(path: Path) -> tuple[list[str], list[str], Counter[int], Counter[int], Counter[int]]:
    kept_lines: list[str] = []
    problems: list[str] = []
    original_counts: Counter[int] = Counter()
    kept_counts: Counter[int] = Counter()
    removed_counts: Counter[int] = Counter()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return [], [f"could not read label: {error}"], original_counts, kept_counts, removed_counts

    if not any(line.strip() for line in lines):
        return [], ["empty label file"], original_counts, kept_counts, removed_counts

    for line_number, raw_line in enumerate(lines, start=1):
        text = raw_line.strip()
        if not text:
            continue
        fields = text.split()
        class_id: int | None = None
        problem: str | None = None
        try:
            class_value = float(fields[0])
            class_id = int(fields[0])
            if math.isfinite(class_value) and class_value == class_id:
                original_counts[class_id] += 1
            else:
                problem = "class ID is not an integer"
            if problem is None and class_id not in SOURCE_CLASS_NAMES:
                problem = f"unknown class ID {class_id}"
            if problem is None and len(fields) != 5:
                problem = f"expected 5 YOLO fields, found {len(fields)}"
            if problem is None:
                values = [float(value) for value in fields[1:]]
                x, y, width, height = values
                if not all(math.isfinite(value) for value in values):
                    problem = "coordinates must be finite"
                elif not all(0 <= value <= 1 for value in values):
                    problem = "coordinates must be normalized to [0, 1]"
                elif width <= 0 or height <= 0:
                    problem = "width and height must be positive"
                elif x - width / 2 < 0 or x + width / 2 > 1 or y - height / 2 < 0 or y + height / 2 > 1:
                    problem = "bounding box extends outside image bounds"
        except (ValueError, OverflowError, IndexError):
            problem = "class ID and coordinates must be numeric"

        if problem:
            problems.append(f"line {line_number}: {problem}")
        elif class_id in CLASS_MAPPING:
            fields[0] = str(CLASS_MAPPING[class_id])
            kept_lines.append(" ".join(fields))
            kept_counts[CLASS_MAPPING[class_id]] += 1
        elif class_id in UNWANTED_CLASS_NAMES:
            removed_counts[class_id] += 1

    return kept_lines, problems, original_counts, kept_counts, removed_counts


def write_report(
    source_classes: dict[int, str],
    stats: dict[str, SplitStats],
    original_counts: Counter[int],
    final_counts: Counter[int],
    final_image_counts: Counter[int],
    removed_counts: Counter[int],
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
        "AeroIntel Dataset D processing report",
        "======================================",
        "Dataset name: aircraft_skin_defects",
        "Dataset version: Version 20 (5 classes grayscale no augmentation)",
        f"Source folder: {SOURCE}",
        "",
        "Original image count:",
        *(f"  {split.title()}: {stats[split].original_images}" for split in SPLITS),
        f"  Total: {total_original_images}",
        "",
        "Original classes and IDs:",
        *(f"  {class_id}: {name}" for class_id, name in sorted(source_classes.items())),
        "",
        "Original annotation counts by class:",
        *(f"  {class_id} ({source_classes.get(class_id, 'Unknown')}): {original_counts[class_id]}" for class_id in sorted(source_classes)),
        "",
        "Mapping performed:",
        "  crack (0) -> Crack (0)",
        "  dent (1) -> Dent (2)",
        "  missing-head (2) -> Missing Fastener (3)",
        "  paint-peel-off (3) -> removed",
        "  scratch (4) -> removed",
        "  Corrosion (1) -> no annotations created",
        "",
        f"Scratch annotations removed: {removed_counts[4]}",
        f"Paint-peel-off annotations removed: {removed_counts[3]}",
        f"Images excluded because they contained only unwanted classes: {excluded}",
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
        raise FileNotFoundError(f"Dataset D directory not found: {SOURCE}")
    source_classes = read_source_classes()
    if source_classes != SOURCE_CLASS_NAMES:
        raise ValueError(f"Unexpected Dataset D classes: {source_classes}")
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
    removed_counts: Counter[int] = Counter()
    details: list[str] = []
    warnings: list[str] = []
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
                excluded += 1
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

            kept_lines, problems, source_line_counts, kept_line_counts, removed_line_counts = parse_label(label_path)
            original_counts.update(source_line_counts)
            removed_counts.update(removed_line_counts)
            if problems:
                invalid += sum("empty label file" not in problem for problem in problems)
                empty += sum("empty label file" in problem for problem in problems)
                quarantine_file(label_path, split, "invalid-label")
                quarantined += 1
                details.append(f"invalid label quarantined: {split}/{label_path.name}: {'; '.join(problems)}")
            if not kept_lines:
                quarantine_file(image_path, split, "excluded-no-target-annotations")
                if not problems:
                    quarantine_file(label_path, split, "excluded-no-target-annotations")
                    quarantined += 2
                else:
                    quarantined += 1
                excluded += 1
                details.append(f"excluded image with no valid target annotations: {split}/{image_path.name}")
                continue

            shutil.copy2(image_path, OUTPUT / split / "images" / image_path.name)
            (OUTPUT / split / "labels" / f"{image_path.stem}.txt").write_text("\n".join(kept_lines) + "\n", encoding="utf-8")
            stats[split].processed_images += 1
            final_counts.update(kept_line_counts)
            for class_id in kept_line_counts:
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
    write_report(source_classes, stats, original_counts, final_counts, final_image_counts, removed_counts, details, excluded, corrupted, invalid, empty, missing_pairs, quarantined, warnings)

    total_original = sum(split.original_images for split in stats.values())
    total_processed = sum(split.processed_images for split in stats.values())
    validation = "PASS" if not (corrupted or missing_pairs) else "FAIL"
    print("DATASET D PROCESSING COMPLETE")
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
    print("\nRemoved:")
    print(f"Scratch: {removed_counts[4]} annotations")
    print(f"Paint-peel-off: {removed_counts[3]} annotations")
    print(f"\nExcluded images:\n{excluded}")
    print(f"\nCorrupted:\n{corrupted}")
    print(f"\nInvalid/empty annotations:\n{invalid + empty}")
    print(f"\nQuarantined:\n{quarantined}")
    print(f"\nValidation:\n{validation}")


if __name__ == "__main__":
    main()
