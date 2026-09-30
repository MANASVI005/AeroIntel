from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.detection import router as detection_router
from app.api.inspection import router as inspection_router
from app.db.database import engine
from app.api.inspection_image import router as inspection_image_router
from app.api.decision import router as decision_router

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