from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Aircraft(Base):
    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    aircraft_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    aircraft_type: Mapped[str | None] = mapped_column(String(100))
    registration_number: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    components: Mapped[list["Component"]] = relationship(
        back_populates="aircraft",
        cascade="all, delete-orphan",
    )
    tracked_defects: Mapped[list["TrackedDefect"]] = relationship(
        back_populates="aircraft",
        cascade="all, delete-orphan",
    )


class Component(Base):
    __tablename__ = "component"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    aircraft_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("aircraft.id", ondelete="CASCADE"),
        nullable=False,
    )
    component_code: Mapped[str] = mapped_column(String(100), nullable=False)
    component_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    aircraft: Mapped["Aircraft"] = relationship(back_populates="components")
    panels: Mapped[list["Panel"]] = relationship(
        back_populates="component",
        cascade="all, delete-orphan",
    )
    tracked_defects: Mapped[list["TrackedDefect"]] = relationship(
        back_populates="component",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("aircraft_id", "component_code"),
    )


class Panel(Base):
    __tablename__ = "panel"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    component_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("component.id", ondelete="CASCADE"),
        nullable=False,
    )
    panel_code: Mapped[str] = mapped_column(String(100), nullable=False)
    panel_location: Mapped[str | None] = mapped_column(String(255))
    material: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    component: Mapped["Component"] = relationship(back_populates="panels")
    inspections: Mapped[list["Inspection"]] = relationship(
        back_populates="panel",
        cascade="all, delete-orphan",
    )
    tracked_defects: Mapped[list["TrackedDefect"]] = relationship(
        back_populates="panel",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("component_id", "panel_code"),
    )


class Inspection(Base):
    __tablename__ = "inspection"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    panel_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("panel.id", ondelete="CASCADE"),
        nullable=False,
    )
    inspection_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    inspection_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    inspector_name: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(
        String(50),
        default="completed",
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    panel: Mapped["Panel"] = relationship(back_populates="inspections")
    images: Mapped[list["InspectionImage"]] = relationship(
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    observations: Mapped[list["DefectObservation"]] = relationship(
        back_populates="inspection",
        cascade="all, delete-orphan",
    )


class InspectionImage(Base):
    __tablename__ = "inspection_image"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    inspection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspection.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    image_width: Mapped[int | None] = mapped_column(Integer)
    image_height: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    inspection: Mapped["Inspection"] = relationship(back_populates="images")
    detections: Mapped[list["Detection"]] = relationship(
        back_populates="inspection_image",
        cascade="all, delete-orphan",
    )


class Detection(Base):
    __tablename__ = "detection"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    inspection_image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspection_image.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_x: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_y: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_width: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_height: Mapped[float] = mapped_column(Double, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    inspection_image: Mapped["InspectionImage"] = relationship(
        back_populates="detections"
    )
    decision_support: Mapped[list["DecisionSupport"]] = relationship(
        back_populates="detection",
        cascade="all, delete-orphan",
    )
    observations: Mapped[list["DefectObservation"]] = relationship(
        back_populates="detection",
    )


class DecisionSupport(Base):
    __tablename__ = "decision_support"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    detection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("detection.id", ondelete="CASCADE"),
        nullable=False,
    )
    severity: Mapped[str | None] = mapped_column(String(50))
    progression_status: Mapped[str | None] = mapped_column(String(100))
    recommended_action: Mapped[str | None] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    detection: Mapped["Detection"] = relationship(
        back_populates="decision_support"
    )


class TrackedDefect(Base):
    __tablename__ = "tracked_defect"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    defect_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    aircraft_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("aircraft.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("component.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    panel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("panel.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    location_x: Mapped[float] = mapped_column(Double, nullable=False)
    location_y: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_x: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_y: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_width: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_height: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_area: Mapped[float] = mapped_column(Double, nullable=False)
    first_seen_inspection_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("inspection.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_seen_inspection_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("inspection.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="NEW",
        nullable=False,
        index=True,
    )
    current_severity: Mapped[str] = mapped_column(
        String(50),
        default="Medium",
        nullable=False,
    )
    current_confidence: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        default=0.0,
    )
    detection_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    aircraft: Mapped["Aircraft"] = relationship(
        back_populates="tracked_defects"
    )
    component: Mapped["Component | None"] = relationship(
        back_populates="tracked_defects"
    )
    panel: Mapped["Panel | None"] = relationship(
        back_populates="tracked_defects"
    )
    first_seen_inspection: Mapped["Inspection | None"] = relationship(
        foreign_keys=[first_seen_inspection_id]
    )
    last_seen_inspection: Mapped["Inspection | None"] = relationship(
        foreign_keys=[last_seen_inspection_id]
    )
    observations: Mapped[list["DefectObservation"]] = relationship(
        back_populates="tracked_defect",
        cascade="all, delete-orphan",
    )


class DefectObservation(Base):
    __tablename__ = "defect_observation"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    tracked_defect_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tracked_defect.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inspection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inspection_image_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("inspection_image.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    detection_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("detection.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_x: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_y: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_width: Mapped[float] = mapped_column(Double, nullable=False)
    bbox_height: Mapped[float] = mapped_column(Double, nullable=False)
    area: Mapped[float] = mapped_column(Double, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    progression_state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NEW",
    )
    growth_rate_pct: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        default=0.0,
    )
    measurement_delta: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )
    dimension_unit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    measurements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tracked_defect: Mapped["TrackedDefect"] = relationship(
        back_populates="observations"
    )
    inspection: Mapped["Inspection"] = relationship(
        back_populates="observations"
    )
    inspection_image: Mapped["InspectionImage | None"] = relationship()
    detection: Mapped["Detection | None"] = relationship(
        back_populates="observations"
    )