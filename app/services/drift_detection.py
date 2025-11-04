"""
Drift detection and anomaly scoring service.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models.signal import SignalEvent, AnomalyRecord, DriftBaseline
from app.config import (
    DRIFT_WINDOW_MINUTES,
    DRIFT_THRESHOLD_PERCENT,
    ANOMALY_THRESHOLD_PERCENT,
    MIN_SIGNALS_FOR_BASELINE
)


class DriftDetectionService:
    """Service for detecting signal drift and anomalies."""

    @staticmethod
    def calculate_baseline(db: Session, agent: str) -> Optional[float]:
        """
        Calculate rolling baseline for an agent from recent signals.
        Uses signals from the past DRIFT_WINDOW_MINUTES.
        """
        window_start = datetime.utcnow() - timedelta(minutes=DRIFT_WINDOW_MINUTES)

        signals = db.query(SignalEvent).filter(
            SignalEvent.agent == agent,
            SignalEvent.timestamp >= window_start
        ).order_by(SignalEvent.timestamp.desc()).all()

        if len(signals) < MIN_SIGNALS_FOR_BASELINE:
            return None

        values = [s.signal_strength for s in signals]
        return float(np.mean(values))

    @staticmethod
    def detect_drift(
        db: Session,
        agent: str,
        current_value: float,
        baseline_value: Optional[float] = None
    ) -> Tuple[float, bool, str]:
        """
        Detect drift in signal strength.

        Returns:
            - variance_percent: Percentage variance from baseline
            - is_anomaly: Boolean indicating if anomaly detected
            - severity: "green", "yellow", or "red"
        """
        if baseline_value is None:
            baseline_value = DriftDetectionService.calculate_baseline(db, agent)

        # If no baseline established yet, assume no drift
        if baseline_value is None:
            return 0.0, False, "green"

        # Calculate variance
        variance = abs(current_value - baseline_value) / baseline_value * 100 if baseline_value != 0 else 0

        # Determine severity and anomaly status
        if variance >= ANOMALY_THRESHOLD_PERCENT:
            severity = "red"
            is_anomaly = True
        elif variance >= DRIFT_THRESHOLD_PERCENT:
            severity = "yellow"
            is_anomaly = False
        else:
            severity = "green"
            is_anomaly = False

        return variance, is_anomaly, severity

    @staticmethod
    def record_anomaly(
        db: Session,
        agent: str,
        signal_event_id: int,
        variance_percent: float,
        severity: str,
        baseline_value: float
    ) -> AnomalyRecord:
        """Record detected anomaly in database."""
        anomaly = AnomalyRecord(
            agent=agent,
            signal_event_id=signal_event_id,
            variance_percent=variance_percent,
            severity=severity,
            baseline_value=baseline_value
        )
        db.add(anomaly)
        db.commit()
        db.refresh(anomaly)
        return anomaly

    @staticmethod
    def get_recent_anomalies(
        db: Session,
        agent: Optional[str] = None,
        minutes: int = 30
    ) -> list:
        """Get recent anomalies."""
        window_start = datetime.utcnow() - timedelta(minutes=minutes)

        query = db.query(AnomalyRecord).filter(
            AnomalyRecord.detected_at >= window_start
        )

        if agent:
            query = query.filter(AnomalyRecord.agent == agent)

        return query.order_by(AnomalyRecord.detected_at.desc()).all()

    @staticmethod
    def calculate_drift_trend(
        db: Session,
        agent: str,
        minutes: int = 30
    ) -> dict:
        """
        Calculate drift trend metrics for an agent over time.

        Returns:
            - avg_variance: Average variance in period
            - max_variance: Peak variance
            - anomaly_count: Number of anomalies detected
            - trend: "stable", "degrading", or "recovering"
        """
        window_start = datetime.utcnow() - timedelta(minutes=minutes)

        anomalies = db.query(AnomalyRecord).filter(
            AnomalyRecord.agent == agent,
            AnomalyRecord.detected_at >= window_start
        ).all()

        if not anomalies:
            return {
                "avg_variance": 0.0,
                "max_variance": 0.0,
                "anomaly_count": 0,
                "trend": "stable"
            }

        variances = [a.variance_percent for a in anomalies]

        # Simple trend detection: compare first half vs second half
        mid_point = len(anomalies) // 2
        first_half_avg = np.mean(variances[:mid_point]) if mid_point > 0 else 0
        second_half_avg = np.mean(variances[mid_point:]) if len(variances) - mid_point > 0 else 0

        if second_half_avg > first_half_avg * 1.1:
            trend = "degrading"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "recovering"
        else:
            trend = "stable"

        return {
            "avg_variance": float(np.mean(variances)),
            "max_variance": float(np.max(variances)),
            "anomaly_count": len(anomalies),
            "trend": trend
        }
