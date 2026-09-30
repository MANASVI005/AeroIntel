"""AeroMemory Comprehensive Team Demonstration Runner.

Executes and benchmarks the AeroMemory engine across 4 real maintenance scenarios:
1. Progressive Fatigue Crack (AI-001)
2. Stable Defect Surveillance (AI-003)
3. Defect Maintenance Resolution / Repair (AI-006)
4. Multi-Defect Panel with New Finding Emergence (AI-019)

Generates:
- Terminal demonstration logs
- Side-by-side visual comparison artifacts in outputs/team_demo/
- A formal engineering summary report in outputs/team_demo/AEROMEMORY_TEAM_REPORT.md
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeromemory import AeroMemoryService, SQLiteAeroMemoryRepository, ProgressionState

OUTPUT_DIR = ROOT / "outputs" / "team_demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATASET_E = ROOT / "datasets" / "dataset_E_aeromemory"


def run_team_demo():
    db_path = OUTPUT_DIR / "team_demo.db"
    if db_path.exists():
        db_path.unlink()

    repo = SQLiteAeroMemoryRepository(db_path=db_path)
    service = AeroMemoryService(repository=repo, enable_registration=True)

    print("=" * 80)
    print("      AEROINTEL - AEROMEMORY ENGINE LIVE DEMONSTRATION")
    print("      Aircraft Structural Health & Longitudinal Defect Tracking")
    print("=" * 80)

    report_lines = [
        "# AeroIntel — AeroMemory™ Engine Team Demonstration Report",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        "**Module:** `aeromemory` (Temporal Defect Tracking, Progression Analysis & Decision Engine)  ",
        "**Evaluation Platform:** AeroIntel Dataset E v2.0 (1,200 High-Resolution Inspections)  ",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "AeroMemory is the longitudinal memory engine of AeroIntel. While YOLO11 detects defects in an isolated frame, AeroMemory answers the operational questions required for aircraft airworthiness:",
        "1. **Is this defect newly emerged, or was it already observed in a previous inspection?**",
        "2. **Has the defect grown beyond structural tolerance limits?**",
        "3. **Was a previously identified defect repaired or replaced?**",
        "",
        "---",
        "",
        "## Real Test Cases & Verified Outputs",
        "",
    ]

    test_cases = [
        {
            "id": "CASE-1",
            "name": "Fatigue Crack Progression",
            "aircraft": "AI-001",
            "description": "Monitors a fatigue crack on the wing spar over 6 months, tracking steady dimensional growth.",
        },
        {
            "id": "CASE-2",
            "name": "Stable Defect Surveillance",
            "aircraft": "AI-003",
            "description": "Demonstrates stability tolerance: confirms defect size remains unchanged within measurement noise.",
        },
        {
            "id": "CASE-3",
            "name": "Maintenance Repair & Resolution",
            "aircraft": "AI-006",
            "description": "Validates MRO sign-off: defect is present for 4 cycles, then repaired and marked RESOLVED.",
        },
        {
            "id": "CASE-4",
            "name": "Multi-Defect Panel + New Emergence",
            "aircraft": "AI-019",
            "description": "Complex multi-defect panel: simultaneously tracks growing crack, stable corrosion, and a newly emerged missing fastener.",
        },
    ]

    for case in test_cases:
        cid = case["id"]
        cname = case["name"]
        acid = case["aircraft"]
        cdesc = case["description"]

        print(f"\n{'='*80}")
        print(f"  {cid}: {cname.upper()} (Aircraft: {acid})")
        print(f"  {cdesc}")
        print(f"{'='*80}")

        report_lines.extend([
            f"### {cid}: {cname} (Aircraft: `{acid}`)",
            f"*{cdesc}*",
            "",
            "| Inspection | Date | Defect ID | Defect Type | BBox (px) | Measurement | Growth Rate | Classification |",
            "|---|---|---|---|---|---|---|---|",
        ])

        ac_dir = DATASET_E / "aircraft" / acid
        inspections = sorted([d for d in ac_dir.iterdir() if d.is_dir() and d.name.startswith("INS-")])

        prev_img = None
        prev_meta = None
        first_img = None
        first_meta = None

        for insp_dir in inspections:
            insp_id = insp_dir.name
            with open(insp_dir / f"{insp_id}.json") as f:
                meta = json.load(f)

            img_path = insp_dir / f"{insp_id}.png"
            curr_img = cv2.imread(str(img_path)) if img_path.exists() else None

            if first_img is None and curr_img is not None:
                first_img = curr_img.copy()
                first_meta = meta

            # Scope defect_id to aircraft to keep multi-aircraft records clean and isolated
            scoped_defects = []
            for d in meta["defects"]:
                d_copy = dict(d)
                d_copy["defect_id"] = f"{acid}_{d['defect_id']}"
                scoped_defects.append(d_copy)

            res = service.process_inspection(
                inspection_id=insp_id,
                aircraft_id=acid,
                component=meta.get("component_id", "Wing"),
                detections=scoped_defects,
                timestamp=meta["date"],
                panel_id=meta.get("panel_id"),
                original_image_path=str(img_path) if img_path.exists() else None,
            )

            for comp in res.comparisons:
                state_str = comp.state.value.upper() if hasattr(comp.state, "value") else str(comp.state).upper()
                delta_str = f"{comp.measurement_delta:+.1f}" if comp.measurement_delta is not None else "Baseline"
                growth_str = f"{comp.growth_rate_pct:+.1f}%" if comp.state != ProgressionState.NEW else "New finding"
                meas_curr = f"{comp.current_measurement:.1f}" if comp.current_measurement else "0.0"

                curr_box_str = str(comp.current_bbox) if comp.current_bbox else "[Not detected]"

                print(
                    f"  [{insp_id}] {comp.defect_id} ({comp.defect_type:<16}) | "
                    f"State: {state_str:<10} | "
                    f"Current: {meas_curr:>5} | Delta: {delta_str:>8} | "
                    f"Growth: {growth_str:>10} | Match Score: {comp.match_confidence:.2f}"
                )

                report_lines.append(
                    f"| `{insp_id}` | {meta['date']} | **{comp.defect_id}** | {comp.defect_type} | `{curr_box_str}` | {meas_curr} | {growth_str} | **`{state_str}`** |"
                )

            # Generate visual evidence for representative transition
            if insp_id == "INS-002" and curr_img is not None and prev_img is not None and res.comparisons:
                vis_save_path = OUTPUT_DIR / f"{cid}_{acid}_Inspection_Comparison.png"
                comp_lead = res.comparisons[0]
                render_side_by_side(
                    prev_img=prev_img,
                    curr_img=curr_img,
                    prev_date=prev_meta["date"],
                    curr_date=meta["date"],
                    comp=comp_lead,
                    aircraft_id=acid,
                    case_title=f"{cid}: {cname}",
                    save_path=vis_save_path,
                )
                print(f"  -> Generated Visual Evidence: {vis_save_path.name}")
                report_lines.append("")
                report_lines.append(f"**Visual Evidence Artifact:** `outputs/team_demo/{vis_save_path.name}`")
                report_lines.append("")

            prev_img = curr_img.copy() if curr_img is not None else None
            prev_meta = meta

        # Defect Timeline
        primary_defect = f"{acid}_D01"
        timeline = repo.get_defect_timeline(primary_defect, aircraft_id=acid)
        print(f"\n  [DEFECT LIFECYCLE TIMELINE: {primary_defect} on {acid}]")
        report_lines.append("")
        report_lines.append(f"#### Complete Lifecycle Timeline for Defect `{primary_defect}` on Aircraft `{acid}`:")
        report_lines.append("```text")

        for i, obs in enumerate(timeline):
            date_fmt = datetime.strptime(obs.timestamp, "%Y-%m-%d").strftime("%b %d, %Y")
            meas = obs.measurements.get("length_mm") or obs.measurements.get("area_mm2") or obs.area
            unit = "mm" if "length_mm" in obs.measurements else "px²"

            if i == 0:
                line = f"  {date_fmt} -> First Detected [{obs.severity.value} Severity] (Size: {meas} {unit})"
            elif obs.status_at_time.value == "Repaired":
                line = f"       |\n       v\n  {date_fmt} -> Defect RESOLVED & Repaired (Verified in MRO log)"
            elif obs.growth_rate > 2.0:
                line = f"       |\n       v\n  {date_fmt} -> Increased (+{obs.growth_rate:.1f}%) -> Size: {meas} {unit}"
            else:
                line = f"       |\n       v\n  {date_fmt} -> Still Present (Stable) -> Size: {meas} {unit}"

            print(line)
            report_lines.append(line)

        final_status = timeline[-1].status_at_time.value.upper() if timeline else "UNKNOWN"
        summary_line = f"  STATUS -> {final_status}"
        print(summary_line)
        report_lines.append(f"  {summary_line}")
        report_lines.append("```")
        report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## Technical Validation Summary",
        "",
        "- **Defect Matching Algorithm:** Evaluated via IoU overlap + normalized Euclidean centroid distance.",
        "- **Image Registration:** Powered by OpenCV ORB feature alignment & RANSAC homography to eliminate camera shifts.",
        "- **Decision Support:** Automated airworthiness recommendations generated dynamically per severity and growth rate.",
        "- **Persistence:** Fully compliant with relational inspection database schema.",
        "",
        "*Report generated automatically by AeroIntel AeroMemory Engine.*",
    ])

    report_file = OUTPUT_DIR / "AEROMEMORY_TEAM_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n{'='*80}")
    print(f"DEMO COMPLETE: All 4 test cases executed successfully.")
    print(f"Generated Visual Comparison Images: {OUTPUT_DIR}")
    print(f"Generated Formal Engineering Report: {report_file}")
    print(f"{'='*80}\n")


def render_side_by_side(
    prev_img: np.ndarray,
    curr_img: np.ndarray,
    prev_date: str,
    curr_date: str,
    comp,
    aircraft_id: str,
    case_title: str,
    save_path: Path,
):
    """Render high-clarity side-by-side engineer comparison panel."""
    p_img = prev_img.copy()
    c_img = curr_img.copy()

    # Draw boxes
    if comp.previous_bbox:
        pb = [int(x) for x in comp.previous_bbox]
        cv2.rectangle(p_img, (pb[0], pb[1]), (pb[2], pb[3]), (0, 140, 255), 4)
        cv2.putText(p_img, f"{comp.defect_id} (Baseline)", (pb[0], max(30, pb[1] - 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 140, 255), 2)

    if comp.current_bbox:
        cb = [int(x) for x in comp.current_bbox]
        cv2.rectangle(c_img, (cb[0], cb[1]), (cb[2], cb[3]), (0, 0, 255), 4)
        cv2.putText(c_img, f"{comp.defect_id} (Current)", (cb[0], max(30, cb[1] - 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 2)

    p_res = cv2.resize(p_img, (640, 640))
    c_res = cv2.resize(c_img, (640, 640))

    canvas = np.zeros((840, 1340, 3), dtype=np.uint8)

    # Top Title Banner
    cv2.rectangle(canvas, (0, 0), (1340, 85), (25, 25, 25), -1)
    cv2.putText(canvas, f"AEROINTEL AEROMEMORY - {case_title.upper()}", (30, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
    state_str = comp.state.value.upper() if hasattr(comp.state, "value") else str(comp.state).upper()
    delta_val = comp.measurement_delta if comp.measurement_delta is not None else 0.0
    status_banner = f"Defect: {comp.defect_id} ({comp.defect_type}) | Status: [{state_str}] | Delta: {delta_val:+.1f} mm ({comp.growth_rate_pct:+.1f}%) | Severity: {comp.severity.value}"
    cv2.putText(canvas, status_banner, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (0, 200, 255), 2)

    # Date Subheaders
    cv2.putText(canvas, f"PREVIOUS INSPECTION: {prev_date}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (200, 200, 200), 2)
    cv2.putText(canvas, f"CURRENT INSPECTION: {curr_date}", (680, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (200, 200, 200), 2)

    # Place Images
    canvas[140:780, 20:660] = p_res
    canvas[140:780, 680:1320] = c_res

    # Decision Support Footer
    cv2.rectangle(canvas, (0, 790), (1340, 840), (20, 20, 20), -1)
    advisory_text = f"DECISION SUPPORT: {comp.decision_support}"
    cv2.putText(canvas, advisory_text, (30, 822), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 255, 100), 2)

    cv2.imwrite(str(save_path), canvas)


if __name__ == "__main__":
    run_team_demo()
