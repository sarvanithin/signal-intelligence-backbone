"""
Signal storage and retrieval service.
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.signal import SignalEvent, CoherenceScore
from app.services.drift_detection import DriftDetectionService


class SignalService:
    """Service for storing and querying signals."""

    @staticmethod
    def store_signal(
        db: Session,
        agent: str,
        user_state: str,
        signal_strength: float,
        timestamp: datetime,
        biometric_data: Optional[dict] = None
    ) -> SignalEvent:
        """Store a signal event in the database."""
        signal = SignalEvent(
            agent=agent,
            user_state=user_state,
            signal_strength=signal_strength,
            timestamp=timestamp,
            biometric_data=json.dumps(biometric_data) if biometric_data else None
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        return signal

    @staticmethod
    def get_recent_signals(
        db: Session,
        agent: Optional[str] = None,
        minutes: int = 30,
        limit: int = 100
    ) -> List[SignalEvent]:
        """Get recent signals, optionally filtered by agent."""
        window_start = datetime.utcnow() - timedelta(minutes=minutes)

        query = db.query(SignalEvent).filter(
            SignalEvent.timestamp >= window_start
        )

        if agent:
            query = query.filter(SignalEvent.agent == agent)

        return query.order_by(
            SignalEvent.timestamp.desc()
        ).limit(limit).all()

    @staticmethod
    def get_signals_by_time_range(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        agent: Optional[str] = None
    ) -> List[SignalEvent]:
        """Get signals within a specific time range."""
        query = db.query(SignalEvent).filter(
            SignalEvent.timestamp >= start_time,
            SignalEvent.timestamp <= end_time
        )

        if agent:
            query = query.filter(SignalEvent.agent == agent)

        return query.order_by(SignalEvent.timestamp.asc()).all()

    @staticmethod
    def get_agent_list(db: Session) -> List[str]:
        """Get list of all agents with signals."""
        return db.query(SignalEvent.agent).distinct().all()

    @staticmethod
    def calculate_coherence_score(
        db: Session,
        agent: str,
        minutes: int = 30
    ) -> CoherenceScore:
        """
        Calculate aggregated coherence score for an agent.
        Coherence = average signal strength adjusted for drift severity.
        """
        signals = SignalService.get_recent_signals(db, agent, minutes)

        if not signals:
            return CoherenceScore(
                agent=agent,
                timestamp=datetime.utcnow(),
                coherence_score=0.0,
                drift_status="unknown",
                signal_count=0,
                avg_signal_strength=0.0
            )

        avg_strength = sum(s.signal_strength for s in signals) / len(signals)

        # Get drift information
        drift_info = DriftDetectionService.calculate_drift_trend(db, agent, minutes)

        # Adjust coherence score based on drift
        coherence = avg_strength
        if drift_info["trend"] == "degrading":
            coherence *= 0.85  # 15% penalty for degrading
        elif drift_info["trend"] == "recovering":
            coherence *= 0.95  # 5% penalty for recovering (better)

        # Cap at 1.0
        coherence = min(coherence, 1.0)

        # Determine drift status from trend
        if drift_info["max_variance"] > 20:
            drift_status = "critical"
        elif drift_info["max_variance"] > 15:
            drift_status = "warning"
        elif drift_info["max_variance"] > 10:
            drift_status = "caution"
        else:
            drift_status = "stable"

        return CoherenceScore(
            agent=agent,
            timestamp=datetime.utcnow(),
            coherence_score=coherence,
            drift_status=drift_status,
            signal_count=len(signals),
            avg_signal_strength=avg_strength
        )

    @staticmethod
    def get_all_agents_summary(
        db: Session,
        minutes: int = 30
    ) -> List[CoherenceScore]:
        """Get coherence summary for all agents."""
        agents_result = db.query(SignalEvent.agent).distinct().all()
        agents = [a[0] for a in agents_result]

        summaries = []
        for agent in agents:
            summary = SignalService.calculate_coherence_score(db, agent, minutes)
            summaries.append(summary)

        return summaries
