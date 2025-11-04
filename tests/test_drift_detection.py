"""
Tests for drift detection service.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.signal import Base, SignalEvent
from app.services.drift_detection import DriftDetectionService


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def create_test_signal(
    db: Session,
    agent: str,
    signal_strength: float,
    offset_minutes: int = 0
) -> SignalEvent:
    """Helper to create test signals."""
    signal = SignalEvent(
        agent=agent,
        user_state="neutral",
        signal_strength=signal_strength,
        timestamp=datetime.utcnow() - timedelta(minutes=offset_minutes)
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


class TestDriftDetection:
    """Test cases for drift detection."""

    def test_baseline_calculation(self, test_db):
        """Test baseline calculation from multiple signals."""
        agent = "test_agent"

        # Create signals with values: 0.7, 0.75, 0.8
        for i, strength in enumerate([0.7, 0.75, 0.8]):
            create_test_signal(test_db, agent, strength, offset_minutes=i)

        baseline = DriftDetectionService.calculate_baseline(test_db, agent)
        assert baseline is not None
        assert 0.7 <= baseline <= 0.8
        assert abs(baseline - 0.75) < 0.05  # Should be around 0.75

    def test_baseline_insufficient_data(self, test_db):
        """Test baseline returns None with insufficient signals."""
        agent = "sparse_agent"

        # Create only 1 signal (below minimum of 5)
        create_test_signal(test_db, agent, 0.75)

        baseline = DriftDetectionService.calculate_baseline(test_db, agent)
        assert baseline is None

    def test_drift_detection_no_variance(self, test_db):
        """Test drift detection with stable signal."""
        agent = "stable_agent"

        # Create signals with stable values
        for i in range(5):
            create_test_signal(test_db, agent, 0.75, offset_minutes=i)

        variance, is_anomaly, severity = DriftDetectionService.detect_drift(
            test_db, agent, 0.76  # Minimal deviation
        )

        assert variance < 5.0  # Less than 5% variance
        assert not is_anomaly
        assert severity == "green"

    def test_drift_detection_warning_level(self, test_db):
        """Test drift detection at warning level."""
        agent = "drifting_agent"

        # Create baseline signals
        for i in range(5):
            create_test_signal(test_db, agent, 0.70, offset_minutes=i)

        # New signal with 16% variance (exceeds 15% threshold but below 20%)
        variance, is_anomaly, severity = DriftDetectionService.detect_drift(
            test_db, agent, 0.813  # ~16% above 0.70
        )

        assert 15.0 <= variance < 20.0
        assert not is_anomaly
        assert severity == "yellow"

    def test_drift_detection_critical_level(self, test_db):
        """Test drift detection at critical level."""
        agent = "critical_agent"

        # Create baseline signals
        for i in range(5):
            create_test_signal(test_db, agent, 0.70, offset_minutes=i)

        # New signal with 25% variance (exceeds 20% threshold)
        variance, is_anomaly, severity = DriftDetectionService.detect_drift(
            test_db, agent, 0.875  # ~25% above 0.70
        )

        assert variance >= 20.0
        assert is_anomaly
        assert severity == "red"

    def test_anomaly_recording(self, test_db):
        """Test anomaly recording in database."""
        agent = "anomaly_agent"
        signal_id = 1

        anomaly = DriftDetectionService.record_anomaly(
            test_db,
            agent=agent,
            signal_event_id=signal_id,
            variance_percent=25.5,
            severity="red",
            baseline_value=0.70
        )

        assert anomaly.id is not None
        assert anomaly.agent == agent
        assert anomaly.variance_percent == 25.5
        assert anomaly.severity == "red"

    def test_recent_anomalies_retrieval(self, test_db):
        """Test retrieving recent anomalies."""
        agent1 = "agent_a"
        agent2 = "agent_b"

        # Record multiple anomalies
        DriftDetectionService.record_anomaly(
            test_db, agent1, 1, 22.0, "red", 0.70
        )
        DriftDetectionService.record_anomaly(
            test_db, agent2, 2, 18.0, "yellow", 0.75
        )

        # Retrieve all recent anomalies
        all_anomalies = DriftDetectionService.get_recent_anomalies(test_db)
        assert len(all_anomalies) == 2

        # Filter by agent
        agent_a_anomalies = DriftDetectionService.get_recent_anomalies(test_db, agent1)
        assert len(agent_a_anomalies) == 1
        assert agent_a_anomalies[0].agent == agent1

    def test_drift_trend_calculation(self, test_db):
        """Test drift trend calculation."""
        agent = "trend_agent"

        # Create baseline signals
        for i in range(5):
            create_test_signal(test_db, agent, 0.70, offset_minutes=i * 2)

        # Record anomalies with increasing variance (degrading trend)
        for i in range(3):
            variance = 15.0 + (i * 2.5)  # 15%, 17.5%, 20%
            DriftDetectionService.record_anomaly(
                test_db, agent, i, variance, "yellow" if variance < 20 else "red", 0.70
            )

        trend = DriftDetectionService.calculate_drift_trend(test_db, agent)

        assert trend["anomaly_count"] == 3
        assert trend["max_variance"] >= 20.0
        assert trend["avg_variance"] > 15.0
        assert trend["trend"] in ["stable", "degrading", "recovering"]

    def test_no_anomalies_trend(self, test_db):
        """Test trend calculation with no anomalies."""
        agent = "clean_agent"

        trend = DriftDetectionService.calculate_drift_trend(test_db, agent)

        assert trend["anomaly_count"] == 0
        assert trend["avg_variance"] == 0.0
        assert trend["max_variance"] == 0.0
        assert trend["trend"] == "stable"
