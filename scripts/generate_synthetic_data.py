"""
Synthetic biometric data generator for testing and demonstration.
"""
import json
import random
from datetime import datetime, timedelta
import numpy as np
import requests

# Configuration
API_BASE_URL = "http://localhost:8000"
AGENTS = ["Axis", "THEIA", "Echo", "Prometheus", "Artemis"]
USER_STATES = ["calm", "neutral", "anxious", "engaged", "fatigued"]

# Biometric parameters (realistic ranges)
HRV_MEAN = 65
HRV_STD = 15
GSR_MEAN = 2.5
GSR_STD = 0.8
SKIN_TEMP_MEAN = 36.5
SKIN_TEMP_STD = 0.3


def generate_hrv(base: float = HRV_MEAN, state_modifier: dict = None) -> float:
    """
    Generate Heart Rate Variability (HRV) data.
    Lower HRV indicates stress; higher HRV indicates relaxation.
    Normal range: 20-100ms
    """
    if state_modifier is None:
        state_modifier = {}

    hrv = np.random.normal(base, HRV_STD)

    # Apply state modifiers
    if "anxious" in str(state_modifier):
        hrv *= 0.75  # Decrease HRV when anxious
    elif "calm" in str(state_modifier):
        hrv *= 1.15  # Increase HRV when calm

    return max(20, min(100, hrv))  # Clamp to valid range


def generate_gsr(base: float = GSR_MEAN, state_modifier: dict = None) -> float:
    """
    Generate Galvanic Skin Response (GSR) data.
    Higher GSR indicates arousal/stress; lower indicates relaxation.
    Normal range: 1.0-10.0 μS
    """
    if state_modifier is None:
        state_modifier = {}

    gsr = np.random.normal(base, GSR_STD)

    # Apply state modifiers
    if "anxious" in str(state_modifier):
        gsr *= 1.4  # Increase GSR when anxious
    elif "calm" in str(state_modifier):
        gsr *= 0.8  # Decrease GSR when calm

    return max(1.0, min(10.0, gsr))


def generate_skin_temperature(
    base: float = SKIN_TEMP_MEAN,
    state_modifier: dict = None
) -> float:
    """
    Generate skin temperature data.
    Ranges from 32-36°C normally
    """
    if state_modifier is None:
        state_modifier = {}

    temp = np.random.normal(base, SKIN_TEMP_STD)
    return max(32.0, min(37.0, temp))


def calculate_signal_strength(
    hrv: float,
    gsr: float,
    user_state: str
) -> float:
    """
    Calculate composite signal strength (0-1) from biometric data.

    Factors:
    - HRV: Higher is better (more relaxed)
    - GSR: Lower is better (less stressed)
    - User state mapping
    """
    # Normalize HRV (20-100 scale) to 0-1
    hrv_score = (hrv - 20) / 80

    # Normalize GSR (1-10 scale) to 0-1, inverted (lower is better)
    gsr_score = (10 - gsr) / 9
    gsr_score = max(0, min(1, gsr_score))

    # Base composite score
    composite = (hrv_score * 0.4 + gsr_score * 0.4) * 0.8 + 0.2

    # Apply user state multiplier
    state_multipliers = {
        "calm": 1.1,
        "neutral": 1.0,
        "anxious": 0.6,
        "engaged": 1.05,
        "fatigued": 0.75
    }
    composite *= state_multipliers.get(user_state, 1.0)

    # Ensure range [0, 1]
    return max(0.0, min(1.0, composite))


def generate_signal_event(agent: str, timestamp: datetime = None) -> dict:
    """Generate a realistic signal event."""
    if timestamp is None:
        timestamp = datetime.utcnow()

    user_state = random.choice(USER_STATES)

    # Generate biometric data
    hrv = generate_hrv(state_modifier=user_state)
    gsr = generate_gsr(state_modifier=user_state)
    skin_temp = generate_skin_temperature()

    # Calculate signal strength
    signal_strength = calculate_signal_strength(hrv, gsr, user_state)

    # Add some realistic noise
    signal_strength += np.random.normal(0, 0.02)
    signal_strength = max(0.0, min(1.0, signal_strength))

    return {
        "agent": agent,
        "user_state": user_state,
        "signal_strength": round(signal_strength, 3),
        "timestamp": timestamp.isoformat() + "Z",
        "biometric_data": {
            "hrv": round(hrv, 2),
            "gsr": round(gsr, 3),
            "skin_temperature": round(skin_temp, 2)
        }
    }


