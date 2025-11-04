# Signal Intelligence Backbone - Complete API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required. Add API key middleware in production.

## Response Format

All responses are JSON unless otherwise specified.

### Success Response (200, 201)

```json
{
  "data": {...},
  "message": "Success"
}
```

Or direct data object:

```json
{
  "id": 1,
  "agent": "Axis",
  ...
}
```

### Error Response (4xx, 5xx)

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Not implemented in prototype. Add in production if needed.

---

# Endpoints

## System

### GET /

Get API information.

**Response:**
```json
{
  "message": "Signal Intelligence Backbone API",
  "docs": "/docs",
  "health": "/health"
}
```

---

### GET /health

System health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "signal-intelligence-backbone"
}
```

---

## Signals

### POST /signals/ingest

Ingest a new signal event with automatic drift detection.

**Request Body:**
```json
{
  "agent": "Axis",
  "user_state": "calm|neutral|anxious|engaged|fatigued",
  "signal_strength": 0.83,
  "timestamp": "2025-10-31T09:10:00Z",
  "biometric_data": {
    "hrv": 65,
    "gsr": 2.3,
    "skin_temperature": 36.5
  }
}
```

**Field Descriptions:**
- `agent` (string, 1-100 chars): Agent identifier
- `user_state` (enum): Emotional/cognitive state
- `signal_strength` (float, 0-1): Signal quality metric
- `timestamp` (ISO 8601): Event timestamp
- `biometric_data` (object, optional): Additional biometric measurements

**Response (200 OK):**
```json
{
  "id": 42,
  "agent": "Axis",
  "user_state": "calm",
  "signal_strength": 0.83,
  "timestamp": "2025-10-31T09:10:00Z",
  "biometric_data": {
    "hrv": 65,
    "gsr": 2.3,
    "skin_temperature": 36.5
  },
  "created_at": "2025-10-31T09:10:00Z"
}
```

**Error Responses:**
- `422 Unprocessable Entity`: Validation error (invalid signal_strength, missing field, etc.)
- `400 Bad Request`: Failed to process signal

**Example:**
```bash
curl -X POST http://localhost:8000/signals/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "Axis",
    "user_state": "calm",
    "signal_strength": 0.83,
    "timestamp": "2025-10-31T09:10:00Z",
    "biometric_data": {"hrv": 65, "gsr": 2.3}
  }'
```

---

### GET /signals/recent

Query recent signals with filtering and pagination.

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `agent` | string | null | No | Filter by agent name |
| `minutes` | integer | 30 | No | Time window (1-1440) |
| `limit` | integer | 100 | No | Max results (1-1000) |

**Response (200 OK):**
```json
[
  {
    "id": 42,
    "agent": "Axis",
    "user_state": "calm",
    "signal_strength": 0.83,
    "timestamp": "2025-10-31T09:10:00Z",
    "biometric_data": {...},
    "created_at": "2025-10-31T09:10:00Z"
  },
  ...
]
```

**Examples:**

Get all recent signals:
```bash
curl http://localhost:8000/signals/recent
```

Get signals from specific agent, last 15 minutes:
```bash
curl "http://localhost:8000/signals/recent?agent=Axis&minutes=15"
```

Get last 50 signals:
```bash
curl "http://localhost:8000/signals/recent?limit=50"
```

---

### GET /signals/agents

Get list of all agents with active signals.

**Query Parameters:** None

**Response (200 OK):**
```json
[
  "Axis",
  "THEIA",
  "Echo",
  "Prometheus"
]
```

**Example:**
```bash
curl http://localhost:8000/signals/agents
```

---

## Drift Detection

### GET /signals/drift/{agent}

Get current drift metrics for specific agent.

**Path Parameters:**
- `agent` (string): Agent identifier

**Query Parameters:** None

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

**Field Descriptions:**
- `baseline_value` (float): Moving baseline from last 10 minutes
- `current_value` (float): Latest signal value
- `variance_percent` (float): Percentage difference from baseline
- `is_anomaly` (boolean): Anomaly detected (>20% variance)
- `severity` (string): "green" (0-15%), "yellow" (15-20%), "red" (>20%)

**Error Responses:**
- `404 Not Found`: No recent signals for agent

**Example:**
```bash
curl http://localhost:8000/signals/drift/Axis
```

---

### GET /signals/drift/{agent}/trend

Get drift trend analysis for agent.

**Path Parameters:**
- `agent` (string): Agent identifier

**Query Parameters:**
- `minutes` (integer, default=30): Analysis window (1-1440)

**Response (200 OK):**
```json
{
  "avg_variance": 8.5,
  "max_variance": 22.3,
  "anomaly_count": 2,
  "trend": "stable"
}
```

**Field Descriptions:**
- `avg_variance` (float): Average variance in period
- `max_variance` (float): Peak variance detected
- `anomaly_count` (integer): Number of anomalies in period
- `trend` (string): "stable", "degrading", or "recovering"

**Example:**
```bash
curl "http://localhost:8000/signals/drift/Axis/trend?minutes=60"
```

---

## Coherence Scoring

### GET /signals/coherence/{agent}

Get coherence score for specific agent.

Coherence combines signal strength (0-1) with drift assessment:
- Stable drift: no adjustment
- Degrading trend: 15% reduction
- Recovering trend: 5% reduction

**Path Parameters:**
- `agent` (string): Agent identifier

**Query Parameters:**
- `minutes` (integer, default=30): Evaluation window (1-1440)

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

**Field Descriptions:**
- `coherence_score` (float, 0-1): Combined score
- `drift_status` (string): "stable", "caution", "warning", "critical"
- `signal_count` (integer): Signals in evaluation window
- `avg_signal_strength` (float, 0-1): Mean signal strength

**Drift Status Mapping:**
| Status | Variance | Action |
|--------|----------|--------|
| stable | 0-10% | Monitor normally |
| caution | 10-15% | Watch for changes |
| warning | 15-20% | Investigate drift |
| critical | >20% | High priority alert |

**Example:**
```bash
curl "http://localhost:8000/signals/coherence/Axis?minutes=30"
```

---

### GET /signals/summary

Get coherence summary for all active agents.

**Query Parameters:**
- `minutes` (integer, default=30): Evaluation window (1-1440)

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

**Example:**
```bash
curl http://localhost:8000/signals/summary?minutes=30
```

---

## Anomalies

### GET /signals/anomalies

Get recent anomalies detected by the system.

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `agent` | string | null | No | Filter by agent |
| `minutes` | integer | 30 | No | Time window |

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
  },
  {
    "id": 2,
    "agent": "THEIA",
    "variance_percent": 18.3,
    "severity": "yellow",
    "baseline_value": 0.82,
    "detected_at": "2025-10-31T09:10:00Z"
  }
]
```

