"""
API routes for signal ingestion and retrieval.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.signal import SignalEventRequest, SignalEventResponse, CoherenceScore, DriftMetric
from app.services.signal_service import SignalService
from app.services.drift_detection import DriftDetectionService

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/ingest", response_model=SignalEventResponse)
async def ingest_signal(
    signal: SignalEventRequest,
    db: Session = Depends(get_db)
) -> SignalEventResponse:
    """
    Ingest a new signal event.

    Expected input:
    ```json
    {
        "agent": "Axis",
        "user_state": "calm",
        "signal_strength": 0.83,
        "timestamp": "2025-10-31T09:10:00Z",
        "biometric_data": {"hrv": 65, "gsr": 2.3}
    }
    ```
    """
    try:
        # Store signal
        stored_signal = SignalService.store_signal(
            db=db,
            agent=signal.agent,
            user_state=signal.user_state,
            signal_strength=signal.signal_strength,
            timestamp=signal.timestamp,
            biometric_data=signal.biometric_data
        )

        # Check for drift
        variance, is_anomaly, severity = DriftDetectionService.detect_drift(
            db=db,
            agent=signal.agent,
            current_value=signal.signal_strength
        )

        # Record anomaly if detected
        if is_anomaly:
            baseline = DriftDetectionService.calculate_baseline(db, signal.agent)
            DriftDetectionService.record_anomaly(
                db=db,
                agent=signal.agent,
                signal_event_id=stored_signal.id,
                variance_percent=variance,
                severity=severity,
                baseline_value=baseline or signal.signal_strength
            )

        return SignalEventResponse.model_validate(stored_signal)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest signal: {str(e)}")


@router.get("/recent", response_model=List[SignalEventResponse])
async def get_recent_signals(
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    minutes: int = Query(30, ge=1, le=1440, description="Time window in minutes"),
    limit: int = Query(100, ge=1, le=1000, description="Max results to return"),
    db: Session = Depends(get_db)
) -> List[SignalEventResponse]:
    """
    Get recent signals, optionally filtered by agent.

    Query parameters:
    - `agent`: Optional agent name to filter by
    - `minutes`: Time window (default 30, max 1440)
    - `limit`: Maximum results (default 100, max 1000)
    """
    signals = SignalService.get_recent_signals(
        db=db,
        agent=agent,
        minutes=minutes,
        limit=limit
    )
    return [SignalEventResponse.model_validate(s) for s in signals]


@router.get("/agents", response_model=List[str])
async def list_agents(db: Session = Depends(get_db)) -> List[str]:
    """Get list of all agents with signals."""
    result = SignalService.get_agent_list(db)
    return [agent[0] for agent in result]


@router.get("/drift/{agent}", response_model=DriftMetric)
async def get_agent_drift(
    agent: str,
    db: Session = Depends(get_db)
) -> DriftMetric:
    """
    Get current drift metrics for a specific agent.

    Returns:
    - `baseline_value`: Moving baseline from recent signals
    - `current_value`: Latest signal value
    - `variance_percent`: Percentage variance from baseline
    - `is_anomaly`: Whether current state is anomalous
    - `severity`: "green" (stable), "yellow" (warning), "red" (critical)
    """
    # Get latest signal
    recent = SignalService.get_recent_signals(db, agent, minutes=1)
    if not recent:
        raise HTTPException(status_code=404, detail=f"No recent signals for agent {agent}")

    latest_signal = recent[0]
    baseline = DriftDetectionService.calculate_baseline(db, agent)

    variance, is_anomaly, severity = DriftDetectionService.detect_drift(
        db=db,
        agent=agent,
        current_value=latest_signal.signal_strength,
        baseline_value=baseline
    )

    return DriftMetric(
        agent=agent,
        timestamp=datetime.utcnow(),
        baseline_value=baseline or 0.0,
        current_value=latest_signal.signal_strength,
        variance_percent=variance,
        is_anomaly=is_anomaly,
        severity=severity
    )


@router.get("/drift/{agent}/trend", response_model=dict)
async def get_drift_trend(
    agent: str,
    minutes: int = Query(30, ge=1, le=1440),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get drift trend for an agent over specified time period.

    Returns:
    - `avg_variance`: Average variance in period
    - `max_variance`: Peak variance
    - `anomaly_count`: Number of anomalies detected
    - `trend`: "stable", "degrading", or "recovering"
    """
    trend = DriftDetectionService.calculate_drift_trend(db, agent, minutes)
    return trend


@router.get("/coherence/{agent}", response_model=CoherenceScore)
async def get_agent_coherence(
    agent: str,
    minutes: int = Query(30, ge=1, le=1440),
    db: Session = Depends(get_db)
) -> CoherenceScore:
    """
    Get coherence score for a specific agent.

    Coherence combines signal strength with drift assessment.
    Degrading trends reduce the score; recovering trends have smaller penalty.
    """
    return SignalService.calculate_coherence_score(db, agent, minutes)


@router.get("/summary", response_model=List[CoherenceScore])
async def get_all_agents_summary(
    minutes: int = Query(30, ge=1, le=1440),
    db: Session = Depends(get_db)
) -> List[CoherenceScore]:
    """
    Get coherence summary for all agents with active signals.

    Useful for dashboards and system-wide monitoring.
    """
    return SignalService.get_all_agents_summary(db, minutes)


@router.get("/anomalies", response_model=List[dict])
async def get_anomalies(
    agent: Optional[str] = Query(None),
    minutes: int = Query(30, ge=1, le=1440),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Get recent anomalies, optionally filtered by agent.

    Returns detected signal anomalies with severity levels.
    """
    anomalies = DriftDetectionService.get_recent_anomalies(db, agent, minutes)
    return [
        {
            "id": a.id,
            "agent": a.agent,
            "variance_percent": a.variance_percent,
            "severity": a.severity,
            "baseline_value": a.baseline_value,
            "detected_at": a.detected_at.isoformat()
        }
        for a in anomalies
    ]
