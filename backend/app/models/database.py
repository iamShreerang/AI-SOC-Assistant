"""SQLAlchemy ORM models for Supabase PostgreSQL."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

from app.schemas.enums import LogSeverity, AlertSeverity, AlertStatus, IncidentStatus, UserRole

Base = declarative_base()

# Helper: tell SQLAlchemy to use enum .value (lowercase) not .name (uppercase)
_use_values = lambda x: [e.value for e in x]


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role", values_callable=_use_values), nullable=False, default=UserRole.ANALYST)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    incidents = relationship("Incident", back_populates="assigned_user", foreign_keys="Incident.assigned_to")
    audit_logs = relationship("AuditLog", back_populates="user")


class Log(Base):
    """Security log model."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source = Column(String(255), nullable=False, index=True)
    severity = Column(SQLEnum(LogSeverity, name="log_severity", values_callable=_use_values), nullable=False, index=True)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    raw = Column(Text, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Alert(Base):
    """Security alert model."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    severity = Column(SQLEnum(AlertSeverity, name="alert_severity", values_callable=_use_values), nullable=False, index=True)
    source = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(AlertStatus, name="alert_status", values_callable=_use_values), nullable=False, default=AlertStatus.OPEN, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    incidents = relationship("Incident", secondary="incident_alerts", back_populates="alerts")
    ml_predictions = relationship("MLPrediction", back_populates="alert")


class Incident(Base):
    """Security incident model."""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(IncidentStatus, name="incident_status", values_callable=_use_values), nullable=False, default=IncidentStatus.OPEN, index=True)
    summary = Column(Text, nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assigned_user = relationship("User", back_populates="incidents", foreign_keys=[assigned_to])
    alerts = relationship("Alert", secondary="incident_alerts", back_populates="incidents")


class IncidentAlert(Base):
    """Many-to-many relationship between incidents and alerts."""
    __tablename__ = "incident_alerts"

    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MLPrediction(Base):
    """Machine learning prediction model."""
    __tablename__ = "ml_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True, index=True)
    model_version = Column(String(50), nullable=False)
    prediction = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    alert = relationship("Alert", back_populates="ml_predictions")


class ServiceHeartbeat(Base):
    """Tracks heartbeats from streaming pipeline services (Spark, etc.)."""
    __tablename__ = "service_heartbeats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service = Column(String(50), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="running")
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AuditLog(Base):
    """Audit log for tracking administrative actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
