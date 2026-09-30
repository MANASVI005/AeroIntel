from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.model_service import AeroIntelModel


router = APIRouter(
    prefix="/api",
    tags=["Detection"],
)

model = AeroIntelModel()


@router.post("/detect")
async def detect_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are supported.",
        )

    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format.",
        )

    try:
        image_bytes = await file.read()

        with NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = Path(temp_file.name)

        detections = model.detect(temp_path)

        return {
            "filename": file.filename,
            "detections": detections,
            "count": len(detections),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Detection failed: {exc}",
        ) from exc

    finally:
        if "temp_path" in locals() and temp_path.exists():
            temp_path.unlink()