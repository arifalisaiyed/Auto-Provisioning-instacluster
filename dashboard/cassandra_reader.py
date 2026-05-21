import os

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import RetryPolicy


def connect():
    contact_points = os.environ["CASSANDRA_CONTACT_POINTS"].split(",")
    port = int(os.getenv("CASSANDRA_PORT", "9042"))
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
    return cluster, session


def get_all_servers_latest(session) -> list[dict]:
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "infra_monitor")
    rows = session.execute(f"SELECT * FROM {keyspace}.server_latest")
    result = []
    for row in rows:
        result.append({
            "server_id":       row.server_id,
            "collected_at":    row.collected_at,
            "cpu_percent":     row.cpu_percent,
            "memory_percent":  row.memory_percent,
            "disk_percent":    row.disk_percent,
            "bytes_in":        row.bytes_in,
            "bytes_out":       row.bytes_out,
            "is_anomaly":      row.is_anomaly,
        })
    return sorted(result, key=lambda x: x["server_id"])


def get_recent_actions(session, limit: int = 20) -> list[dict]:
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "infra_monitor")
    # Query each server partition and merge — Cassandra doesn't support ORDER BY across partitions
    servers = ["web-01", "web-02", "db-01", "db-02", "cache-01"]
    all_actions = []

    for server_id in servers:
        rows = session.execute(
            f"SELECT * FROM {keyspace}.remediation_actions WHERE server_id = %s LIMIT %s",
            (server_id, limit),
        )
        for row in rows:
            all_actions.append({
                "server_id":    row.server_id,
                "actioned_at":  row.actioned_at,
                "triggered_by": row.triggered_by,
                "action_taken": row.action_taken,
                "diagnosis":    row.diagnosis,
                "cpu_percent":  row.cpu_percent,
                "disk_percent": row.disk_percent,
                "memory_percent": row.memory_percent,
            })

    all_actions.sort(key=lambda x: x["actioned_at"], reverse=True)
    return all_actions[:limit]
