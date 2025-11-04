"""
Kafka streaming simulator for testing signal ingestion via Kafka.
Generates synthetic data and publishes to Kafka topic.
"""
import time
import argparse
import sys
from datetime import datetime
from scripts.generate_synthetic_data import generate_signal_event, AGENTS
from app.services.kafka_service import get_producer, close_kafka_connections


def main():
    """Main entry point for Kafka simulator."""
    parser = argparse.ArgumentParser(
        description="Simulate signal streaming via Kafka"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Interval between signals in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=",".join(AGENTS),
        help="Comma-separated agent names"
    )
    parser.add_argument(
        "--broker",
        default="localhost:9092",
        help="Kafka broker address"
    )
    parser.add_argument(
        "--topic",
        default="signals",
        help="Kafka topic name"
    )

    args = parser.parse_args()
    agents = [a.strip() for a in args.agents.split(",")]

    print(f"🔌 Initializing Kafka producer...")
    producer = get_producer(args.broker, args.topic)

    if not producer.producer:
        print("❌ Failed to connect to Kafka broker")
        print(f"   Ensure Kafka is running at {args.broker}")
        return

    print(f"✅ Connected to Kafka broker at {args.broker}")
    print(f"📤 Publishing to topic: {args.topic}")
    print(f"⏱️  Duration: {args.duration}s | Interval: {args.interval}s")
    print(f"🤖 Agents: {', '.join(agents)}")
    print("Press Ctrl+C to stop\n")

    start_time = time.time()
    count = 0

    try:
        while time.time() - start_time < args.duration:
            import random
            agent = random.choice(agents)

            signal = generate_signal_event(agent)

            if producer.send_signal(signal):
                count += 1
                print(
                    f"[{count}] {signal['agent']:12} | "
                    f"Signal: {signal['signal_strength']:.3f} | "
                    f"State: {signal['user_state']:8} | "
                    f"HRV: {signal['biometric_data']['hrv']:.0f}"
                )
            else:
                print(f"❌ Failed to send signal for {agent}")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
    finally:
        close_kafka_connections()
        elapsed = time.time() - start_time
        print(f"\n✅ Simulation complete")
        print(f"   Total signals: {count}")
        print(f"   Duration: {elapsed:.2f}s")
        print(f"   Rate: {count/elapsed:.2f} signals/sec")


if __name__ == "__main__":
    main()
