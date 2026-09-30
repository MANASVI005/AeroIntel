from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.detection import router as detection_router
from app.api.inspection import router as inspection_router
from app.db.database import engine
from app.api.inspection_image import router as inspection_image_router
from app.api.decision import router as decision_router
from app.api.metrics import router as metrics_router

app = FastAPI(
    title="AeroIntel API",
    description="Aircraft defect detection and inspection management API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    # Scope CORS strictly to local development and local LAN IP ranges (192.168.x.x, 10.x.x.x, 172.16-31.x.x, 127.0.0.1, localhost)
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(detection_router)
app.include_router(inspection_router)
app.include_router(inspection_image_router)
app.include_router(decision_router)
app.include_router(metrics_router)

# Serve stored inspection images (data/inspections/...) so the frontend can
# display uploaded frames. GET /data/inspections/{code}/{file}.jpg
from pathlib import Path

from fastapi.staticfiles import StaticFiles

_DATA_DIR = Path("data")
_DATA_DIR.mkdir(exist_ok=True)
app.mount("/data", StaticFiles(directory=str(_DATA_DIR)), name="data")


@app.get("/")
def root():
    return {
        "message": "AeroIntel API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
        }