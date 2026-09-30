import sys
from pathlib import Path

# Add project root and backend to sys.path
sys.path.insert(0, str(Path(".").resolve()))
sys.path.insert(0, str(Path("backend").resolve()))

from datetime import datetime
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
from aeromemory.service import AeroMemoryService

client = TestClient(app)

def setup_test_hierarchy():
    """Set up test aircraft, component, panel, and baseline inspection."""
    db = SessionLocal()
    try:
        ac_code = f"TEST-TX-{int(datetime.now().timestamp())}"
        ac = Aircraft(
            aircraft_code=ac_code,
            aircraft_type="Boeing 737-800",
            registration_number="N-TXTEST",
        )
        db.add(ac)
        db.flush()

        comp = Component(
            aircraft_id=ac.id,
            component_code="WING-RIGHT-TX",
            component_type="Wing",
        )
        db.add(comp)
        db.flush()

        pnl = Panel(
            component_id=comp.id,
            panel_code="PNL-TX-01",
            panel_location="Right Upper Wing",
        )
        db.add(pnl)
        db.flush()

        insp1 = Inspection(
            panel_id=pnl.id,
            inspection_code=f"INSP-TX-001-{int(datetime.now().timestamp())}",
            inspector_name="TxTester",
            notes="Transaction Test Inspection 1",
        )
        db.add(insp1)

        insp2 = Inspection(
            panel_id=pnl.id,
            inspection_code=f"INSP-TX-002-{int(datetime.now().timestamp())}",
            inspector_name="TxTester",
            notes="Transaction Test Inspection 2",
        )
        db.add(insp2)

        db.commit()
        db.refresh(insp1)
        db.refresh(insp2)

        return ac.id, comp.id, pnl.id, insp1.id, insp1.inspection_code, insp2.id, insp2.inspection_code
    finally:
        db.close()

def run_tests():
    print("==================================================")
    print("STARTING PHASE 1 TRANSACTION CONSISTENCY VERIFICATION")
    print("==================================================")

    ac_id, comp_id, pnl_id, insp1_id, insp1_code, insp2_id, insp2_code = setup_test_hierarchy()
    test_img_path = Path("runs/image_test/A_20220424_140515_002_jpg.rf.51421f6112137a618f6bceacfce330ef.jpg")

    assert test_img_path.exists(), f"Test image missing: {test_img_path}"

    print(f"\n--- TEST 1: Normal Success (Inspection {insp1_code}) ---")
    with open(test_img_path, "rb") as f:
        response = client.post(
            f"/api/inspections/{insp1_id}/images",
            files={"file": ("test_img.jpg", f, "image/jpeg")},
        )

    print(f"API Response Status Code: {response.status_code}")
    print(f"API Response Body: {response.json()}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    res_data = response.json()
    insp_img_id = res_data["inspection_image_id"]
    det_ids = [d["id"] for d in res_data["detections"]]

    # Verify DB persistence for Test 1
    db = SessionLocal()
    try:
        insp_img = db.query(InspectionImage).filter_by(id=insp_img_id).first()
        assert insp_img is not None, "InspectionImage not persisted!"

        detections = db.query(Detection).filter_by(inspection_image_id=insp_img_id).all()
        assert len(detections) > 0, "No detections persisted!"

        tracked_defects = db.query(TrackedDefect).filter_by(aircraft_id=ac_id).all()
        assert len(tracked_defects) > 0, "No TrackedDefect created!"

        td = tracked_defects[0]
        observations = db.query(DefectObservation).filter_by(tracked_defect_id=td.id).all()
        obs_count = len(observations)

        print(f"TEST 1 PASSED:")
        print(f"  InspectionImage ID: {insp_img.id}")
        print(f"  Detection IDs: {[d.id for d in detections]}")
        print(f"  TrackedDefect ID: {td.defect_code}")
        print(f"  DefectObservation IDs: {[o.id for o in observations]}")
        print(f"  detection_count field: {td.detection_count}")
        print(f"  observation_count: {obs_count}")

        assert td.detection_count == obs_count, (
            f"Mismatch: detection_count={td.detection_count} != observation_count={obs_count}"
        )
    finally:
        db.close()

    print(f"\n--- TEST 2: Controlled Failure & Rollback (Inspection {insp2_code}) ---")
    # Store DB state before failure test
    db = SessionLocal()
    try:
        count_img_before = db.query(InspectionImage).count()
        count_det_before = db.query(Detection).count()
        count_obs_before = db.query(DefectObservation).count()
        td_before = db.query(TrackedDefect).filter_by(id=td.id).first()
        det_count_before = td_before.detection_count
    finally:
        db.close()

    # Inject temporary failure into AeroMemoryService.process_inspection
    original_process_inspection = AeroMemoryService.process_inspection

    def failing_process_inspection(*args, **kwargs):
        # Run original logic so database operations are flushed to session
        res = original_process_inspection(*args, **kwargs)
        # Injected failure before final db.commit() in endpoint handler
        raise RuntimeError("CONTROLLED_TEST_FAILURE: Injected error before final commit")

    AeroMemoryService.process_inspection = failing_process_inspection

    try:
        with open(test_img_path, "rb") as f:
            fail_response = client.post(
                f"/api/inspections/{insp2_id}/images",
                files={"file": ("test_img_fail.jpg", f, "image/jpeg")},
            )
        print(f"API Failed Response Status Code: {fail_response.status_code}")
        print(f"API Failed Response Detail: {fail_response.json()}")
        assert fail_response.status_code == 500, "Expected 500 status code on controlled failure"
    finally:
        # Restore original process_inspection function immediately
        AeroMemoryService.process_inspection = original_process_inspection

    # Verify atomic rollback in PostgreSQL
    db = SessionLocal()
    try:
        count_img_after = db.query(InspectionImage).count()
        count_det_after = db.query(Detection).count()
        count_obs_after = db.query(DefectObservation).count()
        td_after = db.query(TrackedDefect).filter_by(id=td.id).first()
        det_count_after = td_after.detection_count

        print(f"TEST 2 ROLLBACK VERIFICATION:")
        print(f"  InspectionImage count before: {count_img_before}, after: {count_img_after}")
        print(f"  Detection count before: {count_det_before}, after: {count_det_after}")
        print(f"  DefectObservation count before: {count_obs_before}, after: {count_obs_after}")
        print(f"  TrackedDefect detection_count before: {det_count_before}, after: {det_count_after}")

        assert count_img_before == count_img_after, "Rollback failed: InspectionImage leaked!"
        assert count_det_before == count_det_after, "Rollback failed: Detection leaked!"
        assert count_obs_before == count_obs_after, "Rollback failed: DefectObservation leaked!"
        assert det_count_before == det_count_after, "Rollback failed: detection_count changed!"

        print("\nTEST 2 PASSED: Rollback was 100% atomic with ZERO partial records in PostgreSQL!")
    finally:
        db.close()

    print("\n==================================================")
    print("ALL PHASE 1 TRANSACTION CONSISTENCY TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
