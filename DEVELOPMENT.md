# Development Guide

## Setting Up Development Environment

### 1. Clone Repository

```bash
git clone <repository-url>
cd signal-intelligence-backbone
```

### 2. Install Poetry

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or use brew
brew install poetry
```

### 3. Install Dependencies

```bash
poetry install
```

This installs all dependencies including dev tools (pytest, black, mypy, etc.)

### 4. Create .env File

```bash
cp .env.example .env
```

## Running the Application

### Backend API

```bash
# Terminal 1
poetry shell
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Auto-reloads on code changes
- Docs available at `http://localhost:8000/docs`

### Dashboard

```bash
# Terminal 2
poetry shell
poetry run streamlit run dashboard.py --server.port=8501
```

### Generate Test Data

```bash
# Terminal 3
poetry shell

# Generate 500 signals over 60 minutes and ingest
poetry run python scripts/generate_synthetic_data.py \
  --num-signals 500 \
  --time-span 60 \
  --anomaly-rate 0.2 \
  --send
```

## Code Structure

### Models (`app/models/signal.py`)

Contains Pydantic and SQLAlchemy models:
- `SignalEventRequest`: API input schema
- `SignalEvent`: Database ORM model
- `AnomalyRecord`: Anomaly storage
- `DriftBaseline`: Baseline tracking

### Services

#### `app/services/signal_service.py`
- `store_signal()`: Save signal to database
- `get_recent_signals()`: Query signals by time window
- `calculate_coherence_score()`: Compute agent coherence

#### `app/services/drift_detection.py`
- `calculate_baseline()`: 10-minute moving average
- `detect_drift()`: Calculate variance and classify severity
- `record_anomaly()`: Log detected anomalies
- `get_recent_anomalies()`: Query anomalies
- `calculate_drift_trend()`: Trend analysis

#### `app/services/kafka_service.py`
- `KafkaSignalProducer`: Send signals to Kafka
- `KafkaSignalConsumer`: Receive signals from Kafka

### Routes (`app/routes/signals.py`)

FastAPI endpoints:
- `POST /signals/ingest`: Accept signal events
- `GET /signals/recent`: Query recent signals
- `GET /signals/agents`: List active agents
- `GET /signals/drift/{agent}`: Drift metrics
- `GET /signals/coherence/{agent}`: Coherence score
- `GET /signals/summary`: All agents overview
- `GET /signals/anomalies`: Anomaly history

## Testing

### Running Tests

```bash
# All tests
poetry run pytest

# Verbose output
poetry run pytest -v

# Specific file
poetry run pytest tests/test_drift_detection.py -v

# With coverage
poetry run pytest --cov=app tests/
```

### Test Files

- `tests/test_drift_detection.py`: Drift detection logic
- `tests/test_api.py`: API endpoints

### Writing Tests

Example:

```python
@pytest.mark.asyncio
async def test_signal_ingestion(client):
    """Test signal ingestion endpoint."""
    signal = {
        "agent": "Axis",
        "user_state": "calm",
        "signal_strength": 0.85,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    response = await client.post("/signals/ingest", json=signal)
    assert response.status_code == 200
    assert response.json()["agent"] == "Axis"
```

## Code Quality

### Formatting

```bash
# Format code with Black
poetry run black app tests scripts

# Check formatting
poetry run black --check app tests scripts
```

### Linting

```bash
# Check code style
poetry run flake8 app tests scripts

# Type checking
poetry run mypy app
```

## Database

### SQLite (Development)

Database is auto-created at `signals.db` on first run.

```bash
# Reset database
rm signals.db
```

### Inspect Database

```bash
# Open SQLite
sqlite3 signals.db

# View tables
.tables

# View schema
.schema signal_events

# Query data
SELECT * FROM signal_events LIMIT 5;
```

### Migrate to PostgreSQL

1. Update `pyproject.toml`:
   ```toml
   psycopg2-binary = "^2.9"
   ```

2. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/signals
   ```

3. Update `app/database.py`:
   ```python
   engine = create_engine(DATABASE_URL)  # Remove check_same_thread
   ```

## Configuration

### Default Settings (`app/config.py`)

```python
DRIFT_WINDOW_MINUTES = 10           # Baseline calculation window
DRIFT_THRESHOLD_PERCENT = 15.0      # Warning threshold
ANOMALY_THRESHOLD_PERCENT = 20.0    # Critical threshold
MIN_SIGNALS_FOR_BASELINE = 5        # Min signals to establish baseline
```

### Customize Settings

Edit `app/config.py` to adjust drift detection sensitivity, window sizes, etc.

## Common Development Tasks

### Add New Endpoint

1. Create function in `app/routes/signals.py`:
   ```python
   @router.get("/path")
   async def handler(db: Session = Depends(get_db)):
       return {"result": "..."}
   ```

2. Add tests in `tests/test_api.py`

3. Update README with endpoint documentation

### Add New Service Method

1. Create method in appropriate service (`app/services/`)
2. Add tests in `tests/`
3. Use in routes or other services

### Add New Model Field

1. Update Pydantic model in `app/models/signal.py`
2. Update SQLAlchemy ORM model
3. Database auto-migrates (SQLite) or run migration (RDS)

## Debugging

### Enable Debug Logging

```python
# In app/main.py or config
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Functions

```bash
poetry shell
python

# In Python REPL
from app.services.drift_detection import DriftDetectionService
from app.database import SessionLocal

db = SessionLocal()
baseline = DriftDetectionService.calculate_baseline(db, "Axis")
print(baseline)
```

### Database Debugging

```bash
# Check signals table
sqlite3 signals.db "SELECT COUNT(*) FROM signal_events;"

# View recent signals
sqlite3 signals.db "SELECT agent, signal_strength, timestamp FROM signal_events ORDER BY created_at DESC LIMIT 5;"
```

## Performance Optimization

### Indexing

Indexes are defined in models:
```python
timestamp = Column(DateTime, index=True)
agent = Column(String(100), index=True)
```

### Query Optimization

Use `.limit()` and `.filter()` to reduce result sets:

```python
# Good
signals = db.query(SignalEvent).filter(
    SignalEvent.timestamp >= window_start
).limit(100).all()

# Avoid (loads all into memory)
signals = db.query(SignalEvent).all()
```

### Caching (Future)

For high-traffic scenarios, add caching:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_baseline(agent: str):
    # Cached for 5 minutes
    pass
```

## Deploying Changes

### Local Testing Checklist

- [ ] Code formatted: `poetry run black app`
- [ ] Tests passing: `poetry run pytest -v`
- [ ] API docs updated: `http://localhost:8000/docs`
- [ ] README updated if endpoints changed
- [ ] No hardcoded values (use config.py)
- [ ] Proper error handling

### Deployment Steps

1. Merge to main branch
2. Pull on server
3. Run `poetry install`
4. Test endpoints
5. Restart services

## Troubleshooting

### ModuleNotFoundError

```bash
# Ensure Poetry environment is active
poetry shell

# Or run with poetry run
poetry run uvicorn app.main:app
```

### Port Already in Use

```bash
# Change port
poetry run uvicorn app.main:app --port 8001

# Or kill process
lsof -ti:8000 | xargs kill -9
```

### Database Locked (SQLite)

```bash
# Close all connections and retry
rm signals.db
poetry run uvicorn app.main:app
```

### Tests Failing

```bash
# Ensure clean database
rm signals.db

# Run tests
poetry run pytest -v

# Run specific test
poetry run pytest tests/test_drift_detection.py::TestDriftDetection::test_baseline_calculation -v
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Streamlit API Reference](https://docs.streamlit.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Kafka Python Client](https://kafka-python.readthedocs.io/)

## Contributing Guidelines

1. Create feature branch: `git checkout -b feature/description`
2. Make changes and write tests
3. Format code: `poetry run black app`
4. Run tests: `poetry run pytest -v`
5. Commit with clear message
6. Push and create pull request

---

**Happy developing!** 🚀
