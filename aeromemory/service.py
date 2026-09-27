"""Main orchestration service facade for AeroMemory Engine.

Provides a unified high-level interface:
    service = AeroMemoryService(db_path='aeromemory.db')
    result = service.process_inspection(inspection_payload)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from aeromemory.comparator import DefectComparator
from aeromemory.matcher import DefectMatcher
from aeromemory.models import (
    AeroMemoryResult,
    DefectComparison,
    DefectMeasurement,
    DefectRecord,
    DefectStatus,
    InspectionRecord,
    ObservationRecord,
    ProgressionState,
    SeverityLevel,
)
from aeromemory.progression import ProgressionEngine
from aeromemory.registration import ImageRegistrar
from aeromemory.repository import AeroMemoryRepository, SQLiteAeroMemoryRepository
from aeromemory.severity import assess_severity


class AeroMemoryService:
    """End-to-end service coordinating image alignment, defect matching, and progression."""

    def __init__(
        self,
        repository: Optional[AeroMemoryRepository] = None,
        db_path: Union[str, Path] = "aeromemory.db",
        enable_registration: bool = True,
    ) -> None:
        self.repository = repository or SQLiteAeroMemoryRepository(db_path=db_path)
        self.registrar = ImageRegistrar() if enable_registration else None
        self.matcher = DefectMatcher()
        self.comparator = DefectComparator()
        self.progression_engine = ProgressionEngine()

    def process_inspection(
        self,
        inspection_id: str,
        aircraft_id: str,
        component: str,
        detections: List[Dict[str, Any]],
        timestamp: Optional[str] = None,
        panel_id: Optional[str] = None,
        original_image_path: Optional[str] = None,
        annotated_image_path: Optional[str] = None,
        aircraft_model: str = "Boeing 737-800",
    ) -> AeroMemoryResult:
        """Process an inspection session and compute historical defect progressions."""
        if not timestamp:
            timestamp = datetime.now().isoformat()

        # 1. Fetch previous inspection record for this aircraft & component
        prev_insp = self.repository.get_previous_inspection(
            aircraft_id=aircraft_id,
            component=component,
            before_timestamp=timestamp,
            exclude_id=inspection_id,
        )

        prev_defects: List[DefectRecord] = []
        if prev_insp:
            prev_defects = self.repository.get_active_defects(
                aircraft_id=aircraft_id, component=component
            )

        # 2. Image registration / alignment (if images are present)
        transformed_boxes = None
        alignment_success = False
        inlier_count = 0

        if (
            self.registrar
            and prev_insp
            and prev_insp.original_image_path
            and original_image_path
            and Path(prev_insp.original_image_path).exists()
            and Path(original_image_path).exists()
        ):
            align_res = self.registrar.compute_alignment(
                reference_image=prev_insp.original_image_path,
                current_image=original_image_path,
            )
            alignment_success = align_res.success
            inlier_count = align_res.inliers_count

            if align_res.success and align_res.homography is not None:
                transformed_boxes = [
                    self.registrar.transform_bbox(d.bbox, align_res.homography)
                    for d in prev_defects
                ]

        # 3. Match current detections against historical defect records
        match_result = self.matcher.match(
            current_detections=detections,
            previous_defects=prev_defects,
            transformed_previous_boxes=transformed_boxes,
        )

        comparisons: List[DefectComparison] = []
        matched_count = 0
        new_count = 0
        increased_count = 0
        stable_count = 0
        resolved_count = 0

        # 4. Handle matched defects (existing defects re-observed)
        for curr_det, prev_record, score in match_result.matched_pairs:
            matched_count += 1
            metrics = self.comparator.compare(curr_det, prev_record)
            state = self.progression_engine.evaluate_state(metrics)

            curr_box = self._extract_bbox(curr_det)
            curr_conf = float(curr_det.get("confidence", 0.85))
            severity = assess_severity(prev_record.defect_type, curr_box, curr_conf)
            advisory = self.progression_engine.generate_decision_support(
                defect_type=prev_record.defect_type,
                state=state,
                severity=severity,
                growth_pct=metrics.growth_rate_pct,
            )

            if state == ProgressionState.INCREASED:
                increased_count += 1
                new_status = DefectStatus.PROGRESSING
            elif state == ProgressionState.STABLE:
                stable_count += 1
                new_status = DefectStatus.MONITORED
            else:
                new_status = DefectStatus.MONITORED

            # Update persistent DefectRecord
            cx, cy = self._calc_centroid(curr_box)
            w, h = abs(curr_box[2] - curr_box[0]), abs(curr_box[3] - curr_box[1])

            measurements_dict = curr_det.get("measurements", {})
            updated_measurements = DefectMeasurement(**measurements_dict) if measurements_dict else prev_record.measurements

            prev_record.location_x = round(cx, 4)
            prev_record.location_y = round(cy, 4)
            prev_record.bbox = [round(c, 2) for c in curr_box]
            prev_record.bbox_width = round(w, 2)
            prev_record.bbox_height = round(h, 2)
            prev_record.bbox_area = round(w * h, 2)
            prev_record.last_seen = timestamp
            prev_record.current_confidence = round(curr_conf, 3)
            prev_record.current_severity = severity
            prev_record.status = new_status
            prev_record.detection_count += 1
            prev_record.measurements = updated_measurements
            self.repository.update_defect(prev_record)

            # Record timeline observation
            obs = ObservationRecord(
                observation_id=None,
                defect_id=prev_record.defect_id,
                inspection_id=inspection_id,
                timestamp=timestamp,
                confidence=round(curr_conf, 3),
                bbox=prev_record.bbox,
                area=prev_record.bbox_area,
                severity=severity,
                growth_rate=metrics.growth_rate_pct,
                status_at_time=new_status,
                measurements=measurements_dict,
            )
            self.repository.save_observation(obs)

            comparisons.append(
                DefectComparison(
                    defect_id=prev_record.defect_id,
                    state=state,
                    match_confidence=score,
                    previous_bbox=metrics.previous_bbox,
                    current_bbox=metrics.current_bbox,
                    previous_measurement=metrics.previous_value,
                    current_measurement=metrics.current_value,
                    measurement_delta=metrics.delta_value,
                    growth_rate_pct=metrics.growth_rate_pct,
                    defect_type=prev_record.defect_type,
                    severity=severity,
                    decision_support=advisory,
                )
            )

        # 5. Handle unmatched current detections (new findings)
        for curr_det in match_result.unmatched_current:
            new_count += 1
            curr_box = self._extract_bbox(curr_det)
            curr_conf = float(curr_det.get("confidence", 0.85))
            curr_type = curr_det.get("defect_type", "Crack")
            severity = assess_severity(curr_type, curr_box, curr_conf)

            custom_id = curr_det.get("defect_id")
            defect_id = custom_id if custom_id else self.repository.next_defect_id()

            advisory = self.progression_engine.generate_decision_support(
                defect_type=curr_type,
                state=ProgressionState.NEW,
                severity=severity,
            )

            cx, cy = self._calc_centroid(curr_box)
            w, h = abs(curr_box[2] - curr_box[0]), abs(curr_box[3] - curr_box[1])

            measurements_dict = curr_det.get("measurements", {})
            meas = DefectMeasurement(**measurements_dict) if measurements_dict else DefectMeasurement()

            new_record = DefectRecord(
                defect_id=defect_id,
                aircraft_id=aircraft_id,
                component=component,
                panel_id=panel_id,
                defect_type=curr_type,
                location_x=round(cx, 4),
                location_y=round(cy, 4),
                bbox=[round(c, 2) for c in curr_box],
                bbox_width=round(w, 2),
                bbox_height=round(h, 2),
                bbox_area=round(w * h, 2),
                first_seen=timestamp,
                last_seen=timestamp,
                current_confidence=round(curr_conf, 3),
                current_severity=severity,
                status=DefectStatus.NEW,
                detection_count=1,
                measurements=meas,
                notes=curr_det.get("notes", ""),
            )
            self.repository.save_defect(new_record)

            obs = ObservationRecord(
                observation_id=None,
                defect_id=defect_id,
                inspection_id=inspection_id,
                timestamp=timestamp,
                confidence=round(curr_conf, 3),
                bbox=new_record.bbox,
                area=new_record.bbox_area,
                severity=severity,
                growth_rate=0.0,
                status_at_time=DefectStatus.NEW,
                measurements=measurements_dict,
            )
            self.repository.save_observation(obs)

            primary_val = meas.primary_value() or new_record.bbox_area
            comparisons.append(
                DefectComparison(
                    defect_id=defect_id,
                    state=ProgressionState.NEW,
                    match_confidence=1.0,
                    previous_bbox=None,
                    current_bbox=new_record.bbox,
                    previous_measurement=None,
                    current_measurement=round(primary_val, 2),
                    measurement_delta=None,
                    growth_rate_pct=0.0,
                    defect_type=curr_type,
                    severity=severity,
                    decision_support=advisory,
                )
            )

        # 6. Handle unmatched previous defects (resolved or unobserved)
        for prev_record in match_result.unmatched_previous:
            resolved_count += 1
            prev_record.status = DefectStatus.REPAIRED
            prev_record.last_seen = timestamp
            self.repository.update_defect(prev_record)

            advisory = self.progression_engine.generate_decision_support(
                defect_type=prev_record.defect_type,
                state=ProgressionState.RESOLVED,
                severity=prev_record.current_severity,
            )

            obs = ObservationRecord(
                observation_id=None,
                defect_id=prev_record.defect_id,
                inspection_id=inspection_id,
                timestamp=timestamp,
                confidence=0.0,
                bbox=prev_record.bbox,
                area=0.0,
                severity=prev_record.current_severity,
                growth_rate=-100.0,
                status_at_time=DefectStatus.REPAIRED,
                measurements={"status": "resolved"},
            )
            self.repository.save_observation(obs)

            comparisons.append(
                DefectComparison(
                    defect_id=prev_record.defect_id,
                    state=ProgressionState.RESOLVED,
                    match_confidence=0.0,
                    previous_bbox=prev_record.bbox,
                    current_bbox=None,
                    previous_measurement=prev_record.measurements.primary_value() or prev_record.bbox_area,
                    current_measurement=0.0,
                    measurement_delta=None,
                    growth_rate_pct=-100.0,
                    defect_type=prev_record.defect_type,
                    severity=prev_record.current_severity,
                    decision_support=advisory,
                )
            )

        # 7. Persist this inspection record
        insp_record = InspectionRecord(
            inspection_id=inspection_id,
            aircraft_id=aircraft_id,
            aircraft_model=aircraft_model,
            component=component,
            timestamp=timestamp,
            original_image_path=original_image_path,
            annotated_image_path=annotated_image_path,
            panel_id=panel_id,
            defect_count=len(detections),
            inspection_status="COMPLETED",
        )
        self.repository.save_inspection(insp_record)

        summary = (
            f"Inspection {inspection_id} completed: {len(detections)} defect(s) detected. "
            f"({matched_count} matched, {new_count} new, {increased_count} growing, "
            f"{stable_count} stable, {resolved_count} resolved)."
        )

        return AeroMemoryResult(
            inspection_id=inspection_id,
            aircraft_id=aircraft_id,
            timestamp=timestamp,
            previous_inspection_id=prev_insp.inspection_id if prev_insp else None,
            total_defects_detected=len(detections),
            matched_count=matched_count,
            new_count=new_count,
            increased_count=increased_count,
            stable_count=stable_count,
            resolved_count=resolved_count,
            comparisons=comparisons,
            image_aligned=alignment_success,
            alignment_inliers=inlier_count,
            summary=summary,
        )

    @staticmethod
    def _extract_bbox(det: Dict[str, Any]) -> List[float]:
        if "bbox" in det:
            return [float(c) for c in det["bbox"]]
        if "bbox_px" in det:
            return [float(c) for c in det["bbox_px"]]
        return [0.0, 0.0, 0.0, 0.0]

    @staticmethod
    def _calc_centroid(box: List[float]) -> Tuple[float, float]:
        return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
