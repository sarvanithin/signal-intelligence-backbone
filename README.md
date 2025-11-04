# Signal Intelligence Backbone

Backend service for coherence tracking and signal integrity monitoring in multi-agent environments.

## Overview

The Signal Intelligence Backbone captures, validates, and visualizes agent–human interaction signals for coherence tracking. It detects signal drift, identifies anomalies, and provides real-time observability into system health.

**Key Features:**
- ✅ Real-time signal ingestion and validation (FastAPI)
- ✅ Rolling baseline drift detection (10-minute windows)
- ✅ Anomaly scoring with severity levels (green/yellow/red)
- ✅ Coherence scoring combining signal strength + drift assessment
- ✅ SQLite persistence (easily migrates to RDS)
- ✅ Streamlit dashboard for visualization
- ✅ Kafka streaming support for production environments
- ✅ Comprehensive test suite

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry (for dependency management)
- Optional: Kafka (for streaming features)

### Installation

```bash
# Clone and navigate to project
cd signal-intelligence-backbone

# Install dependencies with Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Running the Backend

```bash
# Start the FastAPI server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

### Running the Dashboard

In a new terminal:

```bash
# Start Streamlit dashboard
poetry run streamlit run dashboard.py --server.port=8501
```

Access at `http://localhost:8501`

## Architecture

### Project Structure

```
signal-intelligence-backbone/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and constants
│   ├── database.py             # Database initialization and session management
│   ├── models/
│   │   └── signal.py           # Pydantic + SQLAlchemy models
│   ├── services/
│   │   ├── signal_service.py   # Signal storage and retrieval
│   │   ├── drift_detection.py  # Drift detection and anomaly scoring
│   │   └── kafka_service.py    # Kafka producer/consumer
│   └── routes/
│       └── signals.py          # Signal API endpoints
├── dashboard.py                # Streamlit dashboard
├── scripts/
│   ├── generate_synthetic_data.py  # Synthetic data generator
│   └── kafka_stream_simulator.py   # Kafka streaming simulator
├── tests/
│   ├── test_drift_detection.py
│   └── test_api.py
├── pyproject.toml              # Poetry dependencies
└── README.md
```

### Data Flow

```
Signal Events
    ↓
[FastAPI /signals/ingest] ← [Kafka Consumer] ← [Kafka Stream]
    ↓
[SQLite Database]
    ↓
[Drift Detection Service] → [Anomaly Records]
    ↓
[Signal Service] → [Coherence Scores]
    ↓
[Streamlit Dashboard] + [REST Endpoints]
```

## API Reference

### Signal Ingestion

**POST** `/signals/ingest`

Ingest a new signal event with validation and drift detection.

```json
{
  "agent": "Axis",
  "user_state": "calm",
  "signal_strength": 0.83,
  "timestamp": "2025-10-31T09:10:00Z",
  "biometric_data": {
    "hrv": 65,
    "gsr": 2.3,
    "skin_temperature": 36.5
  }
}
```

**Response (200 OK):**
```json
{
  "id": 42,
  "agent": "Axis",
  "user_state": "calm",
  "signal_strength": 0.83,
  "timestamp": "2025-10-31T09:10:00Z",
  "biometric_data": {...},
  "created_at": "2025-10-31T09:10:00Z"
}
```

---

### Query Recent Signals

**GET** `/signals/recent?agent=Axis&minutes=30&limit=100`

Get recent signals, optionally filtered by agent.

**Query Parameters:**
- `agent` (optional): Filter by agent name
- `minutes` (optional, default=30): Time window in minutes (1-1440)
- `limit` (optional, default=100): Max results to return (1-1000)

**Response (200 OK):**
```json
[
  {
    "id": 42,
    "agent": "Axis",
    "user_state": "calm",
    "signal_strength": 0.83,
    "timestamp": "2025-10-31T09:10:00Z",
    "created_at": "2025-10-31T09:10:00Z"
  }
]
```

---

### Get Agents

**GET** `/signals/agents`

List all agents with active signals.

**Response (200 OK):**
```json
["Axis", "THEIA", "Echo"]
```

---

### Get Drift Status

**GET** `/signals/drift/{agent}`

Get current drift metrics for a specific agent.

