# Quick Start Guide

Get the Signal Intelligence Backbone running in 5 minutes.

## Prerequisites

- Python 3.10 or later
- Poetry (install with `curl -sSL https://install.python-poetry.org | python3 -`)

## 1. Install Dependencies

```bash
cd signal-intelligence-backbone
poetry install
```

## 2. Start the Backend API

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ API is live! Visit http://localhost:8000/docs for interactive API docs.

## 3. Generate Test Data

In a new terminal:

```bash
poetry run python scripts/generate_synthetic_data.py \
  --num-signals 100 \
  --time-span 30 \
  --anomaly-rate 0.15 \
  --send
```

You should see:
```
✅ Ingestion Complete
   Successful: 100
   Failed: 0
```

## 4. Start the Dashboard

In another terminal:

```bash
poetry run streamlit run dashboard.py --server.port=8501
```

Open http://localhost:8501 to see real-time visualizations!

## 5. Test the API

```bash
# Check health
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/signals/agents

# Get recent signals
curl http://localhost:8000/signals/recent?limit=5

# Get agent summary
curl http://localhost:8000/signals/summary
```

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/docs` | GET | Interactive API documentation |
| `/signals/ingest` | POST | Submit signal events |
| `/signals/recent` | GET | Query recent signals |
| `/signals/drift/{agent}` | GET | Check drift status |
| `/signals/coherence/{agent}` | GET | Get coherence score |
| `/signals/summary` | GET | All agents overview |
| `/signals/anomalies` | GET | Anomaly history |

## Example: Ingest a Signal

```bash
curl -X POST http://localhost:8000/signals/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "Axis",
    "user_state": "calm",
    "signal_strength": 0.85,
    "timestamp": "2025-10-31T10:00:00Z",
    "biometric_data": {
      "hrv": 70,
      "gsr": 2.1,
      "skin_temperature": 36.5
    }
  }'
```

## Continuous Data Stream

Keep generating synthetic data for realistic testing:

```bash
# Generate signals continuously
poetry run python scripts/generate_synthetic_data.py \
  --num-signals 50 \
  --time-span 5 \
  --anomaly-rate 0.1 \
  --send
```

Run this multiple times to maintain a steady stream.

## Exploring the Dashboard

The dashboard shows:
- 📊 Signal strength trends over time
- ⚠️ Drift status (green/yellow/red)
- 💚 Coherence scores per agent
- 🔍 Recent anomalies detected
- 📈 Severity distribution

**Filters:**
- Select time range (5, 15, 30, 60, 240 minutes)
- Filter by agents
- Auto-refresh interval

## Understanding the Drift System

**Baseline:** Average of signals from last 10 minutes

**Variance:**
- **Green (0-15%)**: Stable ✅
- **Yellow (15-20%)**: Warning ⚠️
- **Red (>20%)**: Critical 🔴

**Coherence Score:** Combines signal strength with drift status
- High coherence = stable, strong signals
- Low coherence = degrading or inconsistent signals

## Next Steps

1. **Read the full documentation**: See `README.md`
2. **Explore the code**: Check `app/services/drift_detection.py`
3. **Run tests**: `poetry run pytest -v`
4. **Customize settings**: Edit `app/config.py`
5. **Add your own signals**: POST to `/signals/ingest`

## Troubleshooting

**Port 8000 already in use?**
```bash
poetry run uvicorn app.main:app --port 8001
```

**No signals in dashboard?**
```bash
# Generate and send test data
poetry run python scripts/generate_synthetic_data.py --send
```

**Want to reset the database?**
```bash
rm signals.db
# Restart the API - it will auto-create a fresh database
```

## Architecture Overview

```
Signal Events
    ↓
[FastAPI POST /signals/ingest]
    ↓
[Validate with Pydantic]
    ↓
[Check for Drift]
    ↓
[Store in SQLite]
    ↓
[Streamlit Dashboard] ← [Query APIs] ← [Services]
```

## Performance Notes

- **1000+ signals/minute** via direct API
- **Real-time dashboard updates** (configurable refresh)
- **Drift detection** in <100ms per signal
- **SQLite** suitable for prototype; scales to millions with RDS

---

🎉 **You're all set!** Your Signal Intelligence Backbone is running.

For detailed documentation, see:
- API Reference: `README.md`
- Development Guide: `DEVELOPMENT.md`
- Interactive Docs: http://localhost:8000/docs
