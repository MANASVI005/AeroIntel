"""SQLite Database Manager for AeroMemory (Offline Storage & Defect Records)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from aeromemory.models import (
    DefectRecord,
    DefectStatus,
    InspectionRecord,
    ObservationRecord,
    SeverityLevel,
)
from aeromemory.severity import assess_severity


class AeroMemoryDB:
    """Manages offline local database for inspections and unique defect records."""

    def __init__(self, db_path: str | Path = "aeromemory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize tables according to AeroMemory specification."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Inspections Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    inspection_id TEXT PRIMARY KEY,
                    aircraft_id TEXT NOT NULL,
                    aircraft_model TEXT,
                    component TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    original_image_path TEXT,
                    annotated_image_path TEXT,
                    defect_count INTEGER DEFAULT 0,
                    inspection_status TEXT DEFAULT 'COMPLETED'
                )
            """)

            # 2. Unique Defect Records Table (Part 2)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS defects (
                    defect_id TEXT PRIMARY KEY,
                    aircraft_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    defect_type TEXT NOT NULL,
                    location_x REAL NOT NULL,
                    location_y REAL NOT NULL,
                    bbox TEXT NOT NULL,
                    bbox_width REAL NOT NULL,
                    bbox_height REAL NOT NULL,
                    bbox_area REAL NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    current_confidence REAL NOT NULL,
                    current_severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detection_count INTEGER DEFAULT 1,
                    notes TEXT DEFAULT ''
                )
            """)

            # 3. Defect Observations / Timeline Table (Part 5)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    defect_id TEXT NOT NULL,
                    inspection_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    bbox TEXT NOT NULL,
                    area REAL NOT NULL,
                    severity TEXT NOT NULL,
                    growth_rate REAL DEFAULT 0.0,
                    status_at_time TEXT NOT NULL,
                    FOREIGN KEY (defect_id) REFERENCES defects(defect_id),
                    FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
                )
            """)
            conn.commit()

    def next_defect_id(self) -> str:
        """Generate next sequence defect ID (e.g. DEF-001, DEF-023)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM defects")
            count = cursor.fetchone()["total"] + 1
            return f"DEF-{count:03d}"

    def create_defect_record(
        self,
        aircraft_id: str,
        component: str,
        defect_type: str,
        bbox: List[float],
        confidence: float,
        timestamp: Optional[str] = None,
        inspection_id: Optional[str] = None,
        notes: str = "",
        defect_id: Optional[str] = None,
    ) -> DefectRecord:
        """Create and store a unique defect record (Part 2)."""
        if not defect_id:
            defect_id = self.next_defect_id()
        if not timestamp:
            timestamp = datetime.now().isoformat()

        x1, y1, x2, y2 = bbox
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        centroid_x = (x1 + x2) / 2.0
        centroid_y = (y1 + y2) / 2.0
        area = width * height

        severity = assess_severity(defect_type, bbox, confidence)
        status = DefectStatus.NEW

        record = DefectRecord(
            defect_id=defect_id,
            aircraft_id=aircraft_id,
            component=component,
            defect_type=defect_type,
            location_x=round(centroid_x, 4),
            location_y=round(centroid_y, 4),
            bbox=[round(coord, 2) for coord in bbox],
            bbox_width=round(width, 2),
            bbox_height=round(height, 2),
            bbox_area=round(area, 2),
            first_seen=timestamp,
            last_seen=timestamp,
            current_confidence=round(confidence, 3),
            current_severity=severity,
            status=status,
            detection_count=1,
            notes=notes,
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO defects (
                    defect_id, aircraft_id, component, defect_type,
                    location_x, location_y, bbox, bbox_width, bbox_height, bbox_area,
                    first_seen, last_seen, current_confidence, current_severity,
                    status, detection_count, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.defect_id,
                record.aircraft_id,
                record.component,
                record.defect_type,
                record.location_x,
                record.location_y,
                json.dumps(record.bbox),
                record.bbox_width,
                record.bbox_height,
                record.bbox_area,
                record.first_seen,
                record.last_seen,
                record.current_confidence,
                record.current_severity.value,
                record.status.value,
                record.detection_count,
                record.notes,
            ))
            
            # Also log initial observation in the timeline
            if inspection_id:
                cursor.execute("""
                    INSERT INTO observations (
                        defect_id, inspection_id, timestamp, confidence,
                        bbox, area, severity, growth_rate, status_at_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.defect_id,
                    inspection_id,
                    timestamp,
                    record.current_confidence,
                    json.dumps(record.bbox),
                    record.bbox_area,
                    record.current_severity.value,
                    0.0,
                    record.status.value,
                ))

            conn.commit()

        return record

    def get_defect_record(self, defect_id: str) -> Optional[DefectRecord]:
        """Fetch a single defect record by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM defects WHERE defect_id = ?", (defect_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_defect(row)

    def list_defects_by_aircraft(
        self, aircraft_id: str, component: Optional[str] = None
    ) -> List[DefectRecord]:
        """List all defect records for an aircraft."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if component:
                cursor.execute(
                    "SELECT * FROM defects WHERE aircraft_id = ? AND component = ? ORDER BY first_seen DESC",
                    (aircraft_id, component),
                )
            else:
                cursor.execute(
                    "SELECT * FROM defects WHERE aircraft_id = ? ORDER BY first_seen DESC",
                    (aircraft_id,),
                )
            return [self._row_to_defect(row) for row in cursor.fetchall()]

    def update_defect_record(
        self,
        defect_id: str,
        bbox: List[float],
        confidence: float,
        timestamp: str,
        inspection_id: str,
        status: DefectStatus = DefectStatus.PROGRESSING,
    ) -> DefectRecord:
        """Update existing defect record when re-detected in a new inspection."""
        existing = self.get_defect_record(defect_id)
        if not existing:
            raise ValueError(f"Defect {defect_id} does not exist")

        x1, y1, x2, y2 = bbox
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        centroid_x = (x1 + x2) / 2.0
        centroid_y = (y1 + y2) / 2.0
        new_area = width * height

        # Calculate growth rate compared to previous observation
        growth_rate = 0.0
        if existing.bbox_area > 0:
            growth_rate = ((new_area - existing.bbox_area) / existing.bbox_area) * 100.0

        new_severity = assess_severity(existing.defect_type, bbox, confidence)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE defects SET
                    location_x = ?,
                    location_y = ?,
                    bbox = ?,
                    bbox_width = ?,
                    bbox_height = ?,
                    bbox_area = ?,
                    last_seen = ?,
                    current_confidence = ?,
                    current_severity = ?,
                    status = ?,
                    detection_count = detection_count + 1
                WHERE defect_id = ?
            """, (
                round(centroid_x, 4),
                round(centroid_y, 4),
                json.dumps([round(coord, 2) for coord in bbox]),
                round(width, 2),
                round(height, 2),
                round(new_area, 2),
                timestamp,
                round(confidence, 3),
                new_severity.value,
                status.value,
                defect_id,
            ))

            # Record timeline entry
            cursor.execute("""
                INSERT INTO observations (
                    defect_id, inspection_id, timestamp, confidence,
                    bbox, area, severity, growth_rate, status_at_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                defect_id,
                inspection_id,
                timestamp,
                round(confidence, 3),
                json.dumps([round(coord, 2) for coord in bbox]),
                round(new_area, 2),
                new_severity.value,
                round(growth_rate, 2),
                status.value,
            ))
            conn.commit()

        return self.get_defect_record(defect_id)

    def get_defect_timeline(self, defect_id: str) -> List[ObservationRecord]:
        """Fetch chronological timeline for a defect (Part 5)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM observations WHERE defect_id = ? ORDER BY timestamp ASC",
                (defect_id,),
            )
            timeline = []
            for row in cursor.fetchall():
                timeline.append(
                    ObservationRecord(
                        observation_id=row["observation_id"],
                        defect_id=row["defect_id"],
                        inspection_id=row["inspection_id"],
                        timestamp=row["timestamp"],
                        confidence=row["confidence"],
                        bbox=json.loads(row["bbox"]),
                        area=row["area"],
                        severity=SeverityLevel(row["severity"]),
                        growth_rate=row["growth_rate"],
                        status_at_time=DefectStatus(row["status_at_time"]),
                    )
                )
            return timeline

    def _row_to_defect(self, row: sqlite3.Row) -> DefectRecord:
        return DefectRecord(
            defect_id=row["defect_id"],
            aircraft_id=row["aircraft_id"],
            component=row["component"],
            defect_type=row["defect_type"],
            location_x=row["location_x"],
            location_y=row["location_y"],
            bbox=json.loads(row["bbox"]),
            bbox_width=row["bbox_width"],
            bbox_height=row["bbox_height"],
            bbox_area=row["bbox_area"],
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            current_confidence=row["current_confidence"],
            current_severity=SeverityLevel(row["current_severity"]),
            status=DefectStatus(row["status"]),
            detection_count=row["detection_count"],
            notes=row["notes"] or "",
        )
