"""Verification script to test AeroMemory against Dataset E.

NOTE & DISCLAIMER:
- Dataset E fixtures are synthetic benchmark datasets with simulated defect geometries,
  progression steps, and repair events (10 px/mm synthetic calibration).
- These tests validate state-machine transitions, IoU/centroid matching, delta tracking,
  and database persistence logic within the AeroMemory engine.
- They do NOT establish certified production airworthiness or real-aircraft reliability,
  which require physical NDT inspection calibration and regulatory validation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeromemory import AeroMemoryService, SQLiteAeroMemoryRepository, ProgressionState


def run_dataset_e_verification(selected_aircraft: list[str] | None = None) -> bool:
    dataset_e = ROOT / "datasets" / "dataset_E_aeromemory"
    aircraft_dir = dataset_e / "aircraft"

    if not aircraft_dir.exists():
        print(f"Error: Dataset E aircraft directory not found at {aircraft_dir}")
        return False

    default_test_cases = ["AI-001", "AI-002", "AI-003", "AI-006", "AI-019"]
    aircraft_to_test = selected_aircraft if selected_aircraft else default_test_cases

    print("=" * 78)
    print("           AEROINTEL AEROMEMORY ENGINE VERIFICATION ON DATASET E")
    print("=" * 78)
    print("DISCLAIMER:")
    print("  Dataset E fixtures are synthetic benchmark datasets used to verify")
    print("  temporal matching, state transitions, and database persistence.")
    print("  These tests do NOT establish certified production/real-aircraft reliability.")
    print("=" * 78)
    print(f"Target Aircraft Scenarios: {', '.join(aircraft_to_test)}\n")

    db_test_path = ROOT / "test_verification.db"
    all_passed = True
    total_inspections = 0
    passed_inspections = 0

    for acid in aircraft_to_test:
        ac_path = aircraft_dir / acid
        if not ac_path.exists():
            print(f"Warning: {ac_path} not found. Skipping.")
            continue

        print(f"\nEvaluating Aircraft: {acid}")
        print("-" * 78)

        # Fresh isolated DB per aircraft to prevent defect_id cross-contamination
        if db_test_path.exists():
            db_test_path.unlink()

        repo = SQLiteAeroMemoryRepository(db_path=db_test_path)
        service = AeroMemoryService(repository=repo, enable_registration=True)

        inspections = sorted(
            [d for d in ac_path.iterdir() if d.is_dir() and d.name.startswith("INS-")]
        )

        for insp_dir in inspections:
            total_inspections += 1
            json_file = insp_dir / f"{insp_dir.name}.json"
            png_file = insp_dir / f"{insp_dir.name}.png"

            with open(json_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

            insp_id = meta["inspection_id"]
            component = meta.get("component_id", "DefaultComponent")
            date_str = meta["date"]
            defects = meta.get("defects", [])
            ground_truth = meta.get("comparison_ground_truth", [])

            # Run AeroMemory inspection processing
            result = service.process_inspection(
                inspection_id=insp_id,
                aircraft_id=acid,
                component=component,
                detections=defects,
                timestamp=date_str,
                panel_id=meta.get("panel_id"),
                original_image_path=str(png_file) if png_file.exists() else None,
            )

            # Build state maps for strict comparison
            gt_map = {
                gt["defect_id"]: str(gt["state"]).lower()
                for gt in ground_truth
            }
            pred_map = {
                comp.defect_id: (
                    comp.state.value if hasattr(comp.state, "value") else str(comp.state)
                ).lower()
                for comp in result.comparisons
            }

            insp_passed = True

            # Case A: Both expected and predicted are empty (e.g. post-repair inspection)
            if not gt_map and not pred_map:
                print(
                    f"  [{insp_id}] No active/resolved defects | "
                    f"State: (none)     (GT: (none)    ) | Match: PASS | Comparisons: 0"
                )
            else:
                # Check predicted defects against ground truth
                for defect_id, pred_state in pred_map.items():
                    comp = next(c for c in result.comparisons if c.defect_id == defect_id)
                    delta_str = f"{comp.measurement_delta}" if comp.measurement_delta is not None else "None"
                    growth_str = f"{comp.growth_rate_pct:+.1f}%"

                    if defect_id not in gt_map:
                        print(
                            f"  [{insp_id}] Defect {defect_id:<6} | "
                            f"State: {pred_state:<11} (GT: UNEXPECTED) | Match: FAIL | "
                            f"Delta: {delta_str:<6} | Growth: {growth_str}"
                        )
                        insp_passed = False
                        all_passed = False
                    else:
                        expected_state = gt_map[defect_id]
                        match_ok = (pred_state == expected_state)
                        if not match_ok:
                            insp_passed = False
                            all_passed = False

                        print(
                            f"  [{insp_id}] Defect {defect_id:<6} | "
                            f"State: {pred_state:<11} (GT: {expected_state:<11}) | "
                            f"Match: {'PASS' if match_ok else 'DIFF'} | "
                            f"Delta: {delta_str:<6} | Growth: {growth_str}"
                        )

                # Check for missed ground-truth defects
                for defect_id, expected_state in gt_map.items():
                    if defect_id not in pred_map:
                        print(
                            f"  [{insp_id}] Defect {defect_id:<6} | "
                            f"State: MISSED      (GT: {expected_state:<11}) | Match: FAIL"
                        )
                        insp_passed = False
                        all_passed = False

            if insp_passed:
                passed_inspections += 1

        # Print SQLite timeline check for primary defect
        primary_defect = defects[0]["defect_id"] if defects else "D01"
        timeline = repo.get_defect_timeline(primary_defect, aircraft_id=acid)
        print(f"  -> SQLite timeline observations logged for {primary_defect}: {len(timeline)}")

    print("\n" + "=" * 78)
    print(f"VERIFICATION SUMMARY: {passed_inspections}/{total_inspections} inspections matched ground truth.")
    if all_passed:
        print("RESULT: ALL AEROMEMORY TRANSITIONS MATCHED GROUND TRUTH (PASS)")
    else:
        print("RESULT: VERIFICATION FAILED -- ONE OR MORE DEFECT STATES MISMATCHED (FAIL)")
    print("=" * 78)

    # Clean up test database
    if db_test_path.exists():
        db_test_path.unlink()

    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify AeroMemory on Dataset E")
    parser.add_argument(
        "--aircraft",
        nargs="+",
        help="List of specific aircraft to test (e.g. --aircraft AI-001 AI-006)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all aircraft available in Dataset E",
    )
    args = parser.parse_args()

    selected = None
    if args.all:
        dataset_e_dir = ROOT / "datasets" / "dataset_E_aeromemory" / "aircraft"
        if dataset_e_dir.exists():
            selected = sorted([d.name for d in dataset_e_dir.iterdir() if d.is_dir()])
    elif args.aircraft:
        selected = args.aircraft

    success = run_dataset_e_verification(selected_aircraft=selected)
    sys.exit(0 if success else 1)
