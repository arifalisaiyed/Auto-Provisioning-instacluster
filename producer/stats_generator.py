import random
from datetime import datetime, timezone

SERVERS = ["web-01", "web-02", "db-01", "db-02", "cache-01"]

# Normal operating ranges per server
_BASELINES = {
    "web-01":   dict(cpu=(20, 55), mem=(40, 65), disk=(30, 50), net_in=(500_000, 2_000_000),   net_out=(200_000, 1_000_000)),
    "web-02":   dict(cpu=(20, 55), mem=(40, 65), disk=(30, 50), net_in=(500_000, 2_000_000),   net_out=(200_000, 1_000_000)),
    "db-01":    dict(cpu=(30, 70), mem=(50, 80), disk=(40, 70), net_in=(1_000_000, 5_000_000), net_out=(500_000, 2_000_000)),
    "db-02":    dict(cpu=(30, 70), mem=(50, 80), disk=(40, 70), net_in=(1_000_000, 5_000_000), net_out=(500_000, 2_000_000)),
    "cache-01": dict(cpu=(10, 40), mem=(60, 85), disk=(20, 35), net_in=(2_000_000, 8_000_000), net_out=(1_000_000, 4_000_000)),
}

_ANOMALY_WEIGHTS = [("high_cpu", 0.40), ("high_memory", 0.30), ("disk_nearly_full", 0.20), ("network_spike", 0.10)]
_ANOMALY_PROB = 0.20  # 20% chance per server per run


def _pick_anomaly_type():
    r = random.random()
    cumulative = 0.0
    for name, weight in _ANOMALY_WEIGHTS:
        cumulative += weight
        if r < cumulative:
            return name
    return "high_cpu"


def _apply_anomaly(stats: dict, anomaly_type: str) -> dict:
    if anomaly_type == "high_cpu":
        stats["cpu_percent"] = round(random.uniform(86, 99), 1)
    elif anomaly_type == "high_memory":
        stats["memory_percent"] = round(random.uniform(91, 99), 1)
    elif anomaly_type == "disk_nearly_full":
        stats["disk_percent"] = round(random.uniform(96, 99.5), 1)
    elif anomaly_type == "network_spike":
        stats["bytes_in"] = random.randint(50_000_000, 200_000_000)
        stats["bytes_out"] = random.randint(20_000_000, 80_000_000)
    return stats


def generate_all_stats() -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    results = []

    for server_id in SERVERS:
        b = _BASELINES[server_id]
        stats = {
            "server_id":       server_id,
            "collected_at":    now,
            "cpu_percent":     round(random.uniform(*b["cpu"]), 1),
            "memory_percent":  round(random.uniform(*b["mem"]), 1),
            "disk_percent":    round(random.uniform(*b["disk"]), 1),
            "bytes_in":        random.randint(*b["net_in"]),
            "bytes_out":       random.randint(*b["net_out"]),
            "is_anomaly":      False,
            "anomaly_type":    None,
        }

        if random.random() < _ANOMALY_PROB:
            anomaly_type = _pick_anomaly_type()
            stats = _apply_anomaly(stats, anomaly_type)
            stats["is_anomaly"] = True
            stats["anomaly_type"] = anomaly_type

        results.append(stats)

    return results
