"""Data structures and domain models for the AeroMemory Engine.

Defines the core entities:
- Aircraft, Component, Panel hierarchy
- InspectionRecord, DefectRecord, DefectMeasurement
- ProgressionState (NEW, STABLE, INCREASED, DECREASED, RESOLVED)
- Comparison and Result payloads
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SeverityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DefectStatus(str, Enum):
    NEW = "New"
    MONITORED = "Monitored"
    PROGRESSING = "Progressing"
    REPAIRED = "Repaired"
    CLOSED = "Closed"


class ProgressionState(str, Enum):
    NEW = "new"
    STABLE = "stable"
    INCREASED = "increased"
    DECREASED = "decreased"
    RESOLVED = "resolved"


class DefectType(str, Enum):
    CRACK = "Crack"
    CORROSION = "Corrosion"
    DENT = "Dent"
    MISSING_FASTENER = "Missing Fastener"


@dataclass
class Aircraft:
    aircraft_id: str                    # e.g., "AI-001" or "VT-ALB"
    model: str = "Boeing 737-800"
    operator: str = "Commercial Fleet"
    registration: Optional[str] = None


@dataclass
class Component:
    component_id: str                  # e.g., "COMP-01"
    name: str                          # e.g., "Left Wing"
    aircraft_id: str


@dataclass
class Panel:
    panel_id: str                      # e.g., "PANEL-01"
    component_id: str
    region_id: Optional[str] = None


@dataclass
class DefectMeasurement:
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    area_mm2: Optional[float] = None
    depth_mm: Optional[float] = None
    diameter_mm: Optional[float] = None
    severity_index: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, **kwargs):
        known = {"length_mm", "width_mm", "area_mm2", "depth_mm", "diameter_mm", "severity_index"}
        extra = {}
        for k, v in kwargs.items():
            if k in known:
                setattr(self, k, float(v) if v is not None and isinstance(v, (int, float)) else v)
            else:
                extra[k] = v
        self.extra = extra
        for k in known:
            if not hasattr(self, k):
                setattr(self, k, None)

    def primary_value(self) -> float:
        """Returns the most representative scalar dimension for progression tracking."""
        if self.length_mm is not None:
            return self.length_mm
        if self.area_mm2 is not None:
            return self.area_mm2
        if self.depth_mm is not None:
            return self.depth_mm
        if self.width_mm is not None:
            return self.width_mm
        if self.diameter_mm is not None:
            return self.diameter_mm
        if self.severity_index is not None:
            return self.severity_index
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = {k: getattr(self, k) for k in ("length_mm", "width_mm", "area_mm2", "depth_mm", "diameter_mm", "severity_index") if getattr(self, k, None) is not None}
        if hasattr(self, "extra") and self.extra:
            d.update(self.extra)
        return d


@dataclass
class DefectRecord:
    """Unique Defect Record tracked persistently across the aircraft lifecycle."""
    defect_id: str                      # e.g., "DEF-001" or "D01"
    aircraft_id: str                    # e.g., "AI-001"
    component: str                      # e.g., "Left Wing" or "COMP-01"
    defect_type: str                    # Crack, Corrosion, Dent, Missing Fastener
    location_x: float                   # Centroid X (0.0 to 1.0 or pixel)
    location_y: float                   # Centroid Y (0.0 to 1.0 or pixel)
    bbox: List[float]                   # [x1, y1, x2, y2]
    first_seen: str                     # ISO 8601 timestamp
    last_seen: str                      # ISO 8601 timestamp
    current_confidence: float           # Latest detection confidence
    current_severity: SeverityLevel     # Low, Medium, High, Critical
    status: DefectStatus                # New, Monitored, Progressing, Repaired, Closed
    panel_id: Optional[str] = None      # e.g., "PANEL-01"
    bbox_width: float = 0.0             # Width of bbox
    bbox_height: float = 0.0            # Height of bbox
    bbox_area: float = 0.0              # Area in pixels or relative units
    detection_count: int = 1            # Total times detected across inspections
    measurements: DefectMeasurement = field(default_factory=DefectMeasurement)
    notes: Optional[str] = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["current_severity"] = (
            self.current_severity.value
            if isinstance(self.current_severity, SeverityLevel)
            else self.current_severity
        )
        d["status"] = (
            self.status.value
            if isinstance(self.status, DefectStatus)
            else self.status
        )
        return d


@dataclass
class ObservationRecord:
    """Historical snapshot of a single defect observation in an inspection."""
    observation_id: Optional[int]
    defect_id: str
    inspection_id: str
    timestamp: str
    confidence: float
    bbox: List[float]
    area: float
    severity: SeverityLevel
    growth_rate: float = 0.0            # % change compared to previous observation
    status_at_time: DefectStatus = DefectStatus.NEW
    measurements: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = (
            self.severity.value
            if isinstance(self.severity, SeverityLevel)
            else self.severity
        )
        d["status_at_time"] = (
            self.status_at_time.value
            if isinstance(self.status_at_time, DefectStatus)
            else self.status_at_time
        )
        return d


@dataclass
class InspectionRecord:
    """Record of an aircraft inspection session."""
    inspection_id: str                  # e.g., "INS-001"
    aircraft_id: str                    # e.g., "AI-001"
    aircraft_model: str                 # e.g., "Boeing 737-800"
    component: str                      # e.g., "Left Wing"
    timestamp: str                      # ISO 8601 timestamp
    original_image_path: Optional[str] = None
    annotated_image_path: Optional[str] = None
    panel_id: Optional[str] = None
    defect_count: int = 0
    inspection_status: str = "COMPLETED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DefectComparison:
    """Detailed comparison between a previous defect and current observation."""
    defect_id: str
    state: ProgressionState             # new, stable, increased, decreased, resolved
    match_confidence: float             # Spatial/appearance matching score (0.0 to 1.0)
    previous_bbox: Optional[List[float]] = None
    current_bbox: Optional[List[float]] = None
    previous_measurement: Optional[float] = None
    current_measurement: Optional[float] = None
    measurement_delta: Optional[float] = None
    growth_rate_pct: float = 0.0
    defect_type: str = "Crack"
    severity: SeverityLevel = SeverityLevel.LOW
    decision_support: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value if isinstance(self.state, ProgressionState) else self.state
        d["severity"] = self.severity.value if isinstance(self.severity, SeverityLevel) else self.severity
        return d


@dataclass
class AeroMemoryResult:
    """Comprehensive result returned by AeroMemory for an inspection."""
    inspection_id: str
    aircraft_id: str
    timestamp: str
    previous_inspection_id: Optional[str]
    total_defects_detected: int
    matched_count: int
    new_count: int
    increased_count: int
    stable_count: int
    resolved_count: int
    comparisons: List[DefectComparison] = field(default_factory=list)
    image_aligned: bool = False
    alignment_inliers: int = 0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["comparisons"] = [c.to_dict() for c in self.comparisons]
        return d
