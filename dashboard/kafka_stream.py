import asyncio
import json
import logging
import os

from confluent_kafka import Consumer, KafkaError

log = logging.getLogger(__name__)


def _build_consumer() -> Consumer:
    servers  = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
    username = os.environ["KAFKA_SASL_USERNAME"]
    password = os.environ["KAFKA_SASL_PASSWORD"]
    protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_PLAINTEXT")
    mechanism = os.getenv("KAFKA_SASL_MECHANISM", "SCRAM-SHA-256")

    return Consumer({
        "bootstrap.servers":  servers,
        "group.id":           "dashboard-kafka-stream",
        "auto.offset.reset":  "latest",
        "security.protocol":  protocol,
        "sasl.mechanism":     mechanism,
        "sasl.username":      username,
        "sasl.password":      password,
        "enable.auto.commit": True,
    })


async def kafka_event_stream():
    """Async generator — yields SSE-formatted text for each Kafka message."""
    topic    = os.getenv("KAFKA_TOPIC", "server-stats")
    loop     = asyncio.get_event_loop()
    consumer = _build_consumer()
    consumer.subscribe([topic])
    log.info("SSE stream consumer subscribed to %s", topic)

    try:
        while True:
            msg = await loop.run_in_executor(None, lambda: consumer.poll(1.0))

            if msg is None:
                yield ": keepalive\n\n"
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                log.warning("Kafka stream error: %s", msg.error())
                yield f"event: error\ndata: {msg.error().str()}\n\n"
                continue

            try:
                payload = json.loads(msg.value().decode("utf-8"))
                yield f"data: {json.dumps(payload)}\n\n"
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                yield f"event: error\ndata: {exc}\n\n"
    finally:
        consumer.close()
        log.info("SSE stream consumer closed")
