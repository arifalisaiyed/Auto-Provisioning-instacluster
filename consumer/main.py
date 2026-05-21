import json
import logging
import os
import signal
import sys

from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv

from actions import execute_action
from cassandra_writer import connect, write_action, write_stats
from llm_diagnose import diagnose
from thresholds import check_thresholds

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [consumer] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def _build_consumer() -> Consumer:
    return Consumer({
        "bootstrap.servers":  os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "security.protocol":  os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL"),
        "sasl.mechanism":     os.getenv("KAFKA_SASL_MECHANISM", "PLAIN"),
        "sasl.username":      os.environ["KAFKA_SASL_USERNAME"],
        "sasl.password":      os.environ["KAFKA_SASL_PASSWORD"],
        "group.id":           os.getenv("KAFKA_CONSUMER_GROUP", "infra-monitor-consumer"),
        "auto.offset.reset":  "earliest",
    })


def main():
    cluster, session, keyspace = connect()
    consumer = _build_consumer()
    topic = os.getenv("KAFKA_TOPIC", "server-stats")
    consumer.subscribe([topic])

    running = True

    def _shutdown(signum, frame):
        nonlocal running
        logger.info("Shutting down consumer...")
        running = False

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Consumer started — listening on topic '%s'", topic)

    try:
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error("Kafka error: %s", msg.error())
                continue

            try:
                stats = json.loads(msg.value().decode("utf-8"))
                server_id = stats["server_id"]
                logger.info("Received stats for %s (anomaly=%s)", server_id, stats.get("is_anomaly"))

                write_stats(session, keyspace, stats)

                triggered = check_thresholds(stats)
                if not triggered:
                    continue

                logger.info("Thresholds breached for %s: %s — invoking LLM...", server_id, triggered)
                diagnosis_text, action = diagnose(stats, triggered)

                execute_action(server_id, action)
                write_action(session, keyspace, stats, diagnosis_text, action, triggered)

            except Exception as exc:
                logger.exception("Failed to process message: %s", exc)

    finally:
        consumer.close()
        cluster.shutdown()
        logger.info("Consumer stopped.")


if __name__ == "__main__":
    main()
