"""Validate and preprocess Dataset A without modifying the source dataset."""

from __future__ import annotations

import ast
import hashlib
import math
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "datasets" / "dataset_A"
OUTPUT = SOURCE / "processed"
SPLITS = ("train", "valid", "test")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
FINAL_CLASS_NAMES = {0: "Crack", 1: "Corrosion", 2: "Dent", 3: "Missing Fastener"}


@dataclass
class SplitStats:
    source_images: int = 0
    processed_images: int = 0


@dataclass
class ValidationStats:
    missing_pairs: int = 0
    corrupted_images: int = 0
    empty_labels: int = 0
    invalid_annotations: int = 0
    invalid_boxes: int = 0
    unsupported_files: int = 0
    zero_byte_images: int = 0
    removed_annotations: int = 0
    excluded_images: int = 0
    details: list[str] = field(default_factory=list)


def read_source_names() -> dict[int, str]:
    text = (SOURCE / "data.yaml").read_text(encoding="utf-8")
    match = re.search(r"^names:\s*(\[.*\])\s*$", text, re.MULTILINE)
    if match:
        names = ast.literal_eval(match.group(1))
        if isinstance(names, list):
            return {index: str(name) for index, name in enumerate(names)}
    names: dict[int, str] = {}
    in_names = False
    for line in text.splitlines():
        if line.strip() == "names:":
            in_names = True
            continue
        if in_names:
            match = re.match(r"\s*(\d+):\s*(.+?)\s*$", line)
            if match:
                names[int(match.group(1))] = match.group(2).strip("'\"")
            elif line and not line[0].isspace():
                break
    if not names:
        raise ValueError("Could not read class names from Dataset A data.yaml")
    return names


def validate_image(path: Path) -> tuple[str | None, tuple[int, int] | None]:
    if path.stat().st_size == 0:
        return "zero-byte image", None
    try:
        with Image.open(path) as image:
            dimensions = image.size
            image.verify()
    except (OSError, UnidentifiedImageError) as error:
        return f"{type(error).__name__}: {error}", None
    return None, dimensions


def parse_label(path: Path, corrosion_id: int) -> tuple[list[str], Counter[int], list[str], int, int]:
    kept: list[str] = []
    class_counts: Counter[int] = Counter()
    problems: list[str] = []
    removed = invalid_boxes = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return [], class_counts, [f"could not read label: {error}"], 0, 0
    if not any(line.strip() for line in lines):
        return [], class_counts, ["empty label file"], 0, 0

    for line_number, raw_line in enumerate(lines, start=1):
        text = raw_line.strip()
        if not text:
            continue
        fields = text.split()
        if len(fields) != 5:
            problems.append(f"line {line_number}: expected exactly 5 fields, found {len(fields)}")
            continue
        try:
            class_value = float(fields[0])
            class_id = int(fields[0])
            values = [float(value) for value in fields[1:]]
        except (ValueError, OverflowError):
            problems.append(f"line {line_number}: class ID and coordinates must be numeric")
            continue
        if not math.isfinite(class_value) or class_value != class_id:
            problems.append(f"line {line_number}: class ID is not an integer")
            continue
        if any(not math.isfinite(value) for value in values):
            problems.append(f"line {line_number}: coordinates must be finite")
            continue
        x, y, width, height = values
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1 and 0 < height <= 1):
            problems.append(f"line {line_number}: invalid bounding-box values")
            invalid_boxes += 1
            continue
        if x - width / 2 < 0 or x + width / 2 > 1 or y - height / 2 < 0 or y + height / 2 > 1:
            problems.append(f"line {line_number}: bounding box extends outside image bounds")
            invalid_boxes += 1
            continue
        class_counts[class_id] += 1
        if class_id == corrosion_id:
            fields[0] = "1"
            kept.append(" ".join(fields))
        else:
            removed += 1
    return kept, class_counts, problems, removed, invalid_boxes


def duplicate_names(paths_by_split: dict[str, list[Path]]) -> list[str]:
    occurrences: defaultdict[str, list[str]] = defaultdict(list)
    for split, paths in paths_by_split.items():
        for path in paths:
            occurrences[path.name.lower()].append(f"{split}/{path.name}")
    return [f"{name}: {', '.join(values)}" for name, values in sorted(occurrences.items()) if len(values) > 1]


def duplicate_hash_groups(items: list[tuple[Path, str]]) -> list[list[str]]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for path, digest in items:
        groups[digest].append(str(path))
    return [paths for paths in groups.values() if len(paths) > 1]


