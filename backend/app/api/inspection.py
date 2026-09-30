from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.database_models import Inspection


router = APIRouter(
    prefix="/api/inspections",
    tags=["Inspections"],
)


class InspectionCreate(BaseModel):
    panel_id: int
    inspection_code: str
    inspector_name: str | None = None
    notes: str | None = None


@router.post("")
def create_inspection(
    inspection_data: InspectionCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Inspection)
        .filter(
            Inspection.inspection_code
            == inspection_data.inspection_code
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Inspection code already exists.",
        )

    inspection = Inspection(
        panel_id=inspection_data.panel_id,
        inspection_code=inspection_data.inspection_code,
        inspection_date=datetime.now(),
        inspector_name=inspection_data.inspector_name,
        status="completed",
        notes=inspection_data.notes,
    )

    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    return {
        "id": inspection.id,
        "panel_id": inspection.panel_id,
        "inspection_code": inspection.inspection_code,
        "inspection_date": inspection.inspection_date,
        "inspector_name": inspection.inspector_name,
        "status": inspection.status,
        "notes": inspection.notes,
    }


@router.get("")
def list_inspections(db: Session = Depends(get_db)):
    inspections = db.query(Inspection).order_by(Inspection.id.desc()).all()
    return [
        {
            "id": item.id,
            "panel_id": item.panel_id,
            "inspection_code": item.inspection_code,
            "inspection_date": item.inspection_date.isoformat() if item.inspection_date else None,
            "inspector_name": item.inspector_name,
            "status": item.status,
            "panel_code": item.panel.panel_code if item.panel else None,
            "aircraft_code": item.panel.component.aircraft.aircraft_code if item.panel and item.panel.component and item.panel.component.aircraft else None,
        }
        for item in inspections
    ]