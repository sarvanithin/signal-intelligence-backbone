# Coherence Console v0.2 — UI (MVP)

**Status:** MVP (First UI Pass)
**Branch:** `feat/ui-v0-2`
**Date:** November 4, 2025

---

## Overview

The **Coherence Console** is a real-time operator dashboard for monitoring agent coherence, drift trends, and anomaly events. It consumes the Signal Intelligence Backbone API and provides an intuitive, dark-themed interface for observing multi-agent coherence state.

### Key Features

✅ **Agent Status Cards** — Color-coded coherence score & drift status
✅ **Drift Trend Chart** — 60-minute line chart (Recharts)
✅ **Anomaly Timeline** — Sortable, paginated event list
✅ **Details Drawer** — Full event JSON + biometric data
✅ **Live Polling** — 5-second auto-refresh (configurable)
✅ **DEMO Mode** — Works offline with fixtures
✅ **Dark Theme** — Charcoal matte with Tailwind CSS

---

## Quick Start

### 1. Install Dependencies

```bash
cd ui
npm install
```

### 2. Configure Environment

Copy the example config:

```bash
cp .env.example .env.local
```

Edit `.env.local` (optional — defaults already set):

```env
VITE_API_BASE=http://localhost:8000      # Backend API URL
VITE_POLL_MS=5000                        # Polling interval (ms)
VITE_DEMO=true                           # Use fixtures or live API
```

### 3. Start Development Server

```bash
npm run dev
```

Open your browser to `http://localhost:5173`

---

## Usage

### DEMO Mode (Default)

When `VITE_DEMO=true`, the app loads fixture data from `/public/fixtures/*.json`:

```bash
npm run dev  # Starts in DEMO mode
```

Useful for:
- UI development without backend
- Testing offline
- Demonstrating features

### Live API Mode

When `VITE_DEMO=false`, the app calls the real backend:

```env
VITE_DEMO=false
```

Then restart the dev server:

```bash
npm run dev
```

**Note:** Backend must be running at the `VITE_API_BASE` URL.

---

## API Endpoints (Consumed)

When `VITE_DEMO=false`, the UI expects these endpoints:

### GET /signals/summary?minutes=60

**Response:** List of agent status objects

```json
[
  {
    "agent": "Axis",
    "coherence_score": 0.78,
    "drift_status": "warning",
    "signal_count": 28,
    "avg_signal_strength": 0.82
  },
  {
    "agent": "THEIA",
    "coherence_score": 0.91,
    "drift_status": "stable",
    "signal_count": 35,
    "avg_signal_strength": 0.89
  }
]
```

### GET /signals/drift/{agent}/trend?minutes=60

**Response:** Drift time series

```json
{
  "series": [
    { "t": "2025-11-04T12:00:00Z", "value": 0.82 },
    { "t": "2025-11-04T12:05:00Z", "value": 0.80 },
    ...
  ]
}
```

### GET /signals/anomalies?minutes=60&agent={agent}

**Response:** List of anomaly events

```json
[
  {
    "id": 1,
    "ts": "2025-11-04T12:15:00Z",
    "agent": "Axis",
    "variance_percent": 25.5,
    "severity": "warning",
    "baseline_value": 0.70,
    "current_value": 0.88,
    "interpretation": "Spike above 10-min baseline"
  }
]
```

### GET /signals/anomalies?id={id}

**Response:** Single anomaly event with biometric details

```json
{
  "id": 1,
  "ts": "2025-11-04T12:15:00Z",
  "agent": "Axis",
  "variance_percent": 25.5,
  "severity": "warning",
  "baseline_value": 0.70,
  "current_value": 0.88,
  "biometric_data": {
    "hrv": 65,
    "gsr": 2.3,
    "skin_temperature": 36.5
  },
  "interpretation": "Spike above 10-min baseline — agent experiencing elevated coherence variance"
}
```

---

## Architecture

### Component Tree

```
App.jsx
├── AgentStatusRow
│   └── [Agent Status Cards]
├── DriftTrendChart
│   └── [Recharts LineChart]
├── AnomalyTimeline
│   └── [Pagination + Table]
├── DetailsDrawer
│   └── [Event JSON + Biometrics]
└── Banner
    └── [Error/Warning Messages]
```

### State Management

- **`summary`** — List of agent status objects (from GET /summary)
- **`selected`** — Currently selected agent name
- **`drift`** — Drift time series for selected agent
- **`anoms`** — Anomaly events for selected agent
- **`selectedEvt`** — Full event details (for drawer)
- **`err`** — Current error message
- **`loading`** — Loading indicator state

### Polling Logic

- Starts on component mount or when `selected` agent changes
- Calls `load()` every `VITE_POLL_MS` milliseconds
- Fetches summary, drift, and anomalies in parallel
- Errors non-blocking: shows banner, continues polling

---

## Visual Tokens

### Drift Status → Color Mapping

| Status | Color | Usage |
|--------|-------|-------|
| `stable` | 🟢 Green | Agent operating normally |
| `caution` | 🟡 Yellow | Monitor closely |
| `warning` | 🟠 Orange | Intervention needed |
| `critical` | 🔴 Red | Immediate action required |

### UI Components

