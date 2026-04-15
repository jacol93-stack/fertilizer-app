"""VPS metrics collection — reads from host /proc when mounted, falls back gracefully."""

from __future__ import annotations

import os
import re
from pathlib import Path


def _host_proc() -> str:
    return os.environ.get("HOST_PROC", "/proc")


def _host_root() -> str:
    return os.environ.get("HOST_ROOT", "/")


def get_cpu_percent() -> float | None:
    """Read CPU usage from /proc/stat (average across all cores).

    Returns a percentage 0-100 based on the delta between two reads.
    Since we only have a snapshot, we return the idle ratio from boot.
    For more accuracy, the background collector stores history.
    """
    try:
        stat_path = Path(_host_proc()) / "stat"
        line = stat_path.read_text().splitlines()[0]  # cpu  user nice system idle ...
        parts = line.split()
        if parts[0] != "cpu":
            return None
        values = [int(v) for v in parts[1:]]
        idle = values[3]
        total = sum(values)
        if total == 0:
            return 0.0
        return round((1 - idle / total) * 100, 1)
    except Exception:
        return None


def get_memory_info() -> dict | None:
    """Read memory from /proc/meminfo. Returns used_mb, total_mb, percent."""
    try:
        meminfo_path = Path(_host_proc()) / "meminfo"
        text = meminfo_path.read_text()
        data = {}
        for line in text.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                data[key] = int(parts[1])  # value in kB

        total_kb = data.get("MemTotal", 0)
        available_kb = data.get("MemAvailable", data.get("MemFree", 0))
        used_kb = total_kb - available_kb

        total_mb = total_kb // 1024
        used_mb = used_kb // 1024
        percent = round((used_kb / total_kb) * 100, 1) if total_kb else 0.0

        return {
            "memory_used_mb": used_mb,
            "memory_total_mb": total_mb,
            "memory_percent": percent,
        }
    except Exception:
        return None


def get_disk_info() -> dict | None:
    """Read disk usage via os.statvfs on the host root."""
    try:
        root = _host_root()
        st = os.statvfs(root)
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        used = total - free

        total_gb = round(total / (1024 ** 3), 2)
        used_gb = round(used / (1024 ** 3), 2)
        percent = round((used / total) * 100, 1) if total else 0.0

        return {
            "disk_used_gb": used_gb,
            "disk_total_gb": total_gb,
            "disk_percent": percent,
        }
    except Exception:
        return None


def get_uptime() -> dict | None:
    """Read uptime from /proc/uptime. Returns seconds and human-readable string."""
    try:
        uptime_path = Path(_host_proc()) / "uptime"
        text = uptime_path.read_text().strip()
        seconds = int(float(text.split()[0]))

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        parts = []
        if days:
            parts.append(f"{days}d")
        parts.append(f"{hours}h")
        parts.append(f"{minutes}m")

        return {
            "uptime_seconds": seconds,
            "uptime_human": " ".join(parts),
        }
    except Exception:
        return None


def get_network_bytes() -> dict | None:
    """Read network bytes from /proc/net/dev. Returns total sent/recv across all non-lo interfaces."""
    try:
        net_path = Path(_host_proc()) / "net" / "dev"
        text = net_path.read_text()
        total_recv = 0
        total_sent = 0

        for line in text.splitlines()[2:]:  # skip header lines
            parts = line.split()
            if len(parts) < 10:
                continue
            iface = parts[0].rstrip(":")
            if iface == "lo":
                continue
            total_recv += int(parts[1])
            total_sent += int(parts[9])

        return {
            "net_bytes_sent": total_sent,
            "net_bytes_recv": total_recv,
        }
    except Exception:
        return None


def get_all_metrics() -> dict:
    """Collect all VPS metrics. Returns a flat dict suitable for DB insertion or API response."""
    result = {}

    cpu = get_cpu_percent()
    if cpu is not None:
        result["cpu_percent"] = cpu

    mem = get_memory_info()
    if mem:
        result.update(mem)

    disk = get_disk_info()
    if disk:
        result.update(disk)

    uptime = get_uptime()
    if uptime:
        result.update(uptime)

    net = get_network_bytes()
    if net:
        result.update(net)

    return result
