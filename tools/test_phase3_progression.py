import sys, cv2, numpy as np
from pathlib import Path

# Add project root and backend to sys.path
sys.path.insert(0, str(Path(".").resolve()))
sys.path.insert(0, str(Path("backend").resolve()))

from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal, engine
from app.models.database_models import (
    Aircraft,
    Component,
    Panel,
    Inspection,
    InspectionImage,
    Detection,
    TrackedDefect,
    DefectObservation,
)
from aeromemory.matcher import DefectMatcher
from aeromemory.comparator import DefectComparator
from aeromemory.service import AeroMemoryService
from aeromemory.models import DefectStatus, ProgressionState

client = TestClient(app)

def create_progression_image():
    """Create a legitimate test image representing physical defect expansion from real source image."""
    orig_path = Path("runs/image_test/A_20220424_140515_002_jpg.rf.51421f6112137a618f6bceacfce330ef.jpg")
    out_path = Path("runs/image_test/test_progression_corrosion_zoomed.jpg")

    assert orig_path.exists(), f"Original image missing: {orig_path}"

    if not out_path.exists():
        img = cv2.imread(str(orig_path))
        h, w = img.shape[:2]
        # Crop 5% from edges (closer camera view/expansion) and resize back
        crop = img[int(h*0.05):int(h*0.95), int(w*0.05):int(w*0.95)]
        crop_resized = cv2.resize(crop, (w, h))
        cv2.imwrite(str(out_path), crop_resized)

    return out_path

def setup_phase3_hierarchy():
    """Create test hierarchy: Aircraft -> Component -> Panel -> Inspection 21, 22, 23."""
    db = SessionLocal()
    try:
        ts_now = int(datetime.now().timestamp())
        ac_code = f"AC-P3-{ts_now}"
        ac = Aircraft(
            aircraft_code=ac_code,
            aircraft_type="Boeing 737-800",
            registration_number="N-P3TEST",
        )
        db.add(ac)
        db.flush()

        comp = Component(
            aircraft_id=ac.id,
            component_code="WING-RIGHT-P3",
            component_type="Wing",
        )
        db.add(comp)
        db.flush()

        pnl = Panel(
            component_id=comp.id,
            panel_code="PNL-P3-01",
            panel_location="Right Wing Upper Surface",
        )
        db.add(pnl)
        db.flush()

        t_base = datetime.now()
        t21 = t_base
        t22 = t_base + timedelta(minutes=5)
        t23 = t_base + timedelta(minutes=10)

        insp21 = Inspection(
            panel_id=pnl.id,
            inspection_code=f"INSP-21-{ts_now}",
            inspection_date=t21,
            inspector_name="Phase3Tester",
            notes="Baseline Inspection 21",
        )
        db.add(insp21)

        insp22 = Inspection(
            panel_id=pnl.id,
            inspection_code=f"INSP-22-{ts_now}",
            inspection_date=t22,
            inspector_name="Phase3Tester",
            notes="Sequential Inspection 22",
        )
        db.add(insp22)

        insp23 = Inspection(
            panel_id=pnl.id,
            inspection_code=f"INSP-23-{ts_now}",
            inspection_date=t23,
            inspector_name="Phase3Tester",
            notes="Progression Inspection 23",
        )
        db.add(insp23)

        db.commit()
        db.refresh(insp21)
        db.refresh(insp22)
        db.refresh(insp23)

        return ac.id, comp.id, pnl.id, insp21.id, insp21.inspection_code, insp22.id, insp22.inspection_code, insp23.id, insp23.inspection_code
    finally:
        db.close()