- **Agent Status Cards:** 5-column grid (responsive to mobile)
- **Drift Chart:** Full-width line chart with hover tooltips
- **Anomaly Table:** Scrollable with pagination (5 items/page)
- **Details Drawer:** Fixed right panel (96px width)

---

## Scripts

```bash
# Development
npm run dev          # Start Vite dev server (http://localhost:5173)

# Production
npm run build        # Build optimized production bundle
npm run preview      # Preview production build locally

# Quality
npm run lint         # Run ESLint
npm run format       # Format with Prettier
npm run test         # Run Vitest suite
```

---

## File Structure

```
ui/
├── .env.example
├── .gitignore
├── package.json
├── vite.config.js
├── tailwind.config.cjs
├── postcss.config.cjs
├── index.html
├── README_UI.md
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── styles.css
│   ├── api.js
│   ├── lib/
│   │   └── statusTokens.js
│   └── components/
│       ├── AgentStatusRow.jsx
│       ├── DriftTrendChart.jsx
│       ├── AnomalyTimeline.jsx
│       ├── DetailsDrawer.jsx
│       └── Banner.jsx
└── fixtures/
    ├── summary.json
    ├── drift_Axis.json
    ├── drift_THEIA.json
    ├── anomalies.json
    └── anomaly_1.json
```

---

## Definition of Done (DoD) Checklist

### v0.2 MVP

- [x] **Agent Status Row**
  - [x] Render cards for each agent
  - [x] Display coherence_score (0–1 → %)
  - [x] Display drift_status with color mapping
  - [x] Clickable to select agent (filters drift + anomalies)
  - [x] Responsive grid layout

- [x] **Drift Trend Chart**
  - [x] Fetch drift series for selected agent
  - [x] Render 60-minute line chart (Recharts)
  - [x] Show timestamp on X-axis
  - [x] Show value (0–1) on Y-axis
  - [x] Hover tooltip with exact value

- [x] **Anomaly Timeline**
  - [x] Fetch anomalies for selected agent
  - [x] Render table with: Time, Agent, Variance%, Severity
  - [x] Clickable rows → open Details Drawer
  - [x] Pagination (5 items/page)
  - [x] Handle empty state

- [x] **Details Drawer**
  - [x] Right-side slide-out panel
  - [x] Display full event JSON fields
  - [x] Show biometric_data if present (HRV, GSR, temp)
  - [x] Show interpretation
  - [x] "Copy JSON" button
  - [x] Close button (X)

- [x] **Polling & Error Handling**
  - [x] Auto-refresh every 5s (configurable)
  - [x] Show "Updating..." indicator
  - [x] Non-blocking error banner on fetch failure
  - [x] Continue polling after errors
  - [x] Handle empty data states

- [x] **DEMO Mode**
  - [x] Use `VITE_DEMO` env var
  - [x] Load fixtures from `/fixtures/*.json`
  - [x] Toggle DEMO=true/false via .env.local
  - [x] Works entirely offline

- [x] **Configuration**
  - [x] `.env.example` with defaults
  - [x] `VITE_API_BASE` for backend URL
  - [x] `VITE_POLL_MS` for polling interval
  - [x] `VITE_DEMO` for DEMO/live toggle

- [x] **Styling & Theme**
  - [x] Dark charcoal theme (slate-900 base)
  - [x] Tailwind CSS utility classes
  - [x] Inter font family
  - [x] Responsive design (mobile → desktop)
  - [x] Hover + active states

- [x] **Code Quality**
  - [x] ESLint passing
  - [x] Prettier formatted
  - [x] React best practices (hooks, keys, dependencies)
  - [x] Clean component structure

- [x] **Documentation**
  - [x] README_UI.md (this file)
  - [x] Inline component comments
  - [x] API endpoint documentation
  - [x] Quick start instructions
  - [x] Environment variable docs

---

## Testing

### Run Tests

```bash
npm run test
```

### Test Coverage

Basic render tests for:
- AgentStatusRow (snapshot + interaction)
- DriftTrendChart (data rendering)
- AnomalyTimeline (pagination logic)
- DetailsDrawer (open/close + data display)

---

## Known Limitations (v0.2)

- No authentication (v0.3 candidate)
- No timezone controls (assumes UTC)
- No keyboard navigation (v0.3 candidate)
- No CSV export (v0.3 candidate)
- Pagination hardcoded to 5 items/page (v0.3: configurable)
- Chart X-axis shows time in user's local timezone

---

## Next Steps (v0.3+)

- [ ] API authentication header (Bearer token)
- [ ] User preferences (polling interval, page size)
- [ ] Keyboard navigation (arrow keys in timeline)
- [ ] CSV export of anomalies
- [ ] Custom date/time range selector
- [ ] Timezone picker
- [ ] Real-time Slack/email alerts
- [ ] Mobile-optimized UI

---

## Support

For questions or issues:
1. Check `.env.local` configuration
2. Verify backend is running (`http://localhost:8000`)
3. Check browser DevTools console for fetch errors
4. Try toggling `VITE_DEMO=true` to test with fixtures
5. Restart dev server after .env changes

---

**Built with React, Vite, Tailwind CSS, Recharts**
**Part of Signal Intelligence Backbone v0.2**
