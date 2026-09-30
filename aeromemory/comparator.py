"""Defect measurement comparison engine for AeroMemory.

Compares geometric bounding boxes, areas, and calibrated physical dimensions
(crack length, corrosion surface area, dent depth) between inspection intervals
to quantify the exact growth, stability, or shrinkage delta.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aeromemory.models import DefectMeasurement, DefectRecord


@dataclass
class ComparisonMetrics:
    defect_id: str
    previous_value: float
    current_value: float
    delta_value: float
    growth_rate_pct: float
    dimension_unit: str                 # 'mm', 'mm2', or 'pixels'
    previous_bbox: List[float]
    current_bbox: List[float]
    confidence_delta: float


class DefectComparator:
    """Computes exact metric deltas between successive observations of a defect."""

    def compare(
        self,
        current_detection: Dict[str, Any],
        previous_defect: DefectRecord,
    ) -> ComparisonMetrics:
        """Calculate dimensional change between previous record and current detection."""
        curr_box = self._extract_bbox(current_detection)
        prev_box = previous_defect.bbox

        curr_conf = float(current_detection.get("confidence", 0.0))
        prev_conf = previous_defect.current_confidence
        conf_delta = round(curr_conf - prev_conf, 3)

        # 1. Attempt calibrated physical measurement comparison
        curr_m = current_detection.get("measurements", {})
        prev_m = previous_defect.measurements

        val_prev, val_curr, unit = self._resolve_primary_values(prev_m, curr_m, prev_box, curr_box)

        delta = val_curr - val_prev
        growth_rate = 0.0
        if val_prev > 0:
            growth_rate = (delta / val_prev) * 100.0

        return ComparisonMetrics(
            defect_id=previous_defect.defect_id,
            previous_value=round(val_prev, 2),
            current_value=round(val_curr, 2),
            delta_value=round(delta, 2),
            growth_rate_pct=round(growth_rate, 2),
            dimension_unit=unit,
            previous_bbox=[round(c, 2) for c in prev_box],
            current_bbox=[round(c, 2) for c in curr_box],
            confidence_delta=conf_delta,
        )

    def _resolve_primary_values(
        self,
        prev_m: DefectMeasurement,
        curr_m: Dict[str, Any],
        prev_box: List[float],
        curr_box: List[float],
    ) -> tuple[float, float, str]:
        """Extract matched scalar for comparison (calibrated physical mm preferred over pixels)."""
        # Crack length
        if prev_m.length_mm is not None and "length_mm" in curr_m:
            return float(prev_m.length_mm), float(curr_m["length_mm"]), "mm"

        # Corrosion area
        if prev_m.area_mm2 is not None and "area_mm2" in curr_m:
            return float(prev_m.area_mm2), float(curr_m["area_mm2"]), "mm2"

        # Dent depth or dimensions
        if prev_m.depth_mm is not None and "depth_mm" in curr_m:
            return float(prev_m.depth_mm), float(curr_m["depth_mm"]), "mm"
        if prev_m.width_mm is not None and "width_mm" in curr_m:
            return float(prev_m.width_mm), float(curr_m["width_mm"]), "mm"

        # Fastener diameter
        if prev_m.diameter_mm is not None and "diameter_mm" in curr_m:
            return float(prev_m.diameter_mm), float(curr_m["diameter_mm"]), "mm"

        # If current has a physical measurement but previous didn't record it directly
        if "length_mm" in curr_m:
            prev_len = prev_m.length_mm if prev_m.length_mm else self._box_span(prev_box)
            return float(prev_len), float(curr_m["length_mm"]), "mm"
        if "area_mm2" in curr_m:
            prev_area = prev_m.area_mm2 if prev_m.area_mm2 else self._box_area(prev_box)
            return float(prev_area), float(curr_m["area_mm2"]), "mm2"

        # Fallback to 2D bounding box area (pixel space)
        prev_area = self._box_area(prev_box)
        curr_area = self._box_area(curr_box)
        return float(prev_area), float(curr_area), "pixels"

    @staticmethod
    def _box_area(box: List[float]) -> float:
        w = max(0.0, box[2] - box[0])
        h = max(0.0, box[3] - box[1])
        return w * h

    @staticmethod
    def _box_span(box: List[float]) -> float:
        w = max(0.0, box[2] - box[0])
        h = max(0.0, box[3] - box[1])
        return max(w, h)

    @staticmethod
    def _extract_bbox(det: Dict[str, Any]) -> List[float]:
        if "bbox" in det:
            return [float(c) for c in det["bbox"]]
        if "bbox_px" in det:
            return [float(c) for c in det["bbox_px"]]
        return [0.0, 0.0, 0.0, 0.0]
