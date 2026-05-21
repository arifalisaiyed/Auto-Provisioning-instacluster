import logging
import os
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from kafka_publisher import publish_stats
from stats_generator import generate_all_stats

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [producer] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def publish_job():
    logger.info("Generating stats for all servers...")
    stats = generate_all_stats()
    publish_stats(stats)


def main():
    interval = int(os.getenv("SERVER_POLL_INTERVAL_SECONDS", "300"))
    scheduler = BlockingScheduler()

    def _shutdown(signum, frame):
        logger.info("Shutting down producer...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # Fire immediately on startup, then repeat every interval seconds
    scheduler.add_job(publish_job, "interval", seconds=interval, id="publish")
    publish_job()

    logger.info("Producer started — publishing every %ds", interval)
    scheduler.start()


if __name__ == "__main__":
    main()
