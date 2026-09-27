"""Severity Assessment Engine for AeroMemory.

Calculates severity level (Low, Medium, High, Critical) based on:
1. Defect Type
2. Relative Bounding Box Size / Area
3. Model Confidence
"""

from __future__ import annotations
from typing import List
from aeromemory.models import DefectType, SeverityLevel


def assess_severity(
    defect_type: str,
    bbox: List[float],
    confidence: float,
    image_width: int = 640,
    image_height: int = 640,
) -> SeverityLevel:
    """Assess severity based on defect physics and bounding box extent."""
    x1, y1, x2, y2 = bbox
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    
    # If coordinates are in absolute pixels, normalize by image dimensions
    if w > 1.0 or h > 1.0:
        norm_w = w / max(image_width, 1)
        norm_h = h / max(image_height, 1)
    else:
        norm_w = w
        norm_h = h
        
    rel_area = norm_w * norm_h
    norm_type = defect_type.strip().lower()

    if "crack" in norm_type:
        # Cracks represent immediate structural fatigue risks
        if rel_area > 0.05 or norm_w > 0.35 or norm_h > 0.35:
            return SeverityLevel.CRITICAL
        elif rel_area > 0.015 or confidence > 0.75:
            return SeverityLevel.HIGH
        else:
            return SeverityLevel.MEDIUM

    elif "missing" in norm_type or "fastener" in norm_type:
        # Missing fasteners compromise panel load distribution
        if confidence > 0.80:
            return SeverityLevel.HIGH
        elif confidence > 0.50:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    elif "corrosion" in norm_type:
        # Corrosion involves material loss over area
        if rel_area > 0.08:
            return SeverityLevel.CRITICAL
        elif rel_area > 0.025:
            return SeverityLevel.HIGH
        elif rel_area > 0.005:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    elif "dent" in norm_type:
        # Dents relate to aerodynamic flow and internal rib/stringer damage
        if rel_area > 0.10:
            return SeverityLevel.HIGH
        elif rel_area > 0.03:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    # Default fallback
    return SeverityLevel.MEDIUM
