CPU_THRESHOLD      = 85.0   # percent
MEMORY_THRESHOLD   = 90.0   # percent
DISK_THRESHOLD     = 95.0   # percent
NETWORK_IN_THRESH  = 40_000_000   # bytes per sample
NETWORK_OUT_THRESH = 15_000_000   # bytes per sample


def check_thresholds(stats: dict) -> list[str]:
    triggered = []
    if stats.get("cpu_percent", 0) > CPU_THRESHOLD:
        triggered.append("cpu")
    if stats.get("memory_percent", 0) > MEMORY_THRESHOLD:
        triggered.append("memory")
    if stats.get("disk_percent", 0) > DISK_THRESHOLD:
        triggered.append("disk")
    if stats.get("bytes_in", 0) > NETWORK_IN_THRESH:
        triggered.append("network_in")
    if stats.get("bytes_out", 0) > NETWORK_OUT_THRESH:
        triggered.append("network_out")
    return triggered
