"""Defect matching and temporal re-identification engine for AeroMemory.

Associates newly detected defects in the current inspection with historical
defect records on the same aircraft panel, computing probabilistic matching scores
based on spatial overlap (IoU), normalized centroid proximity, and class consistency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from aeromemory.models import DefectRecord


@dataclass
class MatchCandidate:
    current_index: int
    previous_defect: DefectRecord
    match_score: float                  # 0.0 to 1.0
    iou: float
    centroid_distance: float
    class_match: bool


@dataclass
class MatchResult:
    matched_pairs: List[Tuple[Dict[str, Any], DefectRecord, float]]  # (current_data, previous_record, score)
    unmatched_current: List[Dict[str, Any]]
    unmatched_previous: List[DefectRecord]


class DefectMatcher:
    """Matches current inspection detections to persistent defect records."""

    def __init__(
        self,
        min_match_score: float = 0.35,
        max_centroid_distance: float = 180.0,
        iou_weight: float = 0.45,
        dist_weight: float = 0.35,
        class_weight: float = 0.20,
    ) -> None:
        self.min_match_score = min_match_score
        self.max_centroid_distance = max_centroid_distance
        self.iou_weight = iou_weight
        self.dist_weight = dist_weight
        self.class_weight = class_weight

    def match(
        self,
        current_detections: List[Dict[str, Any]],
        previous_defects: List[DefectRecord],
        transformed_previous_boxes: Optional[List[List[float]]] = None,
    ) -> MatchResult:
        """Find optimal 1-to-1 pairings between current detections and previous records."""
        if not previous_defects:
            return MatchResult(
                matched_pairs=[],
                unmatched_current=list(current_detections),
                unmatched_previous=[],
            )

        if not current_detections:
            return MatchResult(
                matched_pairs=[],
                unmatched_current=[],
                unmatched_previous=list(previous_defects),
            )

        # Build candidate score matrix
        candidates: List[MatchCandidate] = []

        for c_idx, curr in enumerate(current_detections):
            curr_box = self._extract_bbox(curr)
            curr_type = curr.get("defect_type", "").strip().lower()

            for p_idx, prev in enumerate(previous_defects):
                # Use homography-transformed box if supplied, else original record bbox
                prev_box = (
                    transformed_previous_boxes[p_idx]
                    if transformed_previous_boxes and p_idx < len(transformed_previous_boxes)
                    else prev.bbox
                )
                prev_type = prev.defect_type.strip().lower()

                class_match = curr_type == prev_type
                iou = self.calculate_iou(curr_box, prev_box)
                dist = self.calculate_centroid_distance(curr_box, prev_box)

                # If distance is wildly out of panel vicinity, skip immediately
                if dist > self.max_centroid_distance and iou == 0.0:
                    continue

                # Normalized proximity: 1.0 at distance 0, dropping to 0.0 at max_centroid_distance
                norm_prox = max(0.0, 1.0 - (dist / max(self.max_centroid_distance, 1.0)))

                # Weighted composite score
                score = (
                    (self.iou_weight * iou)
                    + (self.dist_weight * norm_prox)
                    + (self.class_weight * (1.0 if class_match else 0.0))
                )

                # Heavy penalty if class contradicts completely unless IoU is very high
                if not class_match:
                    score *= 0.65

                if score >= self.min_match_score:
                    candidates.append(
                        MatchCandidate(
                            current_index=c_idx,
                            previous_defect=prev,
                            match_score=round(score, 3),
                            iou=round(iou, 3),
                            centroid_distance=round(dist, 2),
                            class_match=class_match,
                        )
                    )

        # Greedy bipartite assignment sorted by highest confidence score
        candidates.sort(key=lambda c: c.match_score, reverse=True)

        assigned_curr = set()
        assigned_prev_ids = set()
        matched_pairs: List[Tuple[Dict[str, Any], DefectRecord, float]] = []

        for cand in candidates:
            if cand.current_index in assigned_curr:
                continue
            if cand.previous_defect.defect_id in assigned_prev_ids:
                continue

            assigned_curr.add(cand.current_index)
            assigned_prev_ids.add(cand.previous_defect.defect_id)
            matched_pairs.append(
                (current_detections[cand.current_index], cand.previous_defect, cand.match_score)
            )

        unmatched_curr = [
            d for idx, d in enumerate(current_detections) if idx not in assigned_curr
        ]
        unmatched_prev = [
            p for p in previous_defects if p.defect_id not in assigned_prev_ids
        ]

        return MatchResult(
            matched_pairs=matched_pairs,
            unmatched_current=unmatched_curr,
            unmatched_previous=unmatched_prev,
        )

    @staticmethod
    def calculate_iou(boxA: List[float], boxB: List[float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        inter_w = max(0.0, xB - xA)
        inter_h = max(0.0, yB - yA)
        inter_area = inter_w * inter_h

        areaA = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        areaB = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

        union = areaA + areaB - inter_area
        if union <= 0.0:
            return 0.0

        return inter_area / union

    @staticmethod
    def calculate_centroid_distance(boxA: List[float], boxB: List[float]) -> float:
        cxA = (boxA[0] + boxA[2]) / 2.0
        cyA = (boxA[1] + boxA[3]) / 2.0
        cxB = (boxB[0] + boxB[2]) / 2.0
        cyB = (boxB[1] + boxB[3]) / 2.0
        return ((cxA - cxB) ** 2 + (cyA - cyB) ** 2) ** 0.5

    @staticmethod
    def _extract_bbox(det: Dict[str, Any]) -> List[float]:
        if "bbox" in det:
            return [float(c) for c in det["bbox"]]
        if "bbox_px" in det:
            return [float(c) for c in det["bbox_px"]]
        return [0.0, 0.0, 0.0, 0.0]