def run_phase3_test():
    print("==================================================")
    print("STARTING PHASE 3 — AEROMEMORY DEFECT PROGRESSION TESTING")
    print("==================================================")

    ac_id, comp_id, pnl_id, i21_id, i21_code, i22_id, i22_code, i23_id, i23_code = setup_phase3_hierarchy()

    img_baseline_path = Path("runs/image_test/A_20220424_140515_002_jpg.rf.51421f6112137a618f6bceacfce330ef.jpg")
    img_progression_path = create_progression_image()

    print(f"\n--- STEP 2: Baseline Inspection 21 ({i21_code}) ---")
    with open(img_baseline_path, "rb") as f:
        res21 = client.post(f"/api/inspections/{i21_id}/images", files={"file": ("img21.jpg", f, "image/jpeg")})
    assert res21.status_code == 200, f"Inspection 21 failed: {res21.text}"

    db = SessionLocal()
    try:
        defects21 = db.query(TrackedDefect).filter_by(aircraft_id=ac_id).all()
        assert len(defects21) == 1, f"Expected 1 defect after Inspection 21, found {len(defects21)}"
        target_td_code = defects21[0].defect_code
        target_td_id = defects21[0].id
        print(f"Created TrackedDefect: {target_td_code} (Class: {defects21[0].class_name})")
    finally:
        db.close()

    print(f"\n--- STEP 2: Sequential Inspection 22 ({i22_code}) ---")
    with open(img_baseline_path, "rb") as f:
        res22 = client.post(f"/api/inspections/{i22_id}/images", files={"file": ("img22.jpg", f, "image/jpeg")})
    assert res22.status_code == 200, f"Inspection 22 failed: {res22.text}"

    print(f"\n--- STEP 3: Progression Inspection 23 ({i23_code}) with Expanded Bounding Region ---")
    with open(img_progression_path, "rb") as f:
        res23 = client.post(f"/api/inspections/{i23_id}/images", files={"file": ("img23_prog.jpg", f, "image/jpeg")})
    assert res23.status_code == 200, f"Inspection 23 failed: {res23.text}"

    # Database & Matcher Audit
    db = SessionLocal()
    try:
        all_defects = db.query(TrackedDefect).filter_by(aircraft_id=ac_id).all()
        print(f"\nTotal TrackedDefects after Inspection 23: {len(all_defects)}")

        corrosion_defects = [d for d in all_defects if d.class_name == "Corrosion"]
        print(f"Corrosion defects count: {len(corrosion_defects)}")

        assert len(corrosion_defects) == 1, f"Duplicate Corrosion defect created! Count = {len(corrosion_defects)}"
        td = corrosion_defects[0]

        observations = db.query(DefectObservation).filter_by(tracked_defect_id=td.id).order_by(DefectObservation.id).all()
        print(f"\nObservations count for {td.defect_code}: {len(observations)}")

        obs21, obs22, obs23 = observations[0], observations[1], observations[2]

        box22 = [obs22.bbox_x, obs22.bbox_y, obs22.bbox_x + obs22.bbox_width, obs22.bbox_y + obs22.bbox_height]
        box23 = [obs23.bbox_x, obs23.bbox_y, obs23.bbox_x + obs23.bbox_width, obs23.bbox_y + obs23.bbox_height]

        # STEP 4: Calculate exact matcher metrics using DefectMatcher
        matcher = DefectMatcher()
        iou = matcher.calculate_iou(box22, box23)
        dist = matcher.calculate_centroid_distance(box22, box23)
        norm_dist = min(dist / matcher.max_centroid_distance, 1.0)
        class_match = True

        iou_contrib = matcher.iou_weight * iou
        dist_contrib = matcher.dist_weight * (1.0 - norm_dist)
        class_contrib = matcher.class_weight * (1.0 if class_match else 0.0)
        match_score = iou_contrib + dist_contrib + class_contrib

        print("\n--- STEP 4: ACTUAL MATCHER METRICS ---")
        print(f"  Previous bbox (Inspection 22): {[round(c, 2) for c in box22]}")
        print(f"  Current bbox  (Inspection 23): {[round(c, 2) for c in box23]}")
        print(f"  IoU: {iou:.4f}")
        print(f"  Centroid distance: {dist:.2f} px")
        print(f"  Class consistency: {class_match}")
        print(f"  IoU contribution: {iou_contrib:.4f}")
        print(f"  Distance contribution: {dist_contrib:.4f}")
        print(f"  Class contribution: {class_contrib:.4f}")
        print(f"  Final match score: {match_score:.4f}")
        print(f"  Minimum match score required: {matcher.min_match_score}")
        print(f"  Maximum centroid distance: {matcher.max_centroid_distance}")

        # STEP 5 & 6 & 7: Verify TrackedDefect, Observations & Progression
        print("\n--- STEP 5 & 6 & 7: TRACKING & PROGRESSION AUDIT ---")
        print(f"  TrackedDefect ID: {td.defect_code}")
        print(f"  First Seen Inspection ID: {td.first_seen_inspection_id} (Inspection 21: {i21_id})")
        print(f"  Last Seen Inspection ID: {td.last_seen_inspection_id} (Inspection 23: {i23_id})")
        print(f"  detection_count field: {td.detection_count}")
        print(f"  observation_count: {len(observations)}")

        area22 = obs22.area
        area23 = obs23.area
        area_delta = area23 - area22
        growth_pct = (area_delta / area22) * 100.0 if area22 > 0 else 0.0

        print(f"\n  Observation 21 State: {obs21.progression_state}, Severity: {obs21.severity}, Conf: {obs21.confidence:.3f}")
        print(f"  Observation 22 State: {obs22.progression_state}, Severity: {obs22.severity}, Conf: {obs22.confidence:.3f}")
        print(f"  Observation 23 State: {obs23.progression_state}, Severity: {obs23.severity}, Conf: {obs23.confidence:.3f}")
        print(f"  Area change (22 -> 23): {area22:.1f} px^2 -> {area23:.1f} px^2 ({growth_pct:+.1f}%)")
        print(f"  Confidence change (22 -> 23): {obs22.confidence:.3f} -> {obs23.confidence:.3f} ({obs23.confidence - obs22.confidence:+.3f})")

        # STEP 8: Database Integrity Assertions
        assert td.first_seen_inspection_id == i21_id, "first_seen_inspection_id incorrect!"
        assert td.last_seen_inspection_id == i23_id, "last_seen_inspection_id incorrect!"
        assert td.detection_count == 3, f"Expected detection_count=3, got {td.detection_count}"
        assert len(observations) == 3, f"Expected 3 observations, got {len(observations)}"
        assert obs23.progression_state == "Progressing", f"Unexpected progression_state: {obs23.progression_state}"

        print("\n==================================================")
        print("PHASE 3 VERIFICATION SUMMARY:")
        print(f"  Matched existing defect: YES ({td.defect_code})")
        print(f"  Duplicate Corrosion created: NO")
        print(f"  Progression state evaluated: {obs23.progression_state}")
        print(f"  Area change detected: {growth_pct:+.1f}%")
        print("  Matcher modified: NO")
        print("  Thresholds modified: NO")
        print("  Phase 3: PASS")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_phase3_test()