**Response (200 OK):**
```json
{
  "agent": "Axis",
  "timestamp": "2025-10-31T09:15:00Z",
  "baseline_value": 0.75,
  "current_value": 0.82,
  "variance_percent": 9.33,
  "is_anomaly": false,
  "severity": "green"
}
```

**Severity Levels:**
- `green` (0-15% variance): Stable signal
- `yellow` (15-20% variance): Warning - elevated drift
- `red` (>20% variance): Critical - anomaly detected

---

### Get Drift Trend

**GET** `/signals/drift/{agent}/trend?minutes=30`

Get drift trend over specified time period.

**Response (200 OK):**
```json
{
  "avg_variance": 8.5,
  "max_variance": 22.3,
  "anomaly_count": 2,
  "trend": "stable"
}
```

**Trend Values:**
- `stable`: No significant trend
- `degrading`: Signal quality declining
- `recovering`: Signal quality improving

---

### Get Coherence Score

**GET** `/signals/coherence/{agent}?minutes=30`

Get coherence score for a specific agent.

Coherence combines signal strength with drift assessment:
- High signal strength + stable drift = high coherence
- Degrading trend reduces score by 15%
- Recovering trend reduces score by 5%

**Response (200 OK):**
```json
{
  "agent": "Axis",
  "timestamp": "2025-10-31T09:15:00Z",
  "coherence_score": 0.78,
  "drift_status": "warning",
  "signal_count": 28,
  "avg_signal_strength": 0.82
}
```

**Drift Status:**
- `stable` (0-10% variance): System operating normally
- `caution` (10-15% variance): Minor drift detected
- `warning` (15-20% variance): Significant drift
- `critical` (>20% variance): Critical anomaly

---

### Get Summary for All Agents

**GET** `/signals/summary?minutes=30`

Get coherence summary for all active agents.

**Response (200 OK):**
```json
[
  {
    "agent": "Axis",
    "timestamp": "2025-10-31T09:15:00Z",
    "coherence_score": 0.78,
    "drift_status": "warning",
    "signal_count": 28,
    "avg_signal_strength": 0.82
  },
  {
    "agent": "THEIA",
    "timestamp": "2025-10-31T09:15:00Z",
    "coherence_score": 0.91,
    "drift_status": "stable",
    "signal_count": 35,
    "avg_signal_strength": 0.89
  }
]
```

---

### Get Anomalies

**GET** `/signals/anomalies?agent=Axis&minutes=30`

Get recent anomalies, optionally filtered by agent.

**Query Parameters:**
- `agent` (optional): Filter by agent name
- `minutes` (optional, default=30): Time window in minutes

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "agent": "Axis",
    "variance_percent": 25.5,
    "severity": "red",
    "baseline_value": 0.70,
    "detected_at": "2025-10-31T09:12:00Z"
  }
]
```

## Configuration

Edit `.env` to customize settings:

```env
# Database
DATABASE_URL=sqlite:///./signals.db

# Environment
FASTAPI_ENV=development

# Kafka (for streaming)
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=signals
```

### Application Constants

Edit `app/config.py`:

```python
DRIFT_WINDOW_MINUTES = 10           # Moving baseline window
DRIFT_THRESHOLD_PERCENT = 15.0      # Warning threshold
ANOMALY_THRESHOLD_PERCENT = 20.0    # Critical threshold
MIN_SIGNALS_FOR_BASELINE = 5        # Minimum signals to establish baseline
```

## Usage Examples

### Example 1: Ingest Signals with Curl

```bash
curl -X POST "http://localhost:8000/signals/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "Axis",
    "user_state": "calm",
    "signal_strength": 0.83,
    "timestamp": "2025-10-31T09:10:00Z",
    "biometric_data": {"hrv": 65, "gsr": 2.3}
  }'
```

### Example 2: Generate and Ingest Synthetic Data

```bash
# Generate 100 signals and send to API
poetry run python scripts/generate_synthetic_data.py \
  --num-signals 100 \
  --time-span 30 \
  --anomaly-rate 0.15 \
  --send
```

### Example 3: Stream Data via Kafka

```bash
# Start Kafka (requires docker-compose setup)
docker-compose up -d

# Run Kafka simulator
poetry run python scripts/kafka_stream_simulator.py \
  --duration 120 \
  --interval 1.0 \
  --agents "Axis,THEIA,Echo"
