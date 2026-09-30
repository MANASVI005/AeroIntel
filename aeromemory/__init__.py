"""AeroMemory Engine for AeroIntel.

A temporal defect tracking, progression analysis, and decision-support module
for aircraft structural health monitoring.
"""

from aeromemory.comparator import ComparisonMetrics, DefectComparator
from aeromemory.database import AeroMemoryDB
from aeromemory.matcher import DefectMatcher, MatchCandidate, MatchResult
from aeromemory.models import (
    AeroMemoryResult,
    Aircraft,
    Component,
    DefectComparison,
    DefectMeasurement,
    DefectRecord,
    DefectStatus,
    DefectType,
    InspectionRecord,
    ObservationRecord,
    Panel,
    ProgressionState,
    SeverityLevel,
)
from aeromemory.progression import ProgressionEngine
from aeromemory.registration import AlignmentResult, ImageRegistrar
from aeromemory.repository import AeroMemoryRepository, SQLiteAeroMemoryRepository
from aeromemory.service import AeroMemoryService
from aeromemory.severity import assess_severity

__all__ = [
    "AeroMemoryService",
    "AeroMemoryRepository",
    "SQLiteAeroMemoryRepository",
    "AeroMemoryDB",
    "ImageRegistrar",
    "DefectMatcher",
    "DefectComparator",
    "ProgressionEngine",
    "assess_severity",
    "Aircraft",
    "Component",
    "Panel",
    "DefectRecord",
    "ObservationRecord",
    "InspectionRecord",
    "DefectMeasurement",
    "DefectComparison",
    "AeroMemoryResult",
    "SeverityLevel",
    "DefectStatus",
    "DefectType",
    "ProgressionState",
    "MatchCandidate",
    "MatchResult",
    "AlignmentResult",
    "ComparisonMetrics",
]
