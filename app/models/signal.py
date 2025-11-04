"""
Data models for signal events and metrics.
"""
import json
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Pydantic Models (API Request/Response)
class UserState(str, Enum):
    """Enum for user emotional/cognitive states."""
    calm = "calm"
    neutral = "neutral"
    anxious = "anxious"
    engaged = "engaged"
    fatigued = "fatigued"


class SignalEventRequest(BaseModel):
    """Schema for incoming signal event."""
    agent: str = Field(..., min_length=1, max_length=100)
    user_state: UserState
    signal_strength: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime
    biometric_data: Optional[Union[dict, str]] = None  # HRV, GSR, etc.

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "Axis",
                "user_state": "calm",
                "signal_strength": 0.83,
                "timestamp": "2025-10-31T09:10:00Z",
                "biometric_data": {"hrv": 65, "gsr": 2.3}
            }
        }

    @field_validator("biometric_data", mode="before")
    @classmethod
    def parse_biometric_data(cls, v):
        """Convert JSON string to dict if needed."""
        if isinstance(v, str) and v:
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v


class SignalEventResponse(SignalEventRequest):
    """Response schema for stored signal event."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("biometric_data", mode="before")
    @classmethod
    def parse_biometric_data_response(cls, v):
        """Convert JSON string to dict if needed in response."""
        if isinstance(v, str) and v:
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v


class DriftMetric(BaseModel):
    """Drift detection metric."""
    agent: str
    timestamp: datetime
    baseline_value: float
    current_value: float
    variance_percent: float
    is_anomaly: bool
    severity: str = Field(..., pattern="^(green|yellow|red)$")  # green/yellow/red


class CoherenceScore(BaseModel):
    """Aggregated coherence score per agent."""
    agent: str
    timestamp: datetime
    coherence_score: float = Field(..., ge=0.0, le=1.0)
    drift_status: str
    signal_count: int
    avg_signal_strength: float


# SQLAlchemy Models (Database)
Base = declarative_base()


class SignalEvent(Base):
    """ORM model for signal events in database."""
    __tablename__ = "signal_events"

    id = Column(Integer, primary_key=True, index=True)
    agent = Column(String(100), index=True)
    user_state = Column(String(50))
    signal_strength = Column(Float)
    timestamp = Column(DateTime, index=True)
    biometric_data = Column(String, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AnomalyRecord(Base):
    """ORM model for detected anomalies."""
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    agent = Column(String(100), index=True)
    signal_event_id = Column(Integer, index=True)
    variance_percent = Column(Float)
    severity = Column(String(10))  # green/yellow/red
    baseline_value = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)


class DriftBaseline(Base):
    """ORM model for baseline metrics used in drift detection."""
    __tablename__ = "drift_baselines"

    id = Column(Integer, primary_key=True, index=True)
    agent = Column(String(100), index=True, unique=True)
    baseline_value = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    signal_count = Column(Integer, default=0)
