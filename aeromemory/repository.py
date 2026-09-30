"""Repository layer for AeroMemory storage and retrieval.

Abstracts database operations (SQLite by default, easily extensible to PostgreSQL)
so the AeroMemory domain logic remains completely decoupled from SQL queries.
"""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from aeromemory.models import (
    DefectMeasurement,
    DefectRecord,
    DefectStatus,
    InspectionRecord,
    ObservationRecord,
    SeverityLevel,
)


class AeroMemoryRepository(ABC):
    """Abstract interface defining required persistence contracts."""

    @abstractmethod
    def save_inspection(self, inspection: InspectionRecord) -> None:
        pass

    @abstractmethod
    def get_inspection(self, inspection_id: str) -> Optional[InspectionRecord]:
        pass

    @abstractmethod
    def get_previous_inspection(
        self,
        aircraft_id: str,
        component: Optional[str] = None,
        before_timestamp: Optional[str] = None,
        exclude_id: Optional[str] = None,
    ) -> Optional[InspectionRecord]:
        pass

    @abstractmethod
    def save_defect(self, defect: DefectRecord) -> None:
        pass

    @abstractmethod
    def update_defect(self, defect: DefectRecord) -> None:
        pass

    @abstractmethod
    def get_defect(self, defect_id: str) -> Optional[DefectRecord]:
        pass

    @abstractmethod
    def get_active_defects(
        self, aircraft_id: str, component: Optional[str] = None
    ) -> List[DefectRecord]:
        pass

    @abstractmethod
    def save_observation(self, observation: ObservationRecord) -> None:
        pass

    @abstractmethod
    def get_defect_timeline(self, defect_id: str) -> List[ObservationRecord]:
        pass

    @abstractmethod
    def next_defect_id(self, prefix: str = "DEF") -> str:
        pass


