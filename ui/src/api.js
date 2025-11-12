const DEMO = (import.meta.env.VITE_DEMO || 'true') === 'true';
const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export const fetchSummary = () =>
  DEMO
    ? getJSON('/fixtures/summary.json')
    : getJSON(`${API}/signals/summary?minutes=60`);

export const fetchDrift = (agent) =>
  DEMO
    ? getJSON(`/fixtures/drift_${agent}.json`)
    : getJSON(`${API}/signals/drift/${agent}/trend?minutes=60`);

export const fetchAnomalies = (agent) => {
  const q = agent ? `&agent=${encodeURIComponent(agent)}` : '';
  return DEMO
    ? getJSON('/fixtures/anomalies.json')
    : getJSON(`${API}/signals/anomalies?minutes=60${q}`);
};

export const fetchAnomalyById = (id) =>
  DEMO
    ? getJSON('/fixtures/anomaly_1.json')
    : getJSON(`${API}/signals/anomalies?id=${id}`);
