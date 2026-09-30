"""Image registration and spatial alignment engine for AeroMemory.

Uses OpenCV ORB feature extraction and RANSAC Homography to align historical
inspection images with current images, compensating for camera angles, distance,
and drone positioning variations across maintenance sessions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np


@dataclass
class AlignmentResult:
    """Outcome of homography image registration."""
    success: bool
    homography: Optional[np.ndarray]     # 3x3 transformation matrix
    inliers_count: int
    matches_count: int
    inlier_ratio: float
    message: str


class ImageRegistrar:
    """Aligns aircraft inspection photos using panel landmarks (rivets, seams)."""

    def __init__(self, max_features: int = 2000, match_ratio: float = 0.75) -> None:
        self.max_features = max_features
        self.match_ratio = match_ratio
        self.orb = cv2.ORB_create(nfeatures=max_features)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def compute_alignment(
        self,
        reference_image: Union[str, Path, np.ndarray],
        current_image: Union[str, Path, np.ndarray],
    ) -> AlignmentResult:
        """Calculate the homography mapping reference coordinates to current coordinates."""
        ref_mat = self._load_gray(reference_image)
        curr_mat = self._load_gray(current_image)

        if ref_mat is None or curr_mat is None:
            return AlignmentResult(
                success=False,
                homography=np.eye(3, dtype=np.float32),
                inliers_count=0,
                matches_count=0,
                inlier_ratio=0.0,
                message="Image loading failed or image path not accessible",
            )

        # Detect ORB keypoints and descriptors
        kp_ref, des_ref = self.orb.detectAndCompute(ref_mat, None)
        kp_curr, des_curr = self.orb.detectAndCompute(curr_mat, None)

        if des_ref is None or des_curr is None or len(kp_ref) < 4 or len(kp_curr) < 4:
            return AlignmentResult(
                success=False,
                homography=np.eye(3, dtype=np.float32),
                inliers_count=0,
                matches_count=0,
                inlier_ratio=0.0,
                message="Insufficient structural keypoints detected for alignment",
            )

        # KNN matching with Lowe's ratio test
        raw_matches = self.matcher.knnMatch(des_ref, des_curr, k=2)
        good_matches = []
        for pair in raw_matches:
            if len(pair) == 2 and pair[0].distance < self.match_ratio * pair[1].distance:
                good_matches.append(pair[0])

        if len(good_matches) < 4:
            return AlignmentResult(
                success=False,
                homography=np.eye(3, dtype=np.float32),
                inliers_count=0,
                matches_count=len(good_matches),
                inlier_ratio=0.0,
                message=f"Only {len(good_matches)} good feature matches found (minimum 4 required)",
            )

        # Extract matched point locations
        pts_ref = np.float32([kp_ref[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        pts_curr = np.float32([kp_curr[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Compute Homography via RANSAC
        H, mask = cv2.findHomography(pts_ref, pts_curr, cv2.RANSAC, 5.0)

        if H is None:
            return AlignmentResult(
                success=False,
                homography=np.eye(3, dtype=np.float32),
                inliers_count=0,
                matches_count=len(good_matches),
                inlier_ratio=0.0,
                message="Homography computation failed during RANSAC fitting",
            )

        inliers = int(np.sum(mask)) if mask is not None else 0
        inlier_ratio = inliers / max(len(good_matches), 1)

        return AlignmentResult(
            success=inliers >= 4,
            homography=H,
            inliers_count=inliers,
            matches_count=len(good_matches),
            inlier_ratio=round(inlier_ratio, 3),
            message="Alignment successful",
        )

    def transform_bbox(
        self, bbox: List[float], homography: Optional[np.ndarray] = None
    ) -> List[float]:
        """Project bounding box [x1, y1, x2, y2] through the homography matrix."""
        if homography is None or np.allclose(homography, np.eye(3)):
            return [float(c) for c in bbox]

        x1, y1, x2, y2 = bbox
        corners = np.array([
            [x1, y1],
            [x2, y1],
            [x2, y2],
            [x1, y2]
        ], dtype=np.float32).reshape(-1, 1, 2)

        # Perspective transformation of all four corners
        projected = cv2.perspectiveTransform(corners, homography)
        projected = projected.reshape(-1, 2)

        new_x1 = float(np.min(projected[:, 0]))
        new_y1 = float(np.min(projected[:, 1]))
        new_x2 = float(np.max(projected[:, 0]))
        new_y2 = float(np.max(projected[:, 1]))

        return [round(new_x1, 2), round(new_y1, 2), round(new_x2, 2), round(new_y2, 2)]

    def _load_gray(self, img_input: Union[str, Path, np.ndarray]) -> Optional[np.ndarray]:
        if isinstance(img_input, np.ndarray):
            if len(img_input.shape) == 3:
                return cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY)
            return img_input

        path = Path(img_input)
        if not path.exists():
            return None

        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        return img