class SQLiteAeroMemoryRepository(AeroMemoryRepository):
    """SQLite implementation of AeroMemory persistence for local/offline workflows."""

    def __init__(self, db_path: str | Path = "aeromemory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    inspection_id TEXT PRIMARY KEY,
                    aircraft_id TEXT NOT NULL,
                    aircraft_model TEXT,
                    component TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    original_image_path TEXT,
                    annotated_image_path TEXT,
                    panel_id TEXT,
                    defect_count INTEGER DEFAULT 0,
                    inspection_status TEXT DEFAULT 'COMPLETED'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS defects (
                    defect_id TEXT PRIMARY KEY,
                    aircraft_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    panel_id TEXT,
                    defect_type TEXT NOT NULL,
                    location_x REAL NOT NULL,
                    location_y REAL NOT NULL,
                    bbox TEXT NOT NULL,
                    bbox_width REAL NOT NULL,
                    bbox_height REAL NOT NULL,
                    bbox_area REAL NOT NULL,
                    measurements TEXT DEFAULT '{}',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    current_confidence REAL NOT NULL,
                    current_severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detection_count INTEGER DEFAULT 1,
                    notes TEXT DEFAULT ''
                )
            """)

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
                    measurements TEXT DEFAULT '{}',
                    FOREIGN KEY (defect_id) REFERENCES defects(defect_id),
                    FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
                )
            """)
            conn.commit()

    def save_inspection(self, inspection: InspectionRecord) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO inspections (
                    inspection_id, aircraft_id, aircraft_model, component,
                    timestamp, original_image_path, annotated_image_path,
                    panel_id, defect_count, inspection_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inspection.inspection_id,
                inspection.aircraft_id,
                inspection.aircraft_model,
                inspection.component,
                inspection.timestamp,
                inspection.original_image_path,
                inspection.annotated_image_path,
                inspection.panel_id,
                inspection.defect_count,
                inspection.inspection_status,
            ))
            conn.commit()

    def get_inspection(self, inspection_id: str) -> Optional[InspectionRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return InspectionRecord(
                inspection_id=row["inspection_id"],
                aircraft_id=row["aircraft_id"],
                aircraft_model=row["aircraft_model"] or "",
                component=row["component"],
                timestamp=row["timestamp"],
                original_image_path=row["original_image_path"],
                annotated_image_path=row["annotated_image_path"],
                panel_id=row["panel_id"],
                defect_count=row["defect_count"],
                inspection_status=row["inspection_status"],
            )

    def get_previous_inspection(
        self,
        aircraft_id: str,
        component: Optional[str] = None,
        before_timestamp: Optional[str] = None,
        exclude_id: Optional[str] = None,
    ) -> Optional[InspectionRecord]:
        query = "SELECT * FROM inspections WHERE aircraft_id = ?"
        params: List[Any] = [aircraft_id]

        if component:
            query += " AND component = ?"
            params.append(component)
        if before_timestamp:
            query += " AND timestamp < ?"
            params.append(before_timestamp)
        if exclude_id:
            query += " AND inspection_id != ?"
            params.append(exclude_id)

        query += " ORDER BY timestamp DESC LIMIT 1"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row:
                return None
            return InspectionRecord(
                inspection_id=row["inspection_id"],
                aircraft_id=row["aircraft_id"],
                aircraft_model=row["aircraft_model"] or "",
                component=row["component"],
                timestamp=row["timestamp"],
                original_image_path=row["original_image_path"],
                annotated_image_path=row["annotated_image_path"],
                panel_id=row["panel_id"],
                defect_count=row["defect_count"],
                inspection_status=row["inspection_status"],
            )

    def save_defect(self, defect: DefectRecord) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO defects (
                    defect_id, aircraft_id, component, panel_id, defect_type,
                    location_x, location_y, bbox, bbox_width, bbox_height, bbox_area,
                    measurements, first_seen, last_seen, current_confidence, current_severity,
                    status, detection_count, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                defect.defect_id,
                defect.aircraft_id,
                defect.component,
                defect.panel_id,
                defect.defect_type,
                defect.location_x,
                defect.location_y,
                json.dumps(defect.bbox),
                defect.bbox_width,
                defect.bbox_height,
                defect.bbox_area,
                json.dumps(defect.measurements.to_dict()),
                defect.first_seen,
                defect.last_seen,
                defect.current_confidence,
                defect.current_severity.value if isinstance(defect.current_severity, SeverityLevel) else defect.current_severity,
                defect.status.value if isinstance(defect.status, DefectStatus) else defect.status,
                defect.detection_count,
                defect.notes or "",
            ))
            conn.commit()

    def update_defect(self, defect: DefectRecord) -> None:
        self.save_defect(defect)

    def get_defect(self, defect_id: str) -> Optional[DefectRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM defects WHERE defect_id = ?", (defect_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_defect(row)

    def get_active_defects(
        self, aircraft_id: str, component: Optional[str] = None
    ) -> List[DefectRecord]:
        query = "SELECT * FROM defects WHERE aircraft_id = ? AND status NOT IN ('Closed', 'Repaired')"
        params: List[Any] = [aircraft_id]
        if component:
            query += " AND component = ?"
            params.append(component)
        query += " ORDER BY first_seen ASC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [self._row_to_defect(r) for r in cursor.fetchall()]

    def save_observation(self, observation: ObservationRecord) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO observations (
                    defect_id, inspection_id, timestamp, confidence,
                    bbox, area, severity, growth_rate, status_at_time, measurements
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation.defect_id,
                observation.inspection_id,
                observation.timestamp,
                observation.confidence,
                json.dumps(observation.bbox),
                observation.area,
                observation.severity.value if isinstance(observation.severity, SeverityLevel) else observation.severity,
                observation.growth_rate,
                observation.status_at_time.value if isinstance(observation.status_at_time, DefectStatus) else observation.status_at_time,
                json.dumps(observation.measurements or {}),
            ))
            conn.commit()

    def get_defect_timeline(
        self, defect_id: str, aircraft_id: Optional[str] = None
    ) -> List[ObservationRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if aircraft_id:
                cursor.execute("""
                    SELECT o.* FROM observations o
                    JOIN defects d ON o.defect_id = d.defect_id
                    WHERE o.defect_id = ? AND d.aircraft_id = ?
                    ORDER BY o.timestamp ASC
                """, (defect_id, aircraft_id))
            else:
                cursor.execute(
                    "SELECT * FROM observations WHERE defect_id = ? ORDER BY timestamp ASC",
                    (defect_id,),
                )
            timeline = []
            for row in cursor.fetchall():
                measurements = {}
                if "measurements" in row.keys() and row["measurements"]:
                    try:
                        measurements = json.loads(row["measurements"])
                    except Exception:
                        pass

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
                        measurements=measurements,
                    )
                )
            return timeline

    def next_defect_id(self, prefix: str = "DEF") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM defects")
            count = cursor.fetchone()["total"] + 1
            return f"{prefix}-{count:03d}"

    def _row_to_defect(self, row: sqlite3.Row) -> DefectRecord:
        m_dict = {}
        if "measurements" in row.keys() and row["measurements"]:
            try:
                m_dict = json.loads(row["measurements"])
            except Exception:
                pass

        measurements = DefectMeasurement(**m_dict) if m_dict else DefectMeasurement()

        return DefectRecord(
            defect_id=row["defect_id"],
            aircraft_id=row["aircraft_id"],
            component=row["component"],
            panel_id=row["panel_id"] if "panel_id" in row.keys() else None,
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
            measurements=measurements,
            notes=row["notes"] or "",
        )
