"""Merge the processed Dataset B and C pools into a leakage-safe master dataset."""

from __future__ import annotations

import hashlib
import random
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "B": ROOT / "datasets" / "dataset_B" / "processed",
    "C": ROOT / "datasets" / "dataset_C" / "processed",
}
OUTPUT = ROOT / "datasets" / "master_dataset"
SEED = 20260922
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
CLASS_NAMES = {0: "Crack", 1: "Corrosion", 2: "Dent", 3: "Missing Fastener"}


@dataclass(frozen=True)
class SourceItem:
    source: str
    split: str
    image: Path
    label: Path
    image_hash: str
    average_hash: int


def source_directories(source: str, base: Path, split: str) -> tuple[Path, Path]:
    if source == "B":
        source_split = "val" if split == "valid" else split
        return base / "images" / source_split, base / "labels" / source_split
    return base / split / "images", base / split / "labels"


def validate_image(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
    except (OSError, UnidentifiedImageError) as error:
        return f"{type(error).__name__}: {error}"
    return None


def average_hash(path: Path) -> int:
    with Image.open(path) as image:
        image = image.convert("L").resize((8, 8))
        pixels = list(image.getdata())
    average = sum(pixels) / len(pixels)
    result = 0
    for pixel in pixels:
        result = (result << 1) | int(pixel >= average)
    return result


def validate_label(path: Path) -> tuple[bool, Counter[int], str | None]:
    counts: Counter[int] = Counter()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return False, counts, str(error)
    if not lines or not any(line.strip() for line in lines):
        return False, counts, "empty label"
    for line_number, line in enumerate(lines, start=1):
        fields = line.split()
        if len(fields) != 5 and not (len(fields) >= 7 and (len(fields) - 1) % 2 == 0):
            return False, counts, f"line {line_number}: expected detection or segmentation YOLO fields"
        try:
            class_id = int(fields[0])
            values = [float(value) for value in fields[1:]]
        except (ValueError, IndexError):
            return False, counts, f"line {line_number}: non-numeric annotation"
        if class_id not in CLASS_NAMES:
            return False, counts, f"line {line_number}: unexpected class ID {class_id}"
        if not all(0 <= value <= 1 for value in values):
            return False, counts, f"line {line_number}: coordinates outside [0, 1]"
        if len(fields) == 5:
            x, y, width, height = values
            if width <= 0 or height <= 0:
                return False, counts, f"line {line_number}: non-positive dimensions"
            if x - width / 2 < 0 or x + width / 2 > 1 or y - height / 2 < 0 or y + height / 2 > 1:
                return False, counts, f"line {line_number}: bounding box outside image"
        else:
            points = list(zip(values[::2], values[1::2]))
            if len(points) < 3:
                return False, counts, f"line {line_number}: polygon requires at least three points"
            if min(x for x, _ in points) == max(x for x, _ in points) or min(y for _, y in points) == max(y for _, y in points):
                return False, counts, f"line {line_number}: polygon has zero area"
        counts[class_id] += 1
    return True, counts, None


def hamming_distance(first: int, second: int) -> int:
    return (first ^ second).bit_count()


def write_report(
    source_counts: Counter[str],
    source_annotations: dict[str, Counter[int]],
    total_source: int,
    duplicate_filename_count: int,
    exact_groups: list[list[SourceItem]],
    near_groups: list[tuple[SourceItem, SourceItem]],
    used: int,
    excluded: int,
    split_counts: Counter[str],
    final_annotations: Counter[int],
    warnings: list[str],
) -> None:
    lines = [
        "AeroIntel master Dataset B+C merge report",
        "==========================================",
        "Sources: Dataset B processed + Dataset C processed",
        "Dataset D, E, and F: not included",
        f"Deterministic random seed: {SEED}",
        "",
        "Source image counts:",
        f"  Dataset B: {source_counts['B']}",
        f"  Dataset C: {source_counts['C']}",
        f"  Total source images: {total_source}",
        f"  Number of images used: {used}",
        f"  Number excluded: {excluded}",
        "",
        f"Duplicate filename count: {duplicate_filename_count}",
        f"Exact duplicate image/hash groups: {len(exact_groups)}",
        f"Images in exact duplicate groups: {sum(len(group) for group in exact_groups)}",
        f"Near-duplicate pairs (average-hash distance <= 4, excluding exact hashes): {len(near_groups)}",
        "Exact duplicate groups were assigned as indivisible units so their content cannot cross splits.",
        "",
        "Final split counts:",
        f"  Train: {split_counts['train']}",
        f"  Valid: {split_counts['valid']}",
        f"  Test: {split_counts['test']}",
        "",
        "Final annotation counts:",
        *(f"  {CLASS_NAMES[class_id]}: {final_annotations[class_id]}" for class_id in range(4)),
        "",
        "Annotation counts by source:",
        "  Dataset B:",
        *(f"    {CLASS_NAMES[class_id]}: {source_annotations['B'][class_id]}" for class_id in range(4)),
        "  Dataset C:",
        *(f"    {CLASS_NAMES[class_id]}: {source_annotations['C'][class_id]}" for class_id in range(4)),
        "",
        "Warnings:",
    ]
    lines.extend(f"  {warning}" for warning in warnings) if warnings else lines.append("  None")
    (OUTPUT / "merge_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not all(path.is_dir() for path in SOURCES.values()):
        raise FileNotFoundError("Both processed Dataset B and Dataset C directories are required")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    for split in ("train", "valid", "test"):
        (OUTPUT / split / "images").mkdir(parents=True, exist_ok=True)
        (OUTPUT / split / "labels").mkdir(parents=True, exist_ok=True)

    items: list[SourceItem] = []
    source_counts: Counter[str] = Counter()
    source_annotations = {source: Counter() for source in SOURCES}
    excluded = 0
    warnings: list[str] = []
    filename_occurrences: defaultdict[str, list[SourceItem]] = defaultdict(list)

    for source, base in SOURCES.items():
        for split in ("train", "valid", "test"):
            image_dir, label_dir = source_directories(source, base, split)
            images = sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
            labels = {path.stem: path for path in label_dir.glob("*.txt")}
            for image in images:
                label = labels.get(image.stem)
                if label is None:
                    excluded += 1
                    warnings.append(f"Excluded missing label: {source}/{split}/{image.name}")
                    continue
                image_error = validate_image(image)
                valid_label, label_counts, label_error = validate_label(label)
                if image_error or not valid_label:
                    excluded += 1
                    reason = image_error or label_error or "invalid label"
                    warnings.append(f"Excluded invalid source pair: {source}/{split}/{image.name}: {reason}")
                    continue
                item = SourceItem(source, split, image, label, hashlib.sha256(image.read_bytes()).hexdigest(), average_hash(image))
                items.append(item)
                source_counts[source] += 1
                source_annotations[source].update(label_counts)
                filename_occurrences[image.name.lower()].append(item)
            for label in labels.values():
                if not (image_dir / f"{label.stem}{label.suffix}").exists() and not any(path.stem == label.stem for path in images):
                    excluded += 1
                    warnings.append(f"Excluded missing image: {source}/{split}/{label.name}")

    duplicate_filename_count = sum(len(group) for group in filename_occurrences.values() if len(group) > 1)
    hash_groups: defaultdict[str, list[SourceItem]] = defaultdict(list)
    for item in items:
        hash_groups[item.image_hash].append(item)
    exact_groups = [group for group in hash_groups.values() if len(group) > 1]

    near_groups: list[tuple[SourceItem, SourceItem]] = []
    buckets: defaultdict[tuple[int, int], list[SourceItem]] = defaultdict(list)
    for item in items:
        for band in range(4):
            buckets[(band, (item.average_hash >> (band * 16)) & 0xFFFF)].append(item)
    seen_pairs: set[tuple[str, str]] = set()
    for bucket_items in buckets.values():
        for index, first in enumerate(bucket_items):
            for second in bucket_items[index + 1 :]:
                if first.image_hash == second.image_hash:
                    continue
                pair = tuple(sorted((str(first.image), str(second.image))))
                if pair not in seen_pairs and hamming_distance(first.average_hash, second.average_hash) <= 4:
                    seen_pairs.add(pair)
                    near_groups.append((first, second))

    grouped_items: list[list[SourceItem]] = list(exact_groups)
    grouped_hashes = {item.image_hash for group in exact_groups for item in group}
    grouped_items.extend([group for group in ([item] for item in items) if group[0].image_hash not in grouped_hashes])
    random.Random(SEED).shuffle(grouped_items)
    targets = {"train": len(items) * 0.8, "valid": len(items) * 0.1, "test": len(items) * 0.1}
    split_counts: Counter[str] = Counter()
    assignments: dict[SourceItem, str] = {}
    for group in grouped_items:
        destination = min(("train", "valid", "test"), key=lambda split: split_counts[split] - targets[split])
        for item in group:
            assignments[item] = destination
            split_counts[destination] += 1

    final_annotations: Counter[int] = Counter()
    final_image_counts: Counter[int] = Counter()
    for item in sorted(items, key=lambda value: (assignments[value], value.source, value.split, value.image.name)):
        split = assignments[item]
        filename = f"{item.source}_{item.image.name}"
        shutil.copy2(item.image, OUTPUT / split / "images" / filename)
        label_lines = item.label.read_text(encoding="utf-8").splitlines()
        (OUTPUT / split / "labels" / f"{Path(filename).stem}.txt").write_text("\n".join(label_lines) + "\n", encoding="utf-8")
        valid_label, counts, error = validate_label(OUTPUT / split / "labels" / f"{Path(filename).stem}.txt")
        if not valid_label:
            warnings.append(f"Output validation error: {filename}: {error}")
        final_annotations.update(counts)
        for class_id in counts:
            final_image_counts[class_id] += 1

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
    write_report(source_counts, source_annotations, len(items) + excluded, duplicate_filename_count, exact_groups, near_groups, len(items), excluded, split_counts, final_annotations, warnings)

    missing_pairs = invalid_annotations = corrupted_images = cross_split_duplicates = 0
    seen_hashes: dict[str, str] = {}
    for split in ("train", "valid", "test"):
        image_dir = OUTPUT / split / "images"
        label_dir = OUTPUT / split / "labels"
        images = list(image_dir.iterdir())
        labels = list(label_dir.glob("*.txt"))
        image_stems = {path.stem for path in images}
        label_stems = {path.stem for path in labels}
        missing_pairs += len(image_stems - label_stems) + len(label_stems - image_stems)
        for image in images:
            image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
            if image_hash in seen_hashes and seen_hashes[image_hash] != split:
                cross_split_duplicates += 1
            seen_hashes[image_hash] = split
            if validate_image(image):
                corrupted_images += 1
        for label in labels:
            valid, _, _ = validate_label(label)
            invalid_annotations += int(not valid)

    validation = "PASS" if not (missing_pairs or invalid_annotations or corrupted_images or cross_split_duplicates) else "FAIL"
    print("MASTER DATASET MERGE COMPLETE")
    print(f"\nDataset B images used: {source_counts['B']}")
    print(f"Dataset C images used: {source_counts['C']}")
    print(f"Total images: {len(items)}")
    print(f"\nTrain: {split_counts['train']}")
    print(f"Valid: {split_counts['valid']}")
    print(f"Test: {split_counts['test']}")
    print("\nClasses:")
    for class_id in range(4):
        print(f"{CLASS_NAMES[class_id]}: {final_annotations[class_id]} annotations")
    print(f"\nDuplicate images across splits: {cross_split_duplicates}")
    print(f"Missing image-label pairs: {missing_pairs}")
    print(f"Invalid annotations: {invalid_annotations}")
    print(f"Corrupted images: {corrupted_images}")
    print(f"\nValidation: {validation}")


if __name__ == "__main__":
    main()
