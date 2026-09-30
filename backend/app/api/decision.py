from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.database_models import DecisionSupport, Detection
from app.services.decision_engine import generate_decision_support


router = APIRouter(
    prefix="/api/decisions",
    tags=["Decision Support"],
)


@router.post("/{detection_id}")
def create_decision_support(
    detection_id: int,
    db: Session = Depends(get_db),
):
    # Find the detection
    detection = (
        db.query(Detection)
        .filter(Detection.id == detection_id)
        .first()
    )

    if not detection:
        raise HTTPException(
            status_code=404,
            detail="Detection not found.",
        )

    # Prevent duplicate decision-support records
    existing = (
        db.query(DecisionSupport)
        .filter(
            DecisionSupport.detection_id == detection_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Decision support already exists for this detection.",
        )

    # Run Decision Engine
    result = generate_decision_support(
        class_id=detection.class_id,
        confidence=detection.confidence,
        bbox_width=detection.bbox_width,
        bbox_height=detection.bbox_height,
    )

    # Save result
    decision = DecisionSupport(
        detection_id=detection.id,
        severity=result["severity"],
        progression_status=result["progression_status"],
        recommended_action=result["recommended_action"],
        reasoning=result["reasoning"],
    )

    db.add(decision)
    db.commit()
    db.refresh(decision)

    return {
        "id": decision.id,
        "detection_id": decision.detection_id,
        "severity": decision.severity,
        "progression_status": decision.progression_status,
        "recommended_action": decision.recommended_action,
        "reasoning": decision.reasoning,
    }