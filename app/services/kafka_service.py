"""
Kafka producer and consumer for streaming signal ingestion.
"""
import json
import logging
from typing import Optional, Callable
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from app.config import KAFKA_BROKER, KAFKA_TOPIC

logger = logging.getLogger(__name__)


class KafkaSignalProducer:
    """Producer for sending signals to Kafka."""

    def __init__(self, broker: str = KAFKA_BROKER, topic: str = KAFKA_TOPIC):
        """Initialize Kafka producer."""
        self.broker = broker
        self.topic = topic
        self.producer: Optional[KafkaProducer] = None

    def connect(self) -> bool:
        """Establish connection to Kafka broker."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.broker],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"Connected to Kafka broker at {self.broker}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            return False

    def send_signal(self, signal: dict) -> bool:
        """Send a signal event to Kafka."""
        if not self.producer:
            logger.error("Producer not connected")
            return False

        try:
            future = self.producer.send(
                self.topic,
                value=signal
            )
            # Wait for the message to be delivered
            future.get(timeout=10)
            logger.debug(f"Signal sent to {self.topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to send signal: {str(e)}")
            return False

    def close(self):
        """Close producer connection."""
        if self.producer:
            self.producer.close()
            logger.info("Producer closed")


class KafkaSignalConsumer:
    """Consumer for receiving signals from Kafka."""

    def __init__(self, broker: str = KAFKA_BROKER, topic: str = KAFKA_TOPIC):
        """Initialize Kafka consumer."""
        self.broker = broker
        self.topic = topic
        self.consumer: Optional[KafkaConsumer] = None

    def connect(self) -> bool:
        """Establish connection to Kafka broker."""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=[self.broker],
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='signal-intelligence-backbone',
                consumer_timeout_ms=1000
            )
            logger.info(f"Connected to Kafka topic {self.topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            return False

    def consume_signals(
        self,
        callback: Callable[[dict], None],
        max_messages: Optional[int] = None
    ) -> int:
        """
        Consume signals from Kafka and call callback for each.

        Args:
            callback: Function to call for each signal
            max_messages: Maximum messages to consume (None = continuous)

        Returns:
            Number of messages consumed
        """
        if not self.consumer:
            logger.error("Consumer not connected")
            return 0

        count = 0
        try:
            for message in self.consumer:
                try:
                    callback(message.value)
                    count += 1
                    logger.debug(f"Processed signal {count}")

                    if max_messages and count >= max_messages:
                        break
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

            return count
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")
            return count

    def close(self):
        """Close consumer connection."""
        if self.consumer:
            self.consumer.close()
            logger.info("Consumer closed")


# Convenience functions
_producer: Optional[KafkaSignalProducer] = None
_consumer: Optional[KafkaSignalConsumer] = None


def get_producer(broker: str = KAFKA_BROKER, topic: str = KAFKA_TOPIC) -> KafkaSignalProducer:
    """Get or create Kafka producer singleton."""
    global _producer
    if _producer is None:
        _producer = KafkaSignalProducer(broker, topic)
        _producer.connect()
    return _producer


def get_consumer(broker: str = KAFKA_BROKER, topic: str = KAFKA_TOPIC) -> KafkaSignalConsumer:
    """Get or create Kafka consumer singleton."""
    global _consumer
    if _consumer is None:
        _consumer = KafkaSignalConsumer(broker, topic)
        _consumer.connect()
    return _consumer


def close_kafka_connections():
    """Close all Kafka connections."""
    global _producer, _consumer
    if _producer:
        _producer.close()
        _producer = None
    if _consumer:
        _consumer.close()
        _consumer = None
