from pathlib import Path
from uuid import uuid4

import cv2
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.database_models import Detection, Inspection, InspectionImage
from app.services.model_service import AeroIntelModel
from app.services.aeromemory_postgres_repository import PostgreSQLAeroMemoryRepository
from aeromemory.service import AeroMemoryService


router = APIRouter(
    prefix="/api/inspections",
    tags=["Inspection Images"],
)

model = AeroIntelModel()
aeromemory_service = AeroMemoryService(enable_registration=True)

BASE_IMAGE_DIR = Path("data/inspections")

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def _to_aeromemory_detection(detection: dict) -> dict:
    bbox = detection["bbox"]

    x1 = float(bbox["x"])
    y1 = float(bbox["y"])
    x2 = x1 + float(bbox["width"])
    y2 = y1 + float(bbox["height"])

    return {
        "defect_type": detection["class_name"],
        "confidence": float(detection["confidence"]),
        "bbox": [x1, y1, x2, y2],
    }

@router.post("/{inspection_id}/images")
async def upload_inspection_image(
    inspection_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Check inspection exists
    inspection = (
        db.query(Inspection)
        .filter(Inspection.id == inspection_id)
        .first()
    )

    if not inspection:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    # 2. Validate file
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format.",
        )

    # 3. Create inspection directory
    inspection_dir = BASE_IMAGE_DIR / inspection.inspection_code
    inspection_dir.mkdir(parents=True, exist_ok=True)

    # 4. Generate unique filename
    original_filename = file.filename or "image"
    stored_filename = f"{uuid4().hex}{suffix}"

    image_path = inspection_dir / stored_filename

    try:
        # 5. Save uploaded image
        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty.",
            )

        image_path.write_bytes(image_bytes)

        # 6. Validate image using OpenCV
        image = cv2.imread(str(image_path))

        if image is None:
            image_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a readable image.",
            )

        image_height, image_width = image.shape[:2]

        # 7. Run AeroIntel YOLO model
        detections = model.detect(image_path)

        # 8. Store inspection image
        inspection_image = InspectionImage(
            inspection_id=inspection.id,
            image_path=str(image_path),
            original_filename=original_filename,
            image_width=image_width,
            image_height=image_height,
        )

        db.add(inspection_image)
        db.flush()

        # 9. Store detections
        detection_records = []

        for detection in detections:
            bbox = detection["bbox"]

            detection_record = Detection(
                inspection_image_id=inspection_image.id,
                class_id=detection["class_id"],
                class_name=detection["class_name"],
                confidence=detection["confidence"],
                bbox_x=bbox["x"],
                bbox_y=bbox["y"],
                bbox_width=bbox["width"],
                bbox_height=bbox["height"],
            )

            db.add(detection_record)
            detection_records.append(detection_record)

        # 10. Flush everything so generated IDs are available
        db.flush()

        # Refresh records so generated IDs are available
        db.refresh(inspection_image)

        for record in detection_records:
            db.refresh(record)

        # Process this inspection through AeroMemory using PostgreSQL.
        repository = PostgreSQLAeroMemoryRepository(db)

        aeromemory_detections = [
            _to_aeromemory_detection(detection)
            for detection in detections
        ]

        aeromemory_service = AeroMemoryService(
            repository=repository,
            enable_registration=True,
        )

        aeromemory_result = aeromemory_service.process_inspection(
            inspection_id=inspection.inspection_code,
            aircraft_id=str(inspection.panel.component.aircraft.id),
            component=inspection.panel.component.component_code,
            detections=aeromemory_detections,
            timestamp=inspection.inspection_date.isoformat(),
            panel_id=str(inspection.panel.id),
            original_image_path=str(image_path),
            aircraft_model=(
                inspection.panel.component.aircraft.aircraft_type
                or "Boeing 737-800"
            ),
        )
        # Single atomic commit for entire inspection image upload & AeroMemory processing
        db.commit()

        return {
            "inspection_id": inspection.id,
            "inspection_code": inspection.inspection_code,
            "inspection_image_id": inspection_image.id,
            "original_filename": original_filename,
            "stored_path": str(image_path),
            "image_width": image_width,
            "image_height": image_height,
            "detections": [
                {
                    "id": record.id,
                    "class_id": record.class_id,
                    "class_name": record.class_name,
                    "confidence": record.confidence,
                    "bbox": {
                        "x": record.bbox_x,
                        "y": record.bbox_y,
                        "width": record.bbox_width,
                        "height": record.bbox_height,
                    },
                }
                for record in detection_records
            ],
            "count": len(detection_records),
            "aeromemory": {
                "matched_count": aeromemory_result.matched_count,
                "new_count": aeromemory_result.new_count,
                "comparisons": [
                    {
                        "defect_id": comp.defect_id,
                        "defect_type": comp.defect_type,
                        "state": comp.state.value if hasattr(comp.state, "value") else str(comp.state),
                        "severity": comp.severity.value if hasattr(comp.severity, "value") else str(comp.severity),
                        "match_confidence": comp.match_confidence,
                    }
                    for comp in aeromemory_result.comparisons
                ],
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        # Do not leave an orphaned image if database insertion fails
        image_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Inspection image processing failed: {exc}",
        ) from exc


@router.get("/{inspection_id}/latest-result")
def get_latest_inspection_result(
    inspection_id: int,
    db: Session = Depends(get_db),
):
    latest_img = (
        db.query(InspectionImage)
        .filter(InspectionImage.inspection_id == inspection_id)
        .order_by(InspectionImage.id.desc())
        .first()
    )

    if not latest_img:
        return {"has_result": False, "message": "No inspection image uploaded yet for this inspection."}

    detections = (
        db.query(Detection)
        .filter(Detection.inspection_image_id == latest_img.id)
        .all()
    )

    # Fetch latest AeroMemory records if present
    repository = PostgreSQLAeroMemoryRepository(db)
    tds = repository.get_active_defects(
        aircraft_id=str(latest_img.inspection.panel.component.aircraft.id),
        component=latest_img.inspection.panel.component.component_code,
    )

    comparisons = []
    for td in tds:
        comparisons.append({
            "defect_id": td.defect_id,
            "defect_type": td.defect_type,
            "state": td.status.value if hasattr(td.status, "value") else str(td.status),
            "severity": td.current_severity.value if hasattr(td.current_severity, "value") else str(td.current_severity),
            "match_confidence": float(td.current_confidence),
        })

    return {
        "has_result": True,
        "inspection_id": latest_img.inspection_id,
        "inspection_code": latest_img.inspection.inspection_code,
        "inspection_image_id": latest_img.id,
        "original_filename": latest_img.original_filename,
        "stored_path": latest_img.image_path,
        "image_width": latest_img.image_width,
        "image_height": latest_img.image_height,
        "detections": [
            {
                "id": record.id,
                "class_id": record.class_id,
                "class_name": record.class_name,
                "confidence": record.confidence,
                "bbox": {
                    "x": record.bbox_x,
                    "y": record.bbox_y,
                    "width": record.bbox_width,
                    "height": record.bbox_height,
                },
            }
            for record in detections
        ],
        "count": len(detections),
        "aeromemory": {
            "matched_count": len([c for c in comparisons if c["state"] != "new"]),
            "new_count": len([c for c in comparisons if c["state"] == "new"]),
            "comparisons": comparisons,
        },
    }

    