```

### Example 4: Query Recent Signals

```bash
# Get signals from last 15 minutes, limit 50
curl "http://localhost:8000/signals/recent?minutes=15&limit=50"

# Get signals for specific agent
curl "http://localhost:8000/signals/recent?agent=Axis&minutes=30"
```

### Example 5: Monitor Drift

```bash
# Check current drift for Axis
curl "http://localhost:8000/signals/drift/Axis"

# Get drift trend over 60 minutes
curl "http://localhost:8000/signals/drift/Axis/trend?minutes=60"
```

## Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_drift_detection.py -v

# Run with coverage
poetry run pytest --cov=app tests/
```

## Drift Detection Algorithm

### Baseline Calculation

1. **Window Selection**: Collect signals from last 10 minutes
2. **Minimum Threshold**: Require at least 5 signals
3. **Calculation**: Mean of signal values in window

```python
baseline = mean(signals[-10 minutes:])
```

### Variance Scoring

```python
variance = |current_value - baseline| / baseline * 100
```

### Severity Classification

| Variance | Severity | Status | Action |
|----------|----------|--------|--------|
| 0-15%    | 🟢 Green | Stable | Monitor |
| 15-20%   | 🟡 Yellow | Warning | Alert |
| >20%     | 🔴 Red | Critical | Investigate |

### Coherence Scoring

```
coherence = (avg_signal_strength) * drift_adjustment
  where:
    - drift_adjustment = 0.85 if degrading
    - drift_adjustment = 0.95 if recovering
    - drift_adjustment = 1.0 if stable
```

## Database Schema

### signal_events

```sql
CREATE TABLE signal_events (
    id INTEGER PRIMARY KEY,
    agent VARCHAR(100) NOT NULL,
    user_state VARCHAR(50) NOT NULL,
    signal_strength FLOAT NOT NULL,
    timestamp DATETIME NOT NULL,
    biometric_data TEXT,  -- JSON string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### anomalies

```sql
CREATE TABLE anomalies (
    id INTEGER PRIMARY KEY,
    agent VARCHAR(100) NOT NULL,
    signal_event_id INTEGER NOT NULL,
    variance_percent FLOAT NOT NULL,
    severity VARCHAR(10) NOT NULL,
    baseline_value FLOAT NOT NULL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### drift_baselines

```sql
CREATE TABLE drift_baselines (
    id INTEGER PRIMARY KEY,
    agent VARCHAR(100) NOT NULL UNIQUE,
    baseline_value FLOAT NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    signal_count INTEGER DEFAULT 0
);
```

## Production Deployment

### Migrate to AWS RDS

1. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@rds-endpoint:5432/signals
   ```

2. Install RDS driver:
   ```bash
   poetry add psycopg2-binary
   ```

3. Run migrations:
   ```bash
   # The app auto-creates tables on first run
   poetry run uvicorn app.main:app
   ```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
COPY . .
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t signal-intelligence-backbone .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  signal-intelligence-backbone
```

### Kafka Integration (Production)

For real-time streaming:

1. Set up Kafka cluster
2. Configure `KAFKA_BROKER` in `.env`
3. Create consumer service:

```python
from app.services.kafka_service import get_consumer
from app.services.signal_service import SignalService

consumer = get_consumer()
consumer.consume_signals(SignalService.store_signal)
```

## Troubleshooting

### No signals appearing in dashboard

1. Check API is running: `curl http://localhost:8000/health`
2. Verify database: Check `signals.db` exists
3. Generate test data: `poetry run python scripts/generate_synthetic_data.py --send`

### Kafka connection errors

```bash
# Check Kafka is running
docker-compose ps

# Verify broker address
nc -zv localhost 9092
```

### Tests failing

```bash
# Clear database and run tests
rm signals.db
poetry run pytest -v
```

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `poetry run pytest`
4. Submit pull request

## License

Proprietary - Coherence Labs

## Support

For issues or questions:
- Check API docs: `http://localhost:8000/docs`
- Review logs: Check console output from `uvicorn`
- Run tests: `poetry run pytest -v`

---

**Signal Intelligence Backbone v0.1.0** | Built for multi-agent coherence tracking
