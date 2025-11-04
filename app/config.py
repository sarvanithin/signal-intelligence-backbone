"""
Application configuration.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./signals.db")

# Environment
ENVIRONMENT = os.getenv("FASTAPI_ENV", "development")

# Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "signals")

# Drift Detection Parameters
DRIFT_WINDOW_MINUTES = 10
DRIFT_THRESHOLD_PERCENT = 15.0  # Flag 15%+ variance as decay
ANOMALY_THRESHOLD_PERCENT = 20.0  # More severe threshold for anomalies

# Signal Processing
MIN_SIGNALS_FOR_BASELINE = 5
