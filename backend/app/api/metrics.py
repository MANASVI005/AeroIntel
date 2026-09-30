"""GET /api/metrics — serves the verified model evaluation + latency data.

Source of truth: the files written by the training/eval pipeline:
  - logs/eval_aerointel_v1_yolo11s_test.json   (test-split metrics, per class)
  - logs/latency_aerointel_v1_yolo11s.json     (measured inference latency)
  - models/registry.json                       (model identity / export info)

Paths are resolved relative to this file so the endpoint works no matter which
directory uvicorn is launched from (repo root, backend/, etc.). Files are read
on each request — tiny JSONs, so caching is unnecessary and the data always
reflects the latest eval run.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/api/metrics",
    tags=["Model Metrics"],
)

# Repo root = four levels up from this file
# (metrics.py → api → app → backend → <repo root>).
REPO_ROOT = Path(__file__).resolve().parents[3]

EVAL_PATH = REPO_ROOT / "logs" / "eval_aerointel_v1_yolo11s_test.json"
LATENCY_PATH = REPO_ROOT / "logs" / "latency_aerointel_v1_yolo11s.json"
REGISTRY_PATH = REPO_ROOT / "models" / "registry.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Metrics source missing: {path.name}. Run the eval/latency pipeline first.",
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not read {path.name}: {exc}",
        ) from exc


@router.get("")
def get_model_metrics():
    """Aggregate model card + test-split evaluation + measured latency."""
    registry = _load_json(REGISTRY_PATH)
    eval_data = _load_json(EVAL_PATH)
    latency = _load_json(LATENCY_PATH)

    return {
        "model": {
            "name": registry.get("name"),
            "type": registry.get("type"),
            "version": registry.get("version"),
            "imgsz": registry.get("imgsz"),
            "trained_from": registry.get("trained_from"),
            "exported_at": registry.get("exported_at"),
            "classes": registry.get("classes"),
        },
        "evaluation": {
            "run": eval_data.get("run"),
            "split": eval_data.get("split"),
            "overall": eval_data.get("overall"),
            "per_class": eval_data.get("per_class"),
            "dataset": {
                "images": 8525,
                "annotations": 15252,
            },
        },
        "latency": {
            "device": latency.get("device"),
            "n_images": latency.get("n_images"),
            "p50_ms": latency.get("p50_ms"),
            "p95_ms": latency.get("p95_ms"),
            "conf": latency.get("conf"),
            "iou": latency.get("iou"),
        },
    }
