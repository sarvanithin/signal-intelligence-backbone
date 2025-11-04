"""
Tests for FastAPI endpoints.
"""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.database import get_db
from app.models.signal import Base, SignalEventRequest


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def override_get_db(test_db):
    """Override database dependency."""
    def _get_db():
        yield test_db
    return _get_db


@pytest.fixture
def client(override_get_db):
    """Create test client."""
    app.dependency_overrides[get_db] = override_get_db
    client = AsyncClient(app=app, base_url="http://test")
    yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_ingest_valid_signal(client):
    """Test ingesting a valid signal."""
    signal = {
        "agent": "Axis",
        "user_state": "calm",
        "signal_strength": 0.85,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "biometric_data": {"hrv": 70, "gsr": 2.1}
    }

    response = await client.post("/signals/ingest", json=signal)
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "Axis"
    assert data["signal_strength"] == 0.85
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_ingest_invalid_signal_strength(client):
    """Test ingestion with invalid signal strength."""
    signal = {
        "agent": "Axis",
        "user_state": "calm",
        "signal_strength": 1.5,  # Invalid: >1.0
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    response = await client.post("/signals/ingest", json=signal)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_ingest_missing_field(client):
    """Test ingestion with missing required field."""
    signal = {
        "agent": "Axis",
        "user_state": "calm",
        # Missing signal_strength
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    response = await client.post("/signals/ingest", json=signal)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_agents(client):
    """Test listing agents."""
    # First, ingest signals for different agents
    for agent in ["Axis", "THEIA"]:
        signal = {
            "agent": agent,
            "user_state": "neutral",
            "signal_strength": 0.75,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await client.post("/signals/ingest", json=signal)

    response = await client.get("/signals/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) >= 2
    assert "Axis" in agents or any("Axis" in str(a) for a in agents)


@pytest.mark.asyncio
async def test_get_recent_signals(client):
    """Test getting recent signals."""
    # Ingest a signal
    signal = {
        "agent": "TestAgent",
        "user_state": "engaged",
        "signal_strength": 0.88,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    await client.post("/signals/ingest", json=signal)

    # Retrieve recent signals
    response = await client.get("/signals/recent?agent=TestAgent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["agent"] == "TestAgent"
    assert data[0]["signal_strength"] == 0.88


@pytest.mark.asyncio
async def test_get_drift_no_signals(client):
    """Test drift retrieval with no signals."""
    response = await client.get("/signals/drift/NonexistentAgent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_empty_agents(client):
    """Test listing agents when none exist."""
    response = await client.get("/signals/agents")
    assert response.status_code == 200
    agents = response.json()
    assert agents == []


@pytest.mark.asyncio
async def test_get_coherence_score(client):
    """Test coherence score calculation."""
    # Ingest multiple signals
    for i in range(5):
        signal = {
            "agent": "CoherentAgent",
            "user_state": "calm" if i % 2 == 0 else "neutral",
            "signal_strength": 0.75 + (i * 0.02),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await client.post("/signals/ingest", json=signal)

    response = await client.get("/signals/coherence/CoherentAgent")
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["coherence_score"] <= 1
    assert data["agent"] == "CoherentAgent"
    assert data["signal_count"] >= 5


@pytest.mark.asyncio
async def test_get_summary(client):
    """Test getting summary for all agents."""
    # Ingest signals for multiple agents
    for agent in ["Agent1", "Agent2"]:
        signal = {
            "agent": agent,
            "user_state": "neutral",
            "signal_strength": 0.80,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        await client.post("/signals/ingest", json=signal)

    response = await client.get("/signals/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_anomalies(client):
    """Test anomaly retrieval."""
    response = await client.get("/signals/anomalies")
    assert response.status_code == 200
    data = response.json()
    # Should return empty list if no anomalies
    assert isinstance(data, list)
