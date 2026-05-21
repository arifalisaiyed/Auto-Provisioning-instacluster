import logging
import os
from datetime import datetime

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import RetryPolicy
from cassandra.query import SimpleStatement

logger = logging.getLogger(__name__)

_DDL = [
    """
    CREATE KEYSPACE IF NOT EXISTS {keyspace}
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """,
    """
    CREATE TABLE IF NOT EXISTS {keyspace}.server_stats (
        server_id      TEXT,
        collected_at   TIMESTAMP,
        cpu_percent    DOUBLE,
        memory_percent DOUBLE,
        disk_percent   DOUBLE,
        bytes_in       BIGINT,
        bytes_out      BIGINT,
        is_anomaly     BOOLEAN,
        PRIMARY KEY (server_id, collected_at)
    ) WITH CLUSTERING ORDER BY (collected_at DESC)
      AND default_time_to_live = 86400
    """,
    """
    CREATE TABLE IF NOT EXISTS {keyspace}.server_latest (
        server_id      TEXT PRIMARY KEY,
        collected_at   TIMESTAMP,
        cpu_percent    DOUBLE,
        memory_percent DOUBLE,
        disk_percent   DOUBLE,
        bytes_in       BIGINT,
        bytes_out      BIGINT,
        is_anomaly     BOOLEAN
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS {keyspace}.remediation_actions (
        server_id      TEXT,
        actioned_at    TIMESTAMP,
        cpu_percent    DOUBLE,
        memory_percent DOUBLE,
        disk_percent   DOUBLE,
        bytes_in       BIGINT,
        bytes_out      BIGINT,
        diagnosis      TEXT,
        action_taken   TEXT,
        triggered_by   TEXT,
        PRIMARY KEY (server_id, actioned_at)
    ) WITH CLUSTERING ORDER BY (actioned_at DESC)
      AND default_time_to_live = 604800
    """,
]


def connect() -> tuple:
    contact_points = os.environ["CASSANDRA_CONTACT_POINTS"].split(",")
    port = int(os.getenv("CASSANDRA_PORT", "9042"))
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "infra_monitor")
    username = os.environ["CASSANDRA_USERNAME"]
    password = os.environ["CASSANDRA_PASSWORD"]

    profile = ExecutionProfile(retry_policy=RetryPolicy())
    auth = PlainTextAuthProvider(username=username, password=password)
    cluster = Cluster(
        contact_points,
        port=port,
        auth_provider=auth,
        execution_profiles={EXEC_PROFILE_DEFAULT: profile},
    )
    session = cluster.connect()

    for ddl in _DDL:
        session.execute(SimpleStatement(ddl.format(keyspace=keyspace)))
    logger.info("Cassandra schema initialised (keyspace: %s)", keyspace)

    return cluster, session, keyspace


def write_stats(session, keyspace: str, stats: dict) -> None:
    collected_at = datetime.fromisoformat(stats["collected_at"].replace("Z", "+00:00"))
    session.execute(
        f"INSERT INTO {keyspace}.server_stats "
        "(server_id, collected_at, cpu_percent, memory_percent, disk_percent, bytes_in, bytes_out, is_anomaly) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (stats["server_id"], collected_at,
         stats["cpu_percent"], stats["memory_percent"], stats["disk_percent"],
         stats["bytes_in"], stats["bytes_out"], stats["is_anomaly"]),
    )
    session.execute(
        f"INSERT INTO {keyspace}.server_latest "
        "(server_id, collected_at, cpu_percent, memory_percent, disk_percent, bytes_in, bytes_out, is_anomaly) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (stats["server_id"], collected_at,
         stats["cpu_percent"], stats["memory_percent"], stats["disk_percent"],
         stats["bytes_in"], stats["bytes_out"], stats["is_anomaly"]),
    )


def write_action(session, keyspace: str, stats: dict, diagnosis: str, action: str, triggered: list[str]) -> None:
    collected_at = datetime.fromisoformat(stats["collected_at"].replace("Z", "+00:00"))
    session.execute(
        f"INSERT INTO {keyspace}.remediation_actions "
        "(server_id, actioned_at, cpu_percent, memory_percent, disk_percent, "
        "bytes_in, bytes_out, diagnosis, action_taken, triggered_by) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (stats["server_id"], collected_at,
         stats["cpu_percent"], stats["memory_percent"], stats["disk_percent"],
         stats["bytes_in"], stats["bytes_out"],
         diagnosis, action, ", ".join(triggered)),
    )