def generate_signal_stream(
    agents: list = None,
    num_signals: int = 100,
    time_span_minutes: int = 30,
    anomaly_rate: float = 0.1
) -> list:
    """
    Generate a stream of signals with optional anomalies.

    Args:
        agents: List of agent names
        num_signals: Total signals to generate
        time_span_minutes: Spread signals across this time period
        anomaly_rate: Probability (0-1) of each signal being anomalous
    """
    if agents is None:
        agents = AGENTS

    signals = []
    start_time = datetime.utcnow() - timedelta(minutes=time_span_minutes)

    for i in range(num_signals):
        # Distribute signals across time
        progress = i / num_signals
        timestamp = start_time + timedelta(minutes=time_span_minutes * progress)

        agent = random.choice(agents)

        # Generate signal
        signal = generate_signal_event(agent, timestamp)

        # Introduce anomalies
        if random.random() < anomaly_rate:
            # Create anomalous signal (extreme value)
            signal["signal_strength"] = round(
                random.choice([
                    np.random.normal(0.1, 0.05),  # Too low
                    np.random.normal(0.95, 0.05)  # Too high
                ]),
                3
            )
            signal["signal_strength"] = max(0.0, min(1.0, signal["signal_strength"]))

        signals.append(signal)

    return signals


def send_signals_to_api(signals: list, api_url: str = API_BASE_URL) -> None:
    """Send generated signals to the API."""
    endpoint = f"{api_url}/signals/ingest"

    successful = 0
    failed = 0

    for signal in signals:
        try:
            response = requests.post(endpoint, json=signal, timeout=5)
            if response.status_code == 200:
                successful += 1
            else:
                failed += 1
                print(f"Failed to ingest signal: {response.status_code} - {response.text}")
        except Exception as e:
            failed += 1
            print(f"Error sending signal: {str(e)}")

    print(f"\n✅ Ingestion Complete")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate synthetic biometric data for testing"
    )
    parser.add_argument(
        "--num-signals",
        type=int,
        default=100,
        help="Number of signals to generate (default: 100)"
    )
    parser.add_argument(
        "--time-span",
        type=int,
        default=30,
        help="Time span in minutes to spread signals (default: 30)"
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.1,
        help="Anomaly rate 0-1 (default: 0.1 = 10%)"
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=",".join(AGENTS),
        help="Comma-separated agent names"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file (JSON) instead of sending to API"
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send signals to API (default: False)"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help="API base URL"
    )

    args = parser.parse_args()

    agents = [a.strip() for a in args.agents.split(",")]

    print(f"📊 Generating {args.num_signals} synthetic signals...")
    print(f"   Time span: {args.time_span} minutes")
    print(f"   Anomaly rate: {args.anomaly_rate * 100:.1f}%")
    print(f"   Agents: {', '.join(agents)}")

    signals = generate_signal_stream(
        agents=agents,
        num_signals=args.num_signals,
        time_span_minutes=args.time_span,
        anomaly_rate=args.anomaly_rate
    )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(signals, f, indent=2)
        print(f"\n✅ Signals saved to {args.output}")
        print(f"   Total: {len(signals)} signals")
    elif args.send:
        print(f"\n📤 Sending {len(signals)} signals to {args.api_url}...")
        send_signals_to_api(signals, args.api_url)
    else:
        print(f"\nSample signal:")
        print(json.dumps(signals[0], indent=2))
        print(f"\n💡 Use --send to post to API or --output <file> to save to JSON")


if __name__ == "__main__":
    main()