**Field Descriptions:**
- `id` (integer): Anomaly record ID
- `agent` (string): Agent that generated anomaly
- `variance_percent` (float): Percentage variance from baseline
- `severity` (string): "yellow" (15-20%), "red" (>20%)
- `baseline_value` (float): Baseline at time of detection
- `detected_at` (ISO 8601): Detection timestamp

**Examples:**

Get all recent anomalies:
```bash
curl http://localhost:8000/signals/anomalies
```

Get anomalies for specific agent:
```bash
curl "http://localhost:8000/signals/anomalies?agent=Axis"
```

Get anomalies from last hour:
```bash
curl "http://localhost:8000/signals/anomalies?minutes=60"
```

---

# Data Models

## Signal Event

```json
{
  "id": 42,
  "agent": "Axis",
  "user_state": "calm",
  "signal_strength": 0.83,
  "timestamp": "2025-10-31T09:10:00Z",
  "biometric_data": {
    "hrv": 65,
    "gsr": 2.3,
    "skin_temperature": 36.5
  },
  "created_at": "2025-10-31T09:10:00Z"
}
```

## User State Enum

```
"calm"      # Relaxed, stable
"neutral"   # Baseline state
"anxious"   # Elevated stress
"engaged"   # Active, focused
"fatigued"  # Low energy
```

## Severity Levels

| Level | Variance | Meaning | Color |
|-------|----------|---------|-------|
| green | 0-15% | Stable signal | 🟢 |
| yellow | 15-20% | Warning - drift detected | 🟡 |
| red | >20% | Critical - anomaly | 🔴 |

## Drift Status

| Status | Variance | Meaning |
|--------|----------|---------|
| stable | 0-10% | Operating normally |
| caution | 10-15% | Minor drift, monitor |
| warning | 15-20% | Significant drift |
| critical | >20% | Severe anomaly |

---

# Curl Examples

## Quick Test Suite

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Ingest a signal
curl -X POST http://localhost:8000/signals/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "TestAgent",
    "user_state": "calm",
    "signal_strength": 0.85,
    "timestamp": "2025-10-31T10:00:00Z"
  }'

# 3. Get recent signals
curl http://localhost:8000/signals/recent?limit=5

# 4. List agents
curl http://localhost:8000/signals/agents

# 5. Check drift for agent
curl http://localhost:8000/signals/drift/TestAgent

# 6. Get coherence
curl http://localhost:8000/signals/coherence/TestAgent

# 7. Get summary
curl http://localhost:8000/signals/summary

# 8. Get anomalies
curl http://localhost:8000/signals/anomalies
```

---

# Pagination & Filtering

## Time Windows

All time windows are in minutes:
- Minimum: 1 minute
- Maximum: 1440 minutes (24 hours)
- Default: 30 minutes

## Result Limits

- Minimum: 1
- Maximum: 1000
- Default: 100

## Sorting

Results are returned sorted by timestamp (most recent first).

---

# Status Codes

| Code | Meaning | Cause |
|------|---------|-------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request format |
| 404 | Not Found | Agent or resource doesn't exist |
| 422 | Unprocessable Entity | Validation error (e.g., signal_strength > 1.0) |
| 500 | Internal Server Error | Server error |

---

# Rate Limiting

Not implemented in prototype. Consider adding in production:

```python
# Add to app/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

Then decorate endpoints:
```python
@router.post("/signals/ingest")
@limiter.limit("100/minute")
async def ingest_signal(...):
    pass
```

---

# Webhooks (Future)

Plan to add webhook support for real-time anomaly alerts:

```python
@router.post("/signals/ingest")
async def ingest_signal(signal):
    # ... process signal ...
    if is_anomaly:
        await trigger_webhook("anomaly", signal)
```

---

# Version History

### v0.1.0 (Current)
- Initial release
- Signal ingestion and validation
- Drift detection with 10-minute baseline
- Coherence scoring
- Anomaly detection
- Streamlit dashboard
- Kafka integration (optional)

### v0.2.0 (Planned)
- Authentication (API keys)
- Webhooks for alerts
- Batch signal ingestion
- Advanced filtering
- Metrics export (Prometheus)

---

# API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

These are auto-generated from the FastAPI endpoints.

---

**Last Updated:** 2025-10-31
**Maintainer:** Nithin Sarva
**Organization:** Coherence Labs