def write_report(
    source_names: dict[int, str],
    corrosion_id: int,
    stats: dict[str, SplitStats],
    label_count: int,
    actual_counts: Counter[int],
    image_dimensions: Counter[tuple[int, int]],
    validation: ValidationStats,
    duplicate_filename_entries: list[str],
    exact_groups: list[list[str]],
    final_annotations: int,
) -> None:
    lines = [
        "AeroIntel Dataset A processing report",
        "======================================",
        "",
        "SOURCE DATASET",
        "- Dataset name: Aircraft Corrosion YOLO",
        "- Version: 1",
        "- Source format: Roboflow YOLO Object Detection",
        f"- Source folder: {SOURCE}",
        "- Original Dataset A was not modified.",
        "",
        "ORIGINAL DATA",
        *(f"- {split.title()} images: {stats[split].source_images}" for split in SPLITS),
        f"- Total images: {sum(item.source_images for item in stats.values())}",
        f"- Total labels: {label_count}",
        f"- Classes from data.yaml: {source_names}",
        f"- Actual class IDs found in labels: {dict(sorted(actual_counts.items()))}",
        "- Image dimensions:",
        *(f"  - {width}x{height}: {count}" for (width, height), count in sorted(image_dimensions.items())),
        "",
        "CORROSION",
        f"- Source corrosion class ID: {corrosion_id}",
        "- Final corrosion class ID: 1",
        f"- Corrosion annotations: {final_annotations}",
        f"- Images containing corrosion: {sum(item.processed_images for item in stats.values())}",
        "",
        "VALIDATION",
        f"- Missing image/label pairs: {validation.missing_pairs}",
        f"- Corrupted images: {validation.corrupted_images}",
        f"- Zero-byte images: {validation.zero_byte_images}",
        f"- Unsupported files: {validation.unsupported_files}",
        f"- Empty labels: {validation.empty_labels}",
        f"- Invalid annotations: {validation.invalid_annotations}",
        f"- Invalid bounding boxes: {validation.invalid_boxes}",
        f"- Duplicate filenames: {len(duplicate_filename_entries)}",
        f"- Exact duplicate image groups: {len(exact_groups)}",
        "",
        "FILTERING",
        f"- Non-corrosion annotations removed: {validation.removed_annotations}",
        f"- Images excluded: {validation.excluded_images}",
        "- Near-duplicates were not removed.",
        "",
        "FINAL DATA",
        *(f"- {split.title()} images: {stats[split].processed_images}" for split in SPLITS),
        f"- Total images: {sum(item.processed_images for item in stats.values())}",
        f"- Total corrosion annotations: {final_annotations}",
        "",
        "DETAILS",
        "- Image dimensions and extensions were inspected for every source image.",
    ]
    lines.extend(f"- {detail}" for detail in validation.details)
    if duplicate_filename_entries:
        lines.append("- Duplicate filename entries:")
        lines.extend(f"  - {entry}" for entry in duplicate_filename_entries)
    if exact_groups:
        lines.append("- Exact duplicate image groups:")
        lines.extend(f"  - {', '.join(group)}" for group in exact_groups)
    validation_failed = validation.missing_pairs or validation.corrupted_images or validation.invalid_annotations or validation.unsupported_files
    lines.extend(["", "FINAL VALIDATION: FAIL" if validation_failed else "FINAL VALIDATION: PASS"])
    (OUTPUT / "processing_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not SOURCE.is_dir():
        raise FileNotFoundError(f"Dataset A directory not found: {SOURCE}")
    source_names = read_source_names()
    source_images_by_split: dict[str, list[Path]] = {}
    source_labels_by_split: dict[str, list[Path]] = {}
    actual_counts: Counter[int] = Counter()
    unsupported_files = 0
    for split in SPLITS:
        image_dir = SOURCE / split / "images"
        label_dir = SOURCE / split / "labels"
        image_files = sorted(path for path in image_dir.iterdir() if path.is_file())
        source_images_by_split[split] = [path for path in image_files if path.suffix.lower() in IMAGE_EXTENSIONS]
        unsupported_files += sum(path.suffix.lower() not in IMAGE_EXTENSIONS for path in image_files)
        source_labels_by_split[split] = sorted(path for path in label_dir.iterdir() if path.is_file() and path.suffix.lower() == ".txt")
        for label in source_labels_by_split[split]:
            for line in label.read_text(encoding="utf-8", errors="replace").splitlines():
                fields = line.split()
                if fields:
                    try:
                        class_value = float(fields[0])
                        if math.isfinite(class_value) and class_value.is_integer():
                            actual_counts[int(class_value)] += 1
                    except ValueError:
                        pass
    corrosion_candidates = [class_id for class_id, name in source_names.items() if "corrosion" in name.casefold()]
    observed_ids = set(actual_counts)
    if len(corrosion_candidates) == 1:
        corrosion_id = corrosion_candidates[0]
    elif len(source_names) == 1 and len(observed_ids) <= 1:
        corrosion_id = next(iter(source_names))
    else:
        raise ValueError(f"Could not identify a unique corrosion class: names={source_names}, observed IDs={sorted(observed_ids)}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    for split in SPLITS:
        (OUTPUT / split / "images").mkdir(parents=True, exist_ok=True)
        (OUTPUT / split / "labels").mkdir(parents=True, exist_ok=True)

    stats = {split: SplitStats(len(source_images_by_split[split])) for split in SPLITS}
    validation = ValidationStats(unsupported_files=unsupported_files)
    image_dimensions: Counter[tuple[int, int]] = Counter()
    source_hashes: list[tuple[Path, str]] = []
    final_annotations = 0
    for split in SPLITS:
        images = source_images_by_split[split]
        labels = source_labels_by_split[split]
        image_stems = {path.stem for path in images}
        label_stems = {path.stem for path in labels}
        for stem in image_stems - label_stems:
            validation.missing_pairs += 1
            validation.details.append(f"missing label: {split}/{stem}")
        for stem in label_stems - image_stems:
            validation.missing_pairs += 1
            validation.details.append(f"missing image: {split}/{stem}")
        labels_by_stem = {path.stem: path for path in labels}
        for image in images:
            error, dimensions = validate_image(image)
            if error:
                validation.corrupted_images += 1
                validation.zero_byte_images += int(error == "zero-byte image")
                validation.details.append(f"invalid image: {split}/{image.name}: {error}")
                continue
            image_dimensions[dimensions] += 1
            source_hashes.append((image, hashlib.sha256(image.read_bytes()).hexdigest()))
            label = labels_by_stem.get(image.stem)
            if label is None:
                continue
            kept, class_counts, problems, removed, invalid_boxes = parse_label(label, corrosion_id)
            validation.removed_annotations += removed
            validation.invalid_annotations += len(problems)
            validation.invalid_boxes += invalid_boxes
            validation.empty_labels += int(any(problem == "empty label file" for problem in problems))
            for problem in problems:
                validation.details.append(f"invalid label: {split}/{label.name}: {problem}")
            if not kept:
                validation.excluded_images += 1
                validation.details.append(f"excluded no valid corrosion annotation: {split}/{image.name}")
                continue
            shutil.copy2(image, OUTPUT / split / "images" / image.name)
            (OUTPUT / split / "labels" / f"{image.stem}.txt").write_text("\n".join(kept) + "\n", encoding="utf-8")
            stats[split].processed_images += 1
            final_annotations += len(kept)

    duplicate_filename_entries = duplicate_names(source_images_by_split)
    exact_groups = duplicate_hash_groups(source_hashes)
    (OUTPUT / "data.yaml").write_text(
        """train: train/images\nval: valid/images\ntest: test/images\n\nnc: 4\nnames:\n  0: Crack\n  1: Corrosion\n  2: Dent\n  3: Missing Fastener\n""",
        encoding="utf-8",
    )
    write_report(source_names, corrosion_id, stats, sum(len(paths) for paths in source_labels_by_split.values()), actual_counts, image_dimensions, validation, duplicate_filename_entries, exact_groups, final_annotations)
    print("DATASET A PROCESSING COMPLETE")
    print(f"Original: Train {stats['train'].source_images}, Valid {stats['valid'].source_images}, Test {stats['test'].source_images}, Total {sum(item.source_images for item in stats.values())}")
    print(f"Processed: Train {stats['train'].processed_images}, Valid {stats['valid'].processed_images}, Test {stats['test'].processed_images}, Total {sum(item.processed_images for item in stats.values())}")
    print(f"Corrosion: Images {sum(item.processed_images for item in stats.values())}, Annotations {final_annotations}")
    print(f"Excluded: {validation.excluded_images}")
    print(f"Invalid: {validation.invalid_annotations}")
    print(f"Duplicates: {len(exact_groups)} exact groups, {len(duplicate_filename_entries)} duplicate filename entries")
    print(f"Validation: {'PASS' if not (validation.missing_pairs or validation.corrupted_images or validation.invalid_annotations or validation.unsupported_files) else 'FAIL'}")


if __name__ == "__main__":
    main()