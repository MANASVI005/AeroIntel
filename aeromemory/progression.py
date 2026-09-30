"""Progression state machine and decision support engine for AeroMemory.

Classifies defect temporal transitions into discrete states:
- NEW: First sighting on the aircraft panel
- STABLE: Dimension changes within noise/measurement tolerance
- INCREASED: Active fatigue growth or corrosion spread
- DECREASED: Dimensional reduction (e.g. partial blending or composite repair)
- RESOLVED: Defect absent following scheduled maintenance

Also generates actionable engineer decision-support advisories.
"""

from __future__ import annotations

from typing import Optional

from aeromemory.comparator import ComparisonMetrics
from aeromemory.models import DefectRecord, ProgressionState, SeverityLevel


class ProgressionEngine:
    """Evaluates comparison deltas and assigns aircraft maintenance progression states."""

    def __init__(
        self,
        growth_threshold_pct: float = 4.0,
        reduction_threshold_pct: float = -8.0,
        absolute_tolerance_mm: float = 0.5,
    ) -> None:
        self.growth_threshold_pct = growth_threshold_pct
        self.reduction_threshold_pct = reduction_threshold_pct
        self.absolute_tolerance_mm = absolute_tolerance_mm

    def evaluate_state(
        self,
        metrics: Optional[ComparisonMetrics],
        is_new: bool = False,
        is_resolved: bool = False,
    ) -> ProgressionState:
        """Determine the progression state based on measurement delta and detection presence."""
        if is_new or metrics is None:
            return ProgressionState.NEW

        if is_resolved:
            return ProgressionState.RESOLVED

        # Check physical units tolerance first if calibrated
        if metrics.dimension_unit == "mm":
            if metrics.delta_value > self.absolute_tolerance_mm:
                return ProgressionState.INCREASED
            elif metrics.delta_value < -self.absolute_tolerance_mm:
                return ProgressionState.DECREASED
            return ProgressionState.STABLE

        # Percentage-based threshold for areas / general metrics
        if metrics.growth_rate_pct > self.growth_threshold_pct:
            return ProgressionState.INCREASED
        elif metrics.growth_rate_pct < self.reduction_threshold_pct:
            return ProgressionState.DECREASED
        else:
            return ProgressionState.STABLE

    def generate_decision_support(
        self,
        defect_type: str,
        state: ProgressionState,
        severity: SeverityLevel,
        growth_pct: float = 0.0,
    ) -> str:
        """Generate human-readable engineering action recommendations."""
        dtype = defect_type.strip().lower()

        if state == ProgressionState.NEW:
            if "crack" in dtype:
                return "Create inspection finding: Verify fatigue crack via eddy-current / NDT."
            if "fastener" in dtype:
                return "Create inspection finding: Inspect hole integrity and install replacement fastener."
            return "Create inspection finding and verify defect dimensions."

        if state == ProgressionState.RESOLVED:
            return "Defect resolved: Verify corresponding entry and sign-off in aircraft maintenance log."

        if state == ProgressionState.INCREASED:
            if severity == SeverityLevel.CRITICAL:
                return "CRITICAL FATIGUE PROGRESSION: Ground aircraft for mandatory structural engineering review."
            if "crack" in dtype:
                return f"Crack growing (+{growth_pct:.1f}%): Schedule engineering evaluation prior to next maintenance cycle."
            if "corrosion" in dtype:
                return f"Corrosion spread (+{growth_pct:.1f}%): Measure material loss and perform blend-out."
            return f"Defect progression (+{growth_pct:.1f}%): Flag for priority reinspection."

        if state == ProgressionState.DECREASED:
            return "Defect dimension reduced: Confirm post-repair rework or surface treatment."

        # Stable
        if severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
            return "High severity defect stable: Continue monitored surveillance at each scheduled check."
        return "Defect stable within tolerance: Log in structural monitoring record."
