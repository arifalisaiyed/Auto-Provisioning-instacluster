import json
import logging
import os

from confluent_kafka import Producer

logger = logging.getLogger(__name__)


def _build_producer() -> Producer:
    config = {
        "bootstrap.servers":  os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "security.protocol":  os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL"),
        "sasl.mechanism":     os.getenv("KAFKA_SASL_MECHANISM", "PLAIN"),
        "sasl.username":      os.environ["KAFKA_SASL_USERNAME"],
        "sasl.password":      os.environ["KAFKA_SASL_PASSWORD"],
    }
    return Producer(config)


def _delivery_report(err, msg):
    if err:
        logger.error("Delivery failed for %s: %s", msg.key(), err)
    else:
        logger.debug("Delivered %s to %s [%d]", msg.key(), msg.topic(), msg.partition())


def publish_stats(stats_list: list[dict]) -> None:
    topic = os.getenv("KAFKA_TOPIC", "server-stats")
    producer = _build_producer()

    for stats in stats_list:
        payload = json.dumps(stats).encode("utf-8")
        key = stats["server_id"].encode("utf-8")
        producer.produce(topic, value=payload, key=key, callback=_delivery_report)
        logger.info("Queued stats for %s (anomaly=%s)", stats["server_id"], stats["is_anomaly"])

    producer.flush()
    logger.info("Flushed %d messages to topic '%s'", len(stats_list), topic)
