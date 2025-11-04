"""
Streamlit dashboard for Signal Intelligence Backbone monitoring.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.signal_service import SignalService
from app.services.drift_detection import DriftDetectionService

# Page configuration
st.set_page_config(
    page_title="Signal Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Signal Intelligence Dashboard")
st.markdown("Real-time coherence tracking and drift monitoring for multi-agent environments")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Controls")

    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        [5, 15, 30, 60, 240],
        format_func=lambda x: f"{x} minutes"
    )

    # Agent filter
    db = SessionLocal()
    agents = SignalService.get_agent_list(db)
    agent_list = [agent[0] for agent in agents]

    selected_agents = st.multiselect(
        "Agents to Display",
        agent_list,
        default=agent_list[:3] if agent_list else []
    )

    # Refresh interval
    refresh_interval = st.selectbox(
        "Auto-refresh interval",
        [5, 10, 30, 60],
        format_func=lambda x: f"Every {x}s",
        index=1
    )

    st.markdown("---")

    if st.button("🔄 Refresh Now"):
        st.rerun()

# Main dashboard layout
if not selected_agents:
    st.warning("⚠️ Please select at least one agent from the sidebar")
    st.stop()

db = SessionLocal()

# Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_agents = len(agent_list)
    st.metric("Total Agents", total_agents, delta="active")

with col2:
    total_signals = 0
    for agent in selected_agents:
        signals = SignalService.get_recent_signals(db, agent, minutes=time_range)
        total_signals += len(signals)
    st.metric("Signals Ingested", total_signals)

with col3:
    anomalies = DriftDetectionService.get_recent_anomalies(db, minutes=time_range)
    st.metric("Anomalies Detected", len(anomalies))

with col4:
    summaries = SignalService.get_all_agents_summary(db, time_range)
    avg_coherence = sum(s.coherence_score for s in summaries) / len(summaries) if summaries else 0
    st.metric("Avg Coherence Score", f"{avg_coherence:.2f}")

st.markdown("---")

# Time Series Plot
st.subheader("📈 Signal Strength Over Time")

# Prepare data for time series
from datetime import timezone
ts_data = []
for agent in selected_agents:
    signals = SignalService.get_signals_by_time_range(
        db,
        datetime.now(timezone.utc) - timedelta(minutes=time_range),
        datetime.now(timezone.utc),
        agent=agent
    )
    for signal in signals:
        ts_data.append({
            "Timestamp": signal.timestamp,
            "Agent": agent,
            "Signal Strength": signal.signal_strength,
            "User State": signal.user_state
        })

if ts_data:
    df_ts = pd.DataFrame(ts_data)
    fig_ts = px.line(
        df_ts,
        x="Timestamp",
        y="Signal Strength",
        color="Agent",
        title="Signal Strength Trend",
        markers=True,
        hover_data=["User State"]
    )
    fig_ts.update_yaxes(range=[0, 1])
    fig_ts.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig_ts, width='stretch')
else:
    st.info("No signal data available for selected time range and agents")

# Drift Status Row
st.subheader("⚠️ Drift Status")

col1, col2 = st.columns(2)

with col1:
    # Current Drift Metrics
    st.markdown("### Current Drift Metrics")

    drift_data = []
    for agent in selected_agents:
        try:
            recent = SignalService.get_recent_signals(db, agent, minutes=1)
            if recent:
                latest_signal = recent[0]
                baseline = DriftDetectionService.calculate_baseline(db, agent)
                variance, is_anomaly, severity = DriftDetectionService.detect_drift(
                    db, agent, latest_signal.signal_strength, baseline
                )
                drift_data.append({
                    "Agent": agent,
                    "Variance %": f"{variance:.2f}",
                    "Status": severity.upper(),
                    "Anomaly": "🔴 YES" if is_anomaly else "✅ NO"
                })
        except Exception as e:
            st.warning(f"Error fetching data for {agent}: {str(e)}")

    if drift_data:
        df_drift = pd.DataFrame(drift_data)
        st.dataframe(df_drift, width='stretch', hide_index=True)
    else:
        st.info("No recent signals available")

with col2:
    # Severity Distribution
    st.markdown("### Anomaly Severity Distribution")

    anomalies = DriftDetectionService.get_recent_anomalies(db, minutes=time_range)
    if anomalies:
        severity_counts = {}
        for a in anomalies:
            severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1

        colors = {"red": "#EF553B", "yellow": "#FFC15E", "green": "#00CC96"}
        fig_severity = go.Figure(
            data=[go.Bar(
                y=list(severity_counts.keys()),
                x=list(severity_counts.values()),
                orientation='h',
                marker=dict(color=[colors.get(k, "#636EFA") for k in severity_counts.keys()])
            )]
        )
        fig_severity.update_layout(
            title="Anomalies by Severity",
            xaxis_title="Count",
            yaxis_title="Severity",
            height=300
        )
        st.plotly_chart(fig_severity, width='stretch')
    else:
        st.info("No anomalies detected in this period")

# Coherence Scores
st.subheader("💚 Agent Coherence Scores")

coherence_data = []
for agent in selected_agents:
    score = SignalService.calculate_coherence_score(db, agent, time_range)
    coherence_data.append({
        "Agent": agent,
        "Coherence Score": score.coherence_score,
        "Avg Signal": f"{score.avg_signal_strength:.2f}",
        "Drift Status": score.drift_status.upper(),
        "Signal Count": score.signal_count
    })

if coherence_data:
    df_coherence = pd.DataFrame(coherence_data)

    # Create gauge charts
    cols = st.columns(len(coherence_data))
    for col, (idx, row) in zip(cols, df_coherence.iterrows()):
        with col:
            score = row["Coherence Score"]
            status_color = "green" if score > 0.7 else "orange" if score > 0.5 else "red"

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': row["Agent"]},
                delta={'reference': 0.75},
                gauge={
                    'axis': {'range': [0, 1]},
                    'bar': {'color': status_color},
                    'steps': [
                        {'range': [0, 0.5], 'color': "#ffcccc"},
                        {'range': [0.5, 0.75], 'color': "#ffffcc"},
                        {'range': [0.75, 1], 'color': "#ccffcc"}
                    ],
                    'threshold': {
                        'line': {'color': 'red', 'width': 4},
                        'thickness': 0.75,
                        'value': 0.5
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, width='stretch')

    st.dataframe(df_coherence, width='stretch', hide_index=True)
else:
    st.info("No coherence data available")

# Recent Anomalies Table
st.subheader("🔍 Recent Anomalies")

anomalies = DriftDetectionService.get_recent_anomalies(db, minutes=time_range)
if anomalies:
    anomaly_display = []
    for a in anomalies:
        if a.agent in selected_agents:
            anomaly_display.append({
                "Detected": a.detected_at.strftime("%H:%M:%S"),
                "Agent": a.agent,
                "Variance %": f"{a.variance_percent:.2f}",
                "Severity": a.severity.upper(),
                "Baseline": f"{a.baseline_value:.2f}"
            })

    if anomaly_display:
        df_anomalies = pd.DataFrame(anomaly_display)
        st.dataframe(df_anomalies, width='stretch', hide_index=True)
    else:
        st.info("No anomalies for selected agents")
else:
    st.info("No anomalies detected in this period")

# Footer
st.markdown("---")
st.markdown(
    """
    **Signal Intelligence Backbone** | Real-time coherence monitoring
    - API Docs: http://localhost:8000/docs
    - Health: http://localhost:8000/health
    """
)

db.close()
