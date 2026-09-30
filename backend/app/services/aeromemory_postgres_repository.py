from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from aeromemory.models import (
    DefectMeasurement,
    DefectRecord,
    DefectStatus,
    InspectionRecord,
    ObservationRecord,
    SeverityLevel,
)
from aeromemory.repository import AeroMemoryRepository
from app.models.database_models import (
    Aircraft,
    Detection,
    Component,
    Panel,
    Inspection,
    InspectionImage,
    TrackedDefect,
    DefectObservation,
)


class PostgreSQLAeroMemoryRepository(AeroMemoryRepository):
    """PostgreSQL persistence adapter for AeroMemory."""

    CLASS_IDS = {
        "Crack": 0,
        "Corrosion": 1,
        "Dent": 2,
        "Missing Fastener": 3,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def save_inspection(self, inspection: InspectionRecord) -> None:
        aircraft = self._resolve_aircraft(inspection.aircraft_id)

        component = self._resolve_component(
            aircraft.id,
            inspection.component,
        )

        panel = self._resolve_panel(
            component.id,
            inspection.panel_id,
        )

        if panel is None:
            raise ValueError(
                f"Panel is required for AeroMemory inspection: "
                f"{inspection.inspection_id}"
            )

        existing = (
            self.db.query(Inspection)
            .filter(
                Inspection.inspection_code == inspection.inspection_id
            )
            .first()
        )

        timestamp = self._parse_datetime(inspection.timestamp)

        if existing:
            existing.panel_id = panel.id
            existing.inspection_date = timestamp
            existing.status = (
                inspection.inspection_status or "completed"
            )
            self.db.flush()
            return

        record = Inspection(
            panel_id=panel.id,
            inspection_code=inspection.inspection_id,
            inspection_date=timestamp,
            status=inspection.inspection_status or "completed",
        )

        self.db.add(record)
        self.db.flush()

    def get_inspection(
        self,
        inspection_id: str,
    ) -> Optional[InspectionRecord]:

        record = (
            self.db.query(Inspection)
            .filter(
                Inspection.inspection_code == inspection_id
            )
            .first()
        )

        if not record:
            return None

        return self._inspection_to_domain(record)

    def get_previous_inspection(
        self,
        aircraft_id: str,
        component: Optional[str] = None,
        before_timestamp: Optional[str] = None,
        exclude_id: Optional[str] = None,
    ) -> Optional[InspectionRecord]:

        aircraft = self._resolve_aircraft(aircraft_id)

        query = (
            self.db.query(Inspection)
            .join(
                Panel,
                Inspection.panel_id == Panel.id,
            )
            .join(
                Component,
                Panel.component_id == Component.id,
            )
            .filter(
                Component.aircraft_id == aircraft.id
            )
        )

        if component:
            query = query.filter(
                Component.component_code == component
            )

        if before_timestamp:
            query = query.filter(
                Inspection.inspection_date
                < self._parse_datetime(before_timestamp)
            )

        if exclude_id:
            query = query.filter(
                Inspection.inspection_code != exclude_id
            )

        record = (
            query
            .order_by(
                Inspection.inspection_date.desc()
            )
            .first()
        )

        if not record:
            return None

        return self._inspection_to_domain(record)

    # ------------------------------------------------------------------
    # Defects
    # ------------------------------------------------------------------

    def save_defect(
        self,
        defect: DefectRecord,
    ) -> None:

        aircraft = self._resolve_aircraft(
            defect.aircraft_id
        )

        component = self._resolve_component(
            aircraft.id,
            defect.component,
        )

        panel = self._resolve_panel(
            component.id,
            defect.panel_id,
        )

        class_id = self._class_id(
            defect.defect_type
        )

        first_inspection = (
            self._resolve_inspection_for_timestamp(
                aircraft_id=aircraft.id,
                component_id=component.id,
                timestamp=defect.first_seen,
            )
        )

        last_inspection = (
            self._resolve_inspection_for_timestamp(
                aircraft_id=aircraft.id,
                component_id=component.id,
                timestamp=defect.last_seen,
            )
        )

        existing = (
            self.db.query(TrackedDefect)
            .filter(
                TrackedDefect.defect_code
                == defect.defect_id
            )
            .first()
        )

        values = {
            "aircraft_id": aircraft.id,
            "component_id": component.id,
            "panel_id": (
                panel.id
                if panel is not None
                else None
            ),
            "class_id": class_id,
            "class_name": defect.defect_type,
            "location_x": float(defect.location_x),
            "location_y": float(defect.location_y),
            "bbox_x": float(defect.bbox[0]),
            "bbox_y": float(defect.bbox[1]),
            "bbox_width": float(defect.bbox_width),
            "bbox_height": float(defect.bbox_height),
            "bbox_area": float(defect.bbox_area),
            "first_seen_inspection_id": (
                first_inspection.id
                if first_inspection
                else None
            ),
            "last_seen_inspection_id": (
                last_inspection.id
                if last_inspection
                else None
            ),
            "first_seen_at": self._parse_datetime(
                defect.first_seen
            ),
            "last_seen_at": self._parse_datetime(
                defect.last_seen
            ),
            "status": self._enum_value(
                defect.status
            ),
            "current_severity": self._enum_value(
                defect.current_severity
            ),
            "current_confidence": float(
                defect.current_confidence
            ),
            "detection_count": int(
                defect.detection_count
            ),
            "notes": defect.notes,
        }

        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            record = TrackedDefect(
                defect_code=defect.defect_id,
                **values,
            )
            self.db.add(record)

        self.db.flush()

    def update_defect(
        self,
        defect: DefectRecord,
    ) -> None:
        self.save_defect(defect)

    def get_defect(
        self,
        defect_id: str,
    ) -> Optional[DefectRecord]:

        record = (
            self.db.query(TrackedDefect)
            .filter(
                TrackedDefect.defect_code
                == defect_id
            )
            .first()
        )

        if not record:
            return None

        return self._defect_to_domain(record)

    def get_active_defects(
        self,
        aircraft_id: str,
        component: Optional[str] = None,
    ) -> list[DefectRecord]:

        aircraft = self._resolve_aircraft(
            aircraft_id
        )

        query = (
            self.db.query(TrackedDefect)
            .filter(
                TrackedDefect.aircraft_id
                == aircraft.id
            )
            .filter(
                ~TrackedDefect.status.in_(
                    [
                        DefectStatus.CLOSED.value,
                        DefectStatus.REPAIRED.value,
                    ]
                )
            )
        )

        if component:
            component_record = (
                self._resolve_component(
                    aircraft.id,
                    component,
                )
            )

            query = query.filter(
                TrackedDefect.component_id
                == component_record.id
            )

        records = (
            query
            .order_by(
                TrackedDefect.first_seen_at.asc()
            )
            .all()
        )

        return [
            self._defect_to_domain(record)
            for record in records
        ]

    # ------------------------------------------------------------------
    # Observations
    # ------------------------------------------------------------------

    def save_observation(
        self,
        observation: ObservationRecord,
    ) -> None:

        defect = (
            self.db.query(TrackedDefect)
            .filter(
                TrackedDefect.defect_code
                == observation.defect_id
            )
            .first()
        )

        if not defect:
            raise ValueError(
                f"Tracked defect not found: "
                f"{observation.defect_id}"
            )

        inspection = self._resolve_inspection(
            observation.inspection_id
        )

        if not inspection:
            raise ValueError(
                f"Inspection not found: "
                f"{observation.inspection_id}"
            )

        inspection_image = (
            self.db.query(InspectionImage)
            .filter(
                InspectionImage.inspection_id == inspection.id
            )
            .order_by(InspectionImage.id.desc())
            .first()
        )

        detection_id = None

        if inspection_image:
            candidate_detections = (
                self.db.query(Detection)
                .filter(
                    Detection.inspection_image_id
                    == inspection_image.id
                )
                .filter(
                    Detection.class_id == defect.class_id
                )
                .all()
            )

            if candidate_detections:
                detection = min(
                    candidate_detections,
                    key=lambda item: (
                        abs(
                            float(item.bbox_x)
                            - float(observation.bbox[0])
                        )
                        + abs(
                            float(item.bbox_y)
                            - float(observation.bbox[1])
                        )
                        + abs(
                            float(item.bbox_width)
                            - (
                                float(observation.bbox[2])
                                - float(observation.bbox[0])
                            )
                        )
                        + abs(
                            float(item.bbox_height)
                            - (
                                float(observation.bbox[3])
                                - float(observation.bbox[1])
                            )
                        )
                    ),
                )
                detection_id = detection.id

        record = DefectObservation(
            tracked_defect_id=defect.id,
            inspection_id=inspection.id,
            inspection_image_id=(
                inspection_image.id
                if inspection_image
                else None
            ),
            detection_id=detection_id,
            observed_at=self._parse_datetime(
                observation.timestamp
            ),
            confidence=float(
                observation.confidence
            ),
            bbox_x=float(
                observation.bbox[0]
            ),
            bbox_y=float(
                observation.bbox[1]
            ),
            bbox_width=float(
                observation.bbox[2]
                - observation.bbox[0]
            ),
            bbox_height=float(
                observation.bbox[3]
                - observation.bbox[1]
            ),
            area=float(observation.area),
            severity=self._enum_value(
                observation.severity
            ),
            progression_state=self._enum_value(
                observation.status_at_time
            ),
            growth_rate_pct=float(
                observation.growth_rate
            ),
            measurement_delta=None,
            dimension_unit=None,
            measurements=(
                observation.measurements
                or {}
            ),
        )

        self.db.add(record)
        self.db.flush()

    def get_defect_timeline(
        self,
        defect_id: str,
    ) -> list[ObservationRecord]:

        defect = (
            self.db.query(TrackedDefect)
            .filter(
                TrackedDefect.defect_code
                == defect_id
            )
            .first()
        )

        if not defect:
            return []

        records = (
            self.db.query(DefectObservation)
            .filter(
                DefectObservation.tracked_defect_id
                == defect.id
            )
            .order_by(
                DefectObservation.observed_at.asc()
            )
            .all()
        )

        result = []

        for record in records:
            result.append(
                ObservationRecord(
                    observation_id=str(
                        record.id
                    ),
                    defect_id=defect.defect_code,
                    inspection_id=self._inspection_code(
                        record.inspection_id
                    ),
                    timestamp=record.observed_at.isoformat(),
                    confidence=record.confidence,
                    bbox=[
                        record.bbox_x,
                        record.bbox_y,
                        record.bbox_x
                        + record.bbox_width,
                        record.bbox_y
                        + record.bbox_height,
                    ],
                    area=record.area,
                    severity=SeverityLevel(
                        record.severity
                    ),
                    growth_rate=record.growth_rate_pct,
                    status_at_time=DefectStatus(
                        record.progression_state
                    ),
                    measurements=(
                        record.measurements
                        or {}
                    ),
                )
            )

        return result

    # ------------------------------------------------------------------
    # IDs
    # ------------------------------------------------------------------

    def next_defect_id(
        self,
        prefix: str = "DEF",
    ) -> str:

        existing_codes = (
            self.db.query(
                TrackedDefect.defect_code
            )
            .filter(
                TrackedDefect.defect_code.like(
                    f"{prefix}-%"
                )
            )
            .all()
        )

        max_number = 0

        for (code,) in existing_codes:
            try:
                number = int(
                    str(code).split("-")[-1]
                )
                max_number = max(
                    max_number,
                    number,
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        return (
            f"{prefix}-{max_number + 1:03d}"
        )

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    def _resolve_aircraft(
        self,
        aircraft_id: str,
    ) -> Aircraft:

        try:
            numeric_id = int(
                aircraft_id
            )
        except (
            TypeError,
            ValueError,
        ):
            numeric_id = None

        if numeric_id is not None:
            record = (
                self.db.query(Aircraft)
                .filter(
                    Aircraft.id
                    == numeric_id
                )
                .first()
            )

            if record:
                return record

        record = (
            self.db.query(Aircraft)
            .filter(
                Aircraft.aircraft_code
                == str(aircraft_id)
            )
            .first()
        )

        if not record:
            raise ValueError(
                f"Aircraft not found: "
                f"{aircraft_id}"
            )

        return record

    def _resolve_component(
        self,
        aircraft_id: int,
        component_code: str,
    ) -> Component:

        try:
            numeric_id = int(
                component_code
            )
        except (
            TypeError,
            ValueError,
        ):
            numeric_id = None

        if numeric_id is not None:
            record = (
                self.db.query(Component)
                .filter(
                    Component.id
                    == numeric_id,
                    Component.aircraft_id
                    == aircraft_id,
                )
                .first()
            )

            if record:
                return record

        record = (
            self.db.query(Component)
            .filter(
                Component.aircraft_id
                == aircraft_id,
                Component.component_code
                == str(component_code),
            )
            .first()
        )

        if not record:
            raise ValueError(
                f"Component not found: "
                f"{component_code}"
            )

        return record

    def _resolve_panel(
        self,
        component_id: int,
        panel_id: Optional[str],
    ) -> Optional[Panel]:

        if panel_id is None:
            return None

        try:
            numeric_id = int(
                panel_id
            )
        except (
            TypeError,
            ValueError,
        ):
            numeric_id = None

        if numeric_id is not None:
            record = (
                self.db.query(Panel)
                .filter(
                    Panel.id
                    == numeric_id,
                    Panel.component_id
                    == component_id,
                )
                .first()
            )

            if record:
                return record

        record = (
            self.db.query(Panel)
            .filter(
                Panel.component_id
                == component_id,
                Panel.panel_code
                == str(panel_id),
            )
            .first()
        )

        if not record:
            raise ValueError(
                f"Panel not found: "
                f"{panel_id}"
            )

        return record

    def _resolve_inspection(
        self,
        inspection_id: str,
    ) -> Optional[Inspection]:

        if inspection_id is None:
            return None

        try:
            numeric_id = int(
                inspection_id
            )
        except (
            TypeError,
            ValueError,
        ):
            numeric_id = None

        if numeric_id is not None:
            record = (
                self.db.query(Inspection)
                .filter(
                    Inspection.id
                    == numeric_id
                )
                .first()
            )

            if record:
                return record

        return (
            self.db.query(Inspection)
            .filter(
                Inspection.inspection_code
                == str(inspection_id)
            )
            .first()
        )

    def _resolve_inspection_for_timestamp(
        self,
        aircraft_id: int,
        component_id: int,
        timestamp: str,
    ) -> Optional[Inspection]:

        parsed = self._parse_datetime(
            timestamp
        )

        exact = (
            self.db.query(Inspection)
            .join(
                Panel,
                Inspection.panel_id
                == Panel.id,
            )
            .filter(
                Panel.component_id
                == component_id
            )
            .filter(
                Inspection.inspection_date
                == parsed
            )
            .order_by(
                Inspection.id.desc()
            )
            .first()
        )

        if exact:
            return exact

        return (
            self.db.query(Inspection)
            .join(
                Panel,
                Inspection.panel_id
                == Panel.id,
            )
            .filter(
                Panel.component_id
                == component_id
            )
            .filter(
                Inspection.inspection_date
                <= parsed
            )
            .order_by(
                Inspection.inspection_date.desc(),
                Inspection.id.desc(),
            )
            .first()
        )

    # ------------------------------------------------------------------
    # Domain conversion
    # ------------------------------------------------------------------

    def _inspection_to_domain(
        self,
        record: Inspection,
    ) -> InspectionRecord:

        panel = record.panel
        component = panel.component
        aircraft = component.aircraft

        image = (
            self.db.query(InspectionImage)
            .filter(
                InspectionImage.inspection_id
                == record.id
            )
            .order_by(
                InspectionImage.id.asc()
            )
            .first()
        )

        return InspectionRecord(
            inspection_id=record.inspection_code,
            aircraft_id=str(aircraft.id),
            aircraft_model=(
                aircraft.aircraft_type
                or ""
            ),
            component=component.component_code,
            timestamp=record.inspection_date.isoformat(),
            original_image_path=(
                str(image.image_path)
                if image
                else None
            ),
            annotated_image_path=None,
            panel_id=str(panel.id),
            defect_count=self._inspection_defect_count(
                record.id
            ),
            inspection_status=record.status,
        )

    def _defect_to_domain(
        self,
        record: TrackedDefect,
    ) -> DefectRecord:

        measurements = DefectMeasurement()

        return DefectRecord(
            defect_id=record.defect_code,
            aircraft_id=str(
                record.aircraft_id
            ),
            component=(
                record.component.component_code
                if record.component
                else ""
            ),
            panel_id=(
                str(record.panel_id)
                if record.panel_id is not None
                else None
            ),
            defect_type=record.class_name,
            location_x=record.location_x,
            location_y=record.location_y,
            bbox=[
                record.bbox_x,
                record.bbox_y,
                record.bbox_x
                + record.bbox_width,
                record.bbox_y
                + record.bbox_height,
            ],
            bbox_width=record.bbox_width,
            bbox_height=record.bbox_height,
            bbox_area=record.bbox_area,
            first_seen=record.first_seen_at.isoformat(),
            last_seen=record.last_seen_at.isoformat(),
            current_confidence=record.current_confidence,
            current_severity=SeverityLevel(
                record.current_severity
            ),
            status=DefectStatus(
                record.status
            ),
            detection_count=record.detection_count,
            measurements=measurements,
            notes=record.notes or "",
        )

    def _inspection_defect_count(
        self,
        inspection_id: int,
    ) -> int:

        return (
            self.db.query(
                func.count(
                    DefectObservation.id
                )
            )
            .filter(
                DefectObservation.inspection_id
                == inspection_id
            )
            .scalar()
            or 0
        )

    def _inspection_code(
        self,
        inspection_id: int,
    ) -> str:

        record = (
            self.db.query(Inspection)
            .filter(
                Inspection.id
                == inspection_id
            )
            .first()
        )

        if not record:
            return str(
                inspection_id
            )

        return record.inspection_code

    @classmethod
    def _class_id(
        cls,
        defect_type: str,
    ) -> int:

        normalized = str(
            defect_type
        ).strip()

        if normalized in cls.CLASS_IDS:
            return cls.CLASS_IDS[
                normalized
            ]

        aliases = {
            "crack": 0,
            "corrosion": 1,
            "dent": 2,
            "missing fastener": 3,
            "missing_fastener": 3,
            "missing-fastener": 3,
        }

        normalized_lower = (
            normalized.lower()
        )

        if normalized_lower in aliases:
            return aliases[
                normalized_lower
            ]

        raise ValueError(
            f"Unsupported AeroIntel defect type: "
            f"{defect_type}"
        )

    @staticmethod
    def _enum_value(value) -> str:

        if hasattr(value, "value"):
            return str(value.value)

        return str(value)

    @staticmethod
    def _parse_datetime(
        value: str | datetime,
    ) -> datetime:

        if isinstance(value, datetime):
            return value

        text = str(value)

        if text.endswith("Z"):
            text = (
                text[:-1]
                + "+00:00"
            )

        return datetime.fromisoformat(
            text
        )



